"""Retrouve dans Hartker un neume déjà transcrit dans NR, avec le moins de vision possible.

Usage (Python ordinaire) :
    python -I S/localiser.py <glyphe> [--n 4] [--nom NOM] [--toutes]
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
   (reference/decompositions.tsv), est classée de même ; un alignement local (Smith-Waterman)
   place la pièce sur la page, et donc le neume cherché. Le rang Cantus sert d'a priori quand
   plusieurs placements se valent ;
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
    return _LINES[key]


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


def align(a, b, gap=-1, local=True):
    """Alignement de la pièce (a) sur la page (b) : local (Smith-Waterman) par défaut, sinon
    « fitting » (toute la pièce). Renvoie (score, couples (i, j))."""
    n, m = len(a), len(b)
    S = np.zeros((n + 1, m + 1), np.int32)
    T = np.zeros((n + 1, m + 1), np.int8)       # 1 diag, 2 haut, 3 gauche
    if not local:
        S[1:, 0] = gap * np.arange(1, n + 1)
        T[1:, 0] = 2
    for i in range(1, n + 1):
        ai = a[i - 1]
        for j in range(1, m + 1):
            d = S[i - 1, j - 1] + sim(ai, b[j - 1])
            u = S[i - 1, j] + gap
            l = S[i, j - 1] + gap
            best, t = max((d, 1), (u, 2), (l, 3))
            if local and best <= 0:
                best, t = 0, 0
            S[i, j], T[i, j] = best, t
    if local:
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
        elif t == 2 or (j == 0 and not local):
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
    for k, r in enumerate(rows):
        if cid and r["cantus_id"] == cid:
            return k, len(rows)
    return None, len(rows)


def locate(seg, code, ms, page, glyph, decs):
    """Place la pièce sur la page (et la suivante) ; renvoie une liste d'emplacements du glyphe."""
    T = templates(seg)
    seq, syls = piece_sequence(code, glyph, decs)
    if not seq:
        return []
    keys = [(ms, page)]
    if page.isdigit():
        nxt = (ms, "%03d" % (int(page) + 1))
        if nxt in seg:
            keys.append(nxt)
    obs = [c for k in keys for c in page_sequence(seg, k, T)]
    if not obs:
        return []
    a = [s[0] for s in seq]
    b = [c["cls"] for c in obs]
    score, pairs = align(a, b)
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
                        score=round(conf, 2), sur=sure, syllabe=syls[k][0], nabc=syls[k][1], contexte=ctx,
                        piece="%s %s (%s)" % (code, H.pieces_nr().get(code, {}).get("incipit", "").split(" V")[0],
                                              re.sub(r"<[^>]*>", "", syls[k][0]))))
    return out


# ---------------------------------------------------------------- sélection et planche
def spread(items, n):
    """n éléments sur des pages éloignées."""
    items = sorted(items, key=lambda t: (t["ms"], int(t["page"]) if t["page"].isdigit() else 0))
    if len(items) <= n:
        return items, []
    step = len(items) / n
    pick = [items[int(i * step + step / 2)] for i in range(n)]
    return pick, [t for t in items if t not in pick]


def sheet(nom, found):
    cells = []
    for i, f in enumerate(found):
        x, y, w, h = map(int, f["fenetre"].split(","))
        im = H.crop(f["manuscript"], f["page"], x, y, w, h, pad=0, zoom=1)
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


def run(glyph, n, nom, toutes=False):
    seg = H.load_seg()
    decs = decompositions()
    pn = H.pieces_nr()
    occ = {}
    for code, syl, frag in H.occurrences(glyph):
        p = pn.get(code)
        if p and p["manuscript"] in ("csg-0390", "csg-0391"):
            occ.setdefault(code, p)
    items = [dict(code=c, ms=p["manuscript"], page=p["page"]) for c, p in occ.items()]
    pick, backup = (items, []) if toutes else spread(items, n)
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
    sheet(nom, found)
    for i, f in enumerate(found):
        print("%d. %s p.%s %s,%s,%s,%s conf %.2f %s  %s  [%s]" % (i, f["manuscript"][-3:], f["page"], f["x"], f["y"], f["w"], f["h"],
              f["score"], "aligné" if f["sur"] else "estimé", f["piece"][:50], f["nabc"]))
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
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()
    if args.test:
        test()
    else:
        run(args.glyphe, args.n, args.nom or "loc_" + args.glyphe, args.toutes)


if __name__ == "__main__":
    main()
