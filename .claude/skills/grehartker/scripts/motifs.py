"""Cherche des neumes en plusieurs morceaux : un ou plusieurs neumes de base, avec des prepunctis
et des subpunctis (exemplaires de placement des glyphes composés : viNsut2, ciN, sc, bvN…).

Usage (Python ordinaire) :
    python -I S/motifs.py <nom> --base G [G …] --motifs M [M …] [--n 24] [--par-page 2]

- --base : glyphes dont les lignes de sources/exemplaires.csv servent de gabarits au neume de
  base (ex. `vi viN` : virgas avec ou sans épisème ; `viB` : céphalicus) ;
- --motifs : un ou plusieurs motifs `avant|sous`, ou `avant|sous|k` pour k neumes de base côte à
  côte (bivirga : `|||2`, trivirga : `|||3`… soit `||2`). `avant` : éléments à gauche, de gauche à
  droite ; `sous` : éléments sous le dernier neume, de haut en bas. Lettres : p punctum,
  t tractulus, u tractulus épisémé (uncinus). Exemples : `|pp` climacus, `pp|` scandicus,
  `pp|pp`, `|ptt`, `t|pp`, `||2`, `|tt|2`.
  Classement automatique d'après la forme de la boîte (t : largeur ≥ 2 × hauteur ; u : entre
  1,35 et 2 et au moins 26 px de large ; p sinon) : à vérifier à l'œil. Le script ne distingue
  pas sûrement la virga simple de la virga épisémée (--type ne fait que trier) : choisir à l'œil.

Sortie dans cache/candidats/ : une planche et une liste par motif, <nom>_<motif>.png et .json
(dans le nom de fichier, `|` devient `-`). Chaque candidat donne la boîte de l'ensemble
(x, y, w, h) et celle du seul neume de base qui porte les subpunctis (`base`), à reporter dans
la colonne `base` de sources/exemplaires.csv pour l'import calé (import_hartker.py … base).
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


def parse_motif(m):
    parts = m.split("|")
    avant, sous = parts[0], parts[1] if len(parts) > 1 else ""
    k = int(parts[2]) if len(parts) > 2 and parts[2] else 1
    return avant, sous, k


def analyse(seg, TG, seuil):
    """Pour chaque neume de base reconnu : voisins de base à gauche, prepunctis, subpunctis, et
    le glyphe de base dont les gabarits ressemblent le plus (`type`)."""
    T = [t for ts in TG.values() for t in ts]
    out = []
    for key, comps in seg.items():
        bases = [v for v in comps if 40 <= v["h"] <= 110 and 30 <= v["w"] <= 110 and H.score(v, T) >= seuil]
        for v in bases:
            # neumes de base côte à côte à gauche (bivirga, trivirga), pied à la même hauteur
            row, cur = [v], v
            while True:
                left = [b for b in bases if b is not cur and 0 < cur["x"] - b["x"] <= 75
                        and abs((b["y"] + b["h"]) - (cur["y"] + cur["h"])) <= 22]
                if not left:
                    break
                cur = max(left, key=lambda b: b["x"])
                row.insert(0, cur)
            first = row[0]
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
            pre = sorted([c for c in comps if small(c) and first["x"] - 150 <= c["x"] and c["x"] + c["w"] <= first["x"] + 12
                          and first["y"] + 0.35 * first["h"] <= c["y"] <= first["y"] + first["h"] + 30], key=lambda c: c["x"])
            typ = max(TG, key=lambda g: H.score(v, TG[g]))
            out.append(dict(key=key, v=v, row=row, chain=chain, pre=pre, s=H.score(v, T), type=typ,
                            sous="".join(kind(c) for c in chain), avant="".join(kind(c) for c in pre)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nom")
    ap.add_argument("--base", nargs="+", required=True)
    ap.add_argument("--motifs", nargs="+", required=True)
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--par-page", type=int, default=2)
    ap.add_argument("--seuil", type=float, default=0.25)
    ap.add_argument("--pages", nargs="*", help="limiter la recherche à ces pages (volume:page), "
                    "par exemple les pages sources données par sources_nr.py")
    ap.add_argument("--type", help="ne garder que les neumes de base les plus proches de ce glyphe "
                    "(ex. --base vi viN --type vi : virgas sans épisème) ; classement indicatif")
    args = ap.parse_args()
    seg = H.load_seg()
    with open(os.path.join(H.SKILL, "sources", "exemplaires.csv"), encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["glyph"] in args.base]
    keep = {H.norm_page(*p.split(":")) for p in args.pages} if args.pages else None
    TG = {}
    for r in rows:
        key = (r["manuscript"], r["page"])
        if key in seg:
            box = list(map(int, r["base"].split(","))) if r.get("base") else [int(r[k]) for k in "xywh"]
            c = H.comp_in(seg, key[0], key[1], *box)
            if c:
                TG.setdefault(r["glyph"], []).append(H.template(c))
    if not TG:
        raise SystemExit("aucun gabarit de base dans les pages segmentées")
    found = analyse({k: v for k, v in seg.items() if keep is None or k in keep} if keep else seg, TG, args.seuil)
    if args.type:
        found = [f for f in found if f["type"] == args.type]
    out = os.path.join(H.CACHE, "candidats")
    os.makedirs(out, exist_ok=True)
    for motif in args.motifs:
        avant, sous, k = parse_motif(motif)
        # correspondance exacte : un point d'un neume voisin dans la zone « avant » écarte le
        # candidat, ce qui évite de confondre climacus et climacus à prepunctis
        hits = [f for f in found if f["sous"] == sous and f["avant"] == avant and len(f["row"]) == k]
        hits.sort(key=lambda f: -f["s"])
        seen, pick = {}, []
        for f in hits:
            if seen.get(f["key"], 0) >= args.par_page:
                continue
            seen[f["key"]] = seen.get(f["key"], 0) + 1
            parts = f["row"] + f["chain"] + (f["pre"][-len(avant):] if avant else [])
            x0, y0 = min(c["x"] for c in parts), min(c["y"] for c in parts)
            x1, y1 = max(c["x"] + c["w"] for c in parts), max(c["y"] + c["h"] for c in parts)
            v = f["v"]
            pick.append(dict(manuscript=f["key"][0], page=f["key"][1], x=x0, y=y0, w=x1 - x0, h=y1 - y0,
                             base="%d,%d,%d,%d" % (v["x"], v["y"], v["w"], v["h"]), score=round(float(f["s"]), 3)))
            if len(pick) == args.n:
                break
        tag = "%s_%s" % (args.nom, motif.replace("|", "-"))
        print("%-12s %3d candidats" % (motif, len(pick)), flush=True)
        if not pick:
            continue
        cells = []
        for i, c in enumerate(pick):
            im = H.crop(c["manuscript"], c["page"], c["x"], c["y"], c["w"], c["h"], pad=20, zoom=3, box=True)
            im.thumbnail((400, 400))
            cells.append(("%d. %s p.%s" % (i, c["manuscript"][-3:], c["page"].lstrip("0")), im))
        H.grid(cells, 6, "%s : base %s, motif « %s »" % (args.nom, "/".join(args.base), motif), cell_w=420).save(
            os.path.join(out, tag + ".png"))
        with open(os.path.join(out, tag + ".json"), "w", encoding="utf-8") as fh:
            json.dump(pick, fh, indent=0)


if __name__ == "__main__":
    main()
