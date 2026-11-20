"""Repère seul le neume dans les bandes de localiser.py, avec gregall comme graine, et prépare
les planches de choix (marteo valide ou corrige).

Usage (Python ordinaire) :
    python -I S/auto.py <glyphe> […] [--sur BASE] [--graine BASE] [--n 4] [--inscrire]

--graine BASE : le gabarit du plus grand morceau est l'exemplaire choisi de BASE (forme et
taille de Hartker) au lieu de gregall ; gregall ne sert plus qu'à placer les autres morceaux.
Les bandes lues sont loc_<glyphe>.json et, si elle existe, loc_<glyphe>_b.json (--autre).
Les exemplaires déjà validés du glyphe (sans « à valider ») restent en tête, le choix inchangé.

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


def seed(seg, base):
    """Gabarit tiré de l'exemplaire choisi de base."""
    import csv
    with open(os.path.join(H.SKILL, "sources", "exemplaires.csv"), encoding="utf-8") as fh:
        r = next(r for r in csv.DictReader(fh) if r["glyph"] == base and r["role"] == "choisi")
    box = [int(v) for v in r["base"].split(",")] if r["base"] else [int(r[k]) for k in "xywh"]
    c = H.comp_in(seg, r["manuscript"], r["page"], *box)
    return dict(n=H.norm(c["mask"]), h=c["h"], w=c["w"])


def pick(seg, f, pieces, tpl=None, graine="gregall"):
    key = (f["manuscript"], f["page"])
    fx, fy, fw, fh = map(int, f["fenetre"].split(","))
    tl = L.text_lines(key)
    ex, ey = f["x"] + f["w"] / 2, f["y"] + f["h"] / 2
    bx, by, bw, bh, bm = pieces[0]
    t = tpl or dict(n=H.norm(bm), h=bh, w=bw)
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
                adj=round(float(adj), 2), piece="%s ; %s ; repéré automatiquement (graine %s), à valider" % (f["piece"], f["nabc"], graine))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glyphes", nargs="+")
    ap.add_argument("--sur")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--inscrire", action="store_true")
    ap.add_argument("--graine")
    args = ap.parse_args()
    seg = H.load_seg()
    jobs = []
    for g in args.glyphes:
        paths = [os.path.join(H.CACHE, "candidats", "loc_%s%s.json" % (g, sfx)) for sfx in ("", "_b")]
        found = [f for p in paths if os.path.exists(p) for f in json.load(open(p, encoding="utf-8"))]
        if not found:
            print(g, ": pas de bandes (localiser.py)")
            continue
        pieces = gregall_pieces(g)
        tpl = seed(seg, args.graine) if args.graine else None
        import csv
        with open(os.path.join(H.SKILL, "sources", "exemplaires.csv"), encoding="utf-8") as fh:
            kept = [dict(r) for r in csv.DictReader(fh) if r["glyph"] == g and "à valider" not in r["piece"]]
        done = {(r["manuscript"], r["page"]) for r in kept}
        out = kept + [p for p in (pick(seg, f, pieces, tpl, args.graine or "gregall") for f in found)
                      if p and (p["manuscript"], p["page"]) not in done]
        for r in kept:
            r["adj"] = 99
        for i, p in enumerate(out):
            print("%s %d. %s p.%s %s,%s,%s,%s score %s  %s" % (g, i, p["manuscript"][-3:], p["page"], p["x"], p["y"], p["w"], p["h"], p.get("score", "validé"), p["piece"][:50]))
        with open(os.path.join(H.CACHE, "candidats", "auto_%s.json" % g), "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=0)
        if args.inscrire and out:
            order, pages = [], set()
            for i in sorted(range(len(out)), key=lambda i: -float(out[i]["adj"])):
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
