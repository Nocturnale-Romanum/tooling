"""Fonctions communes aux outils (Python de FontForge)."""
import re


def parse(n):
    """(famille, base, autres neumes liés par !) d'après le nom de glyphe.

    Famille = code du premier neume (`to` pour toS2sut1) ; base = code + modificateurs
    (`toS2`). Familles à part : `ls` (lettres seules), `pp-su` (points seuls), `ob-cb-ni`.
    """
    if n in ("ob", "cb", "ni"):
        return "ob-cb-ni", n, []
    if n.startswith("ls"):
        return "ls", n, []
    if re.match(r"(pp|su)", n):
        return "pp-su", n, []
    m = re.match(r"([a-z]{2})([SGMNBT]*\d?)", n)
    if not m:
        return n, n, []
    return m.group(1), m.group(1) + m.group(2), re.findall(r"E([a-z]{2})", n)


def source_variante(base):
    """Glyphe dont une variante épisémée ou liquescente dérive, sinon None.

    Les modificateurs N (épisème, `-`), B (liquescence augmentative, `>`) et T (liquescence
    diminutive, `~`) modifient un neume existant : `viN` dérive de `vi`, `toN1` de `to`,
    `clSN1` de `clS`, `saNB1` de `sa`. Les modificateurs S, G, M (et le chiffre de variante
    seul) donnent des formes distinctes, qui ne dérivent de rien : `toS2` n'est pas `toS`.
    """
    m = re.match(r"([a-z]{2})([SGMNBT]*)(\d?)$", base)
    if not m or not re.search("[NBT]", m.group(2)):
        return None
    return m.group(1) + re.sub("[NBT]", "", m.group(2))


def fore_bbox(g):
    """Encombrement du seul premier plan, références comprises.

    glyph.boundingBox() de FontForge englobe tous les calques de premier plan, dont le gabarit
    `gregall` : inutilisable ici. Renvoie (0, 0, 0, 0) pour un glyphe vide, comme FontForge.
    """
    boxes = []
    layer = g.layers["Fore"]
    if len(layer):
        boxes.append(layer.boundingBox())
    for r in g.references:
        b = fore_bbox(g.font[r[0]])
        if b == (0, 0, 0, 0):
            continue
        a, bb, c, d, e, f = r[1]
        pts = [(a * x + c * y + e, bb * x + d * y + f) for x in (b[0], b[2]) for y in (b[1], b[3])]
        boxes.append((min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)))
    if not boxes:
        return (0, 0, 0, 0)
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
