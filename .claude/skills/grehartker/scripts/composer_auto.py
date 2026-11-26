"""Compose automatiquement les glyphes composés à partir des formes de base déjà tracées, aux
positions relevées sur leur exemplaire choisi, et pose cet exemplaire en fond.

Usage (avec le Python de FontForge, sans -I) :
    ffpython S/composer_auto.py <police.sfd> [<glyphe> …] [--essai]

Sans glyphe : tous les glyphes de reference/decompositions.tsv qui ne sont ni des formes de base
ni des ligatures et ont un exemplaire choisi. Les glyphes dont le premier plan contient déjà un
tracé ou des références non posées par ce script (couleur autre que bleu) ne sont jamais touchés.
Ne relancer que sur des glyphes nommés : une passe sur tout recompose les composés bleus et efface
les recalages de marteo.

Pour chaque glyphe :
1. masque de l'exemplaire choisi (planche.whole, encre pâle comprise, colonne `exclure`
   respectée), découpé en composantes (taches de moins de MIN_PX pixels ignorées) ;
2. si toutes les formes de la décomposition sont disponibles (premier plan tracé, ou glyphe
   composé plus tôt dans la même passe) et que le nombre de composantes est celui des formes :
   la forme principale (la plus grande) va sur la plus grande composante, les autres, dans
   l'ordre de la décomposition, sur les autres composantes rangées de gauche à droite ; chaque
   forme est posée en référence, centre de son contour sur le centre de sa composante, à
   l'échelle commune (10 unités par pixel) ; la forme principale garde sa hauteur propre
   (décalage vertical nul) ; le groupe est centré horizontalement sur le gabarit gregall ;
   le glyphe passe en bleu (composé automatiquement, à vérifier) ;
3. dans tous les cas, l'exemplaire est importé en fond (calque Back, ×4, comme
   import_hartker.py) : calé sur les formes posées si le glyphe a été composé, sinon bas sur bas
   et centre sur centre du gabarit gregall.
--essai : n'écrit rien, affiche le bilan. --sans-fonds : compose sans importer les exemplaires.
"""
import csv
import os
import re
import sys

import fontforge
import numpy as np
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hartker as H  # noqa: E402
import planche as P  # noqa: E402
from import_hartker import fetch, MARGIN, IMG_SCALE  # noqa: E402

SCALE = 10.0
MIN_PX = 30
COMPOSE = 0x80C0FF          # composé automatiquement, à vérifier
CYAN = 0x80FFFF             # composé d'après gregall : recomposable d'après l'exemplaire
FOND_SEUL = 0xFF80C0        # fond posé, composition automatique impossible : à composer
TOL_PART = 4.0              # une forme secondaire ne doit pas être bien plus grande que sa composante


def lire():
    dec = {r["glyphe"]: r for r in csv.DictReader(open(os.path.join(H.SKILL, "reference", "decompositions.tsv"),
                                                     encoding="utf-8"), delimiter="\t")}
    cho = {r["glyph"]: r for r in csv.DictReader(open(os.path.join(H.SKILL, "sources", "exemplaires.csv"),
                                                     encoding="utf-8")) if r["role"] == "choisi"}
    return dec, cho


def composantes(r):
    """Composantes de l'exemplaire (coordonnées de page) : [(x0, y0, x1, y1, aire)]."""
    seg = H.load_seg([(r["manuscript"], r["page"])])
    x, y, w, h = (int(r[k]) for k in "xywh")
    wh = P.whole(seg, r, pale=True)
    m = wh["mask"]
    # origine du masque : même calcul que planche.whole (pale=True : boîte comprise)
    key = (r["manuscript"], r["page"])
    comps = [c for c in seg[key] if max(0, min(x + w, c["x"] + c["w"]) - max(x, c["x"]))
             * max(0, min(y + h, c["y"] + c["h"]) - max(y, c["y"])) >= 0.6 * c["w"] * c["h"]
             and not H.exclue(r, c)]
    ox = min([c["x"] for c in comps] + [x])
    oy = min([c["y"] for c in comps] + [y])
    lab, n = ndi.label(m, np.ones((3, 3), bool))
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        a = int((lab[sl] == i).sum())
        if a >= MIN_PX:
            out.append((sl[1].start + ox, sl[0].start + oy, sl[1].stop + ox, sl[0].stop + oy, a))
    return out


def bbox(g):
    """Boîte du contour d'une forme : premier plan tracé, ou références (glyphe composé)."""
    b = g.foreground.boundingBox() if len(g.foreground) else None
    if b is None or b == (0, 0, 0, 0):
        b = g.boundingBox()
    return b


def disponible(f, n, faits):
    return n in f and (len(f[n].foreground) > 0 or bool(f[n].references) or n in faits)


def fusionner(comps, n):
    """Tant qu'il y a plus de composantes que de formes, la plus petite (fragment d'un trait pâle,
    moins de la moitié de l'aire médiane) rejoint la composante la plus proche."""
    comps = list(comps)
    while len(comps) > n:
        i = min(range(len(comps)), key=lambda k: comps[k][4])
        if comps[i][4] >= 0.5 * float(np.median([c[4] for c in comps])):
            break
        c = comps.pop(i)
        d = lambda o: max(0, max(o[0], c[0]) - min(o[2], c[2])) + max(0, max(o[1], c[1]) - min(o[3], c[3]))
        j = min(range(len(comps)), key=lambda k: d(comps[k]))
        o = comps[j]
        comps[j] = (min(o[0], c[0]), min(o[1], c[1]), max(o[2], c[2]), max(o[3], c[3]), o[4] + c[4])
    return comps


def composer(f, g, parts, comps):
    """Références posées [(forme, dx, dy)] et passage page → police (X0, Y0), ou raison d'échec."""
    comps = fusionner(comps, len(parts))
    if len(comps) != len(parts):
        return None, "%d composantes pour %d formes" % (len(comps), len(parts))
    boxes = {p: bbox(f[p]) for p in set(parts)}
    area = lambda b: (b[2] - b[0]) * (b[3] - b[1])
    imain = max(range(len(parts)), key=lambda i: area(boxes[parts[i]]))
    cmain = max(range(len(comps)), key=lambda i: comps[i][4])
    rest_p = [i for i in range(len(parts)) if i != imain]
    rest_c = sorted([i for i in range(len(comps)) if i != cmain], key=lambda i: (comps[i][0] + comps[i][2]) / 2)
    assign = {imain: cmain}
    assign.update(dict(zip(rest_p, rest_c)))
    cen = lambda c: ((c[0] + c[2]) / 2, (c[1] + c[3]) / 2)
    mb = boxes[parts[imain]]
    mcx, mcy = (mb[0] + mb[2]) / 2, (mb[1] + mb[3]) / 2
    pcx, pcy = cen(comps[cmain])
    X0, Y0 = mcx - SCALE * pcx, mcy + SCALE * pcy           # police = (X0 + 10 x, Y0 - 10 y)
    refs = []
    for i, p in enumerate(parts):
        c = comps[assign[i]]
        cx, cy = cen(c)
        b = boxes[p]
        if i != imain:
            fw, fh = (b[2] - b[0]) / SCALE, (b[3] - b[1]) / SCALE
            if fw * fh > TOL_PART * max(1, (c[2] - c[0]) * (c[3] - c[1])):
                return None, "forme %s bien plus grande que sa composante" % p
        refs.append((p, X0 + SCALE * cx - (b[0] + b[2]) / 2, Y0 - SCALE * cy - (b[1] + b[3]) / 2))
    # groupe centré horizontalement sur le gabarit gregall
    gx0, _, gx1, _ = g.layers["gregall"].boundingBox()
    lo = min(dx + boxes[p][0] for p, dx, dy in refs)
    hi = max(dx + boxes[p][2] for p, dx, dy in refs)
    s = (gx0 + gx1) / 2 - (lo + hi) / 2
    refs = [(p, dx + s, dy) for p, dx, dy in refs]
    # verticalement : bas du premier élément (le plus à gauche) sur le bas du premier contour du
    # gabarit gregall ; le fond suit (marteo, 25 novembre 2026)
    first = min(refs, key=lambda e: boxes[e[0]][0] + e[1])
    gc = [c.boundingBox() for c in g.layers["gregall"]]
    v = (min(gc, key=lambda b: b[0])[1] - (boxes[first[0]][1] + first[2])) if gc else 0
    refs = [(p, dx, dy + v) for p, dx, dy in refs]
    return (refs, X0 + s, Y0 + v), None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    essai = "--essai" in sys.argv
    sans_fonds = "--sans-fonds" in sys.argv
    sfd, noms = args[0], args[1:]
    dec, cho = lire()
    f = fontforge.open(sfd)
    if not noms:
        from composer_hors import ligature
        noms = [n for n, r in dec.items() if r["statut"] not in ("base", "ligature", "statut") and n in cho
                and not ligature(n)]
    # ordre : les composés qui servent de forme à d'autres d'abord
    noms = sorted(noms, key=lambda n: sum(n in [p.strip() for p in dec[m]["decomposition"].split("+")]
                                          for m in noms if m in dec), reverse=True)
    faits, fonds, bilan = set(), [], {"composé": [], "fond seul": [], "déjà tracé": []}
    cache = os.path.join(H.SKILL, "cache", "decoupes")
    os.makedirs(cache, exist_ok=True)
    for n in noms:
        if n not in f or n not in cho:
            continue
        g, r = f[n], cho[n]
        if (len(g.foreground) > 0 or g.references) and g.color not in (COMPOSE, CYAN):   # tracé, ou composé à la main (pi, sa…)
            bilan["déjà tracé"].append(n)
            continue
        # « lsc@3 » : la lettre lsc (en position 3) ; sa place vient de l'exemplaire
        parts = [p.strip().split("@")[0] for p in dec[n]["decomposition"].split("+")] if n in dec else []
        from composer_hors import a_plat
        parts = a_plat(f, dec, parts)                    # formes composées dépliées (tgSN → pu pu taN)
        res, why = None, "formes manquantes : " + " ".join(p for p in parts if not disponible(f, p, faits))
        if parts and all(disponible(f, p, faits) for p in parts):
            res, why = composer(f, g, parts, composantes(r))
        x, y, w, h = (int(r[k]) for k in "xywh")
        if res:
            refs, X0, Y0 = res
            left, top = X0 + SCALE * (x - MARGIN), Y0 - SCALE * (y - MARGIN)
            if not essai:
                g.references = tuple((p, (1, 0, 0, 1, round(dx), round(dy))) for p, dx, dy in refs)
                g.color = COMPOSE
            faits.add(n)
            bilan["composé"].append(n)
        else:
            gx0, gy0, gx1, gy1 = g.layers["gregall"].boundingBox()
            left = (gx0 + gx1) / 2 - (MARGIN + w / 2) * SCALE
            top = gy0 + (MARGIN + h) * SCALE
            bilan["fond seul"].append("%s (%s)" % (n, why))
            if not essai and not g.references:
                g.color = FOND_SEUL
        if not essai and not sans_fonds:
            img = fetch(cache, r["manuscript"], r["page"], x - MARGIN, y - MARGIN, w + 2 * MARGIN, h + 2 * MARGIN)
            g.importOutlines(img)
            src = "Hartker %s p. %s, boite %d,%d,%d,%d" % (r["manuscript"], r["page"], x, y, w, h)
            note = src + (" ; composé automatiquement (composer_auto.py), à vérifier" if n in faits else "")
            lines = [l for l in (g.comment or "").split("\n") if l and not l.startswith("Hartker ")]
            g.comment = "\n".join(lines + [note])
            fonds.append((n, left, top))
    for k, v in bilan.items():
        print("%s : %d" % (k, len(v)))
        for x in v:
            print("   ", x)
    if essai:
        return
    f.save(sfd)
    f.close()
    place(sfd, fonds)


def place(sfd, fonds):
    """Échelle et position des images importées, fixées dans le .sfd (non exposées par l'API) ;
    seule la dernière image importée est gardée dans chaque glyphe. Une seule passe sur le texte
    (le fichier de travail dépasse 150 Mo : des copies successives épuisaient la mémoire)."""
    pos = {name: (left, top) for name, left, top in fonds}
    img = re.compile(r"^Image2: \S+ \d+ \S+ \S+ (\S+) \S+\n.*?^EndImage2\n", re.S | re.M)

    def fix(m):
        if m.group(1) not in pos:
            return m.group(0)
        left, top = pos[m.group(1)]
        block = m.group(0)
        images = list(img.finditer(block))
        if not images:
            return block
        fresh = [i for i in images if abs(float(i.group(1)) - IMG_SCALE) > 1e-6]
        last = fresh[0] if fresh else images[0]          # FontForge met la nouvelle image en tête
        new_img = re.sub(r"^Image2: (\S+) (\d+) \S+ \S+ \S+ \S+",
                         lambda k: "Image2: %s %s %g %g %g %g" % (k.group(1), k.group(2), left, top, IMG_SCALE, IMG_SCALE),
                         last.group(0), count=1, flags=re.M)
        start = images[0].start()
        rest = img.sub("", block[start:])
        return block[:start] + new_img + rest
    with open(sfd, encoding="latin-1") as fh:
        text = fh.read()
    text = re.sub(r"^StartChar: (\S+)\n.*?^EndChar\n", fix, text, flags=re.S | re.M)
    H.ecrire_sfd(sfd, text)

if __name__ == "__main__":
    main()
