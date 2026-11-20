"""Repère seul le neume dans les bandes de localiser.py, avec gregall comme graine, et prépare
les planches de choix (marteo valide ou corrige).

Usage (Python ordinaire) :
    python -I S/auto.py <glyphe> […] [--sur BASE] [--n 4] [--inscrire]

Pour chaque bande de cache/candidats/loc_<glyphe>.json :
1. gregall rendu à l'échelle de la page (10 unités par pixel), découpé en morceaux d'encre ; son
   plus grand morceau sert de gabarit ;
2. chaque composante de la bande (hors lignes de texte) reçoit un score : ressemblance au
   gabarit (hartker.score, écart de taille peu pénalisé : gregall n'est pas à l'échelle de
   Hartker), moins une pénalité selon la distance à la position estimée par l'alignement ;
3. la meilleure est le neume de base ; gregall y est posé (plus grand morceau sur elle) et les
   composantes de la page qui tombent dans son contour (marge 20 px) complètent la boîte (points,
   tractulus, épisème) ;
4. sortie : cache/candidats/auto_<glyphe>.json (boîtes, score, colonne base) ; avec --inscrire,
   les --n meilleures (pages différentes) sont inscrites comme choix et variantes provisoires
   (retenir.py) et la planche cache/planches/auto_<glyphe>.png est faite (planche.py, --sur BASE
   si donné). La pièce et la syllabe viennent de la bande.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402
import localiser as L  # noqa: E402


DIST = float(os.environ.get("AUTO_DIST", 0.4))   # pénalité de distance (par 300 px)


def gregall_pieces(g):
    """Morceaux d'encre de gregall à l'échelle de la page : [(x, y, w, h, masque)], plus grand d'abord."""
    im = np.asarray(H.gregall_image(g, 100).convert("L")) < 128
    lab, _ = ndi.label(im)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        m = lab[sl] == i
        if m.sum() >= 4:
            out.append((sl[1].start, sl[0].start, m.shape[1], m.shape[0], m))
    return sorted(out, key=lambda p: -p[4].sum())


def score(c, t):
    n = H.norm(c["mask"])
    iou = np.minimum(n, t["n"]).sum() / np.maximum(n, t["n"]).sum()
    return iou - 0.35 * abs(np.log(c["h"] / t["h"])) - 0.35 * abs(np.log(c["w"] / t["w"]))


def pick(seg, f, pieces):
    key = (f["manuscript"], f["page"])
    fx, fy, fw, fh = map(int, f["fenetre"].split(","))
    tl = L.text_lines(key)
    ex, ey = f["x"] + f["w"] / 2, f["y"] + f["h"] / 2
    bx, by, bw, bh, bm = pieces[0]
    t = dict(n=H.norm(bm), h=bh, w=bw)
    best = None
    for c in seg[key]:
        cx, cy = c["x"] + c["w"] / 2, c["y"] + c["h"] / 2
        if not (fx <= cx <= fx + fw and fy <= cy <= fy + fh) or c["h"] < 15:
            continue
        if any(abs(cy - y) < 35 for y in tl):         # lettre de la ligne de texte
            continue
        s = score(c, t)
        d = ((cx - ex) ** 2 + (2 * (cy - ey)) ** 2) ** 0.5
        adj = s - DIST * d / 300
        if best is None or adj > best[0]:
            best = (adj, s, c)
    if best is None:
        return None
    adj, s, c = best
    # gregall posé sur la composante : plus grand morceau sur elle (centres alignés)
    ox, oy = c["x"] + c["w"] / 2 - (bx + bw / 2), c["y"] + c["h"] / 2 - (by + bh / 2)
    gx0 = min(p[0] for p in pieces) + ox - 20
    gy0 = min(p[1] for p in pieces) + oy - 20
    gx1 = max(p[0] + p[2] for p in pieces) + ox + 20
    gy1 = max(p[1] + p[3] for p in pieces) + oy + 20
    comps = [c]
    if len(pieces) > 1:
        for d in seg[key]:
            if d is c:
                continue
            dx, dy = d["x"] + d["w"] / 2, d["y"] + d["h"] / 2
            if gx0 <= dx <= gx1 and gy0 <= dy <= gy1 and d["h"] < 0.9 * c["h"] and not any(abs(dy - y) < 35 for y in tl):
                comps.append(d)
    x0, y0 = min(d["x"] for d in comps), min(d["y"] for d in comps)
    x1, y1 = max(d["x"] + d["w"] for d in comps), max(d["y"] + d["h"] for d in comps)
    return dict(manuscript=key[0], page=key[1], x=x0, y=y0, w=x1 - x0, h=y1 - y0,
                base="%d,%d,%d,%d" % (c["x"], c["y"], c["w"], c["h"]), score=round(float(s), 2),
                adj=round(float(adj), 2), piece="%s ; %s ; repéré automatiquement (graine gregall), à valider" % (f["piece"], f["nabc"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glyphes", nargs="+")
    ap.add_argument("--sur")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--inscrire", action="store_true")
    args = ap.parse_args()
    seg = H.load_seg()
    jobs = []
    for g in args.glyphes:
        path = os.path.join(H.CACHE, "candidats", "loc_%s.json" % g)
        if not os.path.exists(path):
            print(g, ": pas de bandes (localiser.py)")
            continue
        found = json.load(open(path, encoding="utf-8"))
        pieces = gregall_pieces(g)
        out = [p for p in (pick(seg, f, pieces) for f in found) if p]
        for i, p in enumerate(out):
            print("%s %d. %s p.%s %d,%d,%d,%d score %.2f  %s" % (g, i, p["manuscript"][-3:], p["page"], p["x"], p["y"], p["w"], p["h"], p["score"], p["piece"][:50]))
        with open(os.path.join(H.CACHE, "candidats", "auto_%s.json" % g), "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=0)
        if args.inscrire and out:
            order, pages = [], set()
            for i in sorted(range(len(out)), key=lambda i: -out[i]["adj"]):
                k = (out[i]["manuscript"], out[i]["page"])
                if k not in pages and len(order) < args.n:
                    order.append(i)
                    pages.add(k)
            here = os.path.dirname(os.path.abspath(__file__))
            subprocess.run([sys.executable, "-I", os.path.join(here, "retenir.py"), g, "auto_" + g] + [str(i) for i in order], check=True)
            cmd = [sys.executable, "-I", os.path.join(here, "planche.py"), "auto_" + g, g]
            if args.sur and args.sur != g:
                cmd += ["--sur", args.sur]
            jobs.append(cmd)
    del seg                            # planche.py recharge la segmentation : ne pas la garder deux fois
    import gc
    gc.collect()
    for cmd in jobs:
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
