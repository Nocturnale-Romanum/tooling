"""Vectorise l'exemplaire choisi d'un glyphe (potrace) et le pose au premier plan de la police.

Usage (avec le Python de FontForge, sans -I) :
    python S/vectoriser.py <police.sfd> <glyphe> [<glyphe> …] [--sortie autre.sfd] [--planche NOM]

Pour chaque glyphe (ligne « choisi » de sources/exemplaires.csv) :
1. masque de l'exemplaire : composantes d'encre de la boîte (hors colonne `exclure`), plus
   l'encre pâle qui leur est reliée (hampes fines), comme les surimpressions de planche.py ;
2. le masque est agrandi 4 fois et lissé (flou gaussien puis seuil à mi-hauteur) pour ne pas
   reproduire le grain de l'encre ; autour des vrais angles du trait (détecteur de Harris), le
   lissage est faible pour garder l'angle vif ; puis vectorisation par potrace (Bézier) ;
3. le contour remplace le premier plan du glyphe, à l'échelle commune : 10 unités de police par
   pixel e-codices, sans aucune mise à l'échelle propre au glyphe (y vers le haut) ; FontForge
   corrige le sens des contours, ajoute les extrémums, simplifie légèrement et arrondit ;
4. caler.py cale ensuite le contour sur gregall (bas sur bas, `cl` haut sur haut, centrage
   relatif à la chasse, élargissement de chasse ≤ 20 %) : on garde de gregall tout sauf le tracé.
--planche NOM : cache/vectorisation/NOM.png, une ligne par glyphe : exemplaire de Hartker, glyphe
vectorisé rendu, gregall, à la même échelle.
"""
import argparse
import csv
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hartker as H  # noqa: E402
import planche as P  # noqa: E402

SCALE = 10.0      # unités de police par pixel e-codices
UP = 4            # suréchantillonnage avant vectorisation
VDIR = os.path.join(H.CACHE, "vectorisation")    # planches de vectorisation (à part des planches de choix)
SMOOTH = 2.6      # flou gaussien (pixels de page) : efface le grain de l'encre et les vaguelettes
SPECK = 40        # taches isolées (pixels de page) ignorées : aspérités du papier
HOLE = 30         # petits trous (pixels de page) bouchés : encre claire au milieu d'un trait
CORNER_T = 0.45   # seuil relatif de la réponse de Harris pour un vrai angle
CORNER_N = 6      # au plus ce nombre d'angles par glyphe (les plus nets)
CORNER_R = 4      # rayon (pixels de page) de la zone où l'on colle au tracé autour d'un angle


def chosen(glyph):
    with open(os.path.join(H.SKILL, "sources", "exemplaires.csv"), encoding="utf-8") as f:
        return next((r for r in csv.DictReader(f) if r["glyph"] == glyph and r["role"] == "choisi"), None)


def mask_of(r):
    """Masque du neume : composantes de la boîte et encre pâle reliée (planche.whole), nettoyé :
    ouverture morphologique (aspérités du bord), taches isolées retirées, petits trous bouchés."""
    seg = H.load_seg([(r["manuscript"], r["page"])])
    m = P.whole(seg, r, pale=True)["mask"]
    m = ndi.binary_opening(m, np.ones((2, 2), bool)) | (m & ~ndi.binary_dilation(ndi.binary_opening(m, np.ones((2, 2), bool)), iterations=2))
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    m = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= SPECK])
    holes = ndi.binary_fill_holes(m) & ~m
    hl, hn = ndi.label(holes)
    hs = ndi.sum(holes, hl, range(1, hn + 1))
    return m | np.isin(hl, [i + 1 for i, s in enumerate(hs) if s < HOLE])


def trace(mask):
    import potrace
    m = np.pad(mask.astype(float), 3)
    big = np.kron(m, np.ones((UP, UP)))
    smooth = ndi.gaussian_filter(big, SMOOTH * UP)
    sharp = ndi.gaussian_filter(big, 0.6 * UP)
    near = corners(sharp)
    # lissage fort partout, sauf autour des vrais angles du trait où l'on colle au tracé
    w = ndi.gaussian_filter(near.astype(float), 1.5 * UP)
    w = np.clip(w / max(w.max(), 1e-6) * 2, 0, 1)
    final = (w * sharp + (1 - w) * smooth) > 0.5
    bm = potrace.Bitmap(~final)      # potracer prend les pixels à 0 pour l'encre
    return bm.trace(turdsize=SPECK * UP * UP, alphamax=1.0, opticurve=True, opttolerance=0.5), final.shape


def corners(img):
    """Vrais angles du trait (détecteur de Harris sur le masque peu lissé) : disques de
    CORNER_R pixels de page autour des maxima de la réponse, au-dessus d'un seuil relatif."""
    gy, gx = np.gradient(img)
    s = 1.5 * UP
    Ixx, Iyy, Ixy = (ndi.gaussian_filter(a, s) for a in (gx * gx, gy * gy, gx * gy))
    R = Ixx * Iyy - Ixy * Ixy - 0.05 * (Ixx + Iyy) ** 2
    if R.max() <= 0:
        return np.zeros_like(img, bool)
    peaks = (R == ndi.maximum_filter(R, size=int(4 * UP))) & (R > CORNER_T * R.max())
    ys, xs = np.nonzero(peaks)
    keep = np.argsort(-R[ys, xs])[:CORNER_N]
    peaks = np.zeros_like(peaks)
    peaks[ys[keep], xs[keep]] = True
    return ndi.binary_dilation(peaks, iterations=int(CORNER_R * UP))


def to_glyph(g, path, shape):
    import fontforge
    h = shape[0]
    f = lambda p: ((p.x / UP) * SCALE, (h - p.y) / UP * SCALE)   # y vers le haut
    layer = fontforge.layer()
    for curve in path:
        c = fontforge.contour()
        c.moveTo(*f(curve.start_point))
        for seg in curve.segments:
            if seg.is_corner:
                c.lineTo(*f(seg.c))
                c.lineTo(*f(seg.end_point))
            else:
                c.cubicTo(f(seg.c1), f(seg.c2), f(seg.end_point))
        c.closed = True
        layer += c
    g.foreground = layer
    g.correctDirection()
    g.addExtrema()
    g.simplify(4, ("mergelines", "smoothcurves"))
    g.round()
    g.color = 0xFFFF80


def main():
    import fontforge
    os.makedirs(VDIR, exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("sfd")
    ap.add_argument("glyphes", nargs="+")
    ap.add_argument("--sortie")
    ap.add_argument("--planche")
    args = ap.parse_args()
    out = args.sortie or args.sfd
    font = fontforge.open(args.sfd)
    done = []
    for g in args.glyphes:
        r = chosen(g)
        if r is None:
            print(g, ": pas d'exemplaire choisi")
            continue
        if g not in font:
            print(g, ": absent de la police")
            continue
        path, shape = trace(mask_of(r))
        to_glyph(font[g], path, shape)
        print(g, ": %d contour(s), %d points" % (len(path), sum(len(c.segments) for c in path)))
        done.append(g)
    font.save(out)
    font.close()
    if done:
        subprocess.run([sys.executable, os.path.join(HERE, "caler.py"), out] + done, check=True)
    if args.planche and done:
        sheet(out, done, args.planche)


def sheet(sfd, glyphs, nom):
    import fontforge
    rows = []
    font = fontforge.open(sfd)
    em = font.em
    for g in glyphs:
        r = chosen(g)
        x, y, w, h = (int(r[k]) for k in "xywh")
        crop = H.crop(r["manuscript"], r["page"], x, y, w, h, pad=10, zoom=2)
        # rendu : 1 unité = 1/10 pixel de page ; zoom 2 → em/10*2 pixels par em
        tmp = os.path.join(VDIR, "_rendu_%s.png" % g)
        font[g].export(tmp, int(em / SCALE * 2))
        vec = Image.open(tmp).convert("L")
        if np.asarray(vec).mean() < 128:          # FontForge rend en blanc sur noir
            vec = Image.fromarray(255 - np.asarray(vec))
        vec = vec.convert("RGB")
        try:
            gre = H.gregall_image(g, int(100 * 2))
        except KeyError:
            gre = Image.new("RGB", (10, 10), "white")
        rows.append((g, [crop, vec, gre]))
    font.close()
    lab = 30
    W = max(sum(im.width + 20 for im in ims) for _, ims in rows) + 20
    Ht = sum(max(im.height for im in ims) + lab + 10 for _, ims in rows) + 50
    out = Image.new("RGB", (max(W, 700), Ht), "white")
    d = ImageDraw.Draw(out)
    d.text((10, 10), "%s : Hartker | vectorisé (grehartker) | gregall — même échelle" % nom, fill=0, font=H.font(20, True))
    yy = 50
    for g, ims in rows:
        d.text((10, yy), g, fill=(0, 0, 150), font=H.font(18, True))
        xx = 10
        for im in ims:
            out.paste(im, (xx, yy + lab))
            xx += im.width + 20
        yy += max(im.height for im in ims) + lab + 10
    path = os.path.join(VDIR, nom + ".png")
    out.save(path)
    for g in glyphs:
        try:
            os.remove(os.path.join(VDIR, "_rendu_%s.png" % g))
        except OSError:
            pass
    print(path)


if __name__ == "__main__":
    main()
