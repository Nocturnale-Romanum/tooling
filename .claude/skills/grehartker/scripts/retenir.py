"""Inscrit un choix et ses variantes dans sources/exemplaires.csv, depuis une liste de candidats.

Usage (Python ordinaire) :
    python -I S/retenir.py <glyphe> <nom de la liste> <i_choix> [<i_varA> …]
    python -I S/retenir.py <glyphe> --permuter <rôle>          ex. --permuter "variante C"

- La liste est cache/candidats/<nom>.json (candidats.py ou motifs.py) ; les indices sont ceux de
  la planche. Le premier devient « choisi », les suivants « variante A » à « variante D ».
  Règle : choix et variantes viennent de pages toutes différentes (le script le vérifie).
- --permuter : échange le choix et la variante indiquée (décision de marteo sur une planche).
Les lignes précédentes du glyphe sont remplacées.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402

CSV = os.path.join(H.SKILL, "sources", "exemplaires.csv")
FIELDS = ["glyph", "role", "manuscript", "page", "x", "y", "w", "h", "base"]
ROLES = ["choisi", "variante A", "variante B", "variante C", "variante D"]


def read():
    with open(CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(rows):
    with open(CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(argv):
    glyph = argv[0]
    rows = read()
    if argv[1] == "--permuter":
        role = argv[2]
        for r in rows:
            if r["glyph"] == glyph and r["role"] in ("choisi", role):
                r["role"] = role if r["role"] == "choisi" else "choisi"
        mine = sorted([r for r in rows if r["glyph"] == glyph], key=lambda r: ROLES.index(r["role"]))
    else:
        with open(os.path.join(H.CACHE, "candidats", argv[1] + ".json"), encoding="utf-8") as f:
            cands = json.load(f)
        picks = [cands[int(i)] for i in argv[2:]]
        pages = [(c["manuscript"], c["page"]) for c in picks]
        if len(set(pages)) != len(pages):
            raise SystemExit("choix et variantes doivent venir de pages différentes : %s" % pages)
        mine = [dict(glyph=glyph, role=ROLES[k], manuscript=c["manuscript"], page=c["page"], x=c["x"], y=c["y"],
                     w=c["w"], h=c["h"], base=c.get("base", "")) for k, c in enumerate(picks)]
    pos = next((i for i, r in enumerate(rows) if r["glyph"] == glyph), len(rows))
    rest = [r for r in rows if r["glyph"] != glyph]
    write(rest[:pos] + mine + rest[pos:])
    for r in mine:
        print(r["role"], r["manuscript"], r["page"], r["x"], r["y"], r["w"], r["h"], r.get("base", ""))


if __name__ == "__main__":
    main(sys.argv[1:])
