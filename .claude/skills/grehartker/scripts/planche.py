"""Planche de choix pour marteo : glyphe gregall à la même échelle, choix encadré, variantes.

Usage (Python ordinaire) :
    python -I S/planche.py <nom> <glyphe> [<glyphe> …] [--sur G]

Pour chaque glyphe, les lignes de sources/exemplaires.csv (choisi, variantes A–D), découpes
agrandies 4 fois, avec gregall rendu à la même échelle (10 unités par pixel de page) ; une
ligne par glyphe, empilées dans cache/planches/<nom>.png.

--sur G : superpose en rouge l'exemplaire choisi de G (ex. `vi`), entier (toutes ses
composantes : les deux virgas de `bvN`), calé au pied du trait de son neume de base (point le
plus bas à gauche) sur celui du neume de base de chaque exemplaire (colonne `base`). Sert à
vérifier la cohérence d'une variante (viN, viB…) ou d'un composé (bvNsut2 sur bvN) avec le
glyphe retenu : même fût, même angle, même écart.
--calage haut : --sur calé par les points les plus hauts (oriscus de `vs` sur celui de `pi`).
--aussi G : second glyphe superposé en bleu, calé coin haut-gauche contre coin haut-gauche
(la clivis au début d'un porrectus : `planche.py … po --aussi cl`).
--pale : ajoute l'encre pâle de la boîte reliée aux composantes (hampe trop fine pour la
segmentation, ex. `qi`), sauf la colonne `exclure`.

Sous chaque exemplaire : sa page et sa pièce (colonne `piece`).
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


def top(mask):
    ys, xs = np.nonzero(mask)
    i = np.argmin(ys * 1000 + xs)
    return xs[i], ys[i]


def foot(mask):
    ys, xs = np.nonzero(mask)
    i = np.argmax(ys - xs)
    return xs[i], ys[i]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nom")
    ap.add_argument("glyphes", nargs="+")
    ap.add_argument("--sur")
    ap.add_argument("--calage", default="pied", choices=["pied", "haut", "haut-gauche", "forme"],
                    help="point de calage de --sur : pied (défaut), haut (point le plus haut), haut-gauche, "
                         "forme (centre sur centre de la composante de l'exemplaire qui ressemble le plus à --sur)")
    ap.add_argument("--calage-aussi", default="haut-gauche", choices=["pied", "haut", "haut-gauche"])
    ap.add_argument("--aussi", help="second glyphe superposé, en bleu, calé en haut à gauche (cl dans po)")
    ap.add_argument("--pale", action="store_true", help="ajoute à la superposition l'encre pâle de la boîte (hampe fine)")
    args = ap.parse_args()
    seg = H.load_seg()
    ref = ref2 = None
    if args.sur:
        ref = whole(seg, rows_of(args.sur)[0], args.pale)
    if args.aussi:
        ref2 = whole(seg, rows_of(args.aussi)[0], args.pale)
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
                if args.calage == "forme":           # la composante la plus ressemblante de la boîte
                    t = dict(n=H.norm(ref["mask"]), h=ref["mask"].shape[0], w=ref["mask"].shape[1])
                    inside = [d for d in seg[(r["manuscript"], r["page"])]
                              if x <= d["x"] + d["w"] / 2 <= x + w and y <= d["y"] + d["h"] / 2 <= y + h and not H.exclue(r, d)]
                    c = max(inside, key=lambda d: H.score(d, [t])) if inside else None
                else:
                    c = H.comp_in(seg, r["manuscript"], r["page"], *base_box(r))
                if c:
                    im = overlay_at(im, c, ref, x, y, pad, zoom, calage=args.calage)
            if ref2 is not None and (r["manuscript"], r["page"]) in seg:
                c = H.comp_in(seg, r["manuscript"], r["page"], *base_box(r))
                if c:
                    im = overlay_at(im, c, ref2, x, y, pad, zoom, calage=args.calage_aussi, color=(0, 60, 220, 45))
            crops.append((r, im))
        try:
            gi = H.gregall_image(g)
        except KeyError:
            gi = Image.new("RGB", (200, 200), "white")
        H_ = max([gi.height] + [im.height for _, im in crops]) + 140
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
            if r.get("piece"):
                piece = r["piece"] if len(r["piece"]) < 60 else r["piece"][:57] + "…"
                d.text((x, 104 + im.height), piece, fill=(90, 90, 90), font=H.font(14))
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


def base_box(r):
    return [int(v) for v in r["base"].split(",")] if r.get("base") else [int(r[k]) for k in "xywh"]


def whole(seg, r, pale=False):
    """Exemplaire entier (composantes surtout dans sa boîte), avec le pied de son neume de base."""
    x, y, w, h = (int(r[k]) for k in "xywh")
    key = (r["manuscript"], r["page"])
    comps = [c for c in seg[key] if max(0, min(x + w, c["x"] + c["w"]) - max(x, c["x"]))
             * max(0, min(y + h, c["y"] + c["h"]) - max(y, c["y"])) >= 0.6 * c["w"] * c["h"]
             and not H.exclue(r, c)]
    base = H.comp_in(seg, key[0], key[1], *base_box(r))
    comps = comps or [base]
    x0, y0 = min([c["x"] for c in comps] + ([x] if pale else [])), min([c["y"] for c in comps] + ([y] if pale else []))
    x1 = max([c["x"] + c["w"] for c in comps] + ([x + w] if pale else []))
    y1 = max([c["y"] + c["h"] for c in comps] + ([y + h] if pale else []))
    mask = np.zeros((y1 - y0, x1 - x0), bool)
    for c in comps:
        mask[c["y"] - y0:c["y"] - y0 + c["h"], c["x"] - x0:c["x"] - x0 + c["w"]] |= c["mask"]
    if pale:
        # encre pâle de la boîte (trait fin, hampe) reliée aux composantes : seuil bas sous le fond
        from scipy import ndimage as ndi
        g = np.asarray(Image.open(H.download_band(*key)).convert("L")).astype(float)
        sub = g[y0 - H.BAND[1]:y1 - H.BAND[1], x0 - H.BAND[0]:x1 - H.BAND[0]]
        bg = np.percentile(g[max(0, y - 60 - H.BAND[1]):y + h + 60 - H.BAND[1], max(0, x - 60 - H.BAND[0]):x + w + 60 - H.BAND[0]], 85)
        faint = (bg - sub) > 25
        inbox = np.zeros_like(faint)
        inbox[y - y0:y - y0 + h, x - x0:x - x0 + w] = True
        faint &= inbox
        for c in seg[key]:
            if H.exclue(r, c):
                cy, cx = c["y"] - y0, c["x"] - x0
                ys, xs = np.nonzero(c["mask"])
                ok = (ys + cy >= 0) & (ys + cy < faint.shape[0]) & (xs + cx >= 0) & (xs + cx < faint.shape[1])
                faint[ys[ok] + cy, xs[ok] + cx] = False
        # traits pâles proches (≤ 6 px) des composantes, de proche en proche
        for _ in range(4):
            lab, _ = ndi.label(faint)
            near = ndi.binary_dilation(mask, np.ones((13, 13), bool))
            keep = np.unique(lab[near & faint])
            add = np.isin(lab, keep[keep > 0]) & ~mask
            if not add.any():
                break
            mask |= add
    fx, fy = foot(base["mask"])
    return dict(mask=mask, foot=(fx + base["x"] - x0, fy + base["y"] - y0))


def overlay_at(im, comp, ref, bx, by, pad, zoom, calage="pied", color=(220, 0, 0, 45)):
    """Superposition dans une découpe dont le coin est (bx - pad, by - pad) en coordonnées de page."""
    if calage == "haut-gauche":                  # coins haut-gauche des boîtes d'encre
        fx, fy, rx, ry = comp["x"] - bx, comp["y"] - by, 0, 0
    elif calage == "forme":                      # centres alignés
        fx, fy = comp["x"] + comp["w"] / 2 - bx, comp["y"] + comp["h"] / 2 - by
        rx, ry = ref["mask"].shape[1] / 2, ref["mask"].shape[0] / 2
    elif calage == "haut":                       # points les plus hauts (oriscus de vs sur celui de pi)
        fx, fy = top(comp["mask"])
        fx, fy = fx + comp["x"] - bx, fy + comp["y"] - by
        rx, ry = top(ref["mask"])
    else:
        fx, fy = foot(comp["mask"])
        fx, fy = fx + comp["x"] - bx, fy + comp["y"] - by
        rx, ry = ref["foot"]
    ys, xs = np.nonzero(ref["mask"])
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for xx, yy in zip((xs - rx + fx + pad).astype(int), (ys - ry + fy + pad).astype(int)):
        d.rectangle((xx * zoom, yy * zoom, xx * zoom + zoom - 1, yy * zoom + zoom - 1), fill=color)
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")


if __name__ == "__main__":
    main()
