"""Repère les lettres significatives (`lsc`, `lst`…) dans Hartker, autour de leur neume porteur, et
prépare les planches de choix (même démarche qu'auto.py).

Usage (Python ordinaire) :
    python -I S/lettres.py <lettre> […] [--n 4] [--inscrire]

1. localiser.py <lettre> donne, pour chaque pièce NR, la boîte du neume qui porte la lettre (le
   complex glyph qui la précède dans le fragment NABC) : bandes cache/candidats/loc_<lettre>*.json ;
2. la position NABC de la lettre (chiffre après le code : 1 2 3 au-dessus, 4 et 6 à gauche et à
   droite, 7 8 9 au-dessous, comme un pavé numérique) délimite une zone autour du neume ;
3. dans cette zone, hors lignes de texte et hors composantes du neume porteur, la composante qui
   ressemble le plus à la lettre de gregall (rendue à l'échelle de la page) est retenue, moins une
   pénalité de distance au point attendu ; les autres morceaux de la lettre gregall sont cherchés
   à leur place (auto.others) ;
4. sortie cache/candidats/auto_<lettre>.json ; --inscrire : les --n meilleures (pages
   différentes) deviennent choix et variantes provisoires (« à valider ») et la planche
   cache/planches/auto_<lettre>.png est faite.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hartker as H  # noqa: E402
import localiser as L  # noqa: E402
import auto as A  # noqa: E402

MARGE = 110       # étendue de la zone de recherche hors du neume (pixels de page)
DIST = 0.3        # pénalité par 100 px d'écart au point attendu


def zone(pos, x0, y0, x1, y1):
    """(zx0, zy0, zx1, zy1, point attendu) pour une position NABC autour de la boîte du neume."""
    col = {1: 0, 4: 0, 7: 0, 2: 1, 8: 1, 3: 2, 6: 2, 9: 2}.get(pos, 1)
    lig = {1: 0, 2: 0, 3: 0, 4: 1, 6: 1, 7: 2, 8: 2, 9: 2}.get(pos, 0)
    xs = [(x0 - MARGE, x0 + 40), (x0 - 30, x1 + 30), (x1 - 40, x1 + MARGE)][col]
    ys = [(y0 - MARGE, y0 + 30), (y0 - 30, y1 + 30), (y1 - 30, y1 + MARGE)][lig]
    ex = [x0 - 25, (x0 + x1) / 2, x1 + 25][col]
    ey = [y0 - 40, (y0 + y1) / 2, y1 + 40][lig]
    return xs[0], ys[0], xs[1], ys[1], (ex, ey)


def chercher(seg, f, lettre, pieces):
    key = (f["manuscript"], f["page"])
    m = re.search(re.escape(lettre) + r"(\d)", f["nabc"])
    pos = int(m.group(1)) if m else 2
    x0, y0, x1, y1 = f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"]
    zx0, zy0, zx1, zy1, (ex, ey) = zone(pos, x0, y0, x1, y1)
    tl = L.text_lines(key)
    refus = A.rejected(lettre, key)
    bx, by, bw, bh, bm = pieces[0]
    t = dict(n=H.norm(bm), h=bh, w=bw)
    best = None
    for c in seg[key]:
        cx, cy = c["x"] + c["w"] / 2, c["y"] + c["h"] / 2
        if not (zx0 <= cx <= zx1 and zy0 <= cy <= zy1) or c["h"] < 10:
            continue
        if any(abs(cy - y) < 35 for y in tl):
            continue
        inter = max(0, min(x1, c["x"] + c["w"]) - max(x0, c["x"])) * max(0, min(y1, c["y"] + c["h"]) - max(y0, c["y"]))
        if inter > 0.5 * c["w"] * c["h"]:
            continue                                  # morceau du neume porteur
        if any(abs(c["x"] - x) <= 5 and abs(c["y"] - y) <= 5 for x, y in refus):
            continue
        s = A.score(c, t)
        adj = s - DIST * ((cx - ex) ** 2 + (cy - ey) ** 2) ** 0.5 / 100
        if best is None or adj > best[0]:
            best = (adj, s, c)
    if best is None:
        return None
    adj, s, c = best
    extra, frac = A.others(seg, key, c, pieces, tl) if len(pieces) > 1 else ([], 1)
    comps = [c] + extra
    X0, Y0 = min(d["x"] for d in comps), min(d["y"] for d in comps)
    X1, Y1 = max(d["x"] + d["w"] for d in comps), max(d["y"] + d["h"] for d in comps)
    return dict(manuscript=key[0], page=key[1], x=X0, y=Y0, w=X1 - X0, h=Y1 - Y0,
                base="%d,%d,%d,%d" % (c["x"], c["y"], c["w"], c["h"]), score=round(float(s), 2),
                morceaux=round(frac, 2), adj=round(float(adj), 2),
                piece="%s ; %s (position %d) ; repéré automatiquement autour du neume porteur, à valider"
                % (f["piece"], f["nabc"], pos))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lettres", nargs="+")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--inscrire", action="store_true")
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    jobs = []
    for g in args.lettres:
        found = []
        for p in sorted(glob.glob(os.path.join(H.CACHE, "candidats", "loc_%s.json" % g))
                        + glob.glob(os.path.join(H.CACHE, "candidats", "loc_%s_[b-z].json" % g))):
            with open(p, encoding="utf-8") as fh:
                found += json.load(fh)
        if not found:
            print(g, ": pas de bandes (localiser.py)")
            continue
        pieces = A.gregall_pieces(g)
        out = []
        for key in sorted({(f["manuscript"], f["page"]) for f in found}):
            seg = H.load_seg([key])
            for f in found:
                if (f["manuscript"], f["page"]) == key:
                    p = chercher(seg, f, g, pieces)
                    if p:
                        out.append(p)
        for i, p in enumerate(out):
            print("%s %d. %s p.%s %s,%s,%s,%s score %s  %s" % (g, i, p["manuscript"][-3:], p["page"], p["x"], p["y"],
                                                              p["w"], p["h"], p["score"], p["piece"][:60]))
        with open(os.path.join(H.CACHE, "candidats", "auto_%s.json" % g), "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=0)
        if args.inscrire and out:
            order, pages = [], set()
            for i in sorted(range(len(out)), key=lambda i: -out[i]["adj"]):
                k = (out[i]["manuscript"], out[i]["page"])
                if k not in pages and len(order) < args.n:
                    order.append(i)
                    pages.add(k)
            subprocess.run([sys.executable, "-I", os.path.join(here, "retenir.py"), g, "auto_" + g] + [str(i) for i in order], check=True)
            jobs.append([sys.executable, "-I", os.path.join(here, "planche.py"), "auto_" + g, g])
    for c in jobs:
        subprocess.run(c)


if __name__ == "__main__":
    main()
