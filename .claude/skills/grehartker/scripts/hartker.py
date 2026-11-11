"""Fonctions communes aux outils de recherche d'exemplaires dans Hartker (Python ordinaire).

Dépendances : Pillow, numpy, scipy (requirements.txt).

Caches (non versionnés, dans <skill>/cache/) :
- pages/  : bandes pleine résolution des pages de Hartker (zone 600,450 + 5000 × 6600 px de
            l'image e-codices 6132 × 8176), une par page, ~4,5 Mo chacune ;
- seg.pkl : composantes d'encre de chaque page téléchargée (segmenter.py).

Emplacements des autres dépôts (variables d'environnement, sinon dossiers voisins de tooling) :
- GREGORIO_PATCH : copie de github.com/Nocturnale-Romanum/gregorio-patch (gregall.sfd, .ttf) ;
- NR_REPO        : copie de github.com/Nocturnale-Romanum/nocturnale-romanum (gabc/) ;
- GREHARTKER     : copie de github.com/Nocturnale-Romanum/grehartker (src/grehartker.sfd).
"""
import csv
import os
import pickle
import subprocess
import time
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLING = os.path.dirname(os.path.dirname(os.path.dirname(SKILL)))
CACHE = os.path.join(SKILL, "cache")
PAGES = os.path.join(CACHE, "pages")
SEG = os.path.join(CACHE, "seg.pkl")
BAND = (600, 450, 5000, 6600)          # x, y, w, h de la bande téléchargée dans la page
IIIF = "https://media.e-codices.ch/iip/csg/{ms}/{ms}_{page}.jp2/{region}/full/0/default.jpg"
UA = "grehartker-research"


def repo(var, name):
    p = os.environ.get(var) or os.path.join(os.path.dirname(TOOLING), name)
    return p


def gregall_ttf():
    return os.path.join(repo("GREGORIO_PATCH", "gregorio-patch"), "gregall.ttf")


def norm_page(ms, page):
    """('391', '53') -> ('csg-0391', '053')."""
    ms = ms if ms.startswith("csg-") else "csg-%04d" % int(ms)
    return ms, "%03d" % int(page)


# ---------------------------------------------------------------- téléchargement
def fetch(url, path, tries=3):
    """Télécharge url dans path, vérifie que l'image est complète ; essaie urllib puis curl."""
    for _ in range(tries):
        tmp = path + ".part"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
                f.write(r.read())
        except Exception:
            subprocess.run(["curl", "-sfL", "--max-time", "300", "-A", UA, "-o", tmp, url])
        try:
            Image.open(tmp).load()
            os.replace(tmp, path)
            return path
        except Exception:
            time.sleep(3)
    raise RuntimeError("téléchargement impossible : " + url)


def band_path(ms, page):
    ms, page = norm_page(ms, page)
    return os.path.join(PAGES, "%s_%s_band.jpg" % (ms, page))


def download_band(ms, page):
    """Bande pleine résolution d'une page (une seule requête à la fois : le serveur tronque les
    téléchargements parallèles)."""
    ms, page = norm_page(ms, page)
    os.makedirs(PAGES, exist_ok=True)
    p = band_path(ms, page)
    if not os.path.exists(p):
        fetch(IIIF.format(ms=ms, page=page, region="%d,%d,%d,%d" % BAND), p)
    return p


def download_preview(ms, page, width=600):
    ms, page = norm_page(ms, page)
    os.makedirs(PAGES, exist_ok=True)
    p = os.path.join(PAGES, "%s_%s_prev.jpg" % (ms, page))
    if not os.path.exists(p):
        fetch(IIIF.format(ms=ms, page=page, region="full").replace("/full/0/", "/%d,/0/" % width), p)
    return p


# ---------------------------------------------------------------- segmentation
def segment(path):
    """Composantes d'encre des lignes de neumes d'une bande : seuillage à hystérésis (encre
    nette > 55, encre pâle > 30 sous le fond local), lignes de texte écartées par profil."""
    g = np.asarray(Image.open(path).convert("L")).astype(float)
    bg = ndi.median_filter(g[::8, ::8], size=15)
    bg = np.kron(bg, np.ones((8, 8)))[:g.shape[0], :g.shape[1]]
    d = bg - g
    strong = ndi.binary_opening(d > 55, iterations=1)
    weak = d > 30
    lab, n = ndi.label(weak)
    keep = set(np.unique(lab[strong]).tolist()) - {0}
    prof = ndi.uniform_filter1d(strong.sum(1).astype(float), 41)
    text = prof > 0.35 * prof.max()
    comps = []
    for i, s in enumerate(ndi.find_objects(lab)):
        if s is None or (i + 1) not in keep:
            continue
        y0, y1, x0, x1 = s[0].start, s[0].stop, s[1].start, s[1].stop
        h, w = y1 - y0, x1 - x0
        if h < 8 or h > 160 or w > 200 or text[(y0 + y1) // 2]:
            continue
        m = lab[y0:y1, x0:x1] == (i + 1)
        if m.sum() < 60:
            continue
        comps.append(dict(x=x0 + BAND[0], y=y0 + BAND[1], w=w, h=h, mask=m))
    return comps


def load_seg():
    if os.path.exists(SEG):
        with open(SEG, "rb") as f:
            return pickle.load(f)
    return {}


def save_seg(seg):
    os.makedirs(CACHE, exist_ok=True)
    with open(SEG, "wb") as f:
        pickle.dump(seg, f)


def comp_in(seg, ms, page, x, y, w, h):
    """Composante de plus grand recouvrement avec une boîte (coordonnées de page)."""
    best = None
    for c in seg[(ms, page)]:
        ov = max(0, min(x + w, c["x"] + c["w"]) - max(x, c["x"])) * max(0, min(y + h, c["y"] + c["h"]) - max(y, c["y"]))
        if ov and (best is None or ov > best[0]):
            best = (ov, c)
    return best[1] if best else None


# ---------------------------------------------------------------- comparaison de formes
N = 32


def norm(mask):
    im = Image.fromarray((mask * 255).astype("uint8")).resize((N, N), Image.BILINEAR)
    return np.asarray(im).astype(float) / 255


def template(c):
    return dict(n=norm(c["mask"]), h=c["h"], w=c["w"])


def score(c, templates):
    """Ressemblance d'une composante aux gabarits : IoU des masques normalisés, pénalisé par
    l'écart de hauteur et de largeur (échelle de la page)."""
    n = norm(c["mask"])
    best = -9
    for t in templates:
        iou = np.minimum(n, t["n"]).sum() / np.maximum(n, t["n"]).sum()
        best = max(best, iou - 0.8 * abs(np.log(c["h"] / t["h"])) - 0.8 * abs(np.log(c["w"] / t["w"])))
    return best


# ---------------------------------------------------------------- images
_imgs = {}


def crop(ms, page, x, y, w, h, pad=25, zoom=4, box=False):
    """Découpe agrandie d'une zone de page, depuis la bande en cache (téléchargée au besoin)."""
    p = download_band(ms, page)
    if p not in _imgs:
        _imgs[p] = Image.open(p).convert("RGB")
    X, Y = x - BAND[0], y - BAND[1]
    cr = _imgs[p].crop((X - pad, Y - pad, X + w + pad, Y + h + pad))
    cr = cr.resize((cr.width * zoom, cr.height * zoom), Image.LANCZOS)
    if box:
        ImageDraw.Draw(cr).rectangle((pad * zoom - 3, pad * zoom - 3, (pad + w) * zoom + 3, (pad + h) * zoom + 3),
                                     outline=(0, 170, 0), width=2)
    return cr


def font(size=18, bold=False):
    for name in (("arialbd.ttf" if bold else "arial.ttf"), ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def gregall_codepoints():
    path = os.path.join(SKILL, "reference", "gregall_glyphs.csv")
    with open(path, encoding="utf-8") as f:
        return {r["glyphname"]: int(r["unicode"][2:], 16) for r in csv.DictReader(f) if r["unicode"]}


def gregall_image(name, px_per_em=400):
    """Glyphe gregall rendu à px_per_em pixels par em. À 400, l'échelle est celle des découpes
    agrandies 4 fois (10 unités de police par pixel de page)."""
    f = ImageFont.truetype(gregall_ttf(), px_per_em)
    im = Image.new("RGB", (px_per_em * 3, px_per_em * 3), "white")
    ImageDraw.Draw(im).text((px_per_em, int(px_per_em * 2)), chr(gregall_codepoints()[name]), font=f, fill=0, anchor="ls")
    bb = Image.eval(im.convert("L"), lambda v: 255 - v).getbbox()
    im = im.crop(bb)
    out = Image.new("RGB", (im.width + 40, im.height + 40), "white")
    out.paste(im, (20, 20))
    return out


def grid(cells, cols, title=None, cell_w=None, label_h=26):
    """Planche : cells = [(étiquette, image)], images de tailles diverses."""
    cw = cell_w or max(im.width for _, im in cells) + 15
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    hs = [max(im.height for _, im in r) + label_h + 10 for r in rows]
    top = 45 if title else 5
    sh = Image.new("RGB", (cols * cw + 10, top + sum(hs)), "white")
    d = ImageDraw.Draw(sh)
    if title:
        d.text((10, 10), title, fill=0, font=font(24, True))
    y = top
    for r, h in zip(rows, hs):
        for k, (lab, im) in enumerate(r):
            x = 5 + k * cw
            d.text((x, y), lab, fill=(0, 0, 150), font=font(16, True))
            sh.paste(im, (x, y + label_h))
        y += h
    return sh
