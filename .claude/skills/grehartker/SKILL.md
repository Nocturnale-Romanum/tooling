---
name: grehartker
description: Construire la police NABC grehartker (neumes sangalliens pour GregorioTeX, détourés d'après l'antiphonaire de Hartker, Cod. Sang. 390–391, compatible avec gregall) : choisir des exemplaires dans Hartker (pages e-codices, planches de choix et variantes, sources des pièces NR pour les neumes rares), décomposer les glyphes en formes de base, importer les exemplaires retenus dans src/grehartker.sfd, caler et vérifier les métriques. À utiliser dès qu'il est question de grehartker, de gregall, de détourage de neumes, d'exemplaires de Hartker ou de formes de base NABC.
---

# grehartker

**Objet :** une police de neumes sangalliens pour GregorioTeX (NABC), redessinée uniquement
d'après l'antiphonaire de Hartker (St. Gallen, Stiftsbibliothek, Cod. Sang. 390, hiver, et 391,
été, vers 990–1000), qui remplace gregall en changeant le moins possible la mise en page des
livres de Nocturnale Romanum (NR).

**Arbitre :** marteo (Matthias Bry). Il choisit les exemplaires sur les planches et tranche les
décompositions. Rien n'est importé dans la police sans son accord.

**Référence complète :** `docs/methode.md` (spécification, état de gregall, usage dans NR,
calibration, règles détaillées, questions ouvertes). Ce fichier en donne l'essentiel pour
travailler et l'état des lieux.

## Dépôts et prérequis

| Dépôt (github.com/Nocturnale-Romanum/…) | Rôle |
|---|---|
| `grehartker` (privé) | la police seule : `src/grehartker.sfd` (extraits de Hartker retenus en arrière-plan), licences, README court. **Garder ce dépôt propre** : ni outils, ni données de travail. |
| `tooling` | ce skill : `scripts/`, `reference/`, `sources/`, `docs/` |
| `gregorio-patch` | `gregall.sfd`, `gregall.ttf` (version NR de gregall), `gregoriotex-nabc.lua` |
| `nocturnale-romanum` | `gabc/*_marteo.gabc`, pour l'usage des glyphes et les sources des pièces |

Les scripts cherchent ces dépôts à côté de `tooling`, sinon dans les variables
`GREGORIO_PATCH`, `NR_REPO`, `GREHARTKER`.

- **FontForge** avec son Python (`ffpython`, sous Windows
  `C:\Program Files\FontForgeBuilds\bin\ffpython.exe`), pour les scripts marqués *ffpython*.
  Son Python n'a pas HTTPS sous Windows : les téléchargements passent par `curl`.
- **Python 3** avec `pip install -r scripts/requirements.txt` (Pillow, numpy, scipy), de
  préférence dans un environnement virtuel, pour les autres scripts. Lancer avec `python -I`
  et `PYTHONIOENCODING=utf-8`.
- **Réseau :** e-codices (images IIIF) et `https://nocturnale.marteo.fr/chant/<code>` (source de
  chaque pièce NR).
- Les images de Hartker (CC BY-NC) restent dans `cache/` (non versionné) ; seules les boîtes
  des découpes sont versionnées (`sources/`), et les extraits retenus vivent dans le `.sfd`.

Ci-dessous, `S` désigne `scripts/`, `K` la racine du skill, `F` le fichier
`<grehartker>/src/grehartker.sfd`, `GA` le fichier `<gregorio-patch>/gregall.sfd`.

## Règles décidées par marteo

**Compatibilité avec gregall (bloquant, `S/check_metrics.py`)**
- Paramètres de police, noms et encodage des glyphes identiques. La hauteur de `cl` (ymax = 573)
  est le pas de hauteur NABC : identique, exactement.
- Chasses identiques, sauf élargissement de 20 % au plus quand le contour dépasse de sa chasse
  plus que celui de gregall ; jamais réduites.

**Échelle et calage**
- Une seule échelle : 10 unités de police par pixel e-codices pleine résolution (6132 × 8176).
  **Jamais de mise à l'échelle d'un contour** : tout l'intérêt de grehartker est de corriger
  les différences d'échelle entre glyphes de gregall.
- Calage par `S/caler.py` seulement : bas sur le bas de gregall (sauf `cl` : haut sur haut),
  centre horizontal placé par rapport au milieu de la chasse comme dans gregall.

**Formes de base et composés**
- On travaille par lot graphique, pas par fréquence. Un lot réunit tous les glyphes qui
  partagent un élément, pour que choix et tailles soient cohérents (lot « virga » : `vi`, `ci`,
  `sc`, `bv`, `tv`).
- Chaque glyphe se décompose en formes de base (`reference/decompositions.tsv`) ; l'inventaire
  des formes à détourer est `reference/formes_de_base.tsv`.
- **Le dessin de gregall fait foi** pour décomposer un neume en plusieurs morceaux. Vérifier
  chaque morceau contre toutes les variantes de sa famille (`S/gregall_formes.py morceaux`) :
  `cl` et `clS`, `pe` et `peN` se confondent facilement.
- Un glyphe composé reprend son neume de base **en référence**, à la hauteur 0, jamais redétouré
  ni réduit (`S/composer.py`). Les points et traits sont des références aux modèles d'éléments :
  `pu` (su, pp), `ta` (t), `taN` (u), `gr` (w), `grN` (y), `stB` (x : la stropha liquescente
  `st>`, aussi dernier élément de `ds>` et `ts>`). L'exemplaire d'un composé ne sert qu'à placer
  les éléments par rapport au neume de base.
- Une variante épisémée ou liquescente (`viN`, `clN`, `toN1`, `peB`…) ne reprend pas sa base
  telle quelle : fusion du contour de base avec l'épisème ou la liquescence
  (`S/composer.py --copie`), ou détourage complet. Son exemplaire est choisi pour sa cohérence
  avec le glyphe de base retenu (même fût, même angle : `S/planche.py … --sur <base>`).
- Oriscus sans glyphe propre dans gregall : `or_salicus` (∩, salicus), `or_couche` (~, certains
  salicus : `sa1`, `saN1`, `saB2`, `saM1`, `saNB1`, `saM4`), `or_pi` (pressus minor :
  `pi = or_pi + pu`, pendant court de la virga strata du pressus maior : `pr = vs + pu`).
- Ligatures (`!`) : seuls les morceaux qui se touchent sont liés (`clEpi = cl!or_pi + pu`) ; la
  virga d'un salicus lié à une clivis se fond dans la clivis (`saEcl = pu + or_salicus + cl`).

**Choix des exemplaires**
- Pour chaque forme : un choix et quatre variantes, **toutes de pages différentes**, présentés
  sur une planche avec gregall à la même échelle. marteo choisit, ou demande une variante.
- Préférer des pages en module courant. Écarter les mains plus tardives et les autres mises en
  page (391 p. 110, 150, 240 ; 390 p. 192, litanies ; voir `sources/pages_examinees.csv`).
- Pour un neume rare, passer par les pièces NR qui l'emploient (`S/sources_nr.py`) : le site
  NR donne la page de Hartker de chaque pièce.
- Les identifications données en passant par marteo (lettres, éléments…) vont dans
  `sources/reperes.csv`.

**Divers**
- Couleurs de glyphes dans le `.sfd` : rouge à refaire, jaune en cours, vert refait.
- Ne jamais relancer `S/init_grehartker.py` sur `F` : il écraserait le travail.
- Commits et messages en anglais ; documentation en français. `F` n'est commité qu'avec
  `S/check_metrics.py` sans erreur.

## Chercher et choisir des exemplaires

1. **Pages.** Vérifier la main sur des aperçus, télécharger, segmenter :
   ```
   python -I S/pages.py apercu 391:50 391:70 …
   python -I S/pages.py telecharger 391:50 391:70 …
   python -I S/pages.py segmenter
   ```
   Le cache (`cache/pages`, `cache/seg.pkl`) se reconstitue sur un nouvel ordinateur :
   `python -I S/pages.py liste` puis télécharger les pages de `sources/pages_examinees.csv`
   dont on a besoin (celles des exemplaires et repères au minimum).
2. **Candidats.** Une forme d'un seul tenant, à partir d'exemplaires connus :
   ```
   python -I S/candidats.py <nom> --glyphe taN | --repere stB | --boite 391:53:1003,2876,57,56
   ```
   Un neume avec points (placement d'un composé) :
   ```
   python -I S/motifs.py <nom> --base vi viN [--type vi] --motifs "|tt" "pp|" "||2" … [--pages 391:53 …]
   ```
   Un neume rare : `python -I S/sources_nr.py <neume> --nr <NR> --telecharger`, puis repérer la
   syllabe sur la page et relever la boîte, ou lancer `candidats.py` sur les pages téléchargées.
3. **Proposer.** Inscrire choix et variantes, puis faire la planche pour marteo :
   ```
   python -I S/retenir.py <glyphe> <nom> <i_choix> <i_A> <i_B> <i_C> <i_D>
   python -I S/planche.py <nom> <glyphe> … [--sur vi]
   ```
   Après la décision : `S/retenir.py <glyphe> --permuter "variante C"` si besoin.
4. **Importer** (après accord de marteo seulement), puis vérifier et commiter `F` dans grehartker :
   ```
   ffpython S/import_hartker.py F <glyphe> <ms> <page> <x> <y> <w> <h> [bas|haut]
   ffpython S/import_hartker.py F <composé> <ms> <page> <x> <y> <w> <h> base <bx>,<by>,<bw>,<bh>
   ffpython S/check_metrics.py GA F K/reference/usage_nr.tsv
   ```
   `haut` pour `cl` ; `base` après `S/composer.py` pour un composé (boîte du seul neume de base,
   colonne `base` de `sources/exemplaires.csv`) ou après `S/composer.py --copie` pour une variante.

## Détourer et construire (pas encore commencé)

1. Détourer la forme de base au premier plan de `F` (FontForge), d'après l'image d'arrière-plan.
2. `ffpython S/caler.py F <glyphe>` : calage et chasse ; les composés qui le référencent suivent.
3. Composés : `ffpython S/composer.py F <composé>` (référence au neume de base), puis placer les
   références aux modèles d'éléments aux positions de l'exemplaire. **À faire :** un outil qui
   construit le composé entier depuis `reference/decompositions.tsv` et les boîtes mesurées sur
   l'exemplaire.
4. `ffpython S/check_metrics.py GA F K/reference/usage_nr.tsv`, puis
   `ffpython S/build.py F build/grehartker.ttf` et un document de test GregorioTeX.

## Autres scripts

| Commande | Effet |
|---|---|
| `python -I S/decompose.py K/reference/familles.tsv K/reference/decompositions.tsv K/reference/formes_de_base.tsv` | décompose tous les glyphes NR et refait l'inventaire (décompositions tranchées : dictionnaires en tête du script) |
| `ffpython S/familles.py GA K/reference/usage_nr.tsv K/reference/familles.tsv` | familles par code NABC, base, variante d'origine, écarts de taille dans gregall |
| `python -I S/gregall_formes.py famille <fam>` / `glyphes …` / `morceaux …` | planches de gregall ; morceaux d'un glyphe comparés aux glyphes simples |
| `texlua S/nabc_usage.lua <gregoriotex-nabc.lua> S/gregall_metrics.lua <sortie.tsv> gabc/*_marteo.gabc` | recompte l'usage des glyphes dans NR (depuis le dépôt NR) |
| `python -I S/calibrate.py` | recalcule l'échelle d'après `sources/calibration.csv` (fait : 10 u/px) |
| `ffpython S/dump_metrics.py <police.sfd> <dossier>` | paramètres et métriques par glyphe |
| `ffpython S/init_grehartker.py GA <nouveau.sfd>` | crée une police de travail depuis gregall (déjà fait) |

## Pièges connus

- `glyph.boundingBox()` de FontForge englobe le calque gabarit `gregall` : utiliser
  `commun.fore_bbox()`. `glyph.transform()` déplace aussi le gabarit : transformer le calque.
- Échelle et position des images d'arrière-plan ne sont pas exposées par l'API Python :
  `import_hartker.py` les écrit directement dans le `.sfd`.
- Téléchargements e-codices : un à la fois, sinon le serveur tronque les images.
- La segmentation inclut le halo d'encre pâle : les boîtes sont un peu plus grandes que le trait.
- La détection automatique se trompe : une « stropha » peut être une lettre `i`, le haut d'un
  `c` de `co`, un point de `su2`… Tout candidat se vérifie à l'œil, et marteo tranche.

## État au 11 novembre 2026

- **Dans la police (`F`), exemplaire importé en arrière-plan, rien de détouré :** `ta`, `taN`,
  `pu`, `stB`, `gr`, `grN`, `vi`, `viN`, `viB`, `ciN` (placement des points), `cl`, `clN`, `pe`,
  `peS`, `to`. `check_metrics` : 0 erreur.
- **Choisis, pas encore importés :** les exemplaires de placement des composés `viNsut2`,
  `viNsu1sut2`, `viNsut1su2`, `viNsuu1su2`, `viNsuu2`, `viNsut3`, `viNsu1sut1`, `viNpp2`.
- **Choisis avant la règle de cohérence par lot, à revoir avec leur lot :** `cl`, `clN`, `pe`,
  `peS`, `to`.
- **Décompositions :** les 414 glyphes utilisés dans NR, tous tranchés ; 145 formes de base
  (71 neumes, 7 modèles d'éléments, 27 lettres dont le c mi-long `lsc_semi`, 34 ligatures,
  3 crochets/vide, 3 sans glyphe propre : `or_salicus`, `or_pi`, `or_couche`).
- **Lot virga (12 novembre 2026) :** exemplaires de placement proposés pour 30 glyphes de plus
  (`ci`, `ciNpp2`, `sc`, `bvN`, `bv`, `ciS`, `ci1`, `ciS1`, `scS`, `scB`, `tvN`, `bvNsut2` et
  18 `vi…su/pp`), en attente de la décision de marteo ; `viNB` pas encore trouvé avec certitude.
  Sans exemplaire propre (placement à emprunter au glyphe le plus proche) : `ciB`, `ciM`,
  `ciMN` (comme `ci`/`ciN`), `viNsut4`, `viBppt2`, `visuu1su2`, `viNsuu2su2`, `vippt1su1sut1`,
  `viNppt3`, `visu1suu1su2`, `visuu3`, `viNpp4`, `visut1sux1`, `viNsu1sux1`, `visu2sux1`.
- **Pages examinées :** 104 (`sources/pages_examinees.csv`), dont 4 exclues ; 100 en cache.

**Prochaines étapes :**
1. Lot virga : décision de marteo sur les propositions, `viNB`, puis import.
2. Outil de construction des composés par références (voir plus haut).
3. Lots suivants, par usage : clivis, pes, torculus, quilisma…, avec revue des choix anciens.
4. Exemplaires des formes sans glyphe propre : `or_salicus`, `or_pi` (sur les mêmes pages que
   `vs`), `or_couche`.
5. Licence et demande à la Stiftsbibliothek (`docs/`), auteur à confirmer.
