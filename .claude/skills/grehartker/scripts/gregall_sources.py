"""Provenance des glyphes de gregall, d'après la documentation de Gregorio (GregorioNabcRef.tex,
« manuscript sources of the gregall font ») : reference/gregall_sources.tsv.

Usage (Python ordinaire) :
    python -I S/gregall_sources.py [<GregorioNabcRef.tex ou .tex.gz>]

Par défaut, la source est cherchée dans la documentation TeX Live
(texmf-dist/doc/luatex/gregoriotex ou /usr/share/doc/texlive-doc/luatex/gregoriotex).

Colonnes : glyphe (nom gregall), nabc, source (code de la doc : C = Cantatorium 359,
E = Einsiedeln 121, H = Hartker, G = 339, N = 376, A = 374, B = Bamberg), pour Hartker manuscript
et page (H<n> = 390 p. n jusqu'à 194, puis 391 p. n − 194), piece (incipit) et ref (édition :
NR, AM…), mot (syllabe ou mot du manuscrit), echelle (facteur noté dans la doc, image agrandie).
La page est celle du début de la pièce : le neume peut être sur la page suivante.
"""
import csv
import glob
import gzip
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402

DOCS = ["/usr/share/doc/texlive-doc/luatex/gregoriotex/GregorioNabcRef.tex*",
        "/usr/share/texlive/texmf-dist/doc/luatex/gregoriotex/GregorioNabcRef.tex*",
        "/usr/local/texlive/*/texmf-dist/doc/luatex/gregoriotex/GregorioNabcRef.tex*",
        "C:/Program Files/MiKTeX/doc/luatex/gregoriotex/GregorioNabcRef.tex*"]


def read(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return f.read()


def glyph_name(nabc):
    return nabc.replace("-", "N").replace(">", "B").replace("~", "T").replace("!", "E")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else next((p for d in DOCS for p in sorted(glob.glob(d))), None)
    if not path:
        raise SystemExit("GregorioNabcRef.tex introuvable : le donner en argument")
    text = read(path)
    start = text.index("manuscript sources of the gregall font")
    end = text.index("manuscript sources of the grelaon font")
    part = text[start:end]
    pieces = {}
    for m in re.finditer(r"\\texttt\{(H\d+[A-Z])\} ([^&\\\n]+?)(?: \\texttt\{([^}]*)\})?(?:\\\\|$)", part, re.M):
        pieces[m.group(1)] = (m.group(2).strip(), m.group(3) or "")
    rows, section = [], ""
    for line in part.split("\n"):
        m = re.search(r"\\multicolumn\{\d\}\{l\}\{\\textbf\{(.*?)\}\}", line)
        if m:
            section = m.group(1)
            continue
        m = re.match(r"\\sneume\{.*?\} & \\texttt\{(.*?)\} & \\texttt\{([A-Z]\d+[A-Za-z]*)\} & ([^&\\]*)(.*)", line)
        if not m:
            continue
        nabc, src, mot, rest = m.groups()
        ech = re.search(r"\\fbox\{([\d.]+)x\}", rest)
        r = dict(glyphe=glyph_name(nabc), nabc=nabc, section=section, source=src, manuscript="", page="",
                 piece="", ref="", mot=mot.strip(), echelle=ech.group(1) if ech else "")
        if src.startswith("H"):
            n = int(re.match(r"H(\d+)", src).group(1))
            r["manuscript"], r["page"] = ("csg-0390", n) if n <= 194 else ("csg-0391", n - 194)
            r["page"] = "%03d" % r["page"]
            r["piece"], r["ref"] = pieces.get(src, ("", ""))
        rows.append(r)
    out = os.path.join(H.SKILL, "reference", "gregall_sources.tsv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "glyphes,", sum(r["source"].startswith("H") for r in rows), "de Hartker ->", out)


if __name__ == "__main__":
    main()
