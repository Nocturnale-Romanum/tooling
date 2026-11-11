"""Formes de gregall : planche d'une famille, et morceaux d'un glyphe comparés aux glyphes simples.

Usage (Python ordinaire) :
    python -I S/gregall_formes.py famille <famille> [<famille> …]   tous les glyphes NR de la famille
    python -I S/gregall_formes.py glyphes <glyphe> …               ces glyphes, à la même échelle
    python -I S/gregall_formes.py morceaux <glyphe> …              chaque morceau + glyphes simples proches

`morceaux` sert à décomposer ou à vérifier une décomposition (reference/decompositions.tsv) :
chaque composante connexe du dessin gregall est comparée, par la forme seule (taille ignorée), à
tous les glyphes de gregall d'un seul tenant. Les scores sont indicatifs : gregall est
inhomogène, et deux variantes proches (`cl`/`clS`, `pe`/`peN`) se départagent à l'œil.
Le dessin de gregall fait foi pour les décompositions. Sorties dans cache/gregall/.
"""
import csv
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402

UNI = H.gregall_codepoints()
OUT = os.path.join(H.CACHE, "gregall")


def render(name, size=300):
    f = ImageFont.truetype(H.gregall_ttf(), size)
    im = Image.new("L", (size * 5, size * 4), 0)
    ImageDraw.Draw(im).text((size, int(size * 2.4)), chr(UNI[name]), font=f, fill=255, anchor="ls")
    return np.asarray(im) > 128


def pieces(mask):
    lab, _ = ndi.label(mask)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab)):
        c = lab[sl] == i + 1
        if c.sum() >= 60:
            out.append(dict(mask=ndi.binary_fill_holes(c), x=sl[1].start, y=sl[0].start, w=c.shape[1], h=c.shape[0]))
    return sorted(out, key=lambda c: (c["x"], c["y"]))


def tile(mask, size=110):
    ys, xs = np.nonzero(mask)
    m = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    im = Image.fromarray((~m).astype(np.uint8) * 255).convert("RGB")
    im.thumbnail((size, size))
    t = Image.new("RGB", (size, size), "white")
    t.paste(im, ((size - im.width) // 2, (size - im.height) // 2))
    return t


def nnorm(c, n=40):
    m = c["mask"]
    h, w = m.shape
    s = max(h, w)
    pad = np.zeros((s, s), bool)
    pad[(s - h) // 2:(s - h) // 2 + h, (s - w) // 2:(s - w) // 2 + w] = m
    return np.asarray(Image.fromarray(pad.astype(np.uint8) * 255).resize((n, n), Image.BILINEAR)).astype(float) / 255


_lib = None


def library():
    global _lib
    if _lib is None:
        _lib = {}
        for n in UNI:
            if re.fullmatch(r"[a-z]{2}[SGMNBT]*\d?", n):
                ps = pieces(render(n))
                if len(ps) == 1:
                    _lib[n] = (nnorm(ps[0]), ps[0]["w"] / ps[0]["h"])
    return _lib


def closest(c, k=5):
    v, a = nnorm(c), c["w"] / c["h"]
    sc = [(np.minimum(v, t).sum() / np.maximum(v, t).sum() - 0.3 * abs(np.log(a / ta)), n) for n, (t, ta) in library().items()]
    return sorted(sc, reverse=True)[:k]


def sheet_glyphs(names, title, path):
    cells = []
    for n in names:
        if n in UNI:
            cells.append((n, tile(render(n), 220)))
    H.grid(cells, 8, title, cell_w=235).save(path)
    print(path)


def main(cmd, args):
    os.makedirs(OUT, exist_ok=True)
    if cmd == "famille":
        with open(os.path.join(H.SKILL, "reference", "familles.tsv"), encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f, delimiter="\t") if r["famille"] in args]
        sheet_glyphs([r["glyphe"] for r in rows], "Familles %s dans gregall" % ", ".join(args),
                     os.path.join(OUT, "famille_%s.png" % "_".join(args)))
    elif cmd == "glyphes":
        sheet_glyphs(args, "gregall", os.path.join(OUT, "glyphes.png"))
    elif cmd == "morceaux":
        blocks = []
        for g in args:
            ps = pieces(render(g))
            im = Image.new("RGB", (1000, 40 + 140 * len(ps)), "white")
            d = ImageDraw.Draw(im)
            d.text((10, 8), "%s : %d morceau(x)" % (g, len(ps)), fill=0, font=H.font(18, True))
            im.paste(tile(render(g), 200), (10, 40))
            for i, c in enumerate(ps):
                y, x = 40 + i * 140, 230
                im.paste(tile(c["mask"]), (x, y))
                d.text((x, y + 112), "morceau %d" % (i + 1), fill=(0, 0, 150), font=H.font(14))
                for s, n in closest(c):
                    x += 125
                    im.paste(tile(render(n)), (x, y))
                    d.text((x, y + 112), "%s %.2f" % (n, s), fill=(90, 90, 90), font=H.font(14))
            blocks.append(im)
        out = Image.new("RGB", (1000, sum(b.height for b in blocks)), "white")
        y = 0
        for b in blocks:
            out.paste(b, (0, y))
            y += b.height
        path = os.path.join(OUT, "morceaux.png")
        out.save(path)
        print(path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
