"""Pages de Hartker : aperçus, téléchargement et segmentation.

Usage (Python ordinaire, depuis n'importe où) :
    python -I S/pages.py apercu 391:50 391:70 390:140 …   planche d'aperçus pour vérifier la main
    python -I S/pages.py telecharger 391:50 390:140 …     bandes pleine résolution (cache/pages)
    python -I S/pages.py segmenter                         segmente les bandes nouvelles (cache/seg.pkl)
    python -I S/pages.py liste                             pages en cache et pages examinées

Une page s'écrit <volume>:<page>, volume 390 (hiver) ou 391 (été), page e-codices (sans zéros).
Vérifier la main sur l'aperçu avant de télécharger : certaines pages sont d'une main plus
tardive ou d'une autre mise en page (391 p. 110, 150, 240) ; les noter dans
sources/pages_examinees.csv. Les téléchargements se font un par un : le serveur e-codices
tronque les requêtes parallèles.
"""
import csv
import glob
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I n'ajoute pas le dossier du script
import hartker as H  # noqa: E402


def parse(arg):
    ms, p = arg.split(":")
    return H.norm_page(ms, p)


def apercu(args):
    cells = []
    for a in args:
        ms, p = parse(a)
        im = Image.open(H.download_preview(ms, p)).convert("RGB")
        im.thumbnail((500, 660))
        cells.append(("%s p.%s" % (ms[-3:], p.lstrip("0")), im))
    out = os.path.join(H.CACHE, "apercu.png")
    H.grid(cells, 6, "Aperçus (vérifier la main avant téléchargement)", cell_w=510).save(out)
    print(out)


def telecharger(args):
    for a in args:
        ms, p = parse(a)
        print(H.download_band(ms, p), flush=True)


def segmenter():
    seg = H.load_seg()
    new = 0
    for path in sorted(glob.glob(os.path.join(H.PAGES, "*_band.jpg"))):
        ms, p = os.path.basename(path).split("_")[:2]
        if (ms, p) in seg:
            continue
        seg[(ms, p)] = H.segment(path)
        print(ms, p, len(seg[(ms, p)]), "composantes", flush=True)
        new += 1
        if new % 10 == 0:           # seg.pkl pèse des centaines de Mo : ne pas le réécrire à chaque page
            H.save_seg(seg)
    if new:
        H.save_seg(seg)
    print(len(seg), "pages segmentées")


def liste():
    seg = H.load_seg()
    print("en cache :", " ".join("%s:%s" % (ms[-3:], p.lstrip("0")) for ms, p in sorted(seg)))
    path = os.path.join(H.SKILL, "sources", "pages_examinees.csv")
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print("examinées :", len(rows), "dont exclues :",
          ", ".join("%s p.%s (%s)" % (r["manuscript"][-3:], r["page"].lstrip("0"), r["note"]) for r in rows if r["statut"] == "exclue"))


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    {"apercu": lambda: apercu(args), "telecharger": lambda: telecharger(args),
     "segmenter": segmenter, "liste": liste}[cmd]()
