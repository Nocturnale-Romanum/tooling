"""Cherche dans les pages segmentées les composantes qui ressemblent à des exemplaires connus.

Usage (Python ordinaire) :
    python -I S/candidats.py <nom> [--glyphe G …] [--repere E …] [--boite 391:53:x,y,w,h …]
                             [--gregall G …] [--pages 391:53 …] [--n 36] [--par-page 2] [--seuil 0.4]

Graines (au moins une) :
- --glyphe G   : toutes les lignes de G dans sources/exemplaires.csv (choix et variantes) ;
- --repere E   : toutes les lignes de E dans sources/reperes.csv ;
- --boite      : une boîte de page donnée à la main (volume:page:x,y,w,h, pixels pleine page) ;
- --gregall G  : le glyphe G de gregall, rendu à l'échelle de la page (10 unités par pixel), pour
                 une forme qui n'a encore aucun exemplaire (gabarit grossier : trier à l'œil) ;
                 seul son plus grand morceau sert (la ligature de clEpi, sans son punctum).
Chaque graine est ramenée à sa composante d'encre dans la segmentation (pages.py segmenter).
--pages : limiter la recherche à ces pages (volume:page), par exemple celles de sources_nr.py.
--trait T [--seuil-trait v] : ne garder que les composantes qui portent un trait mesuré (valeur ≥ v),
pour séparer les variantes d'une même famille que la ressemblance globale confond (avec par
exemple --glyphe cl clN comme graines) :
- pied     : le pied de la dernière jambe part vers la droite (clS, ciG) ; v ≈ 0,85 ;
- episeme  : encre en haut à droite (clN, viN…) ; v ≈ 0,4 ;
- boucle   : boucle fermée (cl>, vi>…) ; v ≈ 0,05 ;
- etroite  : forme haute et étroite ; v ≈ 0,3 ;
- patte    : la jambe droite descend plus bas que la gauche, en fraction de la hauteur (clM) ;
             v ≈ 0,25.

Sortie dans cache/candidats/ : <nom>.png (planche, au plus --par-page candidats par page, triés
par ressemblance) et <nom>.json (boîtes des candidats, dans l'ordre de la planche). On choisit
ensuite à l'œil ; une seule composante d'encre par candidat : pour les neumes en plusieurs
morceaux, utiliser motifs.py.
"""
import argparse
import csv
import json
import os
import sys

import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402


def seeds_from(args, seg):
    boxes = []
    for fn, key, wanted in (("exemplaires.csv", "glyph", args.glyphe), ("reperes.csv", "element", args.repere)):
        if not wanted:
            continue
        with open(os.path.join(H.SKILL, "sources", fn), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r[key] in wanted:
                    boxes.append((r["manuscript"], r["page"], *(int(r[k]) for k in "xywh")))
    for b in args.boite or []:
        vol, page, xywh = b.split(":")
        ms, p = H.norm_page(vol, page)
        boxes.append((ms, p, *map(int, xywh.split(","))))
    comps = []
    for g in args.gregall or []:
        im = H.gregall_image(g, 100).convert("L")
        lab, n = ndi.label(np.asarray(im) < 128)
        m = lab == 1 + int(np.argmax(ndi.sum(lab > 0, lab, range(1, n + 1))))   # le morceau principal seul
        ys, xs = np.nonzero(m)
        m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        comps.append((("gregall", g), dict(x=-1, y=-1, w=m.shape[1], h=m.shape[0], mask=m)))
    for ms, p, x, y, w, h in boxes:
        if (ms, p) not in seg:
            print("page %s %s non segmentée : pages.py telecharger puis segmenter" % (ms, p))
            continue
        c = H.comp_in(seg, ms, p, x, y, w, h)
        if c:
            comps.append(((ms, p), c))
    return comps


def traits(m):
    """Traits de forme d'un masque (voir --trait)."""
    h, w = m.shape
    bot = m[int(h * 0.85):]
    bx = np.nonzero(bot)[1]
    top = m[:max(2, int(h * 0.2))]
    return dict(pied=(bx.max() + 1) / w if len(bx) else 0,
                episeme=top[:, int(w * 0.6):].sum() / top.sum() if top.sum() else 0,
                boucle=(ndi.binary_fill_holes(m) & ~m).sum() / max(1, m.sum()),
                etroite=1 - w / h,
                patte=patte(m))


def patte(m):
    h, w = m.shape
    left, right = np.nonzero(m[:, :w // 2])[0], np.nonzero(m[:, w // 2:])[0]
    return (right.max() - left.max()) / h if len(left) and len(right) else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nom")
    ap.add_argument("--glyphe", nargs="*")
    ap.add_argument("--repere", nargs="*")
    ap.add_argument("--boite", nargs="*")
    ap.add_argument("--gregall", nargs="*")
    ap.add_argument("--pages", nargs="*")
    ap.add_argument("--n", type=int, default=36)
    ap.add_argument("--par-page", type=int, default=2)
    ap.add_argument("--seuil", type=float, default=0.4)
    ap.add_argument("--trait", choices=["pied", "episeme", "boucle", "etroite", "patte"])
    ap.add_argument("--seuil-trait", type=float, default=0.5)
    args = ap.parse_args()
    seg = H.load_seg()
    seeds = seeds_from(args, seg)
    if args.pages:
        keep = {H.norm_page(*p.split(":")) for p in args.pages}
        seg = {k: v for k, v in seg.items() if k in keep}
    if not seeds:
        raise SystemExit("aucune graine trouvée")
    T = [H.template(c) for _, c in seeds]
    hs = [c["h"] for _, c in seeds]
    ws = [c["w"] for _, c in seeds]
    known = {(k, c["x"], c["y"]) for k, c in seeds}
    found = []
    for key, comps in seg.items():
        for c in comps:
            if not (0.6 * min(hs) <= c["h"] <= 1.6 * max(hs) and 0.6 * min(ws) <= c["w"] <= 1.6 * max(ws)):
                continue
            if (key, c["x"], c["y"]) in known:
                continue
            if args.trait and traits(c["mask"])[args.trait] < args.seuil_trait:
                continue
            s = H.score(c, T)
            if s >= args.seuil:
                found.append((s, key, c))
    found.sort(key=lambda t: -t[0])
    seen, pick = {}, []
    for s, key, c in found:
        if seen.get(key, 0) >= args.par_page:
            continue
        seen[key] = seen.get(key, 0) + 1
        pick.append(dict(manuscript=key[0], page=key[1], x=c["x"], y=c["y"], w=c["w"], h=c["h"], score=round(float(s), 3)))
        if len(pick) == args.n:
            break
    out = os.path.join(H.CACHE, "candidats")
    os.makedirs(out, exist_ok=True)
    cells = []
    for i, c in enumerate(pick):
        im = H.crop(c["manuscript"], c["page"], c["x"], c["y"], c["w"], c["h"], pad=35, zoom=3, box=True)
        im.thumbnail((280, 300))
        cells.append(("%d. %s p.%s" % (i, c["manuscript"][-3:], c["page"].lstrip("0")), im))
    H.grid(cells, 9, "%s : %d candidats (%d graines, %d pages)" % (args.nom, len(pick), len(seeds), len(seg)), cell_w=290).save(
        os.path.join(out, args.nom + ".png"))
    with open(os.path.join(out, args.nom + ".json"), "w", encoding="utf-8") as f:
        json.dump(pick, f, indent=0)
    print(os.path.join(out, args.nom + ".png"))


if __name__ == "__main__":
    main()
