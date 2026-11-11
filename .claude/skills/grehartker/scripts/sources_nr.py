"""Trouve, pour un neume rare, les pièces NR qui l'emploient et leur page source dans Hartker.

Usage (Python ordinaire) :
    python -I S/sources_nr.py <neume NABC ou nom de glyphe> [--nr <dossier NR>] [--telecharger]

Exemples : `st>`, `ds>`, `gr-`, `vi->` ; un nom de glyphe gregall est converti (`viNB` -> `vi->`,
B = `>`, N = `-`, E = `!`, T = `~`).

Le script cherche le neume dans les NABC des gabc/*_marteo.gabc (recherche de sous-chaîne,
à vérifier sur le contexte affiché), puis lit pour chaque pièce le lien e-codices donné par
https://nocturnale.marteo.fr/chant/<code> (pièces venant de Hartker seulement). Il affiche la
syllabe et le neume pour retrouver l'endroit sur la page, puis les pages par nombre de pièces.
--telecharger : télécharge les bandes de ces pages (390 et 391 seulement) ; les segmenter
ensuite avec pages.py segmenter.
"""
import argparse
import collections
import glob
import os
import sys
import re
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402

SITE = "https://nocturnale.marteo.fr/chant/%s"


def to_nabc(s):
    if re.fullmatch(r"[a-z]{2}[A-Za-z0-9]*", s) and any(ch.isupper() for ch in s):
        return s.replace("B", ">").replace("N", "-").replace("E", "!").replace("T", "~")
    return s


def source_of(code):
    req = urllib.request.Request(SITE % code, headers={"User-Agent": H.UA})
    try:
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    except Exception:
        return None
    m = re.search(r"e-codices\.unifr\.ch/[a-z]+/csg/(\d{4})/(\d+[a-z]?)", html)
    return (m.group(1), m.group(2)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("neume")
    ap.add_argument("--nr", default=H.repo("NR_REPO", "nocturnale-romanum"))
    ap.add_argument("--telecharger", action="store_true")
    args = ap.parse_args()
    nabc = to_nabc(args.neume)
    pat = re.compile(r"(?<!l)" + re.escape(nabc))
    hits = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(args.nr, "gabc", "*_marteo.gabc"))):
        code = os.path.basename(path)[:-len("_marteo.gabc")]
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for m in re.finditer(r"([^\s()]*)\(([^)]*)\)", text):
            parts = m.group(2).split("|")
            if any(pat.search(p) for p in parts[1:]):
                hits[code].append("%s(%s)" % (m.group(1), m.group(2)))
    if not hits:
        raise SystemExit("aucune pièce avec %s dans %s" % (nabc, args.nr))
    pages = collections.Counter()
    print("%d pièces avec %s" % (len(hits), nabc))
    for code, ctx in sorted(hits.items()):
        src = source_of(code)
        where = "csg-%s p.%s" % src if src else "(pas de source Hartker)"
        if src and src[0] in ("0390", "0391"):
            pages[src] += 1
        print("  %-12s %-22s %s" % (code, where, "  ".join(ctx[:3])))
    print("pages :", ", ".join("%s:%s (%d)" % (ms[-3:], p, n) for (ms, p), n in pages.most_common()))
    if args.telecharger:
        for ms, p in pages:
            print(H.download_band(ms, p), flush=True)


if __name__ == "__main__":
    main()
