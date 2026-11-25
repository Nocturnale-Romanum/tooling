"""Compose les glyphes de gregall absents de Hartker (pas d'exemplaire) à partir des formes de
base, avec les écarts typiques mesurés dans les composés placés d'après Hartker.

Usage (avec le Python de FontForge, sans -I) :
    ffpython S/composer_hors.py <police.sfd> [<glyphe> …] [--essai]

Sans glyphe : ceux de reference/decompositions.tsv sans exemplaire choisi, dont le premier plan
est vide et dont toutes les formes sont disponibles (tracées ou composées).

1. Écarts typiques (médianes) relevés dans les composés placés d'après leur exemplaire (bleus) :
   1er subpunctis / forme principale (centre du point moins bord droit et haut de la forme),
   subpunctis suivant / précédent (entre centres), dernier prepunctis / forme principale (bord
   gauche et bas), prepunctis précédent / suivant. Médiane par (famille, point) si au moins
   MIN_N cas, sinon par point toutes familles, sinon toutes mesures.
2. Une seule forme principale : elle garde sa hauteur propre ; les points sont posés d'après
   ces écarts. Sans forme principale (`su3`, `ppt2`…) : le premier point sert d'origine, les
   suivants d'après les écarts entre points ; le haut du groupe est calé sur le haut du gabarit.
   Variantes du trigon (`tgM`, `tgS1`, `tg1`…) : les trois premiers éléments aux places des
   trois points du `tg` composé ; `tg1` : le 4e point dans l'alignement des points 2 et 3.
   Plusieurs formes principales (`tv`, `bvB`, `poG`…) : faute de mesures, chaque forme est
   centrée sur le contour correspondant du gabarit gregall (contours rangés de gauche à droite).
3. Le groupe est calé à gauche sur le gabarit gregall et, verticalement, comme gregall pose ses
   éléments (caler_vertical) ; couleur cyan (composé hors Hartker,
   à vérifier).
"""
import collections
import csv
import os
import sys

import fontforge
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hartker as H  # noqa: E402

PTS = {"pu", "ta", "taN", "taNN", "suv1", "gr", "grN", "stB"}   # suv1 : forme taNN
COMPOSE_HARTKER = 0x80C0FF
COULEUR = 0x80FFFF
MIN_N = 3
SAUF = {"tgSsuu1", "clN1su2"}   # construit à la main ; décomposition douteuse (marteo, 24 novembre 2026)


def lire():
    dec = {r["glyphe"]: r for r in csv.DictReader(open(os.path.join(H.SKILL, "reference", "decompositions.tsv"),
                                                     encoding="utf-8"), delimiter="\t")}
    cho = {r["glyph"] for r in csv.DictReader(open(os.path.join(H.SKILL, "sources", "exemplaires.csv"),
                                                   encoding="utf-8")) if r["role"] == "choisi"}
    return dec, cho


def parts_of(r):
    return [p.strip() for p in r["decomposition"].split("+")]


def boxes(f):
    cache = {}

    def b(n):
        if n not in cache:
            cache[n] = f[n].boundingBox()
        return cache[n]
    return b


def elements(f, g, parts, box):
    """Éléments posés d'un composé, dans l'ordre de la décomposition (FontForge réordonne les
    références : les éléments de même nom sont rangés de gauche à droite)."""
    by = collections.defaultdict(list)
    for r in g.references:
        b = box(r[0])
        by[r[0]].append((r[0], b[0] + r[1][4], b[1] + r[1][5], b[2] + r[1][4], b[3] + r[1][5]))
    if sorted(parts) != sorted(n for n, v in by.items() for _ in v):
        return None
    for v in by.values():
        v.sort(key=lambda e: e[1] + e[3])
    cnt, el = collections.Counter(), []
    for p in parts:
        el.append(by[p][cnt[p]])
        cnt[p] += 1
    return el


def cen(e):
    return (e[1] + e[3]) / 2, (e[2] + e[4]) / 2


def mesurer(f, dec):
    box = boxes(f)
    m = {k: collections.defaultdict(list) for k in ("first", "step", "pre", "prestep")}
    for g in f.glyphs():
        if g.color != COMPOSE_HARTKER or not g.references or g.glyphname not in dec:
            continue
        el = elements(f, g, parts_of(dec[g.glyphname]), box)
        if not el:
            continue
        mains = [i for i, e in enumerate(el) if e[0] not in PTS]
        if len(mains) != 1:
            continue
        i0 = mains[0]
        M = el[i0]
        fam = M[0][:2]
        for i in range(i0 + 1, len(el)):
            cx, cy = cen(el[i])
            if i == i0 + 1:
                m["first"][(fam, el[i][0])].append((cx - M[3], cy - M[4]))
            else:
                px, py = cen(el[i - 1])
                m["step"][(el[i - 1][0], el[i][0])].append((cx - px, cy - py))
        for i in range(i0 - 1, -1, -1):
            cx, cy = cen(el[i])
            if i == i0 - 1:
                m["pre"][(fam, el[i][0])].append((cx - M[1], cy - M[2]))
            else:
                nx, ny = cen(el[i + 1])
                m["prestep"][(el[i][0], el[i + 1][0])].append((cx - nx, cy - ny))
    return m


def mediane(d, a, b):
    """Médiane pour (a, b), sinon b seul (a quelconque), sinon a seul, sinon tout."""
    for keys in ([(a, b)], [k for k in d if k[1] == b], [k for k in d if k[0] == a], list(d)):
        v = [x for k in keys for x in d.get(k, [])]
        if len(v) >= MIN_N or (keys == list(d) and v):
            return np.median(np.array(v), 0)
    return np.array([0.0, 0.0])


def placer(f, n, parts, m, box, tg_pts):
    """[(forme, dx, dy)] ou raison d'échec."""
    mains = [i for i, p in enumerate(parts) if p not in PTS]
    pos = {}                                     # i -> centre visé (x, y)
    if n.startswith("tg") and not mains:
        if not tg_pts:
            return None, "tg non composé"
        for i in range(min(3, len(parts))):
            pos[i] = tg_pts[i]
        if n == "tg1":
            (x2, y2), (x3, y3) = tg_pts[1], tg_pts[2]
            pos[3] = (2 * x3 - x2, 2 * y3 - y2)
        elif len(parts) > 3:
            return None, "variante du trigon à plus de trois éléments"
    elif len(mains) == 1:
        i0 = mains[0]
        b = box(parts[i0])
        M = (parts[i0], b[0], b[1], b[2], b[3])
        fam = parts[i0][:2]
        pos[i0] = cen(M)
        for i in range(i0 + 1, len(parts)):
            if i == i0 + 1:
                d = mediane(m["first"], fam, parts[i])
                pos[i] = (M[3] + d[0], M[4] + d[1])
            else:
                d = mediane(m["step"], parts[i - 1], parts[i])
                pos[i] = (pos[i - 1][0] + d[0], pos[i - 1][1] + d[1])
        for i in range(i0 - 1, -1, -1):
            if i == i0 - 1:
                d = mediane(m["pre"], fam, parts[i])
                pos[i] = (M[1] + d[0], M[2] + d[1])
            else:
                d = mediane(m["prestep"], parts[i], parts[i + 1])
                pos[i] = (pos[i + 1][0] + d[0], pos[i + 1][1] + d[1])
    elif not mains:
        pos[0] = (0.0, 0.0)
        su = n.startswith("su")
        for i in range(1, len(parts)):
            if su:
                d = mediane(m["step"], parts[i - 1], parts[i])
            else:                                 # prepunctis, de gauche à droite
                d = -mediane(m["prestep"], parts[i - 1], parts[i])
            pos[i] = (pos[i - 1][0] + d[0], pos[i - 1][1] + d[1])
    else:
        cs = sorted(f[n].layers["gregall"], key=lambda c: c.boundingBox()[0])
        if len(cs) != len(parts):
            return None, "%d contours gregall pour %d formes" % (len(cs), len(parts))
        for i, c in enumerate(cs):
            b = c.boundingBox()
            pos[i] = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    refs = []
    for i, p in enumerate(parts):
        b = box(p)
        if len(mains) == 1 and i == mains[0]:
            refs.append((p, 0.0, 0.0))
        else:
            refs.append((p, pos[i][0] - (b[0] + b[2]) / 2, pos[i][1] - (b[1] + b[3]) / 2))
    # calage : à gauche sur le gabarit ; sans forme principale, haut sur haut
    gx0, gy0, gx1, gy1 = f[n].layers["gregall"].boundingBox()
    lo = min(dx + box(p)[0] for p, dx, dy in refs)
    sx = gx0 - lo
    sy = 0.0
    if not mains or (n.startswith("tg") and not mains):
        hi = max(dy + box(p)[3] for p, dx, dy in refs)
        sy = gy1 - hi
    if len(mains) > 1:
        sx = 0.0
    refs = [(p, dx + sx, dy + sy) for p, dx, dy in refs]
    s = caler_vertical(f, f[n], refs, box)
    return [(p, dx, dy + s) for p, dx, dy in refs], None


def caler_vertical(f, g, refs, box):
    """Décalage vertical qui pose le composé comme gregall pose le sien : éléments et contours du
    gabarit rangés de gauche à droite, médiane des écarts entre centres ; si leurs nombres
    diffèrent, centre de la boîte sur centre du gabarit. gregall surélève la forme principale de ses
    composés (médiane +151 unités) : la garder à sa hauteur propre mettait les composés trop bas
    (marteo, 25 novembre 2026)."""
    els = sorted(refs, key=lambda e: box(e[0])[0] + e[1])
    ours = [(box(p)[1] + box(p)[3]) / 2 + dy for p, dx, dy in els]
    gc = sorted(g.layers["gregall"], key=lambda c: c.boundingBox()[0])
    if gc and len(gc) == len(ours):
        return float(np.median(np.array([(c.boundingBox()[1] + c.boundingBox()[3]) / 2 for c in gc]) - np.array(ours)))
    gb = g.layers["gregall"].boundingBox()
    lo = min(box(p)[1] + dy for p, dx, dy in refs)
    hi = max(box(p)[3] + dy for p, dx, dy in refs)
    return ((gb[1] + gb[3]) - (lo + hi)) / 2


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    essai = "--essai" in sys.argv
    sfd, noms = args[0], args[1:]
    dec, cho = lire()
    f = fontforge.open(sfd)
    dispo = lambda p: p in f and (len(f[p].foreground) > 0 or bool(f[p].references))
    if not noms:
        noms = [n for n, r in dec.items() if n in f and n not in cho and not len(f[n].foreground)
                and not f[n].references and r["statut"] not in ("base", "ligature")
                and "+" in r["decomposition"] and n not in SAUF]
    m = mesurer(f, dec)
    box = boxes(f)
    tg = f["tg"]
    el = elements(f, tg, ["pu", "pu", "pu"], box) if tg.references else None
    tg_pts = [cen(e) for e in el] if el else None
    faits, echecs = [], []
    for n in noms:
        parts = parts_of(dec[n])
        miss = [p for p in dict.fromkeys(parts) if not dispo(p)]
        if miss:
            echecs.append("%s (formes manquantes : %s)" % (n, " ".join(miss)))
            continue
        refs, why = placer(f, n, parts, m, box, tg_pts)
        if not refs:
            echecs.append("%s (%s)" % (n, why))
            continue
        if not essai:
            g = f[n]
            g.references = tuple((p, (1, 0, 0, 1, round(dx), round(dy))) for p, dx, dy in refs)
            g.color = COULEUR
            note = "Composé hors Hartker (composer_hors.py, écarts typiques), à vérifier"
            g.comment = "\n".join([l for l in (g.comment or "").split("\n") if l and "composer_hors" not in l] + [note])
        faits.append(n)
    print("composés : %d" % len(faits))
    print("   ", " ".join(faits))
    print("non composés : %d" % len(echecs))
    for e in echecs:
        print("   ", e)
    if not essai:
        f.save(sfd)


if __name__ == "__main__":
    main()
