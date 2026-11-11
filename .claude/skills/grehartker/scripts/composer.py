"""Prépare un glyphe composé ou une variante épisémée / liquescente à partir du glyphe de base.

Usage (avec le Python de FontForge) :
    ffpython S/composer.py src/grehartker.sfd <glyphe composé> [...]
    ffpython S/composer.py src/grehartker.sfd --copie <variante> [...]

Pour chaque glyphe composé (ex. `toSsu2`, base `toS` ; `cllsc3`, base `cl`) :
- le premier plan est vidé (le contour gregall en bouche-trou reste visible dans le calque
  `gregall`) ;
- on y place une référence au glyphe de base, sans décalage : le neume de base a donc
  exactement la taille, la forme et la hauteur du glyphe de base, et suivra ses retouches ;
- le glyphe passe en jaune.
Il reste à importer un exemplaire de Hartker du glyphe composé, calé sur le neume de base
(`S/import_hartker.py … base <x>,<y>,<w>,<h>`), à détourer au premier plan ce qui s'ajoute
au neume de base (points, lettres : pour une lettre significative, de préférence une référence
au glyphe `ls…` correspondant), puis à lancer `S/caler.py`.

La base est déduite du nom (code du neume + modificateurs, cf. S/familles.py). Les ligatures
avec `!` (`toEcl`…) ne sont pas traitées : elles se détourent d'un seul tenant.

--copie : variante épisémée ou liquescente d'un glyphe de base (`viN`, `clN`, `toN1`, `peB`…,
colonne `variante_de` de reference/familles.tsv). Elle ne peut pas reprendre le glyphe dont elle
dérive tel quel : le premier plan reçoit une copie (et non une référence) de son contour, comme
point de départ, à fusionner avec l'épisème ou la liquescence détourés d'un exemplaire de Hartker
cohérent avec le glyphe retenu. Si l'exemplaire s'en écarte trop, on détoure tout de zéro.
"""
import sys

import fontforge

from commun import parse, source_variante

WIP = 0xFFFF80


def copie(f, n):
    src = source_variante(n)
    if src is None or parse(n)[1] != n:
        sys.exit("%s n'est pas une variante épisémée ou liquescente d'un glyphe de base" % n)
    g = f[n]
    g.layers["Fore"] = f[src].layers["Fore"]
    g.references = ()
    g.color = WIP
    note = "Contour de départ copié de %s : fusionner avec l'épisème / la liquescence de l'exemplaire" % src
    g.comment = (g.comment + "\n" if g.comment else "") + note
    print("%s : contour de %s copié" % (n, src))


def main(sfd, *names):
    f = fontforge.open(sfd)
    if names and names[0] == "--copie":
        for n in names[1:]:
            copie(f, n)
        f.save(sfd)
        return
    for n in names:
        fam, base, others = parse(n)
        if base == n or fam in ("ls", "pp-su", "ob-cb-ni"):
            sys.exit("%s n'est pas un glyphe composé" % n)
        if others:
            sys.exit("%s est une ligature (!) : à détourer d'un seul tenant" % n)
        if base not in f:
            sys.exit("%s : glyphe de base %s absent" % (n, base))
        g = f[n]
        empty = fontforge.layer()
        empty.is_quadratic = f.layers["Fore"].is_quadratic
        g.layers["Fore"] = empty
        g.references = ()
        g.addReference(base)
        g.color = WIP
        print("%s : référence à %s posée" % (n, base))
    f.save(sfd)


if __name__ == "__main__":
    main(*sys.argv[1:])
