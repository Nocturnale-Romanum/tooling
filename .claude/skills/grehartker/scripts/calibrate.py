"""Calcule l'échelle commune Hartker -> grehartker (unités de police par pixel e-codices).

Usage (Python ordinaire avec Pillow, numpy et scipy) :
    python S/calibrate.py [sources/calibration.csv] [reference/gregall_glyphs.csv]

Chaque ligne de sources/calibration.csv repère un neume de Hartker (virga `vi`, clivis `cl`,
pes `pe`) par sa boîte (x, y, w, h) en pixels de l'image e-codices en pleine résolution
(6132 x 8176). Le script télécharge la découpe correspondante par IIIF (cache :
cache/decoupes/), remesure la hauteur du neume par seuillage à hystérésis (encre foncée,
étendue à l'encre claire pour ne pas perdre les traits fins), écarte les mesures fusionnées
avec un voisin, puis compare la médiane par classe à la hauteur du glyphe gregall.
"""
import csv
import os
import statistics as st
import sys
import urllib.request

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

IIIF = "https://media.e-codices.ch/iip/csg/{ms}/{ms}_{page}.jp2/{x},{y},{w},{h}/full/0/default.jpg"
MARGIN = 40
STRONG, WEAK = 55, 30   # écart au fond du parchemin (niveaux de gris)
# Une mesure est écartée si l'encre retenue touche le bord de la découpe (fusion avec un
# voisin ou trait coupé) ou dépasse MAX_GROWTH fois la boîte de départ.
MAX_GROWTH = 2.0

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
cal_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "sources", "calibration.csv")
ref_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "reference", "gregall_glyphs.csv")
cache = os.path.join(root, "cache", "decoupes")
os.makedirs(cache, exist_ok=True)


def crop(ms, page, x, y, w, h):
    path = os.path.join(cache, "%s_%s_%d_%d_%d_%d.jpg" % (ms, page, x, y, w, h))
    if not os.path.exists(path):
        req = urllib.request.Request(IIIF.format(ms=ms, page=page, x=x, y=y, w=w, h=h),
                                     headers={"User-Agent": "grehartker-calibration"})
        with urllib.request.urlopen(req) as r, open(path, "wb") as f:
            f.write(r.read())
    return np.asarray(Image.open(path).convert("L")).astype(float)


def measure(row):
    x, y, w, h = (int(row[k]) for k in "xywh")
    g = crop(row["manuscript"], row["page"], x - MARGIN, y - MARGIN, w + 2 * MARGIN, h + 2 * MARGIN)
    d = np.percentile(g, 85) - g            # encre = plus sombre que le parchemin
    core = np.zeros_like(d, bool)
    core[MARGIN:MARGIN + h, MARGIN:MARGIN + w] = d[MARGIN:MARGIN + h, MARGIN:MARGIN + w] > STRONG
    lab, _ = ndi.label(d > WEAK)
    keep = np.unique(lab[core])
    ys, xs = np.nonzero(np.isin(lab, keep[keep > 0]))
    touches = xs.min() == 0 or ys.min() == 0 or xs.max() == d.shape[1] - 1 or ys.max() == d.shape[0] - 1
    # boîte affinée, en coordonnées de la page
    return (x - MARGIN + xs.min(), y - MARGIN + ys.min(),
            xs.max() - xs.min() + 1, ys.max() - ys.min() + 1, touches)


ref = {r["glyphname"]: r for r in csv.DictReader(open(ref_path, encoding="utf-8"))}
rows = list(csv.DictReader(open(cal_path, encoding="utf-8")))
by_class, rejected, refined = {}, 0, []
for r in rows:
    mx, my, mw, mh, touches = measure(r)
    if touches or mh > MAX_GROWTH * int(r["h"]) or mw > MAX_GROWTH * int(r["w"]):
        rejected += 1
        continue
    by_class.setdefault(r["class"], []).append(mh)
    refined.append([r["manuscript"], r["page"], r["class"], mx, my, mw, mh])

# Boîtes affinées (traits fins compris) : ce sont elles qu'il faut passer à import_hartker.py.
with open(os.path.join(os.path.dirname(cal_path), "calibration_mesures.csv"), "w",
          newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["manuscript", "page", "class", "x", "y", "w", "h"])
    w.writerows(refined)

print("%d échantillons, %d écartés (fusion avec un voisin)\n" % (len(rows), rejected))
print("classe  n   hauteur Hartker (px)       hauteur gregall   unités/px")
scales = []
for c, hs in by_class.items():
    gh = float(ref[c]["ymax"]) - float(ref[c]["ymin"])
    s = gh / st.median(hs)
    scales.append(s)
    print("%-6s %3d   médiane %5.1f  [%3d-%3d]   %7.1f          %5.2f"
          % (c, len(hs), st.median(hs), min(hs), max(hs), gh, s))
print("\nÉtalon : la virga (une seule note, hauteur indépendante des intervalles, contrairement")
print("à la clivis et au pes) -> %.2f unités de police par pixel e-codices ; échelle retenue : 10."
      % (float(ref["vi"]["ymax"]) - float(ref["vi"]["ymin"])) / st.median(by_class["vi"]))
