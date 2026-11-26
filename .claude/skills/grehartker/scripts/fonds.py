"""Images de fond (exemplaires de Hartker) hors de git : le fichier de détourage officiel est
versionné sans images, avec un manifeste qui permet de les reconstruire à l'identique.

Usage (avec le Python de FontForge) :
    ffpython S/fonds.py exporter  <travail.sfd> <officiel.sfd> <fonds.tsv>
    ffpython S/fonds.py restaurer <officiel.sfd> <fonds.tsv> <travail.sfd>

exporter : copie le fichier de travail (celui que marteo ouvre dans FontForge, avec ses fonds)
vers le fichier officiel en retirant toutes les images, et écrit le manifeste : une ligne par
fond (glyphe, source Hartker lue dans le commentaire du glyphe, position et échelle de l'image).
Rien n'est écrit si une image n'a pas de source reconnue.
restaurer : reconstruit le fichier de travail depuis le fichier officiel et le manifeste ; les
découpes viennent de cache/decoupes/ ou, à défaut, d'e-codices (IIIF), agrandies ×4 comme dans
import_hartker.py (même fichier PNG, donc même image).
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hartker as H  # noqa: E402

IMG = re.compile(r"^Image2: (\S+) (\d+) (\S+) (\S+) (\S+) (\S+)\n.*?^EndImage2\n", re.S | re.M)
SRC = re.compile(r"Hartker (csg-\d+) p\. (\d+), boite (\d+),(\d+),(\d+),(\d+)")
CHAR = re.compile(r"^StartChar: (\S+)\n.*?^EndChar\n", re.S | re.M)
FIELDS = ["glyphe", "manuscript", "page", "x", "y", "w", "h", "gauche", "haut", "echelle"]


def exporter(travail, officiel, manifeste):
    with open(travail, encoding="latin-1") as fh:
        text = fh.read()
    if "StartChar:" not in text:
        sys.exit("fichier de travail vide ou illisible, rien n'est écrit : %s" % travail)
    rows, sans_source, out, last = [], [], [], 0
    for m in CHAR.finditer(text):
        block = m.group(0)
        imgs = list(IMG.finditer(block))
        if not imgs:
            continue
        srcs = SRC.findall(block)
        if not srcs:
            sans_source.append(m.group(1))
            continue
        ms, page, x, y, w, h = srcs[-1]
        i = imgs[-1]
        rows.append(dict(glyphe=m.group(1), manuscript=ms, page=page, x=x, y=y, w=w, h=h,
                         gauche=i.group(3), haut=i.group(4), echelle=i.group(5)))
        out.append(text[last:m.start()])
        out.append(IMG.sub("", block))
        last = m.end()
    if sans_source:
        sys.exit("images sans source reconnue (commentaire « Hartker … boite … ») : " + " ".join(sans_source))
    out.append(text[last:])
    H.ecrire_sfd(officiel, "".join(out))
    with open(manifeste, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print("%d fonds retirés ; %s, %s" % (len(rows), officiel, manifeste))


def restaurer(officiel, manifeste, travail):
    import fontforge
    import hartker as H
    from import_hartker import fetch, MARGIN
    with open(manifeste, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    cache = os.path.join(H.SKILL, "cache", "decoupes")
    os.makedirs(cache, exist_ok=True)
    f = fontforge.open(officiel)
    for r in rows:
        x, y, w, h = (int(r[k]) for k in "xywh")
        f[r["glyphe"]].importOutlines(fetch(cache, r["manuscript"], r["page"], x - MARGIN, y - MARGIN,
                                            w + 2 * MARGIN, h + 2 * MARGIN))
    f.save(travail)
    f.close()
    with open(travail, encoding="latin-1") as fh:
        text = fh.read()
    pos = {r["glyphe"]: r for r in rows}

    def fix(m):
        r = pos.get(m.group(1))
        if not r:
            return m.group(0)
        return IMG.sub(lambda i: "Image2: %s %s %s %s %s %s\n" % (i.group(1), i.group(2), r["gauche"], r["haut"],
                                                                   r["echelle"], r["echelle"])
                       + i.group(0).split("\n", 1)[1], m.group(0))
    text = CHAR.sub(fix, text)
    H.ecrire_sfd(travail, text)
    print("%d fonds restaurés dans %s" % (len(rows), travail))


if __name__ == "__main__":
    cmd, *a = sys.argv[1:]
    {"exporter": exporter, "restaurer": restaurer}[cmd](*a)
