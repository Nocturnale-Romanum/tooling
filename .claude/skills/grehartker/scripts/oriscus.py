"""Oriscus sans glyphe de police (`or_pi`, `or_salicus`, `or_couche`) : extraits à la demande
des formes de base tracées qui les contiennent (`pi`, `sa`, `sa1`).

Ils n'ont pas de glyphe dans la police (décision de marteo, 24 novembre 2026) : les composeurs
(composer_auto.py, composer_hors.py) les ré-extraient à chaque composition et les recopient en
contours (et non en références) dans les glyphes composés. Toute retouche de `pi`, `sa` ou
`sa1` n'atteint donc les composés qu'en les régénérant : régénérer systématiquement les
composés qui contiennent un oriscus après une modification de ces trois glyphes.

Extraction : dans le glyphe source, on retire les contours qui reproduisent ceux des autres
formes de sa décomposition (`pi` = `or_pi` + `pu` ; `sa` = `pu` + `or_salicus` + `vi` ;
`sa1` = `pu` + `or_couche` + `vi`) — même nombre de points, même taille de boîte à 2 unités
près ; il doit rester exactement un contour. Les coordonnées restent celles du glyphe source.

Usage (contrôle, avec le Python de FontForge) :
    ffpython S/oriscus.py <police.sfd>
"""
import sys

import fontforge

SOURCES = {"or_pi": ("pi", ["pu"]), "or_salicus": ("sa", ["pu", "vi"]), "or_couche": ("sa1", ["pu", "vi"])}


def _taille(c):
    b = c.boundingBox()
    return len(c), b[2] - b[0], b[3] - b[1]


def extraire(f, nom):
    """Calque contenant le seul contour de l'oriscus `nom`, ou None (avec la raison en stderr)."""
    src, autres = SOURCES[nom]
    if src not in f or not len(f[src].foreground):
        return None
    connus = [_taille(c) for a in autres if a in f for c in f[a].foreground]
    reste = [c for c in f[src].foreground
             if not any(n == k[0] and abs(w - k[1]) <= 2 and abs(h - k[2]) <= 2 for k in connus for n, w, h in [_taille(c)])]
    if len(reste) != 1:
        sys.stderr.write("%s : %d contour(s) restant dans %s au lieu d'un\n" % (nom, len(reste), src))
        return None
    lay = fontforge.layer()
    lay += reste[0].dup()
    return lay


def est_oriscus(nom):
    return nom in SOURCES


_CACHE = {}


def forme(f, nom):
    """Calque de l'oriscus (extrait une fois par police ouverte)."""
    k = (id(f), nom)
    if k not in _CACHE:
        _CACHE[k] = extraire(f, nom)
    return _CACHE[k]


def disponible(f, nom):
    """Forme utilisable dans un composé : oriscus extractible, ou glyphe tracé ou composé."""
    if est_oriscus(nom):
        return forme(f, nom) is not None
    return nom in f and (len(f[nom].foreground) > 0 or bool(f[nom].references))


def boite(f, nom):
    if est_oriscus(nom):
        return forme(f, nom).boundingBox()
    g = f[nom]
    b = g.foreground.boundingBox() if len(g.foreground) else None
    if b is None or b == (0, 0, 0, 0):
        b = g.boundingBox()
    return b


def poser(f, g, placees):
    """Pose [(forme, dx, dy)] dans g : références aux formes de base, oriscus recopiés en
    contours (premier plan remplacé)."""
    import psMat
    g.references = tuple((p, (1, 0, 0, 1, round(dx), round(dy))) for p, dx, dy in placees if not est_oriscus(p))
    lay = fontforge.layer()
    for p, dx, dy in placees:
        if est_oriscus(p):
            o = forme(f, p).dup()
            o.transform(psMat.translate(round(dx), round(dy)))
            lay += o
    g.foreground = lay


if __name__ == "__main__":
    f = fontforge.open(sys.argv[1])
    for n in SOURCES:
        lay = extraire(f, n)
        print(n, "←", SOURCES[n][0], ":", "boîte %s, %d points" % ([round(v) for v in lay.boundingBox()], len(lay[0]))
              if lay else "échec")
