"""Mesure la localisation sur les exemplaires validés dont la pièce et la syllabe sont sûres
(colonne piece avec « ; », issus des bandes de localiser.py et désignés par marteo).

Usage (Python ordinaire) :
    python -I S/evaluer_localisation.py [max]            V=1 : détail par cas ; METH=page : ancienne méthode
Réussite : centre trouvé à moins de max(60 px, demi-largeur + 20) du centre de l'exemplaire ;
« dans la bande » : à moins de 150 px en hauteur et 900 px en largeur. Biais : marteo n'a
désigné que des neumes visibles sur les bandes, les échecs de l'ancienne méthode y manquent."""
import sys, os, csv, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hartker as H0
K = H0.SKILL
import hartker as H, localiser as L
seg = H.load_seg(); decs = L.decompositions(); pn = H.pieces_nr(); pr = H.piece_rows()
cases = []
for r in csv.DictReader(open(K + "/sources/exemplaires.csv", encoding="utf-8")):
    if " ; " not in (r["piece"] or ""): continue
    m = re.match(r"(\S+) .*?\(([^)]*)\)", r["piece"] or "")
    if not m or m.group(1) == "?" or m.group(1) not in pn or m.group(1) not in pr: continue
    code, syl = m.group(1), m.group(2).split(",")[0].strip()
    p = pn[code]
    if p["manuscript"] != r["manuscript"]: continue
    if not any(r["glyph"] in x["glyphes"].split() for x in pr[code]): continue
    cases.append((r["glyph"], code, syl, p["page"], r))
mx = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 6
fn = lambda *a: L.locate(*a, methode=os.environ.get("METH", "marques"))
ok = band = n = 0
for g, code, syl, page, r in cases[:mx]:
    tx, ty = int(r["x"]) + int(r["w"]) / 2, int(r["y"]) + int(r["h"]) / 2
    res = [f for f in fn(seg, code, r["manuscript"], page, g, decs) if f["page"] == r["page"]]
    rs = [f for f in res if re.sub(r"<[^>]*>", "", f["syllabe"]).strip(" ,.;:*") .lower().startswith(syl.strip(" ,.;:*").lower()[:3])] or res
    n += 1
    if rs:
        d = min(((f["x"] + f["w"] / 2 - tx) ** 2 + (f["y"] + f["h"] / 2 - ty) ** 2) ** .5 for f in rs)
        b = any(abs(f["y"] + f["h"] / 2 - ty) < 150 and abs(f["x"] + f["w"] / 2 - tx) < 900 for f in rs)
        ok += d < max(60, int(r["w"]) / 2 + 20); band += b
        if os.environ.get("V"): print("%-14s %s p.%s %-10s d=%5d %-6s %s conf %.2f" % (g, r["manuscript"][-3:], r["page"], code, d, "bande" if b else "", rs[0].get("methode"), rs[0]["score"]))
    elif os.environ.get("V"): print("%-14s %s p.%s %-10s rien" % (g, r["manuscript"][-3:], r["page"], code))
print("cas %d : neume exact %d (%.0f %%), dans la bande %d (%.0f %%)" % (n, ok, 100 * ok / n, band, 100 * band / n))
