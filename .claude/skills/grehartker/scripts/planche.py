"""Planche de choix pour marteo : glyphe gregall à la même échelle, choix encadré, variantes.

Usage (Python ordinaire) :
    python -I S/planche.py <nom> <glyphe> [<glyphe> …] [--sur G]

Pour chaque glyphe, les lignes de sources/exemplaires.csv (choisi, variantes A–D), découpes
agrandies 4 fois, avec gregall rendu à la même échelle (10 unités par pixel de page) ; une
ligne par glyphe, empilées dans cache/planches/<nom>.png.

--sur G : superpose en rouge l'exemplaire choisi de G (ex. `vi`), calé au pied du trait
(point le plus bas à gauche). Sert à vérifier la cohérence d'une variante (viN, viB…) avec
le glyphe de base retenu : même fût, même angle.
"""
import argparse
import csv
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402


def rows_of(glyph):
    with open(os.path.join(H.SKILL, "sources", "exemplaires.csv"), encoding="utf-8") as f:
        order = ["choisi", "variante A", "variante B", "variante C", "variante D"]
        return sorted([r for r in csv.DictReader(f) if r["glyph"] == glyph], key=lambda r: order.index(r["role"]))


def foot(mask):
    ys, xs = np.nonzero(mask)
    i = np.argmax(ys - xs)
    return xs[i], ys[i]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nom")
    ap.add_argument("glyphes", nargs="+")
    ap.add_argument("--sur")
    args = ap.parse_args()
    seg = H.load_seg()
    ref = None
    if args.sur:
        r = rows_of(args.sur)[0]
        ref = H.comp_in(seg, r["manuscript"], r["page"], *(int(r[k]) for k in "xywh"))
    sheets = []
    for g in args.glyphes:
        rows = rows_of(g)
        if not rows:
            print("pas d'exemplaire pour", g)
            continue
        pad, zoom = 25, 4
        crops = []
        for r in rows:
            x, y, w, h = (int(r[k]) for k in "xywh")
            im = H.crop(r["manuscript"], r["page"], x, y, w, h, pad=pad, zoom=zoom)
            if ref is not None and (r["manuscript"], r["page"]) in seg:
                c = H.comp_in(seg, r["manuscript"], r["page"], x, y, w, h)
                if c:
                    im = overlay_at(im, c, ref, x, y, pad, zoom)
            crops.append((r, im))
        try:
            gi = H.gregall_image(g)
        except KeyError:
            gi = Image.new("RGB", (200, 200), "white")
        H_ = max([gi.height] + [im.height for _, im in crops]) + 120
        W = gi.width + sum(im.width for _, im in crops) + 40 * (len(crops) + 2)
        sh = Image.new("RGB", (W, H_), "white")
        d = ImageDraw.Draw(sh)
        d.text((20, 10), g, fill=0, font=H.font(26, True))
        d.text((20, 55), "gregall (même échelle)", fill=(90, 90, 90), font=H.font(17))
        sh.paste(gi, (20, 85))
        x = 20 + gi.width + 40
        for r, im in crops:
            first = r["role"] == "choisi"
            d.text((x, 45), r["role"].upper() if first else r["role"], fill=(0, 130, 0) if first else (0, 0, 140),
                   font=H.font(26 if first else 20, first))
            d.text((x, 72), "Cod. Sang. %s, p. %s" % (r["manuscript"][-3:], r["page"].lstrip("0")), fill=(60, 60, 60), font=H.font(17))
            sh.paste(im, (x, 98))
            if first:
                d.rectangle((x - 5, 93, x + im.width + 4, 98 + im.height + 4), outline=(0, 170, 0), width=6)
            x += im.width + 40
        sheets.append(sh)
    W = max(s.width for s in sheets)
    out = Image.new("RGB", (W, sum(s.height + 20 for s in sheets)), "white")
    y = 0
    for s in sheets:
        out.paste(s, (0, y))
        y += s.height + 20
    os.makedirs(os.path.join(H.CACHE, "planches"), exist_ok=True)
    path = os.path.join(H.CACHE, "planches", args.nom + ".png")
    out.save(path)
    print(path)


def overlay_at(im, comp, ref, bx, by, pad, zoom):
    """Superposition dans une découpe dont le coin est (bx - pad, by - pad) en coordonnées de page."""
    fx, fy = foot(comp["mask"])
    fx, fy = fx + comp["x"] - bx, fy + comp["y"] - by
    rx, ry = foot(ref["mask"])
    ys, xs = np.nonzero(ref["mask"])
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for xx, yy in zip(xs - rx + fx + pad, ys - ry + fy + pad):
        d.rectangle((xx * zoom, yy * zoom, xx * zoom + zoom - 1, yy * zoom + zoom - 1), fill=(220, 0, 0, 90))
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")


if __name__ == "__main__":
    main()
