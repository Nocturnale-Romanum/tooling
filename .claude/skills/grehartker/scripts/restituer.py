"""Restitution d'un glyphe composé avec les formes de base retenues, pour juger l'harmonie.

Usage (Python ordinaire) :
    python -I S/restituer.py <nom> <glyphe> [<glyphe> …] [--role choisi]

Pour chaque glyphe : l'exemplaire de placement (sources/exemplaires.csv, rôle choisi par défaut),
sa décomposition (reference/decompositions.tsv) et les exemplaires choisis de ses formes de base.
Chaque forme est posée à la place de l'élément correspondant de l'exemplaire :
- neume de base (vi, viN, viB…) : bas et centre horizontal sur ceux du neume de base de
  l'exemplaire, comme import_hartker.py … base ;
- modèles d'éléments (pu, ta, taN, stB, gr, grN) : centrés sur l'élément.
Les éléments sont pris dans l'ordre de la décomposition : prepunctis de gauche à droite, neumes
de base de gauche à droite, subpunctis de haut en bas. Les lettres significatives sont ignorées.

Sortie : cache/planches/<nom>.png, une ligne par glyphe : l'exemplaire avec les contours des
formes posées (rouge), la restitution seule (noir), et gregall à la même échelle.
"""
import argparse
import csv
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402

NEUMES = {"vi", "viN", "viB", "viNB"}
PAD, ZOOM = 25, 3


def rows():
    with open(os.path.join(H.SKILL, "sources", "exemplaires.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def decompositions():
    with open(os.path.join(H.SKILL, "reference", "decompositions.tsv"), encoding="utf-8") as f:
        return {r["glyphe"]: [t.strip().split("@")[0] for t in r["decomposition"].split(" + ")]
                for r in csv.DictReader(f, delimiter="\t")}


def box(r, col="xywh"):
    if col == "base":
        return [int(v) for v in r["base"].split(",")]
    return [int(r[k]) for k in "xywh"]


def components(seg, r):
    """Composantes de l'exemplaire : surtout dans sa boîte ; le neume de base d'après la colonne base."""
    x, y, w, h = box(r)
    out = []
    for c in seg[(r["manuscript"], r["page"])]:
        ix = max(0, min(x + w, c["x"] + c["w"]) - max(x, c["x"]))
        iy = max(0, min(y + h, c["y"] + c["h"]) - max(y, c["y"]))
        if ix * iy >= 0.6 * c["w"] * c["h"]:
            out.append(c)
    return out


def assign(comps, dec, basebox):
    """Associe les éléments de la décomposition aux composantes de l'exemplaire."""
    forms = [f for f in dec if not f.startswith("ls")]
    nb = sum(f in NEUMES for f in forms)
    first = next(i for i, f in enumerate(forms) if f in NEUMES)
    pre, subs = forms[:first], forms[first + nb:]
    bases = sorted(comps, key=lambda c: -c["h"])[:nb]
    if basebox:
        bx, by, bw, bh = basebox
        main = max(comps, key=lambda c: max(0, min(bx + bw, c["x"] + c["w"]) - max(bx, c["x"]))
                   * max(0, min(by + bh, c["y"] + c["h"]) - max(by, c["y"])))
        if main not in bases:
            bases = [main] + bases[:nb - 1]
    bases.sort(key=lambda c: c["x"])
    rest = [c for c in comps if all(c is not b for b in bases)]
    left = sorted([c for c in rest if c["x"] + c["w"] / 2 < bases[0]["x"] + bases[0]["w"] * 0.3], key=lambda c: c["x"])
    below = sorted([c for c in rest if all(c is not l for l in left)], key=lambda c: c["y"])
    pairs = list(zip(pre, left[-len(pre):] if pre else [])) + list(zip(forms[first:first + nb], bases)) \
        + list(zip(subs, below))
    note = ""
    if len(left) != len(pre) or len(below) != len(subs):
        note = "éléments : %d avant, %d dessous dans l'exemplaire ; attendu %d et %d" % (len(left), len(below), len(pre), len(subs))
    return pairs, note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nom")
    ap.add_argument("glyphes", nargs="+")
    ap.add_argument("--role", default="choisi")
    args = ap.parse_args()
    seg = H.load_seg()
    allrows = rows()
    chosen = {r["glyph"]: r for r in allrows if r["role"] == "choisi"}
    decs = decompositions()
    models = {}
    lines = []
    for g in args.glyphes:
        r = next((r for r in allrows if r["glyph"] == g and r["role"] == args.role), None)
        if r is None or (r["manuscript"], r["page"]) not in seg:
            print("%s : pas d'exemplaire « %s » segmenté" % (g, args.role))
            continue
        comps = components(seg, r)
        pairs, note = assign(comps, decs[g], box(r, "base") if r["base"] else None)
        x, y, w, h = box(r)
        x0, y0 = x - PAD, y - PAD
        W, Hh = w + 2 * PAD, h + 2 * PAD
        band = Image.open(H.download_band(r["manuscript"], r["page"])).convert("L")
        page = band.crop((x0 - H.BAND[0], y0 - H.BAND[1], x0 - H.BAND[0] + W, y0 - H.BAND[1] + Hh))
        fill = np.zeros((Hh, W), bool)
        edge = np.zeros((Hh, W), bool)
        missing = []
        for form, c in pairs:
            m = models.get(form)
            if m is None and form in chosen:
                mr = chosen[form]
                key = (mr["manuscript"], mr["page"])
                if key in seg:
                    m = models[form] = H.comp_in(seg, key[0], key[1], *box(mr, "base" if mr["base"] else "xywh"))
            if m is None:
                missing.append(form)
                continue
            mh, mw = m["mask"].shape
            if form in NEUMES:
                tx, ty = c["x"] + c["w"] / 2 - mw / 2, c["y"] + c["h"] - mh
            else:
                tx, ty = c["x"] + c["w"] / 2 - mw / 2, c["y"] + c["h"] / 2 - mh / 2
            tx, ty = int(round(tx - x0)), int(round(ty - y0))
            sl = (slice(max(ty, 0), min(ty + mh, Hh)), slice(max(tx, 0), min(tx + mw, W)))
            sub = m["mask"][sl[0].start - ty:sl[0].stop - ty, sl[1].start - tx:sl[1].stop - tx]
            fill[sl] |= sub
            e = sub & ~ndi.binary_erosion(sub)
            edge[sl] |= e
        big = lambda im: im.resize((im.width * ZOOM, im.height * ZOOM), Image.LANCZOS)
        over = big(page.convert("RGB"))
        edge_z = np.kron(ndi.binary_dilation(edge), np.ones((ZOOM, ZOOM), bool))
        a = np.asarray(over).copy()
        a[edge_z] = (220, 0, 0)
        over = Image.fromarray(a)
        rec = big(Image.fromarray(np.where(fill, 0, 255).astype("uint8")).convert("RGB"))
        greg = H.gregall_image(g, 100 * ZOOM) if g in H.gregall_codepoints() else None
        lines.append((g, r, note, missing, [over, rec] + ([greg] if greg else [])))
    if not lines:
        raise SystemExit("rien à restituer")
    lab_h = 50
    rows_h = [max(im.height for im in ims) + lab_h + 10 for *_, ims in lines]
    width = max(sum(im.width + 20 for im in ims) for *_, ims in lines) + 20
    sheet = Image.new("RGB", (max(width, 1400), sum(rows_h) + 60), "white")
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), "%s : exemplaire + formes de base retenues (rouge), restitution, gregall" % args.nom, fill=0, font=H.font(24, True))
    yy = 55
    for (g, r, note, missing, ims), rh in zip(lines, rows_h):
        info = "%s  —  %s p.%s  %s" % (g, r["manuscript"][-3:], r["page"].lstrip("0"), r.get("piece", "")[:110])
        d.text((10, yy), info, fill=(0, 0, 150), font=H.font(18, True))
        warn = "; ".join(filter(None, [note, ("sans exemplaire : " + ", ".join(missing)) if missing else ""]))
        if warn:
            d.text((10, yy + 24), warn, fill=(200, 0, 0), font=H.font(16))
        xx = 10
        for im in ims:
            sheet.paste(im, (xx, yy + lab_h))
            xx += im.width + 20
        yy += rh
    out = os.path.join(H.CACHE, "planches", args.nom + ".png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
