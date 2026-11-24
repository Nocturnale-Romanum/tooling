"""(Expérimental) Trace une ligature (`xxExx`) en fusionnant les glyphes qu'elle lie, placés
d'après son exemplaire choisi.

Usage (avec le Python de FontForge, sans -I) :
    ffpython S/ligaturer.py <police.sfd> <sortie.sfd> [<ligature> …] [--controle] [--planche NOM]

Pour chaque ligature (par défaut : celles en orange dont le premier plan est vide) :
1. les glyphes liés (`qlEclB` → `ql`, `clB`) doivent être tracés (premier plan, ou références
   à des formes tracées) ;
2. chacun est rastérisé à l'échelle de la page (10 unités par pixel) et calé sur le masque de
   l'exemplaire (encre pâle comprise, `exclure` respecté) par corrélation : encre recouverte
   comptée positivement, débord sur le fond négativement ; les glyphes sont cherchés de gauche
   à droite, chacun à droite du centre du précédent ;
3. les contours placés sont réunis (union : l'extrémité d'un glyphe noyée dans l'autre
   disparaît) ; s'ils ne se touchent pas, un pont de l'épaisseur du trait relie les points les
   plus proches, puis union ; le premier glyphe garde sa hauteur, le tout est centré
   horizontalement sur le gabarit gregall ; couleur violette (essai) ;
4. --controle : refait aussi les ligatures déjà tracées par marteo (sans les écrire) et mesure
   leur recouvrement (IoU) avec son tracé ; --planche : cache/vectorisation/NOM.png
   (exemplaire, essai, tracé de marteo s'il existe).
"""
import csv
import os
import re
import sys

import fontforge
import numpy as np
import psMat
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.signal import fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hartker as H  # noqa: E402
import planche as P  # noqa: E402

SCALE = 10.0
ESSAI = 0xC080FF
ORANGE = 0xFFB060
CHEVAUCHEMENT = 0.4      # pénalité par pixel commun à deux gabarits (jonction seule attendue)


def parts(n):
    return re.findall(r"(?:^|E)([a-z]{2}[A-Z0-9]*?)(?=E[a-z]|$)", n)


def layer_of(f, n):
    """Contours d'un glyphe, références dépliées."""
    g = f[n]
    if not g.references:
        return g.foreground.dup()
    tmp = f.createChar(-1, "_tmp_lig")
    tmp.foreground = g.foreground
    tmp.references = g.references
    tmp.unlinkRef()
    lay = tmp.foreground.dup()
    f.removeGlyph(tmp)
    return lay


def flatten(c, n=8):
    pts = list(c)
    out, i = [], 0
    if not pts:
        return out
    k = len(pts)
    start = next((j for j in range(k) if pts[j].on_curve), 0)
    seq = pts[start:] + pts[:start] + [pts[start]]
    i = 0
    while i < len(seq) - 1:
        p0 = seq[i]
        if seq[i + 1].on_curve:
            out.append((p0.x, p0.y))
            i += 1
        else:
            p1, p2, p3 = seq[i + 1], seq[i + 2], seq[i + 3]
            for t in np.linspace(0, 1, n, endpoint=False):
                a = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
                out.append((a[0] * p0.x + a[1] * p1.x + a[2] * p2.x + a[3] * p3.x,
                            a[0] * p0.y + a[1] * p1.y + a[2] * p2.y + a[3] * p3.y))
            i += 3
    return out


def raster(lay, step=SCALE):
    """Masque (pas de `step` unités) et coin haut-gauche (x0, y1) en unités."""
    x0, y0, x1, y1 = lay.boundingBox()
    W, Hh = int((x1 - x0) / step) + 3, int((y1 - y0) / step) + 3
    m = np.zeros((Hh, W), bool)
    for c in lay:
        im = Image.new("1", (W, Hh), 0)
        ImageDraw.Draw(im).polygon([((x - x0) / step + 1, (y1 - y) / step + 1) for x, y in flatten(c)], fill=1)
        m ^= np.asarray(im, bool)
    return m, (x0 - step, y1 + step)


def exemplar_mask(r):
    seg = H.load_seg([(r["manuscript"], r["page"])])
    return P.whole(seg, r, pale=True)["mask"]


def place(M, temps):
    """Translations (ligne, colonne) des gabarits dans M, de gauche à droite."""
    S = np.where(M, 1.0, -0.6)
    pad = max(max(t.shape) for t in temps)
    Sp = np.pad(S, pad, constant_values=-0.6)
    out, xmin = [], -10 ** 9
    for t in temps:
        sc = fftconvolve(Sp, t[::-1, ::-1].astype(float), mode="valid")
        cols = np.arange(sc.shape[1]) - pad + t.shape[1] / 2
        sc[:, cols < xmin] = -1e9
        r, c = np.unravel_index(np.argmax(sc), sc.shape)
        out.append((r - pad, c - pad))
        xmin = c - pad + t.shape[1] / 2
        # l'encre déjà couverte ne compte plus pour les gabarits suivants
        Sp[r:r + t.shape[0], c:c + t.shape[1]][t] = -0.6
    return affiner(S, temps, out)


def affiner(S, temps, pos, win=12, passes=3):
    """Calage conjoint : chaque gabarit est déplacé (± win pixels) pour que l'union de tous
    couvre au mieux l'encre de l'exemplaire (un recouvrement entre gabarits ne compte qu'une
    fois)."""
    pad = max(max(t.shape) for t in temps) + win + 2
    Sp = np.pad(S, pad, constant_values=-0.6)
    pos = [list(p) for p in pos]

    def union(skip=None):
        U = np.zeros(Sp.shape, bool)
        for k, (t, (r, c)) in enumerate(zip(temps, pos)):
            if k != skip:
                U[r + pad:r + pad + t.shape[0], c + pad:c + pad + t.shape[1]] |= t
        return U
    for _ in range(passes):
        for i, t in enumerate(temps):
            U = union(skip=i)
            best = None
            for dr in range(-win, win + 1, 2):
                for dc in range(-win, win + 1, 2):
                    r, c = pos[i][0] + dr + pad, pos[i][1] + dc + pad
                    sub = U[r:r + t.shape[0], c:c + t.shape[1]] | t
                    Uw = U[r:r + t.shape[0], c:c + t.shape[1]]
                    s = (Sp[r:r + t.shape[0], c:c + t.shape[1]] * (sub & ~Uw)).sum() - CHEVAUCHEMENT * (t & Uw).sum()
                    if best is None or s > best[0]:
                        best = (s, dr, dc)
            pos[i][0] += best[1]
            pos[i][1] += best[2]
    return [tuple(p) for p in pos]


def bridge(lay, width):
    """Relie les contours extérieurs séparés par un pont (quadrilatère) entre leurs points les
    plus proches."""
    outer = [c for c in lay if c.isClockwise()] or list(lay)
    if len(outer) < 2:
        return lay
    pts = [np.array([(p.x, p.y) for p in c if p.on_curve]) for c in outer]
    for i in range(len(outer) - 1):
        a, b = pts[i], pts[i + 1]
        d = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2)
        ia, ib = np.unravel_index(np.argmin(d), d.shape)
        pa, pb = a[ia], b[ib]
        v = pb - pa
        nv = np.array([-v[1], v[0]]) / max(np.linalg.norm(v), 1e-6) * width / 2
        q = fontforge.contour()
        q.moveTo(*(pa + nv - v * 0.2))
        q.lineTo(*(pb + nv + v * 0.2))
        q.lineTo(*(pb - nv + v * 0.2))
        q.lineTo(*(pa - nv - v * 0.2))
        q.closed = True
        lay += q
    return lay


def stroke_width(M):
    """Épaisseur médiane du trait de l'exemplaire (unités)."""
    dt = ndi.distance_transform_edt(M)
    sk = dt[(dt > 0) & (dt == ndi.maximum_filter(dt, 3))]
    return 2 * float(np.median(sk)) * SCALE if sk.size else 60.0


def ligaturer(f, n, r):
    ps = parts(n)
    layers = [layer_of(f, p) for p in ps]
    rasters = [raster(l) for l in layers]
    M = exemplar_mask(r)
    pos = place(M, [m for m, _ in rasters])
    # page → police : le premier glyphe garde sa place (décalage nul)
    (r0, c0), (_, (ux0, uy1)) = pos[0], rasters[0]
    A, B = ux0 - SCALE * c0, uy1 + SCALE * r0
    out = fontforge.layer()
    for lay, (_, (ux, uy)), (rr, cc) in zip(layers, rasters, pos):
        dx, dy = A + SCALE * cc - ux, B - SCALE * rr - uy
        lay.transform(psMat.translate(dx, dy))
        out += lay
    g = f[n]
    tmp = f.createChar(-1, "_tmp_lig2")
    tmp.foreground = out
    tmp.removeOverlap()
    if len([c for c in tmp.foreground if c.isClockwise()]) > 1:
        tmp.foreground = bridge(tmp.foreground, 0.8 * stroke_width(M))
        tmp.removeOverlap()
    tmp.correctDirection()
    tmp.addExtrema()
    tmp.simplify(2, ("mergelines", "smoothcurves", "removesingletonpoints"))
    tmp.round()
    lay = tmp.foreground.dup()
    f.removeGlyph(tmp)
    gx0, _, gx1, _ = g.layers["gregall"].boundingBox()
    x0, _, x1, _ = lay.boundingBox()
    lay.transform(psMat.translate(round((gx0 + gx1) / 2 - (x0 + x1) / 2), 0))
    return lay, M


def iou(a, b):
    ma, (ax, ay) = raster(a, 5)
    mb, (bx, by) = raster(b, 5)
    # alignement des centres de boîte (le calage vertical peut différer)
    H_, W_ = max(ma.shape[0], mb.shape[0]) + 4, max(ma.shape[1], mb.shape[1]) + 4
    pa, pb = np.zeros((H_, W_), bool), np.zeros((H_, W_), bool)
    for m, p in ((ma, pa), (mb, pb)):
        oy, ox = (H_ - m.shape[0]) // 2, (W_ - m.shape[1]) // 2
        p[oy:oy + m.shape[0], ox:ox + m.shape[1]] = m
    return (pa & pb).sum() / max(1, (pa | pb).sum())


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    controle = "--controle" in sys.argv
    nom = sys.argv[sys.argv.index("--planche") + 1] if "--planche" in sys.argv else None
    if nom:
        args.remove(nom)
    src, dst, noms = args[0], args[1], args[2:]
    cho = {r["glyph"]: r for r in csv.DictReader(open(os.path.join(H.SKILL, "sources", "exemplaires.csv"),
                                                     encoding="utf-8")) if r["role"] == "choisi"}
    f = fontforge.open(src)
    ligs = [g.glyphname for g in f.glyphs() if re.search(r"[a-z0-9]E[a-z]", g.glyphname)]
    if not noms:
        noms = [n for n in ligs if f[n].color == ORANGE and not len(f[n].foreground)]
        if controle:
            noms += [n for n in ligs if len(f[n].foreground) and n in cho]
    rows = []
    for n in noms:
        if n not in cho:
            print("%-12s pas d'exemplaire choisi" % n)
            continue
        ps = parts(n)
        miss = [p for p in ps if p not in f or not (len(f[p].foreground) or f[p].references)]
        if miss:
            print("%-12s glyphes non tracés : %s" % (n, " ".join(miss)))
            continue
        lay, M = ligaturer(f, n, cho[n])
        trace = len(f[n].foreground) > 0
        if trace:
            print("%-12s contrôle : IoU avec le tracé de marteo %.2f" % (n, iou(lay, f[n].foreground)))
        else:
            f[n].foreground = lay
            f[n].color = ESSAI
            print("%-12s tracé (essai) : %d contour(s)" % (n, len(lay)))
        rows.append((n, cho[n], lay, f[n].foreground if trace else None))
    f.save(dst)
    if nom:
        sheet(rows, nom)


def sheet(rows, nom):
    out_rows = []
    for n, r, lay, ref in rows:
        x, y, w, h = (int(r[k]) for k in "xywh")
        crop = H.crop(r["manuscript"], r["page"], x, y, w, h, pad=10, zoom=2).convert("RGB")
        ims = [crop]
        for l in ([lay] + ([ref] if ref is not None else [])):
            m, _ = raster(l, 5)
            ims.append(Image.fromarray(np.where(m, 0, 255).astype(np.uint8)).convert("RGB"))
        out_rows.append((n, ims))
    W = max(sum(i.width + 20 for i in ims) for _, ims in out_rows) + 20
    Ht = sum(max(i.height for i in ims) + 40 for _, ims in out_rows) + 50
    im = Image.new("RGB", (max(W, 700), Ht), "white")
    d = ImageDraw.Draw(im)
    d.text((10, 10), "%s : exemplaire | essai de ligature | tracé de marteo (contrôle) — même échelle" % nom,
           fill=0, font=H.font(20, True))
    yy = 50
    for n, ims in out_rows:
        d.text((10, yy), n, fill=(0, 0, 150), font=H.font(18, True))
        xx = 10
        for i in ims:
            im.paste(i, (xx, yy + 28))
            xx += i.width + 20
        yy += max(i.height for i in ims) + 40
    path = os.path.join(H.CACHE, "vectorisation", nom + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    print(path)


if __name__ == "__main__":
    main()
