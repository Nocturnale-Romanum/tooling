"""Regroupe les glyphes utilisés dans NR par neume de base (lots de travail) et mesure, dans gregall,
l'écart de taille du neume de base d'un glyphe composé par rapport au glyphe de base seul.

Usage (avec le Python de FontForge) :
    ffpython S/familles.py <gregall.sfd> reference/usage_nr.tsv reference/familles.tsv

Famille = code du premier neume (deux lettres : `to` regroupe to, toN1, toS, toSsu2, tolsc3,
toEcl…). Familles à part : `ls` (lettres significatives seules), `pp/su` (points seuls) et
`ob cb ni`. Un glyphe lié par `!` (E dans le nom) est rangé dans la famille de son premier
neume ; la colonne `ligature_avec` donne les autres.

`variante_de` : pour un glyphe de base épisémé ou liquescent (N, B, T), le glyphe dont il
dérive (`viN` → `vi`, `clSN1` → `clS`). Il ne peut pas le reprendre tel quel : on fusionne le
contour déjà détouré avec l'épisème ou la liquescence d'un exemplaire, ou on le détoure
entièrement d'un exemplaire cohérent avec le glyphe retenu (S/composer.py --copie).

Base d'un glyphe = code + modificateurs (S G M N B T et chiffre de variante) : la base de
`toS2sut1` est `toS2`. Pour un glyphe composé dont la base existe seule, `base_h_pct` et
`base_w_pct` comparent le plus grand contour du composé à celui de la base, dans gregall.
C'est une mesure approchée (le plus grand contour peut être une lettre, ou des points soudés
au neume) : elle sert à repérer les cas à regarder, pas à conclure.
"""
import csv
import sys

import fontforge

from commun import parse, source_variante


def main_contour(g):
    best = None
    for c in g.foreground:
        xs = [p.x for p in c]
        ys = [p.y for p in c]
        if xs:
            b = (min(xs), min(ys), max(xs), max(ys))
            if best is None or (b[2] - b[0]) * (b[3] - b[1]) > (best[2] - best[0]) * (best[3] - best[1]):
                best = b
    return best


def main(sfd, usage_path, out_path):
    f = fontforge.open(sfd)
    with open(usage_path, encoding="utf-8") as fh:
        use = {r["glyphname"]: int(r["uses"]) for r in csv.DictReader(fh, delimiter="\t")}
    used = [n for n, u in use.items() if u > 0]
    names = {g.glyphname for g in f.glyphs()}
    fam_use = {}
    rows = []
    for n in used:
        fam, base, others = parse(n)
        fam_use[fam] = fam_use.get(fam, 0) + use[n]
        h = w = ""
        if n != base and base in use and fam not in ("ls", "pp-su", "ob-cb-ni") and not others:
            a, b = main_contour(f[base]), main_contour(f[n])
            if a and b:
                h = round(100 * (b[3] - b[1]) / (a[3] - a[1]))
                w = round(100 * (b[2] - b[0]) / (a[2] - a[0]))
        src = source_variante(n) if n == base and fam not in ("ls", "pp-su", "ob-cb-ni") else None
        if src and src not in names:
            src += " (absent de gregall)"
        rows.append({"famille": fam, "glyphe": n, "base": base,
                     "variante_de": src or "",
                     "ligature_avec": " ".join(others),
                     "usages_NR": use[n], "base_h_pct": h, "base_w_pct": w})
    rows.sort(key=lambda r: (-fam_use[r["famille"]], r["base"] != r["glyphe"], -r["usages_NR"]))
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        wr.writeheader()
        wr.writerows(rows)
    for fam in sorted(fam_use, key=lambda k: -fam_use[k]):
        k = sum(r["famille"] == fam for r in rows)
        print("%-9s %3d glyphes %6d occurrences" % (fam, k, fam_use[fam]))


if __name__ == "__main__":
    main(*sys.argv[1:4])
