"""Cale les contours détourés (premier plan) sur le gabarit gregall et ajuste la chasse.

Usage (avec le Python de FontForge) :
    ffpython S/caler.py src/grehartker.sfd [glyphe ...]

Sans nom de glyphe : tous les glyphes jaunes ou verts déjà détourés (premier plan différent
du calque `gregall`). Avec des noms : ces glyphes, plus les glyphes composés qui les
référencent (S/composer.py), recentrés après eux.

Règles (README, § 5) :
- aucune mise à l'échelle : on ne fait que translater le contour, pour garder les proportions
  de Hartker d'un glyphe à l'autre ;
- vertical : bas du contour sur le bas du contour gregall (ymin identique). Exception : `cl`,
  haut sur haut (ymax = 573, pas de hauteur des descripteurs h[a-np]) ;
- glyphes composés (neume de base en référence, S/composer.py) : pas de calage vertical
  propre, la référence au neume de base reste à la hauteur 0 ; le neume de base est donc à la
  même hauteur que dans le glyphe de base, et les points ou lettres se placent autour ;
- horizontal : le centre du contour est à la même distance du milieu de la chasse que dans
  gregall ;
- chasse : si le contour dépasse de la chasse, à gauche ou à droite, plus que le contour
  gregall, la chasse est élargie juste assez pour ne pas dépasser davantage, dans la limite
  de +20 % de la chasse gregall. Le contour reste centré comme ci-dessus, par rapport à la
  nouvelle chasse. Jamais de réduction de chasse.

Le calque Back (image de Hartker) est déplacé de la même translation. Le script ajoute les
points d'extrémum et arrondit les points à l'unité avant de caler, pour que l'encombrement
du TTF soit celui que calcule FontForge.
"""
import csv
import math
import os
import re
import sys

import fontforge
import psMat

from commun import fore_bbox, parse

WIP, DONE = 0xFFFF80, 0x80FF80
MAX_WIDEN = 0.20
TOP_ALIGNED = {"cl"}
SKIP = {"ni", "ob", "cb", "space"}


def gregall_widths(root):
    with open(os.path.join(root, "reference", "gregall_glyphs.csv"), encoding="utf-8") as fh:
        return {r["glyphname"]: int(r["width"]) for r in csv.DictReader(fh)}


def base_ref(g):
    """Référence au neume de base si g est un glyphe composé (S/composer.py), sinon None."""
    base = parse(g.glyphname)[1]
    for r in g.references:
        if r[0] == base and base != g.glyphname:
            return r
    return None


def is_traced(g):
    """Le premier plan n'est plus le contour gregall laissé en bouche-trou."""
    if g.references:
        return True
    fore, greg = g.layers["Fore"], g.layers["gregall"]
    if len(fore) != len(greg):
        return True
    return any(sorted((p.x, p.y) for p in a) != sorted((p.x, p.y) for p in b) for a, b in zip(fore, greg))


def target(g, gw):
    """Translation (dx, dy) et nouvelle chasse pour le glyphe g, chasse gregall gw."""
    gx0, gy0, gx1, gy1 = g.layers["gregall"].boundingBox()
    nx0, ny0, nx1, ny1 = fore_bbox(g)             # premier plan, références comprises
    W = nx1 - nx0
    d = (gx0 + gx1) / 2 - gw / 2                  # décalage du centre gregall / milieu de chasse
    over_l, over_r = max(0.0, -gx0), max(0.0, gx1 - gw)   # dépassements gregall
    need = max(gw, W - 2 * d - 2 * over_l, W + 2 * d - 2 * over_r)
    cap = int(math.floor(gw * (1 + MAX_WIDEN)))
    width = min(int(math.ceil(need - 1e-6)), cap)
    dx = round(width / 2 + d - (nx0 + nx1) / 2)
    ref = base_ref(g)
    if ref is not None:
        dy = -round(ref[1][5])                    # référence au neume de base ramenée à 0
    elif g.glyphname in TOP_ALIGNED:
        dy = round(gy1 - ny1)
    else:
        dy = round(gy0 - ny0)
    return dx, dy, width, need > cap


def shift_images(sfd, moves):
    """Déplace les images d'arrière-plan des glyphes calés (left/top dans le .sfd)."""
    with open(sfd, encoding="latin-1") as fh:
        text = fh.read()
    for name, (dx, dy) in moves.items():
        if not (dx or dy):
            continue
        start = text.index("StartChar: %s\n" % name)
        end = text.index("EndChar\n", start)
        block = re.sub(r"^Image2: (\S+) (\d+) (\S+) (\S+) (\S+) (\S+)$",
                       lambda m: "Image2: %s %s %g %g %s %s" % (m.group(1), m.group(2), float(m.group(3)) + dx,
                                                                 float(m.group(4)) + dy, m.group(5), m.group(6)),
                       text[start:end], flags=re.M)
        text = text[:start] + block + text[end:]
    with open(sfd, "w", encoding="latin-1", newline="\n") as fh:
        fh.write(text)


def main(sfd, *names):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    widths = gregall_widths(root)
    f = fontforge.open(sfd)
    if names:
        glyphs = [f[n] for n in names]
        users = [g for g in f.glyphs() if g.glyphname not in names and any(r[0] in names for r in g.references)]
        glyphs += users
    else:
        glyphs = [g for g in f.glyphs() if g.color in (WIP, DONE) and g.glyphname not in SKIP and is_traced(g)]
    glyphs.sort(key=lambda g: bool(g.references))   # glyphes de base d'abord, composés ensuite
    moves = {}
    for g in glyphs:
        n = g.glyphname
        if n in SKIP or not is_traced(g):
            print("%-12s ignoré (pas encore détouré)" % n)
            continue
        fore = g.layers["Fore"]     # copie : glyph.transform déplacerait aussi le gabarit
        fore.addExtrema()
        fore.round()
        g.layers["Fore"] = fore
        gw = widths[n]
        dx, dy, width, capped = target(g, gw)
        fore.transform(psMat.translate(dx, dy))
        g.layers["Fore"] = fore
        g.references = tuple((r[0], (r[1][0], r[1][1], r[1][2], r[1][3], r[1][4] + dx, r[1][5] + dy))
                             for r in g.references)
        g.width = width
        moves[n] = (dx, dy)
        gx0, gy0, gx1, gy1 = g.layers["gregall"].boundingBox()
        nx0, ny0, nx1, ny1 = fore_bbox(g)
        msg = "%-12s dx %+5d dy %+5d | chasse %4d" % (n, dx, dy, width)
        if width != gw:
            msg += " (gregall %d, %+.1f %%)" % (gw, 100.0 * (width - gw) / gw)
        msg += " | haut %+.0f bas %+.0f par rapport à gregall" % (ny1 - gy1, ny0 - gy0)
        if capped:
            msg += " | PLAFOND : dépasse encore de %.0f à gauche, %.0f à droite" % (max(0, -nx0), max(0, nx1 - width))
        print(msg)
    f.save(sfd)
    f.close()
    shift_images(sfd, moves)


if __name__ == "__main__":
    main(*sys.argv[1:])
