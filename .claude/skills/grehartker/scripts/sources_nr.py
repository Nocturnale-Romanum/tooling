"""Trouve, pour un glyphe, les pièces NR qui l'emploient et leur page source dans Hartker.

Usage (Python ordinaire) :
    python -I S/sources_nr.py <glyphe> [<glyphe> …] [--telecharger] [--suivantes]

Le glyphe est un nom gregall (`viNB`, `scB`, `qlEcl`…). Les emplois viennent du vrai parseur de
gregoriotex-nabc.lua (cache/nabc_occurrences.tsv, alias compris : `vi>pp2` pose `scB`), les pages
de sources/pieces_nr.tsv (export de la base du site, export_pieces_nr.py). La page est celle où
commence la pièce : le neume peut être sur la suivante (--suivantes les ajoute).

Affiche, par page : les pièces, la syllabe et le fragment NABC, pour retrouver l'endroit ; puis la
source du glyphe dans gregall quand elle est dans Hartker (reference/gregall_sources.tsv), à
proposer parmi les variantes, et la liste des pages pour motifs.py --pages.
--telecharger : télécharge les bandes de ces pages ; les segmenter ensuite (pages.py segmenter).
"""
import argparse
import collections
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402


def gregall_source(glyph):
    with open(os.path.join(H.SKILL, "reference", "gregall_sources.tsv"), encoding="utf-8") as f:
        return next((r for r in csv.DictReader(f, delimiter="\t") if r["glyphe"] == glyph), None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glyphes", nargs="+")
    ap.add_argument("--telecharger", action="store_true")
    ap.add_argument("--suivantes", action="store_true")
    args = ap.parse_args()
    pn = H.pieces_nr()
    if not pn:
        raise SystemExit("sources/pieces_nr.tsv manque : lancer export_pieces_nr.py dans le shell du site")
    allpages = set()
    for glyph in args.glyphes:
        occ = H.occurrences(glyph)
        bypage = collections.defaultdict(lambda: collections.defaultdict(list))
        other = set()
        for code, syl, frag in occ:
            p = pn.get(code)
            if p:
                bypage[(p["manuscript"], p["page"])][code].append("%s(%s)" % (syl, frag))
            else:
                other.add(code)
        print("== %s : %d emplois, %d pièces d'après Hartker, %d d'autres sources"
              % (glyph, len(occ), sum(len(v) for v in bypage.values()), len(other)))
        for (ms, page), codes in sorted(bypage.items()):
            for code, ctx in sorted(codes.items()):
                print("  %s p.%-4s %-12s %-34s %s" % (ms[-3:], page.lstrip("0"), code,
                                                      pn[code]["incipit"].split(" V")[0][:34], "  ".join(ctx[:4])))
            allpages.add((ms, page))
            if args.suivantes and page.isdigit():
                allpages.add((ms, "%03d" % (int(page) + 1)))
        g = gregall_source(glyph)
        if g and g["manuscript"]:
            print("  gregall : %s p.%s, %s (%s), mot « %s »%s" % (g["manuscript"][-3:], g["page"].lstrip("0"), g["piece"],
                  g["ref"], g["mot"], (", image agrandie %s×" % g["echelle"]) if g["echelle"] else ""))
        elif g:
            print("  gregall : %s, mot « %s » (pas Hartker)" % (g["source"], g["mot"]))
    pages = sorted(allpages)
    print("pages :", " ".join("%s:%s" % (ms[-3:], p.lstrip("0")) for ms, p in pages))
    if args.telecharger:
        for ms, p in pages:
            print(H.download_band(ms, p), flush=True)


if __name__ == "__main__":
    main()
