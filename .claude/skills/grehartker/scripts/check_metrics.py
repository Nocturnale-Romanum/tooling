"""Vérifie que grehartker reste compatible avec gregall et mesure l'avancement.

Usage (avec le Python de FontForge) :
    ffpython S/check_metrics.py <gregall.sfd> <grehartker.sfd> [reference/usage_nr.tsv] [rapport.csv]

Bloquant (ERREUR) :
- paramètres de police différents (em, ascent/descent, métriques OS/2 et hhea) ;
- glyphe de gregall absent, ou encodage différent ;
- chasse (advance width) réduite, élargie de plus de 20 %, ou élargie sur un glyphe qui
  n'est pas détouré (rouge) ; l'élargissement est réservé aux contours qui dépassent de la
  chasse plus que gregall (S/caler.py) ;
- hauteur du glyphe `cl` différente : gregoriotex-nabc.lua s'en sert comme pas de
  hauteur (descripteurs h[a-np]) ; elle doit rester à l'identique.
Signalé (ATTENTION), seulement pour les glyphes refaits (couleur verte), hors `cl` :
- glyphe composé (ex. `toSsu2`) qui ne reprend pas son neume de base (`toS`) en référence à la
  hauteur 0 (S/composer.py) : le neume de base doit avoir la même taille et la même
  hauteur dans toute la famille ;
- bas (ymin) différent de gregall, pour les glyphes qui ne sont pas des composés : le calage
  se fait bas sur bas (S/caler.py) ;
- centre horizontal décalé par rapport au milieu de la chasse autrement que dans gregall :
  les lettres significatives sont centrées sur la chasse ;
- haut (ymax) très éloigné de gregall. C'est voulu (aucune mise à l'échelle : on garde les
  proportions de Hartker), mais la hauteur sert à placer les lettres significatives et à
  empiler les neumes : à vérifier sur un document de test.
Pour information : liste des chasses élargies.
"""
import csv
import sys

import fontforge

from commun import fore_bbox, parse

DONE, WIP, TODO = 0x80FF80, 0xFFFF80, 0xFF8080
PARAMS = ["em", "ascent", "descent", "os2_typoascent", "os2_typodescent", "os2_typolinegap",
          "os2_winascent", "os2_windescent", "hhea_ascent", "hhea_descent", "hhea_linegap",
          "os2_use_typo_metrics", "italicangle"]
TOL_TOP = 0.12     # écart de haut signalé, en fraction de la hauteur totale du glyphe gregall
TOL_TOP_MIN = 40   # ... mais jamais moins de 40 unités
TOL_CALAGE = 2     # bas et centre horizontal : calage exact par S/caler.py, à l'arrondi près
MAX_WIDEN = 0.20   # élargissement maximal de la chasse


def main(ref_path, new_path, usage_path=None, report_path=None):
    ref, new = fontforge.open(ref_path), fontforge.open(new_path)
    errors, warnings, infos, rows = [], [], [], []

    for p in PARAMS:
        if getattr(ref, p) != getattr(new, p):
            errors.append("paramètre %s : gregall=%s grehartker=%s" % (p, getattr(ref, p), getattr(new, p)))

    usage = {}
    if usage_path:
        with open(usage_path, encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                usage[r["glyphname"]] = int(r["uses"])

    new_names = {g.glyphname for g in new.glyphs()}
    for g in ref.glyphs():
        n = g.glyphname
        if n not in new_names:
            errors.append("glyphe manquant : %s" % n)
            continue
        h = new[n]
        if h.encoding != g.encoding:
            errors.append("%s : encodage %d au lieu de %d" % (n, h.encoding, g.encoding))
        status = {DONE: "fait", WIP: "en cours"}.get(h.color, "à faire")
        if h.width < g.width or h.width > g.width * (1 + MAX_WIDEN):
            errors.append("%s : chasse %d hors de [%d, %d]" % (n, h.width, g.width, g.width * (1 + MAX_WIDEN)))
        elif h.width != g.width:
            if status == "à faire":
                errors.append("%s : chasse %d au lieu de %d sur un glyphe non détouré" % (n, h.width, g.width))
            else:
                infos.append("%s : chasse %d au lieu de %d (%+.1f %%)" % (n, h.width, g.width,
                                                                       100.0 * (h.width - g.width) / g.width))
        rx0, ry0, rx1, ry1 = fore_bbox(g)
        nx0, ny0, nx1, ny1 = fore_bbox(h)
        if n == "cl" and abs(ny1 - ry1) > 0.5:
            errors.append("cl : ymax %.1f au lieu de %.1f (pas de hauteur NABC)" % (ny1, ry1))
        dy_top, dy_bot = ny1 - ry1, ny0 - ry0
        # centre du contour par rapport au milieu de la chasse, comparé à gregall
        dx = ((nx0 + nx1) / 2 - h.width / 2) - ((rx0 + rx1) / 2 - g.width / 2)
        fam, base, others = parse(n)
        composite = base != n and base in new_names and fam not in ("ls", "pp-su", "ob-cb-ni") and not others
        if status == "fait" and composite:
            refs = [r for r in h.references if r[0] == base]
            if not refs:
                warnings.append("%s : neume de base %s non repris en référence (S/composer.py)" % (n, base))
            elif abs(refs[0][1][5]) > 0.5:
                warnings.append("%s : référence à %s décalée verticalement de %.0f (lancer S/caler.py)"
                                % (n, base, refs[0][1][5]))
        if status == "fait" and n not in ("ni", "ob", "cb", "cl"):
            if abs(dy_bot) > TOL_CALAGE and not composite:
                warnings.append("%s : bas à %.0f au lieu de %.0f (lancer S/caler.py)" % (n, ny0, ry0))
            if abs(dx) > TOL_CALAGE:
                warnings.append("%s : centre horizontal décalé de %.0f unités (lancer S/caler.py)" % (n, dx))
            if abs(dy_top) > max(TOL_TOP * (ry1 - ry0), TOL_TOP_MIN):
                warnings.append("%s : haut à %.0f au lieu de %.0f (proportions de Hartker ; vérifier les "
                                "lettres significatives)" % (n, ny1, ry1))
        rows.append({"glyphname": n, "statut": status, "usages_NR": usage.get(n, 0),
                     "chasse_gregall": g.width, "chasse": h.width, "d_ymax": round(dy_top),
                     "d_ymin": round(dy_bot), "d_centre_x": round(dx)})
    for n in sorted(new_names - {g.glyphname for g in ref.glyphs()}):
        warnings.append("glyphe supplémentaire (absent de gregall) : %s" % n)

    total = len(rows)
    done = sum(r["statut"] == "fait" for r in rows)
    wip = sum(r["statut"] == "en cours" for r in rows)
    tot_use = sum(r["usages_NR"] for r in rows) or 1
    done_use = sum(r["usages_NR"] for r in rows if r["statut"] == "fait")
    for e in errors:
        print("ERREUR    ", e)
    for w in warnings:
        print("ATTENTION ", w)
    for i in infos:
        print("INFO      ", i)
    print("\n%d erreur(s), %d avertissement(s)" % (len(errors), len(warnings)))
    print("Avancement : %d/%d glyphes refaits, %d en cours ; %.1f %% des occurrences NABC de NR couvertes"
          % (done, total, wip, 100.0 * done_use / tot_use))
    if report_path:
        with open(report_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(sorted(rows, key=lambda r: -r["usages_NR"]))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
