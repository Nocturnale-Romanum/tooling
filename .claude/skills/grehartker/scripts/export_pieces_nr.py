"""Exporte, depuis la base du site NR, la page de Hartker de chaque pièce NR (propositions de marteo,
celles des gabc/*_marteo.gabc) : sources/pieces_nr.tsv, lu par sources_nr.py et retenir.py.

À lancer dans le shell Django du site (lecture seule), depuis le dossier du site :
    source venv/bin/activate
    SKILL=<skill> python manage.py shell < <skill>/scripts/export_pieces_nr.py

La sortie est <skill>/sources/pieces_nr.tsv. Relancer quand des pièces sont ajoutées ou que leur
source change.
"""
import csv
import os
import re

from home.models import Proposal

OUT = os.path.join(os.environ["SKILL"], "sources", "pieces_nr.tsv")
MS = {"CH-SGs 390": "csg-0390", "CH-SGs 391": "csg-0391"}

rows = []
for p in (Proposal.objects.filter(submitter__username="marteo", source__siglum__in=list(MS))
          .select_related("chant", "chant__feast", "source")):
    raw = p.sourcepage.strip()
    m = re.search(r"\d+[a-z]?", raw)
    if not m:
        continue
    page = m.group(0).zfill(3 + (not m.group(0)[-1].isdigit()))
    rows.append(dict(code=p.chant.code, manuscript=MS[p.source.siglum], page=page, incipit=p.chant.incipit,
                     office_part=p.chant.office_part, feast=p.chant.feast.title,
                     note="" if raw.isdigit() else "page source : " + raw))
rows.sort(key=lambda r: (r["manuscript"], r["page"], r["code"]))
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["code", "manuscript", "page", "incipit", "office_part", "feast", "note"],
                       delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print(len(rows), "pièces ->", OUT)
