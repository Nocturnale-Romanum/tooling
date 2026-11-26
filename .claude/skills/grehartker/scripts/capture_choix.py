"""Inscrit comme choix validé l'exemplaire désigné par une capture de marteo ; les exemplaires
précédents du glyphe passent en variantes (A, B…, au plus D), sans changer leur statut.

Usage (Python ordinaire) :
    python -I S/capture_choix.py <glyphe> <ms> <page> <x> <y> <w> <h> <base x,y,w,h> "<pièce>"
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hartker as H  # noqa: E402

ROLES = ["variante A", "variante B", "variante C", "variante D"]


def main(g, ms, page, x, y, w, h, base, piece):
    path = os.path.join(H.SKILL, "sources", "exemplaires.csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    fields = list(rows[0].keys())
    old = [r for r in rows if r["glyph"] == g]
    i = rows.index(old[0]) if old else len(rows)
    rest = [r for r in rows if r["glyph"] != g]
    order = sorted(old, key=lambda r: (r["role"] != "choisi", r["role"]))[:len(ROLES)]
    for r, role in zip(order, ROLES):
        r["role"] = role
    new = dict(glyph=g, role="choisi", manuscript=ms, page=page, x=x, y=y, w=w, h=h, base=base,
               piece=piece + " ; capture d'écran de marteo, validé par marteo", exclure="")
    rest[i:i] = [new] + order
    with open(path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        wr.writeheader()
        wr.writerows(rest)
    print("%s : choix %s p.%s %s,%s,%s,%s ; %d ancien(s) exemplaire(s) en variantes" % (g, ms, page, x, y, w, h, len(order)))


if __name__ == "__main__":
    main(*sys.argv[1:])
