"""Cherche des neumes en plusieurs morceaux : un neume de base suivi de subpunctis ou précédé de
prepunctis (exemplaires de placement des glyphes composés : viNsut2, ciN, sc, viNpp2…).

Usage (Python ordinaire) :
    python -I S/motifs.py <nom> --base G [G …] [--sous tt] [--avant pp] [--n 24] [--par-page 2]

- --base : glyphes dont les lignes de sources/exemplaires.csv servent de gabarits au neume de
  base (ex. `vi viN` : virgas avec ou sans épisème) ;
- --sous : suite attendue des éléments sous le neume, de haut en bas ; --avant : éléments à
  gauche, de gauche à droite. Lettres : p punctum, t tractulus, u tractulus épisémé (uncinus).
  Classement automatique d'après la forme de la boîte (t : largeur ≥ 2 × hauteur ; u : entre
  1,35 et 2 et au moins 26 px de large ; p sinon) : à vérifier à l'œil.

Sortie dans cache/candidats/ : <nom>.png et <nom>.json. Chaque candidat donne la boîte de
l'ensemble (x, y, w, h) et celle du seul neume de base (`base`), à reporter dans la colonne
`base` de sources/exemplaires.csv pour l'import calé (import_hartker.py … base).
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402


def kind(c):
    r = c["w"] / c["h"]
    if r >= 2.0:
        return "t"
    if r >= 1.35 and c["w"] >= 26:
        return "u"
    return "p"


def small(c):
    return 7 <= c["h"] <= 34 and 8 <= c["w"] <= 60


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nom")
    ap.add_argument("--base", nargs="+", required=True)
    ap.add_argument("--sous", default="")
    ap.add_argument("--avant", default="")
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--par-page", type=int, default=2)
    ap.add_argument("--seuil", type=float, default=0.25)
    args = ap.parse_args()
    seg = H.load_seg()
    with open(os.path.join(H.SKILL, "sources", "exemplaires.csv"), encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["glyph"] in args.base]
    T = []
    for r in rows:
        key = (r["manuscript"], r["page"])
        if key in seg:
            bx = r.get("base") or ""
            box = list(map(int, bx.split(","))) if bx else [int(r[k]) for k in "xywh"]
            c = H.comp_in(seg, key[0], key[1], *box)
            if c:
                T.append(H.template(c))
    if not T:
        raise SystemExit("aucun gabarit de base dans les pages segmentées")
    found = []
    for key, comps in seg.items():
        for v in comps:
            if not (40 <= v["h"] <= 110 and 30 <= v["w"] <= 110):
                continue
            s = H.score(v, T)
            if s < args.seuil:
                continue
            cand = sorted([c for c in comps if small(c) and v["x"] + 0.3 * v["w"] <= c["x"] <= v["x"] + v["w"] + 70
                           and v["y"] + 0.3 * v["h"] <= c["y"] <= v["y"] + v["h"] + 140], key=lambda c: c["y"])
            chain, last = [], v["y"] + 0.55 * v["h"]
            for c in cand:
                if c["y"] - last > 48:
                    break
                if chain and abs(c["y"] - chain[-1]["y"]) < 6:
                    continue
                chain.append(c)
                last = c["y"] + c["h"]
            pre = sorted([c for c in comps if small(c) and v["x"] - 150 <= c["x"] and c["x"] + c["w"] <= v["x"] + 12
                          and v["y"] + 0.35 * v["h"] <= c["y"] <= v["y"] + v["h"] + 30], key=lambda c: c["x"])
            if "".join(kind(c) for c in chain) != args.sous:
                continue
            if args.avant and "".join(kind(c) for c in pre)[-len(args.avant):] != args.avant:
                continue
            parts = [v] + chain + (pre[-len(args.avant):] if args.avant else [])
            x0, y0 = min(c["x"] for c in parts), min(c["y"] for c in parts)
            x1, y1 = max(c["x"] + c["w"] for c in parts), max(c["y"] + c["h"] for c in parts)
            found.append((s, key, dict(x=x0, y=y0, w=x1 - x0, h=y1 - y0), v))
    found.sort(key=lambda t: -t[0])
    seen, pick = {}, []
    for s, key, b, v in found:
        if seen.get(key, 0) >= args.par_page:
            continue
        seen[key] = seen.get(key, 0) + 1
        pick.append(dict(manuscript=key[0], page=key[1], **b, base="%d,%d,%d,%d" % (v["x"], v["y"], v["w"], v["h"]),
                         score=round(float(s), 3)))
        if len(pick) == args.n:
            break
    out = os.path.join(H.CACHE, "candidats")
    os.makedirs(out, exist_ok=True)
    cells = []
    for i, c in enumerate(pick):
        im = H.crop(c["manuscript"], c["page"], c["x"], c["y"], c["w"], c["h"], pad=20, zoom=3, box=True)
        im.thumbnail((400, 400))
        cells.append(("%d. %s p.%s" % (i, c["manuscript"][-3:], c["page"].lstrip("0")), im))
    if not cells:
        raise SystemExit("aucun candidat")
    H.grid(cells, 6, "%s : base %s, avant « %s », sous « %s »" % (args.nom, "/".join(args.base), args.avant, args.sous),
           cell_w=420).save(os.path.join(out, args.nom + ".png"))
    with open(os.path.join(out, args.nom + ".json"), "w", encoding="utf-8") as f:
        json.dump(pick, f, indent=0)
    print(os.path.join(out, args.nom + ".png"), len(pick), "candidats")


if __name__ == "__main__":
    main()
