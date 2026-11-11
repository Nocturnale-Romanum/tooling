"""Crée src/grehartker.sfd à partir de gregall.sfd.

Usage (avec le Python de FontForge) :
    ffpython S/init_grehartker.py <gregall.sfd> <grehartker.sfd>

Ce que fait le script :
- conserve tous les paramètres de police de gregall (em, ascent/descent, métriques
  OS/2 et hhea, interligne), l'encodage, les noms de glyphes, les chasses et les
  commentaires : un document mis en forme avec gregall se compose à l'identique ;
- renomme la police en grehartker (FontName/FamilyName/FullName) et retire le XUID ;
- copie le contour gregall de chaque glyphe dans un calque d'arrière-plan « gregall »
  (gabarit de taille et de position pour le détourage) ;
- laisse le contour gregall au premier plan comme bouche-trou, pour que la police
  reste complète tant que tous les glyphes ne sont pas redessinés ;
- supprime les images source de gregall du calque Back (elles proviennent d'autres
  manuscrits) : le calque Back reçoit désormais les découpes de Hartker ;
- colore tous les glyphes en rouge (= à refaire). Convention : rouge à refaire,
  jaune en cours, vert refait d'après Hartker.
"""
import os
import re
import sys
import tempfile

import fontforge

TODO = 0xFF8080

HEADER = (
    "grehartker font, created with FontForge.\n"
    "Glyph outlines traced from the Hartker Antiphonary "
    "(St. Gallen, Stiftsbibliothek, Cod. Sang. 390-391).\n"
    "Font parameters, glyph set, glyph names and advance widths derived from gregall:\n"
)


def main(src, dst):
    f = fontforge.open(src)
    f.fontname = f.familyname = f.fullname = "grehartker"
    f.version = "0.1"
    f.xuid = ""
    f.copyright = HEADER + f.copyright
    f.layers.add("gregall", f.layers["Fore"].is_quadratic, True)
    for g in f.glyphs():
        g.layers["gregall"] = g.layers["Fore"]
        g.color = TODO
    tmp = tempfile.NamedTemporaryFile(suffix=".sfd", delete=False).name
    f.save(tmp)
    f.close()

    # Les images d'arrière-plan ne sont pas accessibles via l'API Python :
    # on retire les blocs Image2 ... EndImage2 directement dans le texte du .sfd.
    with open(tmp, encoding="latin-1") as fh:
        text = fh.read()
    os.remove(tmp)
    text, n = re.subn(r"^Image2?: .*?^EndImage2?\n", "", text, flags=re.S | re.M)
    with open(dst, "w", encoding="latin-1", newline="\n") as fh:
        fh.write(text)

    f = fontforge.open(dst)  # relecture de contrôle
    print("%s : %d glyphes, %d images retirées, calques : %s"
          % (dst, len(list(f.glyphs())), n, [f.layers[i].name for i in range(f.layer_cnt)]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
