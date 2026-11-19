"""Marques de début de pièce dans Hartker : R rouge (répons), A rouge (antienne), lettre rouge des
autres pièces ; grandes initiales ornées des fêtes. Les versets (U barré, noir) ne sont pas
cherchés : NR transcrit le verset avec son répons.

Usage (Python ordinaire) :
    python -I S/marques.py <vol:page> …     liste les marques trouvées et les pièces de l'index Cantus
    python -I S/marques.py --toutes         calcule toutes les pages segmentées (cache) et le bilan

Détection, sans vision, sur la bande de la page réduite au quart :
- encre rouge : R - G > 68 et G - B > 40 (l'encre brune reste sous ces seuils) ;
- amas rouges (lettres et barres d'abréviation) ; une barre rouge plate au-dessus d'une lettre
  rouge en fait partie ;
- une lettre rouge est une marque si elle est isolée sur sa ligne, ou nettement plus haute
  (× 1,45) que les lettres rouges voisines (rubrique écrite juste après la marque) ; les mots des
  rubriques sont faits de lettres rouges voisines de même hauteur ;
- un amas rouge de plus de 300 px dans les deux sens est une initiale ornée (début de pièce).
Certaines pages n'ont pas de rubrication (390 p. 57 : grandes initiales noires en marge) ;
initiales_noires() y repère les lettres noires très hautes (≥ 2,3 fois la hauteur d'x de la
ligne, assez larges : pas les hampes de s, f, l), début probable de pièce ; localiser.py essaie
aussi chaque début de ligne.
Cache : cache/marques.json (marques rouges), cache/initiales_noires.json.
"""
import csv
import json
import os
import sys
from collections import defaultdict

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402

CACHE = os.path.join(H.CACHE, "marques.json")
SANS_MARQUE = {"V", "AV"}          # genres Cantus qui ne portent pas de marque rouge
_M = {}


def red_clusters(ms, page, dil=6):
    a = np.asarray(Image.open(H.download_band(ms, page)).convert("RGB").reduce(4)).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = ndi.binary_opening((R - G > 68) & (G - B > 40), np.ones((2, 2)))
    lab, _ = ndi.label(ndi.binary_dilation(m, np.ones((dil, dil))))
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        part = m[sl] & (lab[sl] == i)
        if part.sum() * 16 < 400:
            continue
        ys, xs = np.nonzero(part)
        x0, y0 = int(xs.min() + sl[1].start) * 4 + H.BAND[0], int(ys.min() + sl[0].start) * 4 + H.BAND[1]
        x1, y1 = int(xs.max() + sl[1].start) * 4 + H.BAND[0], int(ys.max() + sl[0].start) * 4 + H.BAND[1]
        out.append(dict(x=x0, y=y0, w=x1 - x0, h=y1 - y0))
    return out


def detect(ms, page):
    lets = [c for c in red_clusters(ms, page) if c["h"] > 32]
    out = []
    for c in lets:
        if c["h"] > 300 and c["w"] > 300:
            out.append(dict(c, kind="initiale"))
            continue
        cy = c["y"] + c["h"] / 2
        nb = [d for d in lets if d is not c and abs(d["y"] + d["h"] / 2 - cy) < 90
              and d["x"] - (c["x"] + c["w"]) < 230 and c["x"] - (d["x"] + d["w"]) < 230]
        if c["w"] > 280 or c["h"] < 60 or (nb and c["h"] < 1.45 * max(d["h"] for d in nb)):
            continue
        out.append(dict(c, kind="marque"))
    return sorted(out, key=lambda c: (c["y"], c["x"]))


def marques(ms, page):
    """Marques de la page (coordonnées de page), en cache."""
    if not _M and os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            _M.update(json.load(f))
    k = "%s:%s" % (ms, page)
    if k not in _M:
        _M[k] = detect(ms, page)
        with open(CACHE, "w", encoding="utf-8") as f:
            json.dump(_M, f)
    return _M[k]


_N = {}
CACHE_N = os.path.join(H.CACHE, "initiales_noires.json")


def initiales_noires(ms, page):
    """Lettres noires très hautes posées sur la ligne de texte (début de pièce probable)."""
    import localiser as L
    if not _N and os.path.exists(CACHE_N):
        with open(CACHE_N, encoding="utf-8") as f:
            _N.update(json.load(f))
    k = "%s:%s" % (ms, page)
    if k in _N:
        return _N[k]
    g = np.asarray(Image.open(H.download_band(ms, page)).convert("L").reduce(2)).astype(float)
    bg = ndi.median_filter(g[::8, ::8], size=9)
    bg = np.kron(bg, np.ones((8, 8)))[:g.shape[0], :g.shape[1]]
    ink = (bg - g) > 60
    out = []
    for yc in L.text_lines((ms, page)):
        y0, y1 = int((yc - 200 - H.BAND[1]) / 2), int((yc + 70 - H.BAND[1]) / 2)
        if y0 < 0 or y1 > ink.shape[0]:
            continue
        lab, _ = ndi.label(ink[y0:y1])
        cs = []
        for sl in ndi.find_objects(lab):
            h, w = (sl[0].stop - sl[0].start) * 2, (sl[1].stop - sl[1].start) * 2
            bot = (sl[0].stop + y0) * 2 + H.BAND[1]
            if abs(bot - (yc + 25)) < 45 and h >= 20:
                cs.append(dict(x=sl[1].start * 2 + H.BAND[0], y=bot - h, w=w, h=h))
        if len(cs) < 5:
            continue
        hm = float(np.median([c["h"] for c in cs]))
        out += [dict(c, kind="noire") for c in cs if c["h"] >= 2.3 * hm and c["w"] >= 1.3 * hm]
    _N[k] = out
    with open(CACHE_N, "w", encoding="utf-8") as f:
        json.dump(_N, f)
    return out


_C = {}


def cantus_page(ms, page):
    """Entrées de l'index Cantus qui commencent sur la page, dans l'ordre."""
    if not _C:
        with open(os.path.join(H.SKILL, "sources", "cantus_hartker.tsv"), encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                _C.setdefault((r["manuscript"], r["folio"]), []).append(r)
        for v in _C.values():
            v.sort(key=lambda r: int(r["seq"] or 0))
    return _C.get((ms, page), [])


def main():
    args = sys.argv[1:]
    if args == ["--toutes"]:
        import re
        pages = sorted(re.match(r"(csg-\d+)_(\d+)_band", f).groups() for f in os.listdir(H.PAGES)
                       if re.match(r"csg-\d+_\d+_band\.jpg$", f))
        diff = defaultdict(int)
        for ms, page in pages:
            n = len(marques(ms, page))
            e = sum(r["genre"] not in SANS_MARQUE for r in cantus_page(ms, page))
            diff[max(-3, min(3, n - e))] += 1
        print("marques − pièces Cantus (bornée à ±3) : nombre de pages")
        for d in sorted(diff):
            print("  %+d : %d" % (d, diff[d]))
        return
    for a in args:
        ms, page = H.norm_page(*a.split(":"))
        print("%s p.%s  Cantus : %s" % (ms, page, " ".join(r["genre"] for r in cantus_page(ms, page))))
        for m in marques(ms, page):
            print("  %-8s %5d %5d %4d %4d" % (m["kind"], m["x"], m["y"], m["w"], m["h"]))


if __name__ == "__main__":
    main()
