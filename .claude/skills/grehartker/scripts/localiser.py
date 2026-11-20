"""Retrouve dans Hartker un neume déjà transcrit dans NR, avec le moins de vision possible.

Usage (Python ordinaire) :
    python -I S/localiser.py <glyphe> [--n 4] [--nom NOM] [--toutes] [--autre]
    python -I S/localiser.py --test          validation sur des cas connus (clS1, clM, scB)

Méthode :
1. occurrences du glyphe dans les transcriptions NR, une par pièce (hartker.piece_rows : marteo
   d'abord), hors NABC synthétique (entre `ob` et `cb`) ;
2. page de Hartker de la pièce (sources/pieces_nr.tsv, base du site) et rang de la pièce sur la
   page dans l'index de Cantus (sources/cantus_hartker.tsv, par le cantus_id) ;
3. au plus --n occurrences sur des pages éloignées (les autres sont gardées en secours) ;
4. localisation sans regarder la page : les composantes d'encre de la page (et de la suivante),
   rangées par lignes de neumes puis de gauche à droite, sont classées grossièrement (point,
   tractulus, virga, neume) ; la suite des glyphes NR de la pièce, décomposés en formes de base
   (reference/decompositions.tsv), est classée de même ; la pièce entière est alignée à partir
   de chaque départ possible (marques rouges R/A de S/marques.py, initiales noires, débuts de
   ligne), avec le rang Cantus comme a priori (place_by_marks) ; à défaut, alignement local
   (Smith-Waterman) sur toute la page et la suivante (place_whole) ;
5. sortie : cache/candidats/<nom>.json (boîte de la fenêtre et, si l'alignement est sûr, du neume)
   et cache/candidats/<nom>.png, planche des fenêtres pour marteo, avec pièce, syllabe, contexte
   NABC et score de confiance. Les boîtes de la liste se passent à retenir.py.
"""
import argparse
import csv
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402

SKIP = re.compile(r"^(ls|lt)|^(ob|cb|ni)$")
POINTS = {"pu", "stB", "st", "stN"}
TRAITS = {"ta", "taN", "taNN", "gr", "grN", "taB"}
VIRGAS = {"vi", "viN", "viB", "viNB", "vs", "vsN", "vsB"}


# ---------------------------------------------------------------- classes de formes
def decompositions():
    with open(os.path.join(H.SKILL, "reference", "decompositions.tsv"), encoding="utf-8") as f:
        return {r["glyphe"]: [t.strip().split("@")[0].rstrip("?") for t in r["decomposition"].split(" + ")]
                for r in csv.DictReader(f, delimiter="\t")}


def form_class(form):
    if form.startswith("ls") or form in ("ob", "cb", "ni"):
        return None
    if form in POINTS:
        return "p"
    if form in TRAITS:
        return "t"
    if form in VIRGAS:
        return "v"
    return "n"


_T = {}


def templates(seg):
    """Gabarits des formes de base qui ont un exemplaire choisi (sources/exemplaires.csv)."""
    if not _T:
        decs = decompositions()
        formes = {f for v in decs.values() for f in v}
        with open(os.path.join(H.SKILL, "sources", "exemplaires.csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["glyph"] in formes and r["role"] == "choisi" and (r["manuscript"], r["page"]) in seg:
                    box = [int(v) for v in r["base"].split(",")] if r["base"] else [int(r[k]) for k in "xywh"]
                    c = H.comp_in(seg, r["manuscript"], r["page"], *box)
                    if c is not None and c["h"] >= 30:
                        _T[r["glyph"]] = H.template(c)
    return _T


def label(c, T):
    """Nom de la forme la plus ressemblante (si assez sûre), sinon classe grossière."""
    if c["h"] >= 30 and T:
        best = max(T, key=lambda g: H.score(c, [T[g]]))
        if H.score(c, [T[best]]) >= 0.35:
            return best
    return comp_class(c)


def coarse(lbl):
    return lbl if lbl in ("p", "t", "v", "n") else form_class(lbl)


def comp_class(c):
    h, w = c["h"], c["w"]
    if h <= 28 and w <= 30:
        return "p"
    if h <= 30 and w >= 1.6 * h:
        return "t"
    if h >= 38 and w <= 0.95 * h and w <= 60:
        return "v"
    return "n"


# ---------------------------------------------------------------- pièce : suite attendue
def piece_sequence(code, glyph, decs):
    """[(classe, glyphe, n° de syllabe, est_cible)] pour une pièce, sans le NABC synthétique ;
    et la liste des syllabes."""
    rows = H.piece_rows().get(code, [])
    seq, syls, synth = [], [], False
    for k, r in enumerate(rows):
        syls.append((r["syllabe"], r["nabc"]))
        for g in r["glyphes"].split():
            if g == "ob":
                synth = True
                continue
            if g == "cb":
                synth = False
                continue
            if synth or SKIP.search(g):
                continue
            for form in decs.get(g, [g]):
                cl = form_class(form)
                if cl:
                    seq.append((form if form in _T else cl, g, k, g == glyph))
    return seq, syls


def synthetic(code, k):
    """Le fragment k de la pièce est-il dans du NABC synthétique (entre ob et cb) ?"""
    inside = False
    for i, r in enumerate(H.piece_rows().get(code, [])):
        for g in r["glyphes"].split():
            if g == "ob":
                inside = True
            elif g == "cb":
                inside = False
            elif i == k:
                return inside
    return False


# ---------------------------------------------------------------- page : suite observée
_LINES = {}


def text_lines(key):
    """Centres (y, coordonnées de page) des lignes de texte de la page : profil d'encre forte,
    comme hartker.segment. Mis en cache dans cache/lignes_texte.json."""
    path = os.path.join(H.CACHE, "lignes_texte.json")
    if not _LINES and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            _LINES.update({tuple(k.split(":")): v for k, v in json.load(f).items()})
    if key not in _LINES:
        from PIL import Image
        from scipy import ndimage as ndi
        g = np.asarray(Image.open(H.download_band(*key)).convert("L").reduce(4)).astype(float)
        bg = ndi.median_filter(g[::2, ::2], size=15)
        bg = np.kron(bg, np.ones((2, 2)))[:g.shape[0], :g.shape[1]]
        strong = (bg - g) > 55
        prof = ndi.uniform_filter1d(strong.sum(1).astype(float), 11)
        text = prof > 0.35 * prof.max()
        lab, n = ndi.label(text)
        cents = [float(np.mean(np.nonzero(lab == i)[0])) * 4 + H.BAND[1] for i in range(1, n + 1)
                 if (lab == i).sum() * 4 >= 25]
        _LINES[key] = sorted(cents)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"%s:%s" % k: v for k, v in _LINES.items()}, f)
    return fill_lines(_LINES[key])


def fill_lines(tl):
    """Lignes de texte manquées par le profil (fréquent : 182 pages sur 241, souvent une ligne
    peu encrée) : un écart d'environ k interlignes (médiane) reçoit k - 1 lignes régulières."""
    if len(tl) < 4:
        return tl
    m = float(np.median(np.diff(tl)))
    out = [tl[0]]
    for a, b in zip(tl, tl[1:]):
        k = int(round((b - a) / m))
        if k >= 2 and abs((b - a) / k - m) < 0.2 * m:
            out += [a + (b - a) * i / k for i in range(1, k)]
        out.append(b)
    return out


def page_sequence(seg, key, T):
    """Composantes de la page rangées par ligne (chaque neume appartient à la ligne de texte
    située juste en dessous de son centre), puis de gauche à droite."""
    tl = text_lines(key)
    comps = [c for c in seg.get(key, []) if c["h"] >= 9 and c["w"] >= 9]
    out = []
    for c in comps:
        yc = c["y"] + c["h"] / 2
        li = next((i for i, t in enumerate(tl) if t > yc - 20), len(tl))
        out.append(dict(c, line=li, key=key, cls=label(c, T)))
    out.sort(key=lambda c: (c["line"], c["x"]))
    return out


# ---------------------------------------------------------------- alignement
def sim(x, y):
    if x == y:
        return 3 if x not in ("p", "t", "v", "n") else 1
    return 1 if coarse(x) == coarse(y) else -1


def align(a, b, gap=-1, local=True, mode=None):
    """Alignement de la pièce (a) sur la page (b). Modes : « local » (Smith-Waterman, par
    défaut), « fitting » (toute la pièce, n'importe où dans b), « ancre » (toute la pièce, à partir
    du début de b : segment qui commence à la marque de la pièce). Renvoie (score, couples (i, j)).
    Chaque ligne se calcule d'un coup : S[i, j] = max(D[j], S[i, j-1] + gap) est un maximum
    cumulé de D[k] + gap (j - k)."""
    mode = mode or ("local" if local else "fitting")
    n, m = len(a), len(b)
    bl = np.array(b, dtype=object)
    bc = np.array([coarse(x) for x in b], dtype=object)
    S = np.zeros((n + 1, m + 1), np.int32)
    T = np.zeros((n + 1, m + 1), np.int8)       # 1 diag, 2 haut, 3 gauche
    if mode != "local":
        S[1:, 0] = gap * np.arange(1, n + 1)
        T[1:, 0] = 2
    if mode == "ancre":
        S[0, 1:] = gap * np.arange(1, m + 1)
        T[0, 1:] = 3
    ramp = gap * np.arange(m + 1)
    for i in range(1, n + 1):
        ai = a[i - 1]
        fine = ai not in ("p", "t", "v", "n")
        sm = np.where(bl == ai, 3 if fine else 1, np.where(bc == coarse(ai), 1, -1)).astype(np.int32)
        diag = S[i - 1, :-1] + sm
        up = S[i - 1, 1:] + gap
        D = np.maximum(diag, up)
        if mode == "local":
            D = np.maximum(D, 0)
        full = np.concatenate(([S[i, 0]], D))
        row = np.maximum.accumulate(full - ramp) + ramp
        S[i, 1:] = row[1:]
        t = np.where(row[1:] == diag, 1, np.where(row[1:] == up, 2, 3))
        if mode == "local":
            t = np.where(row[1:] == 0, 0, t)
        T[i, 1:] = t
    if mode == "local":
        i, j = np.unravel_index(np.argmax(S), S.shape)
    else:
        i, j = n, int(np.argmax(S[n]))
    score = int(S[i, j])
    pairs = []
    while i > 0 and j >= 0:
        t = T[i, j]
        if t == 1:
            pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif t == 2 or (j == 0 and mode != "local"):
            i -= 1
        elif t == 3:
            j -= 1
        else:
            break
    return score, pairs[::-1]


def bande(key, line, xc, demi=850):
    """Fenêtre large : la bande de la ligne de neumes (de la ligne de texte au-dessus à celle du
    dessous), sur ±demi px autour de la position estimée. L'alignement peut se tromper de quelques
    neumes : la fenêtre les couvre, et marteo (ou un coup d'œil sur cette seule bande) tranche."""
    tl = text_lines(key)
    top = tl[line - 1] + 40 if 0 < line <= len(tl) else (tl[0] - 380 if tl else H.BAND[1])
    bot = tl[line] + 30 if line < len(tl) else top + 420
    x0 = int(max(H.BAND[0], xc - demi))
    x1 = int(min(H.BAND[0] + H.BAND[2], xc + demi))
    y0 = int(max(H.BAND[1], top))
    return "%d,%d,%d,%d" % (x0, y0, x1 - x0, int(bot) - y0)


def snap(seq, obs, idx, mapped, reach=30, ctx=5):
    """Recalage local : autour de la position alignée du glyphe, la composante qui porte sa
    première forme et dont le voisinage (formes avant et après, sans trou) ressemble le mieux."""
    i0 = idx[0]
    est = mapped.get(i0)
    if est is None:
        near = [i for i in mapped if abs(i - i0) <= 6]
        if not near:
            return None
        i = min(near, key=lambda i: abs(i - i0))
        est = mapped[i] + (i0 - i)
    first = seq[i0][0]
    best = None
    for j in range(max(0, est - reach), min(len(obs), est + reach + 1)):
        if coarse(obs[j]["cls"]) != coarse(first):
            continue
        sc = 0
        for d in range(-ctx, len(idx) + ctx):
            ii, jj = i0 + d, j + d
            if 0 <= ii < len(seq) and 0 <= jj < len(obs):
                w = 2 if 0 <= d < len(idx) else 1
                sc += w * sim(seq[ii][0], obs[jj]["cls"])
        sc -= 0.15 * abs(j - est)
        if best is None or sc > best[0]:
            best = (sc, j)
    return best[1] if best else None


def cantus_rank(code, ms, page):
    """(rang de la pièce sur la page, nombre de pièces de la page) d'après l'index Cantus."""
    pn = H.pieces_nr().get(code, {})
    cid = pn.get("cantus_id", "")
    path = os.path.join(H.SKILL, "sources", "cantus_hartker.tsv")
    with open(path, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f, delimiter="\t") if r["manuscript"] == ms and r["folio"] == page]
    rows.sort(key=lambda r: int(r["seq"] or 0))
    # NR donne un seul cantus_id pour le répons et son verset ; dans l'index, le verset est une
    # entrée à part dont le cantus_id est celui du répons suivi d'une lettre (007467a…)
    found = [k for k, r in enumerate(rows) if cid and re.fullmatch(re.escape(cid) + r"[a-z]?", r["cantus_id"])]
    if found:
        return found[0], len(rows)
    return None, len(rows)


def next_key(seg, ms, page):
    nxt = (ms, "%03d" % (int(page) + 1)) if page.isdigit() else None
    return nxt if nxt in seg else None


def place_whole(seg, ms, page, a, T):
    """Pièce alignée (localement) sur toute la page et la suivante."""
    keys = [(ms, page)] + [k for k in [next_key(seg, ms, page)] if k]
    obs = [c for k in keys for c in page_sequence(seg, k, T)]
    if not obs:
        return None
    score, pairs = align(a, [c["cls"] for c in obs])
    return obs, pairs, score, "page entière"


def mark_pos(m, tl):
    """(ligne, x) du début de la pièce d'après sa marque : ligne de texte de la marque (pour une
    initiale ornée, qui couvre plusieurs lignes : la première ligne de texte sous son sommet)."""
    if m["kind"] == "initiale":
        li = next((i for i, t in enumerate(tl) if t > m["y"]), len(tl) - 1)
    else:
        cy = m["y"] + m["h"] / 2
        li = int(np.argmin([abs(t - cy) for t in tl])) if tl else 0
    return li, m["x"] - 30


BONUS = 0.1        # départ = marque du rang Cantus, quand la page a autant de marques que de pièces
MIN_CONF = 0.2     # en dessous : alignement sur la page entière


def place_by_marks(seg, code, ms, page, a, T):
    """Pièce alignée à partir de son début : segment qui va du point de départ au bas de la page,
    puis sur la page suivante jusqu'à sa première marque (pièce à cheval sur deux pages ; l'index
    donne la page de début). Alignement ancré (toute la pièce, dès le début du segment).
    Départs essayés : marques rouges, grandes initiales noires, débuts de ligne ; score pénalisé
    selon l'écart entre la place du départ dans la page et le rang Cantus de la pièce (versets
    exceptés) ; si la page a autant de marques rouges que l'index a de pièces marquées, la
    marque de même rang reçoit un bonus (l'égalité peut être fortuite : pas de confiance
    aveugle). Confiance trop basse : None (le cas revient à l'alignement sur la page entière)."""
    import marques as M
    key = (ms, page)
    obs = page_sequence(seg, key, T)
    if not obs:
        return None
    tl = text_lines(key)
    marks = M.marques(ms, page)
    entries = [r for r in M.cantus_page(ms, page) if r["genre"] not in M.SANS_MARQUE]
    cid = H.pieces_nr().get(code, {}).get("cantus_id", "")
    rank = next((k for k, r in enumerate(entries) if cid and re.fullmatch(re.escape(cid) + r"[a-z]?", r["cantus_id"])), None)
    tail = []
    nk = next_key(seg, ms, page)
    if nk:
        nm = [mark_pos(m, text_lines(nk)) for m in M.marques(*nk)]
        stop = min(nm) if nm else (10 ** 6, 0)
        tail = [c for c in page_sequence(seg, nk, T) if (c["line"], c["x"]) < stop]
    exact = marks and rank is not None and len(marks) == len(entries)
    starts = [(mark_pos(m, tl), "marque rouge %d/%d" % (k + 1, len(marks)), BONUS if exact and k == rank else 0)
              for k, m in enumerate(marks)]
    starts += [(mark_pos(dict(m, kind="marque"), tl), "initiale noire", 0) for m in M.initiales_noires(ms, page)]
    starts += [((li, -10 ** 6), "début de ligne", 0) for li in sorted({c["line"] for c in obs})]
    prior = 0.3 if rank is not None else 0
    full = float(sum(3 if x not in ("p", "t", "v", "n") else 1 for x in a))
    expect = (rank + 0.5) / max(1, len(entries)) if rank is not None else 0
    best, seen = None, set()
    for pos, how, bonus in sorted(starts, key=lambda t: -t[2]):
        i0 = next((k for k, c in enumerate(obs) if (c["line"], c["x"]) >= pos), None)
        if i0 is None or i0 in seen:
            continue
        seen.add(i0)
        b = (obs[i0:] + tail)[:3 * len(a) + 60]
        score, pairs = align(a, [c["cls"] for c in b], mode="ancre")
        adj = score / full - prior * abs(i0 / len(obs) - expect) + bonus
        if best is None or adj > best[0]:
            best = (adj, b, pairs, score, how, i0 / len(obs))
    if best is None:
        return None
    _, b, pairs, score, how, frac = best
    return dict(placed=(b, pairs, score, how), sure=score / full >= MIN_CONF, frac=frac,
                expect=expect if rank is not None else None, n=len(obs))


def locate(seg, code, ms, page, glyph, decs, methode="marques"):
    """Place la pièce sur la page (et la suivante) ; renvoie une liste d'emplacements du glyphe."""
    T = templates(seg)
    seq, syls = piece_sequence(code, glyph, decs)
    if not seq:
        return []
    a = [s[0] for s in seq]
    pm = place_by_marks(seg, code, ms, page, a, T) if methode == "marques" else None
    placed = pm["placed"] if pm and pm["sure"] else None
    if placed is None:
        placed = place_whole(seg, ms, page, a, T)
        # repli peu sûr lui aussi : s'il tombe loin du rang Cantus attendu (> 30 % de la page),
        # garder le départ ancré, qui tient compte de ce rang
        if pm and pm["expect"] is not None and placed is not None:
            first = placed[1][0][1] if placed[1] else 0
            key0 = placed[0][first]["key"] if placed[0] else None
            pos = (sum(1 for c in placed[0][:first] if c["key"] == key0) / pm["n"]) if key0 == (ms, page) else 1.0
            if abs(pos - pm["expect"]) > 0.3:
                b, pairs, score, how = pm["placed"]
                placed = (b, pairs, score, how + " (confiance basse, rang Cantus)")
        placed = placed or (pm["placed"] if pm else None)
    if placed is None:
        return []
    obs, pairs, score, how = placed
    conf = score / float(sum(3 if x not in ("p", "t", "v", "n") else 1 for x in a))
    mapped = dict(pairs)
    out = []
    targets = sorted({s[2] for s in seq if s[3]})
    for k in targets:
        idx = [i for i, s in enumerate(seq) if s[2] == k and s[3]]
        j = snap(seq, obs, idx, mapped)
        if j is not None:
            mapped = dict(mapped)
            for d, i in enumerate(idx):
                if j + d < len(obs):
                    mapped[i] = j + d
        hits = [obs[mapped[i]] for i in idx if i in mapped]
        if not hits:
            # pas aligné : voisins alignés les plus proches
            near = sorted(mapped, key=lambda i: abs(i - idx[0]))[:2]
            hits = [obs[mapped[i]] for i in near]
            sure = False
        else:
            sure = True
        key = hits[0]["key"]
        hits = [h for h in hits if h["key"] == key]
        ctxi = [i for i, sq in enumerate(seq) if k - 2 <= sq[2] <= k + 2 and i in mapped and obs[mapped[i]]["key"] == key
                and obs[mapped[i]]["line"] == hits[0]["line"]]
        win = [obs[mapped[i]] for i in ctxi] + hits
        wx0, wy0 = min(h["x"] for h in win), min(h["y"] for h in win)
        wx1, wy1 = max(h["x"] + h["w"] for h in win), max(h["y"] + h["h"] for h in win)
        x0, y0 = min(h["x"] for h in hits), min(h["y"] for h in hits)
        x1, y1 = max(h["x"] + h["w"] for h in hits), max(h["y"] + h["h"] for h in hits)
        ctx = " ".join("%s(%s)" % (s, n) for s, n in syls[max(0, k - 2):k + 3])
        out.append(dict(manuscript=key[0], page=key[1], x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0),
                        fenetre=bande(key, hits[0]["line"], (x0 + x1) / 2, 1000 if conf >= 0.3 else 3000),
                        score=round(conf, 2), sur=sure, methode=how, syllabe=syls[k][0], nabc=syls[k][1], contexte=ctx,
                        piece="%s %s (%s)" % (code, H.pieces_nr().get(code, {}).get("incipit", "").split(" V")[0],
                                              re.sub(r"<[^>]*>", "", syls[k][0]))))
    return out


# ---------------------------------------------------------------- sélection et planche
def spread(items, n, offset=0.5):
    """n éléments sur des pages éloignées."""
    items = sorted(items, key=lambda t: (t["ms"], int(t["page"]) if t["page"].isdigit() else 0))
    if len(items) <= n:
        return items, []
    step = len(items) / n
    pick = [items[int(i * step + step * offset)] for i in range(n)]
    return pick, [t for t in items if t not in pick]


def ruler(im, x0, y0, w, h, step=100):
    """Graduation en coordonnées de page (x en haut, y à gauche), pour relever une position."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    for x in range((x0 // step + 1) * step, x0 + w, step):
        d.line((x - x0, 0, x - x0, 10), fill=(0, 0, 255), width=2)
        if x % 200 == 0:
            d.text((x - x0 + 2, 10), str(x), fill=(0, 0, 255), font=H.font(16))
    for y in range((y0 // step + 1) * step, y0 + h, step):
        d.line((0, y - y0, 10, y - y0), fill=(200, 0, 0), width=2)
        d.text((12, y - y0 - 8), str(y), fill=(200, 0, 0), font=H.font(16))


def sheet(nom, found, glyph=None):
    cells = []
    if glyph:
        try:
            cells.append(("gregall " + glyph + " (échelle de la page)", H.gregall_image(glyph, 100)))
        except KeyError:
            pass
    for i, f in enumerate(found):
        x, y, w, h = map(int, f["fenetre"].split(","))
        im = H.crop(f["manuscript"], f["page"], x, y, w, h, pad=0, zoom=1)
        ruler(im, x, y, w, h)
        if w > 2600:                       # ligne entière : deux demi-bandes l'une sous l'autre
            from PIL import Image
            half = w // 2 + 60
            a_, b_ = im.crop((0, 0, half, h)), im.crop((w - half, 0, w, h))
            im = Image.new("RGB", (half, 2 * h + 12), "white")
            im.paste(a_, (0, 0)); im.paste(b_, (0, h + 12))
        from PIL import ImageDraw
        d = ImageDraw.Draw(im)
        if w <= 2600:
            d.rectangle((f["x"] - x - 6, f["y"] - y - 6, f["x"] - x + f["w"] + 6, f["y"] - y + f["h"] + 6),
                        outline=(230, 140, 0), width=4)
        im.thumbnail((1700, 500))
        lab = "%d. %s p.%s  %s  [%s]   contexte : %s" % (i, f["manuscript"][-3:], f["page"].lstrip("0"), f["piece"][:45],
                                                          f["nabc"][:24], f["contexte"][:90])
        cells.append((lab, im))
    if cells:
        H.grid(cells, 1, nom + " : bandes localisées (orange : position estimée, à quelques neumes près)",
               cell_w=1720).save(os.path.join(H.CACHE, "candidats", nom + ".png"))


def run(glyph, n, nom, toutes=False, autre=False):
    seg = H.load_seg()
    decs = decompositions()
    pn = H.pieces_nr()
    occ = {}
    for code, syl, frag in H.occurrences(glyph):
        p = pn.get(code)
        if p and p["manuscript"] in ("csg-0390", "csg-0391"):
            occ.setdefault(code, p)
    items = [dict(code=c, ms=p["manuscript"], page=p["page"]) for c, p in occ.items()
             if not all(synthetic(c, k) for k, r in enumerate(H.piece_rows().get(c, [])) if glyph in r["glyphes"].split())]
    if autre:
        # autre série : pages pas encore montrées dans cache/candidats/<nom>.json
        prev = os.path.join(H.CACHE, "candidats", nom + ".json")
        shown = {(f["manuscript"], f["page"]) for f in json.load(open(prev, encoding="utf-8"))} if os.path.exists(prev) else set()
        items = [t for t in items if (t["ms"], t["page"]) not in shown]
        nom += "_b"
    pick, backup = (items, []) if toutes else spread(items, n, 0.25 if autre else 0.5)
    for t in pick:
        key = (t["ms"], t["page"])
        if key not in seg:
            H.download_band(*key)
    if any((t["ms"], t["page"]) not in seg for t in pick):
        import subprocess
        subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages.py"), "segmenter"])
        seg = H.load_seg()
    found = []
    for t in pick:
        for f in locate(seg, t["code"], t["ms"], t["page"], glyph, decs):
            if not synthetic(t["code"], next((k for k, (s, nb) in enumerate([(r["syllabe"], r["nabc"]) for r in H.piece_rows()[t["code"]]])
                                              if s == f["syllabe"] and nb == f["nabc"]), -1)):
                rk = cantus_rank(t["code"], t["ms"], t["page"])
                f["rang_cantus"] = "%s/%s" % rk if rk[0] is not None else ""
                found.append(f)
    out = os.path.join(H.CACHE, "candidats")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, nom + ".json"), "w", encoding="utf-8") as fh:
        json.dump(found, fh, indent=0, ensure_ascii=False)
    with open(os.path.join(out, nom + "_secours.json"), "w", encoding="utf-8") as fh:
        json.dump(backup, fh, indent=0)
    sheet(nom, found, glyph)
    for i, f in enumerate(found):
        print("%d. %s p.%s %s,%s,%s,%s conf %.2f %s  %s  [%s]" % (i, f["manuscript"][-3:], f["page"], f["x"], f["y"], f["w"], f["h"],
              f["score"], "aligné" if f["sur"] else "estimé", f["piece"][:50], f["nabc"]))
    synth = [c for c, p in occ.items() if all(synthetic(c, k) for k, r in enumerate(H.piece_rows().get(c, []))
                                              if glyph in r["glyphes"].split())]
    if synth:
        print("NABC synthétique (entre ob et cb), écarté :", " ".join(synth))
    print("%d pièces, %d retenues, %d en secours" % (len(items), len(pick), len(backup)))
    return found


TESTS = [("clS1", "0106I", "csg-0390", "072", (3564, 2478, 79, 59)),
         ("clM", "0118N3R1", "csg-0391", "088", (3303, 2922, 53, 81)),
         ("scB", "ODEFN3R3b", "csg-0391", "198", (4565, 4507, 142, 135))]


def test():
    seg = H.load_seg()
    decs = decompositions()
    for glyph, code, ms, page, (bx, by, bw, bh) in TESTS:
        res = locate(seg, code, ms, page, glyph, decs)
        best = None
        for f in res:
            dx = (f["x"] + f["w"] / 2) - (bx + bw / 2)
            dy = (f["y"] + f["h"] / 2) - (by + bh / 2)
            d = (dx * dx + dy * dy) ** 0.5
            if f["page"] == page and (best is None or d < best[0]):
                best = (d, f)
        if best:
            d, f = best
            print("%-5s %s p.%s : à %d px du neume connu (conf %.2f, %s, %d emplacement(s))"
                  % (glyph, ms[-3:], page, d, f["score"], "aligné" if f["sur"] else "estimé", len(res)))
        else:
            print("%-5s %s p.%s : non trouvé (%d emplacement(s))" % (glyph, ms[-3:], page, len(res)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glyphe", nargs="?")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--nom")
    ap.add_argument("--toutes", action="store_true")
    ap.add_argument("--autre", action="store_true", help="autre série : pages pas encore montrées (sortie <nom>_b)")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()
    if args.test:
        test()
    else:
        run(args.glyphe, args.n, args.nom or "loc_" + args.glyphe, args.toutes, args.autre)


if __name__ == "__main__":
    main()
