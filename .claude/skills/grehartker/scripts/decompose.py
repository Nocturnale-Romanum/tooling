"""Décompose tous les glyphes utilisés dans NR en formes de base, et dresse l'inventaire des formes.

Usage (Python ordinaire) :
    python S/decompose.py reference/familles.tsv reference/decompositions.tsv reference/formes_de_base.tsv

Principe : un glyphe est une suite de formes de base. Une forme de base est soit un neume à un
seul tenant (`vi`, `viN`, `pe`, `clS`, `to`, `vs`…), soit un modèle d'élément pour les points et
traits (`pu` punctum : su, pp ; `ta` tractulus : t ; `taN` tractulus épisémé : u ; `gr` gravis :
w ; `grN` gravis épisémé : y ; `stB` stropha liquescente : x ; `suv`, tractulus à double
épisème, n'a pas encore de modèle : `taNN?`), soit une lettre significative (`lsc`, notée
`lsc@3` avec sa position), soit une forme sans glyphe propre dans gregall (les deux oriscus du
salicus, `or_salicus` en ∩ et `or_couche` en ~ ; l'oriscus du pressus minor, `or_pi`, pendant
court de la virga strata `vs` du pressus maior). Le c mi-long de `pflsc2` (`lsc_semi`, entre `lsc` et `lscw`) n'a pas non plus de
glyphe propre.

Les neumes de gregall en plusieurs morceaux (climacus, scandicus, pressus, salicus, strophae
répétées, trigonus…) sont décomposés d'après le dessin de gregall, qui fait foi (11 novembre
2026). Un « ? » marque un élément douteux, à faire confirmer.

Sorties :
- decompositions.tsv : lot, famille, glyphe, decomposition (formes séparées par ` + `, dans
  l'ordre d'écriture), statut, usages_NR. Statuts : `base` (le glyphe est lui-même une forme de
  base), `régulier` (décomposition déduite du nom), `d'après gregall` (neume en plusieurs
  morceaux, décomposé d'après le dessin), `à examiner` (décomposition douteuse), `ligature`
  (neumes liés par `!`, détourés d'un seul tenant : la ligature `ql!cl` est une forme de base ;
  ses points, traits et lettres restent des formes séparées).
- formes_de_base.tsv : inventaire des formes de base nécessaires, avec le nombre de glyphes
  et d'occurrences NABC de NR qui les emploient (un glyphe compte autant de fois qu'il contient
  la forme), et l'état de l'exemplaire de Hartker (sources/exemplaires.csv).

Lots : le lot « virga » réunit `vi`, `ci`, `sc`, `bv`, `tv` ; les formes de ces familles qui
contiennent un pes ou une clivis vont aux lots « pes » ou « clivis » ; les autres familles
forment chacune leur lot.
"""
import csv
import os
import re
import sys

LOT_VIRGA = {"vi", "ci", "sc", "bv", "tv"}
ELEM = {"": "pu", "t": "ta", "u": "taN", "v": "taNN?", "w": "gr", "x": "stB", "y": "grN"}

# neumes en plusieurs morceaux : décomposition (ordre d'écriture)
REGULIERES = {
    "ci": ["vi", "pu", "pu"],
    "ciN": ["viN", "pu", "pu"],
    "sc": ["pu", "pu", "vi"],
    "bv": ["vi", "vi"],
    "bvN": ["viN", "viN"],
    "tv": ["vi", "vi", "vi"],
    "tvN": ["viN", "viN", "viN"],
}
D_APRES_GREGALL = {
    # lot virga
    "ci1": ["vi", "pu", "pu", "pu"], "ciS": ["vi", "pu", "ta"], "ciS1": ["vi", "ta", "ta"],
    "ciM": ["vi", "pu", "gr"], "ciMN": ["viN", "pu", "gr"], "ciB": ["vi", "pu", "stB"],
    "scS": ["ta", "ta", "vi"], "scN": ["ta", "ta", "viN"], "scB": ["pu", "pu", "viB"],
    # vont aux lots pes / clivis
    "ciG": ["clS", "ta"], "ciG1": ["clS", "pu", "pu"],
    "scG": ["ta", "pe"], "scG1": ["pe", "vi"], "scGN1": ["peN", "vi"], "scM1": ["viN", "pe"],
    "scM2": ["vi", "pe"],
    # pressus
    "pr": ["vs", "pu"], "prN": ["vsN", "pu"], "prM": ["vs", "gr"], "prB": ["vs", "stB"],
    "pi": ["or_pi", "pu"], "piM1": ["or_pi", "ta"], "piB": ["or_pi", "stB"],
    # salicus
    "sa": ["pu", "or_salicus", "vi"], "saB": ["pu", "or_salicus", "viB"],
    "saN": ["pu", "or_salicus", "viN"], "sa1": ["pu", "or_couche", "vi"],
    "saN1": ["pu", "or_couche", "viN"], "saB2": ["ta", "or_couche", "viB"],
    "saM": ["vi", "or_salicus", "vi"], "saM1": ["vi", "or_couche", "vi"],
    "saM5": ["pu", "or_salicus", "vi"], "saM6": ["viN", "or_salicus", "vi"],
    "saMN1": ["vi", "or_salicus", "viN"], "saNB1": ["viN", "or_couche", "viB"],
    "saG": ["ta", "pq"],
    # strophae
    "ds": ["st", "st"], "dsN": ["st", "stN"], "dsB": ["st", "stB"],
    "ts": ["st", "st", "st"], "tsB": ["st", "st", "stB"], "tsN": ["st", "st", "stN"],
    "tsM": ["st", "st", "st"], "tsMN": ["st", "st", "stN"], "tsMB": ["st", "st", "stB"],
    # trigonus
    "tg": ["pu", "pu", "pu"], "tgS": ["pu", "pu", "ta"], "tgSN": ["pu", "pu", "taN"],
    "tgS3": ["pu", "pu", "ta", "ta"],
    # scandicus flexus
    "sf": ["pu", "pu", "cl"], "sfN": ["ta", "ta", "clN"], "sfS": ["ta", "ta", "cl"],
    # divers
    "peB2": ["ta", "taB"], "toG": ["ta", "cl"],
    # formes de gregall sans logique apparente, tranchées par marteo le 12 novembre 2026
    "pf1": ["pf"], "clN1": ["clSN"],
    # tranchés le 11 novembre 2026
    "trM": ["viN", "po"], "trG": ["ta", "po"], "poGN": ["clN", "viN"], "saM2": ["vi", "pq"],
    "saM4": ["viN", "or_couche", "vi"], "peG": ["vi", "vi"],
}
A_EXAMINER = {}
SANS_GLYPHE = {"or_salicus", "or_couche", "or_pi"}


def suffix_elements(rest):
    """Éléments des groupes pp…/su…/ls… qui suivent la base. Renvoie (avant, après, reste)."""
    before, after = [], []
    while rest:
        m = re.match(r"(pp|su)([tuvwxy]?)(\d)", rest)
        if m:
            (before if m.group(1) == "pp" else after).extend([ELEM[m.group(2)]] * int(m.group(3)))
            rest = rest[m.end():]
            continue
        m = re.match(r"ls([a-z]+?)(\d)", rest)
        if m:
            after.append("ls%s@%s" % (m.group(1), m.group(2)))
            rest = rest[m.end():]
            continue
        return before, after, rest
    return before, after, ""


def head_of(base):
    if base in REGULIERES:
        return REGULIERES[base], "régulier"
    if base in D_APRES_GREGALL:
        return D_APRES_GREGALL[base], "d'après gregall"
    if base in A_EXAMINER:
        return A_EXAMINER[base], "à examiner"
    return [base], "base"


# glyphes entiers dont le dessin gregall ne suit pas le nom (tranchés par marteo, 12 novembre 2026) :
# pflsc2 est dessiné comme deux clivis suivies d'un c mi-long, entre `lsc` et `lscw`.
GLYPHES = {
    "pflsc2": (["cl", "cl", "lsc_semi@2"], "d'après gregall"),
}


def decompose(glyph):
    if glyph in GLYPHES:
        dec, statut = GLYPHES[glyph]
        return " + ".join(dec), statut
    if glyph in ("ob", "cb", "ni") or glyph.startswith("ls"):
        return glyph, "base"
    if "E" in glyph[2:]:
        # ligature : seuls les morceaux qui se touchent sont liés. Pour un neume en plusieurs
        # morceaux (pi, pr, sa…), c'est son dernier morceau (à gauche du !) ou son premier (à
        # droite) ; les autres restent séparés (`clEpi = cl!or_pi + pu`). La virga d'un salicus
        # liée à une clivis se fond dans la clivis (`saEcl = pu + or_salicus + cl`). Les points,
        # traits et lettres de chaque segment restent des formes séparées.
        pieces, before, after = [], [], []
        for seg in glyph.split("E"):
            m = re.match(r"([a-z]{2}[SGMNBT]*\d?)", seg)
            bs, af, left = suffix_elements(seg[m.end():])
            if left:
                return "", "à examiner"
            pieces.append(head_of(m.group(1))[0]); before += bs; after += af
        out, lig = list(pieces[0][:-1]), [pieces[0][-1]]
        for nxt in pieces[1:]:
            lig.append(nxt[0])
            if len(nxt) > 1:
                out.append("!".join(lig)); out += nxt[1:-1]; lig = [nxt[-1]]
        out.append("!".join(lig))
        out = [re.sub(r"^vi!(cl[SGMNBT]*\d?)$", r"\1", f) for f in out]
        statut = "ligature" if any("!" in f for f in out) else "d'après gregall"
        return " + ".join(before + out + after), statut
    if glyph.startswith(("pp", "su")):
        before, after, left = suffix_elements(glyph)
        return (" + ".join(before + after), "régulier") if not left else ("", "à examiner")
    m = re.match(r"([a-z]{2}[SGMNBT]*\d?)", glyph)
    base = m.group(1)
    head, statut = head_of(base)
    before, after, left = suffix_elements(glyph[m.end():])
    if left:
        return "", "à examiner"
    if (before or after) and statut == "base":
        statut = "régulier"
    return " + ".join(before + head + after), statut


def lot_of(fam, dec, statut):
    if fam in LOT_VIRGA and statut != "ligature":
        elems = dec.split(" + ")
        if any(re.match(r"cl[SGMNBT]*\d?$", e) for e in elems):
            return "clivis"
        if any(re.match(r"pe[SGMNBT]*\d?$", e) for e in elems):
            return "pes"
        return "virga"
    return {"pe": "pes", "cl": "clivis"}.get(fam, fam)


def forme_type(f):
    if f.startswith("ls"):
        return "lettre"
    if f in ("ob", "cb", "ni"):
        return "crochet, vide"
    if f in SANS_GLYPHE:
        return "sans glyphe propre dans gregall"
    if "!" in f:
        return "ligature"
    if f in ("pu", "ta", "taN", "taNN", "gr", "grN", "stB"):
        return "modèle d'élément"
    return "neume"


def main(src, out, inv):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(src, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    res = []
    for r in rows:
        dec, statut = decompose(r["glyphe"])
        res.append({"lot": lot_of(r["famille"], dec, statut), "famille": r["famille"], "glyphe": r["glyphe"],
                    "decomposition": dec, "statut": statut, "usages_NR": r["usages_NR"]})
    ordre_lots = {"virga": 0, "pes": 1, "clivis": 2}
    ordre_statut = {"base": 0, "régulier": 1, "d'après gregall": 2, "à examiner": 3, "ligature": 4}
    res.sort(key=lambda r: (ordre_lots.get(r["lot"], 3), r["lot"], ordre_statut[r["statut"]], -int(r["usages_NR"])))
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(res[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(res)

    # inventaire des formes de base
    with open(os.path.join(root, "sources", "exemplaires.csv"), encoding="utf-8") as fh:
        chosen = {r["glyph"] for r in csv.DictReader(fh) if r["role"] == "choisi"}
    inv_rows = {}
    for r in res:
        u = int(r["usages_NR"])
        for f in r["decomposition"].split(" + "):
            f = f.split("@")[0]
            douteux = f.endswith("?")
            f = f.rstrip("?")
            e = inv_rows.setdefault(f, {"forme": f, "type": forme_type(f), "glyphes": 0, "occurrences_NR": 0,
                                        "douteux": "", "exemplaire": "choisi" if f in chosen else ""})
            e["glyphes"] += 1
            e["occurrences_NR"] += u
            if douteux:
                e["douteux"] = "oui"
    inv_list = sorted(inv_rows.values(), key=lambda e: -e["occurrences_NR"])
    with open(inv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["forme", "type", "glyphes", "occurrences_NR", "douteux", "exemplaire"],
                           delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(inv_list)

    for s in ordre_statut:
        sel = [r for r in res if r["statut"] == s]
        print("%-16s %3d glyphes %6d occurrences" % (s, len(sel), sum(int(r["usages_NR"]) for r in sel)))
    by_type = {}
    for e in inv_list:
        by_type.setdefault(e["type"], []).append(e)
    print("\n%d formes de base, dont %d avec un exemplaire choisi" % (len(inv_list), sum(1 for e in inv_list if e["exemplaire"])))
    for t, lst in by_type.items():
        print("  %-32s %3d" % (t, len(lst)))


if __name__ == "__main__":
    main(*sys.argv[1:4])
