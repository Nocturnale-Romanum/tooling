"""Importe une découpe de Hartker en arrière-plan d'un glyphe, à l'échelle commune.

Usage (avec le Python de FontForge) :
    ffpython S/import_hartker.py src/grehartker.sfd <glyphe> <ms> <page> <x> <y> <w> <h> [bas|haut|centre]
    ffpython S/import_hartker.py src/grehartker.sfd <glyphe composé> <ms> <page> <x> <y> <w> <h> base <bx>,<by>,<bw>,<bh>

<ms> : csg-0390 ou csg-0391 ; <page> : numéro e-codices sur 3 chiffres (031, 100…).
<x> <y> <w> <h> : boîte du neume en pixels de l'image e-codices en pleine résolution
(6132 x 8176), telle que dans sources/calibration.csv.

Le script :
- télécharge la découpe par IIIF (marge de 40 px autour de la boîte) dans cache/decoupes/ (non versionné) ;
- l'importe dans le calque Back du glyphe, en remplaçant une éventuelle image précédente ;
- la met à l'échelle commune (SCALE unités de police par pixel, cf. S/calibrate.py) ;
- la cale sur le gabarit gregall (calque `gregall`) : centre horizontal de la boîte sur le
  centre du contour gregall ; verticalement, bas de la boîte sur le bas du contour gregall
  (par défaut), ou haut sur haut (`haut`, à utiliser pour `cl` : ymax doit rester 573), ou
  centre sur centre (`centre`) ;
- glyphe composé (`base`, après S/composer.py) : <bx>,<by>,<bw>,<bh> est la boîte du seul
  neume de base dans l'exemplaire (pixels de la page). L'image est calée pour que ce neume
  tombe sur la référence au glyphe de base : centre sur centre, bas sur bas. Les points et
  lettres de l'exemplaire se trouvent alors à leur place par rapport au neume de base ;
- variante épisémée ou liquescente (`base`, après S/composer.py --copie) : idem, la boîte
  étant celle de la partie commune avec le glyphe dont la variante dérive (la virga d'une
  virga épisémée, sans l'épisème), calée sur la position de ce glyphe ;
- passe le glyphe en jaune (en cours) et note la source dans son commentaire.
Il reste à détourer au premier plan, puis à lancer S/caler.py (calage définitif, sans mise
à l'échelle).
"""
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

import fontforge

from commun import fore_bbox, parse, source_variante

SCALE = 10.0   # unités de police par pixel e-codices (S/calibrate.py)
MARGIN = 40
WIP = 0xFFFF80
IIIF = "https://media.e-codices.ch/iip/csg/{ms}/{ms}_{page}.jp2/{x},{y},{w},{h}/full/0/default.jpg"


def fetch(cache, ms, page, x, y, w, h):
    path = os.path.join(cache, "%s_%s_%d_%d_%d_%d.jpg" % (ms, page, x, y, w, h))
    if not os.path.exists(path):
        url = IIIF.format(ms=ms, page=page, x=x, y=y, w=w, h=h)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "grehartker-import"})
            with urllib.request.urlopen(req) as r:
                data = r.read()
            with open(path, "wb") as f:
                f.write(data)
        except urllib.error.URLError:
            # le Python de FontForge pour Windows n'a pas de support HTTPS : on passe par curl
            subprocess.run(["curl", "-sfL", "-A", "grehartker-import", "-o", path, url], check=True)
    return path


def main(sfd, name, ms, page, x, y, w, h, align="bas", basebox=None):
    x, y, w, h = int(x), int(y), int(w), int(h)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache = os.path.join(root, "cache", "decoupes")
    os.makedirs(cache, exist_ok=True)
    img = fetch(cache, ms, page, x - MARGIN, y - MARGIN, w + 2 * MARGIN, h + 2 * MARGIN)

    f = fontforge.open(sfd)
    g = f[name]
    gx0, gy0, gx1, gy1 = g.layers["gregall"].boundingBox()
    left = (gx0 + gx1) / 2 - (MARGIN + w / 2) * SCALE          # bord gauche de l'image
    if align == "base":
        base = parse(name)[1]
        if base == name:                      # variante épisémée / liquescente
            base = source_variante(name)
            if base is None:
                sys.exit("%s n'est ni un composé ni une variante épisémée ou liquescente" % name)
            ox = oy = 0
        else:
            refs = [r for r in g.references if r[0] == base]
            if not refs:
                sys.exit("%s : pas de référence à %s (lancer d'abord S/composer.py)" % (name, base))
            ox, oy = refs[0][1][4], refs[0][1][5]
        rx0, ry0, rx1, ry1 = fore_bbox(f[base])
        bx, by, bw, bh = (int(v) for v in basebox.split(","))
        left = ox + (rx0 + rx1) / 2 - ((bx - (x - MARGIN)) + bw / 2) * SCALE
        top = oy + ry0 + ((by + bh) - (y - MARGIN)) * SCALE
    elif align == "haut":
        top = gy1 + MARGIN * SCALE
    elif align == "centre":
        top = (gy0 + gy1) / 2 + (MARGIN + h / 2) * SCALE
    else:
        top = gy0 + (MARGIN + h) * SCALE
    g.importOutlines(img)   # va dans le calque Back
    g.color = WIP
    src = "Hartker %s p. %s, boite %d,%d,%d,%d" % (ms, page, x, y, w, h)
    if align == "base":
        src += " (neume de base %s)" % basebox
    g.comment = (g.comment + "\n" if g.comment else "") + src
    f.save(sfd)
    f.close()

    # Echelle et position de l'image : non exposées par l'API Python, on les fixe dans le
    # .sfd. On ne garde que la dernière image importée dans ce glyphe.
    with open(sfd, encoding="latin-1") as fh:
        text = fh.read()
    start = text.index("StartChar: %s\n" % name)
    end = text.index("EndChar\n", start)
    block = text[start:end]
    images = list(re.finditer(r"^Image2: \S+ \d+ \S+ \S+ (\S+) \S+\n.*?^EndImage2\n",
                              block, flags=re.S | re.M))
    # l'image qui vient d'être importée est celle que FontForge a mise à son échelle par
    # défaut (em / hauteur de l'image) ; les précédentes sont déjà à SCALE
    fresh = [m for m in images if abs(float(m.group(1)) - SCALE) > 1e-6]
    last = fresh[0] if fresh else images[-1]
    new_img = re.sub(r"^Image2: (\S+) (\d+) \S+ \S+ \S+ \S+",
                     lambda m: "Image2: %s %s %g %g %g %g" % (m.group(1), m.group(2), left, top, SCALE, SCALE),
                     last.group(0), count=1, flags=re.M)
    for m in reversed(images):
        block = block[:m.start()] + block[m.end():]
    pos = images[0].start()
    block = block[:pos] + new_img + block[pos:]
    text = text[:start] + block + text[end:]
    with open(sfd, "w", encoding="latin-1", newline="\n") as fh:
        fh.write(text)
    print("%s : %s importé (échelle %g, calage %s)" % (name, src, SCALE, align))


if __name__ == "__main__":
    main(*sys.argv[1:12])
