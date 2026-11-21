"""Repère seul le neume dans les bandes de localiser.py, avec gregall comme graine, et prépare
les planches de choix (marteo valide ou corrige).

Usage (Python ordinaire) :
    python -I S/auto.py <glyphe> […] [--sur BASE] [--graine BASE] [--n 4] [--inscrire]

--graine BASE : le gabarit du plus grand morceau est l'exemplaire choisi de BASE (forme et
taille de Hartker) au lieu de gregall ; gregall ne sert plus qu'à placer les autres morceaux.
Les bandes lues sont loc_<glyphe>.json et les séries suivantes loc_<glyphe>_b, _c… (--autre) ;
--serie c : seulement la série c (nouvelles propositions sans reprendre les pages écartées).
Les exemplaires déjà validés du glyphe (sans « à valider ») restent en tête, le choix inchangé.

Pour chaque bande de cache/candidats/loc_<glyphe>.json :
1. gregall rendu à l'échelle de la page (10 unités par pixel), découpé en morceaux d'encre ; son
   plus grand morceau sert de gabarit ;
2. chaque composante de la bande (hors lignes de texte) reçoit un score : ressemblance au
   gabarit (hartker.score, écart de taille peu pénalisé : gregall n'est pas à l'échelle de
   Hartker), moins une pénalité selon la distance à la position estimée par l'alignement ;
3. pour un glyphe en plusieurs morceaux, gregall est posé sur chacune des meilleures composantes
   (mis à son échelle) et l'on cherche les autres morceaux à leur place attendue (points,
   tractulus, virga) ; la proportion trouvée s'ajoute au score ; la boîte réunit les morceaux
   trouvés. --large : toute la page de chaque bande, sans a priori de position (dernier recours :
   peut trouver une forme semblable ailleurs sur la page, comme pour poGN ; vérifier d'abord
   si la boîte de la bande n'est pas déjà la bonne) ;
4. sortie : cache/candidats/auto_<glyphe>.json (boîtes, score, colonne base) ; avec --inscrire,
   les --n meilleures (pages différentes) sont inscrites comme choix et variantes provisoires
   (retenir.py) et la planche cache/planches/auto_<glyphe>.png est faite (planche.py, --sur BASE
   si donné). La pièce et la syllabe viennent de la bande.
"""
import argparse
import json
import os
import re
import subprocess
import sys

import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402
import localiser as L  # noqa: E402


DIST = float(os.environ.get("AUTO_DIST", 0.4))   # pénalité de distance (par 300 px)


BONUS_MORCEAUX = 0.15   # autres morceaux de gregall trouvés à leur place (un point près d'un trait
                        # quelconque ne doit pas l'emporter sur la forme : pr de la série c)
MIN_FORME = 0.25        # ressemblance minimale pour inscrire une proposition (avec --graine : gabarit
                        # tiré de Hartker ; avec gregall, les ressemblances sont plus basses)


def gregall_pieces(g):
    """Morceaux d'encre de gregall à l'échelle de la page : [(x, y, w, h, masque)], plus grand d'abord."""
    im = np.asarray(H.gregall_image(g, 100).convert("L")) < 128
    lab, _ = ndi.label(im)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        m = lab[sl] == i
        if m.sum() >= 4:
            out.append((sl[1].start, sl[0].start, m.shape[1], m.shape[0], m))
    return sorted(out, key=lambda p: -p[4].sum())


def score(c, t):
    n = H.norm(c["mask"])
    iou = np.minimum(n, t["n"]).sum() / np.maximum(n, t["n"]).sum()
    return iou - 0.35 * abs(np.log(c["h"] / t["h"])) - 0.35 * abs(np.log(c["w"] / t["w"]))


def seed(seg, base):
    """Gabarit tiré de l'exemplaire choisi de base."""
    import csv
    with open(os.path.join(H.SKILL, "sources", "exemplaires.csv"), encoding="utf-8") as fh:
        r = next(r for r in csv.DictReader(fh) if r["glyph"] == base and r["role"] == "choisi")
    if r["base"]:
        c = H.comp_in(seg, r["manuscript"], r["page"], *[int(v) for v in r["base"].split(",")])
        return dict(n=H.norm(c["mask"]), h=c["h"], w=c["w"])
    # sans colonne base : toutes les composantes de la boîte (neume en plusieurs traits)
    import planche
    m = planche.whole(seg, r, pale=True)["mask"]      # traits pâles compris (hampe de vs, de qi…)
    return dict(n=H.norm(m), h=m.shape[0], w=m.shape[1])


def rejected(glyph, key):
    """Coins (x, y) des propositions écartées par marteo pour ce glyphe sur cette page
    (reperes.csv : « proposé à tort pour <glyphe> »)."""
    import csv
    with open(os.path.join(H.SKILL, "sources", "reperes.csv"), encoding="utf-8") as fh:
        return [(int(r["x"]), int(r["y"])) for r in csv.DictReader(fh)
                if (r["manuscript"], r["page"]) == key and glyph and ("à tort pour %s " % glyph) in r["note"] + " "]


def others(seg, key, c, pieces, tl):
    """Les autres morceaux de gregall, posés d'après la composante c (plus grand morceau), mis à
    l'échelle de c : pour chacun, la composante de la page la plus proche de la place attendue
    (à moins de 30 px × échelle, taille compatible). Renvoie (composantes trouvées, fraction)."""
    bx, by, bw, bh, _ = pieces[0]
    k = (c["w"] / bw + c["h"] / bh) / 2
    cx0, cy0 = c["x"] + c["w"] / 2, c["y"] + c["h"] / 2
    found = []
    for px, py, pw, ph, _ in pieces[1:]:
        ex = cx0 + (px + pw / 2 - (bx + bw / 2)) * k
        ey = cy0 + (py + ph / 2 - (by + bh / 2)) * k
        best = None
        for d in seg[key]:
            if d is c or d in found or any(abs(d["y"] + d["h"] / 2 - y) < 35 for y in tl):
                continue
            dist = ((d["x"] + d["w"] / 2 - ex) ** 2 + (d["y"] + d["h"] / 2 - ey) ** 2) ** 0.5
            size = max(d["w"] * d["h"], 1) / max(pw * ph * k * k, 1)
            if dist < 30 * k and 0.3 < size < 3.5 and (best is None or dist < best[0]):
                best = (dist, d)
        if best:
            found.append(best[1])
    return found, len(found) / max(1, len(pieces) - 1)


def pick(seg, f, pieces, tpl=None, graine="gregall", large=False):
    key = (f["manuscript"], f["page"])
    fx, fy, fw, fh = map(int, f["fenetre"].split(","))
    if large:                                    # page entière, sans a priori de position
        fx, fy, fw, fh = H.BAND
    tl = L.text_lines(key)
    ex, ey = f["x"] + f["w"] / 2, f["y"] + f["h"] / 2
    bx, by, bw, bh, bm = pieces[0]
    refus = rejected(f.get("glyphe_cible"), key)
    t = tpl or dict(n=H.norm(bm), h=bh, w=bw)
    cands = []
    for c in seg[key]:
        cx, cy = c["x"] + c["w"] / 2, c["y"] + c["h"] / 2
        if not (fx <= cx <= fx + fw and fy <= cy <= fy + fh) or c["h"] < 15:
            continue
        if any(abs(cy - y) < 35 for y in tl):         # lettre de la ligne de texte
            continue
        if any(abs(c["x"] - x) <= 5 and abs(c["y"] - y) <= 5 for x, y in refus):
            continue                                  # déjà écarté par marteo (reperes.csv)
        s = score(c, t)
        d = 0 if large else ((cx - ex) ** 2 + (2 * (cy - ey)) ** 2) ** 0.5
        cands.append((s - DIST * d / 300, s, c))
    if not cands:
        return None
    cands.sort(key=lambda t: -t[0])
    best = None
    for adj, s, c in cands[:(150 if large else 40) if len(pieces) > 1 else 1]:
        extra, frac = others(seg, key, c, pieces, tl) if len(pieces) > 1 else ([], 1)
        tot = adj + (1.0 if large else BONUS_MORCEAUX) * frac
        if best is None or tot > best[0]:
            best = (tot, adj, s, c, extra, frac)
    tot, adj, s, c, extra, frac = best
    comps = [c] + extra
    x0, y0 = min(d["x"] for d in comps), min(d["y"] for d in comps)
    x1, y1 = max(d["x"] + d["w"] for d in comps), max(d["y"] + d["h"] for d in comps)
    return dict(manuscript=key[0], page=key[1], x=x0, y=y0, w=x1 - x0, h=y1 - y0,
                base="%d,%d,%d,%d" % (c["x"], c["y"], c["w"], c["h"]), score=round(float(s), 2), morceaux=round(frac, 2),
                adj=round(float(tot), 2), piece="%s ; %s ; repéré automatiquement (graine %s), à valider" % (f["piece"], f["nabc"], graine))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glyphes", nargs="+")
    ap.add_argument("--sur")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--inscrire", action="store_true")
    ap.add_argument("--graine")
    ap.add_argument("--seuil", type=float, default=MIN_FORME, help="ressemblance minimale avec --graine")
    ap.add_argument("--calage", default="pied", help="calage de la surimpression --sur (planche.py)")
    ap.add_argument("--serie", help="ne lire que la série de bandes loc_<glyphe>_<serie> (b, c…)")
    ap.add_argument("--large", action="store_true", help="chercher sur toute la page de chaque bande, sans a priori de position")
    args = ap.parse_args()
    import csv
    import glob
    keys = set()
    for g in args.glyphes:
        for path in glob.glob(os.path.join(H.CACHE, "candidats", "loc_%s*.json" % g)):
            if re.fullmatch(r"loc_%s(_[b-h])?\.json" % re.escape(g), os.path.basename(path)):
                keys |= {(f["manuscript"], f["page"]) for f in json.load(open(path, encoding="utf-8"))}
    with open(os.path.join(H.SKILL, "sources", "exemplaires.csv"), encoding="utf-8") as fh:
        keys |= {(r["manuscript"], r["page"]) for r in csv.DictReader(fh) if r["glyph"] in set(args.glyphes) | {args.graine}}
    seg = H.load_seg(keys)              # seulement les pages utiles (mémoire)
    jobs = []
    for g in args.glyphes:
        import glob
        paths = sorted(p for p in glob.glob(os.path.join(H.CACHE, "candidats", "loc_%s*.json" % g))
                       if re.fullmatch(r"loc_%s(_[b-h])?\.json" % re.escape(g), os.path.basename(p)))
        if args.serie:
            paths = [p for p in paths if p.endswith("_%s.json" % args.serie)]
        found = [f for p in paths if os.path.exists(p) for f in json.load(open(p, encoding="utf-8"))]
        if not found:
            print(g, ": pas de bandes (localiser.py)")
            continue
        pieces = gregall_pieces(g)
        tpl = seed(seg, args.graine) if args.graine else None
        import csv
        with open(os.path.join(H.SKILL, "sources", "exemplaires.csv"), encoding="utf-8") as fh:
            kept = [dict(r) for r in csv.DictReader(fh) if r["glyph"] == g and "à valider" not in r["piece"]]
        done = {(r["manuscript"], r["page"]) for r in kept}
        out = kept + [p for p in (pick(seg, dict(f, glyphe_cible=g), pieces, tpl, args.graine or "gregall", args.large) for f in found)
                      if p and (p["manuscript"], p["page"]) not in done]
        for r in kept:
            r["adj"] = 99
        for i, p in enumerate(out):
            print("%s %d. %s p.%s %s,%s,%s,%s score %s morceaux %s  %s" % (g, i, p["manuscript"][-3:], p["page"], p["x"], p["y"], p["w"], p["h"], p.get("score", "validé"), p.get("morceaux", "-"), p["piece"][:50]))
        with open(os.path.join(H.CACHE, "candidats", "auto_%s.json" % g), "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=0)
        if args.inscrire and out:
            order, pages = [], set()
            for i in sorted(range(len(out)), key=lambda i: -float(out[i]["adj"])):
                if args.graine and out[i].get("score") is not None and out[i]["score"] < args.seuil:
                    continue
                k = (out[i]["manuscript"], out[i]["page"])
                if k not in pages and len(order) < args.n:
                    order.append(i)
                    pages.add(k)
            if not order:
                print(g, ": aucune proposition assez ressemblante")
                continue
            here = os.path.dirname(os.path.abspath(__file__))
            subprocess.run([sys.executable, "-I", os.path.join(here, "retenir.py"), g, "auto_" + g] + [str(i) for i in order], check=True)
            cmd = [sys.executable, "-I", os.path.join(here, "planche.py"), "auto_" + g, g]
            if args.sur and args.sur != g:
                cmd += ["--sur", args.sur, "--calage", args.calage]
            jobs.append(cmd)
    if jobs:
        # planche.py recharge la segmentation : remplacer ce processus (qui la garde en mémoire) par
        # un petit lanceur, sinon la machine manque de mémoire (planches tuées)
        path = os.path.join(H.CACHE, "candidats", "auto_planches.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(jobs, fh)
        os.execv(sys.executable, [sys.executable, "-I", "-c",
                                  "import json, subprocess, sys; [subprocess.run(c) for c in json.load(open(sys.argv[1]))]", path])


if __name__ == "__main__":
    main()
