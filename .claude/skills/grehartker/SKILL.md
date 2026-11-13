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
  Son Python n'a pas HTTPS sous Windows : les téléchargements passent par `curl`. Sous Linux, le
  module `fontforge` du système suffit : un environnement virtuel créé avec
  `--system-site-packages` sert à la fois de `python` et de `ffpython`. Les scripts *ffpython*
  se lancent **sans** `-I` (sinon `import commun` échoue).
- **Python 3** avec `pip install -r scripts/requirements.txt` (Pillow, numpy, scipy), de
  préférence dans un environnement virtuel, pour les autres scripts. Lancer avec `python -I`
  et `PYTHONIOENCODING=utf-8`.
- **Réseau :** e-codices (images IIIF).
- **Pièces NR :** `sources/pieces_nr.tsv` (page de Hartker de chaque pièce NR, **toutes
  contributions** : marteo, dcrochu, sandhofe, mattiacus…) s'exporte de la base du site par son
  shell Django, en lecture seule (`S/export_pieces_nr.py`, voir son en-tête) ; les emplois des
  glyphes lisent les gabc de marteo (dépôt NR) et ceux des autres contributeurs (dossier gabc du
  site). Ne pas se limiter aux transcriptions de marteo : on manquerait des pages (390 p. 72 pour
  `clS1`, transcrite par dcrochu) ;
  `texlua` pour `S/nabc_occurrences.lua` (emplois des glyphes par pièce et syllabe).
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
- **Ligatures traitées en dernier** (décision de marteo, 13 novembre 2026) : une fois choisis les
  glyphes qui les composent, pour juger leur cohérence par superposition en transparence.
- Ligatures (`!`) : seuls les morceaux qui se touchent sont liés (`clEpi = cl!or_pi + pu`) ; la
  virga d'un salicus lié à une clivis se fond dans la clivis (`saEcl = pu + or_salicus + cl`).

**Choix des exemplaires**
- Pour chaque forme : un choix et quatre variantes, **toutes de pages différentes**, présentés
  sur une planche avec gregall à la même échelle. marteo choisit, ou demande une variante.
- Préférer des pages en module courant. Écarter les mains plus tardives et les autres mises en
  page (391 p. 110, 150, 240 ; 390 p. 192, litanies ; voir `sources/pages_examinees.csv`).
- Pour un neume rare, ou dont la recherche automatique ne donne que de faux neumes, passer par
  les pièces NR qui l'emploient (`S/sources_nr.py`) : il donne les pages de Hartker, les pièces
  et les syllabes ; puis chercher sur ces pages (`motifs.py --pages … --serre`).
- **Provenance toujours notée, le plus précisément possible :** page, boîte et pièce (code NR,
  incipit, syllabe), colonne `piece` de `sources/exemplaires.csv`. `S/retenir.py` la remplit
  d'après les pièces NR de la page qui emploient le glyphe (« ? a | b » si plusieurs sont
  possibles) ; la compléter à la main quand on la connaît mieux.
- **Glyphes de gregall venus de Hartker** (`reference/gregall_sources.tsv`, d'après
  GregorioNabcRef : 131 glyphes, avec pièce et mot) : les proposer parmi les variantes, sans les
  privilégier.
- **En cas de doute, repartir des exemplaires identifiés dans NR** (`sources_nr.py` : pièce,
  syllabe, page), et relever le neume sur la page, plutôt que de se fier à la recherche par
  ressemblance (ex. `clBppt2` : la recherche donnait des `toppt2` et `toppt1`).
- Contrôle d'échelle : superposer en rouge très transparent le glyphe de base associé
  (`planche.py … --sur <base>`) ; les planches de restitution ne sont plus demandées.
- **Vrais neumes seulement :** un scandicus n'est pas une virga précédée des points du neume
  voisin, une bivirga n'est pas deux virgas isolées, un climacus à quatre points n'est pas un
  climacus à deux points suivi de deux points d'un autre neume. Les éléments d'un vrai neume se
  suivent de près et régulièrement (`--serre`).
- Un exemplaire de placement d'une forme voisine peut servir en dernier recours (ex. un
  `viNsuu2su2` pour placer `viNsuu1sut1su2` en posant bien `taN ta pu pu`), mais on cherche
  d'abord un vrai exemplaire. Les exemplaires reconnus en passant vont dans `sources/reperes.csv`.
- Un composé d'une variante (`bvNsut2`) se choisit cohérent avec le choix de la variante (`bvN`) :
  superposer (`planche.py … --sur bvN`).
- Les identifications données en passant par marteo (lettres, éléments…) vont dans
  `sources/reperes.csv`.
- **Rappel :** l'exemplaire d'un composé ne sert qu'à placer les éléments les uns par rapport aux
  autres ; les éléments eux-mêmes (neume de base, `pu`, `ta`, `taN`…) sont réutilisés d'un composé
  à l'autre. `S/restituer.py` pose les formes retenues sur l'exemplaire pour juger l'harmonie.

**Vocabulaire de marteo**
- Le *céphalicus* est la forme en crosse qui s'enroule vers l'intérieur (`cl>`, `clB` : 390 p. 61,
  Valde honorandus, *commendavit*). Le « P » (hampe et petite boucle fermée en haut) est `viB`,
  pas un céphalicus.
- Le « Ꝛ » à pied tourné à droite suivi d'un tractulus dessous, devant une virga épisémée à deux
  points, est `toS2sut1` (ou `clSsut1`) suivi d'un `ci-`, pas un `vippt1su2`.

- `clM` : petite jambe gauche, longue jambe droite qui descend bien plus bas (forme de « 7 ») ;
  ce n'est ni une clivis à jambes presque égales, ni un `toM1` (qui a la note initiale du
  torculus). Référence : 391 p. 88, *Quem dicunt*, *Filium* (avec `lsc`). `clMN` : même forme
  avec épisème.

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
   Un neume rare : `python -I S/sources_nr.py <glyphe> … --telecharger [--suivantes]`, puis
   `pages.py segmenter` et `motifs.py … --pages <pages données> --serre`, ou repérer la syllabe
   sur la page et relever la boîte.
3. **Proposer.** Inscrire choix et variantes, puis faire la planche pour marteo :
   ```
   python -I S/retenir.py <glyphe> <nom> <i_choix> <i_A> <i_B> <i_C> <i_D>
   python -I S/planche.py <nom> <glyphe> … [--sur vi]
   python -I S/restituer.py <nom> <glyphe> …        # formes de base retenues posées sur l'exemplaire
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
| `python -I S/gregall_sources.py [GregorioNabcRef.tex]` | provenance des glyphes de gregall d'après la doc de Gregorio : `reference/gregall_sources.tsv` |
| `SKILL=<skill> python manage.py shell < S/export_pieces_nr.py` | (dans le site NR, venv activé) page de Hartker de chaque pièce NR : `sources/pieces_nr.tsv` |
| `texlua S/nabc_occurrences.lua <gregoriotex-nabc.lua> S/gregall_metrics.lua cache/nabc_occurrences.tsv gabc/*_marteo.gabc` | glyphes posés par pièce et syllabe (refait automatiquement s'il manque) |
| `python -I S/calibrate.py` | recalcule l'échelle d'après `sources/calibration.csv` (fait : 10 u/px) |
| `ffpython S/dump_metrics.py <police.sfd> <dossier>` | paramètres et métriques par glyphe |
| `ffpython S/init_grehartker.py GA <nouveau.sfd>` | crée une police de travail depuis gregall (déjà fait) |

## Pièges connus

- `glyph.boundingBox()` de FontForge englobe le calque gabarit `gregall` : utiliser
  `commun.fore_bbox()`. `glyph.transform()` déplace aussi le gabarit : transformer le calque.
- Échelle et position des images d'arrière-plan ne sont pas exposées par l'API Python :
  `import_hartker.py` les écrit directement dans le `.sfd`.
- Téléchargements e-codices : un à la fois, sinon le serveur tronque les images.
- Ne pas lancer deux scripts quand `pages.py segmenter` tourne : il réécrit `cache/seg.pkl`
  après chaque page. Une bande décodée pèse ~100 Mo : `hartker.crop` n'en garde que six.
- Le parseur NABC applique des alias (`vipp2` → `sc`, `vi>pp2` → `scB`, `cippt1` → `vippt1su2`) :
  chercher les emplois d'un glyphe par `hartker.occurrences()`, pas dans le texte des gabc.
- La segmentation inclut le halo d'encre pâle : les boîtes sont un peu plus grandes que le trait.
- La détection automatique se trompe : une « stropha » peut être une lettre `i`, le haut d'un
  `c` de `co`, un point de `su2`… Tout candidat se vérifie à l'œil, et marteo tranche.

## État au 13 novembre 2026

- **Dans la police (`F`), exemplaire importé en arrière-plan, rien de détouré :** `ta`, `taN`,
  `pu`, `stB`, `gr`, `grN`, `vi`, `viN`, `viB`, `ciN` (placement des points), `cl`, `clN`, `pe`,
  `peS`, `to`. `check_metrics` : 0 erreur.
- **Choisis, pas encore importés :** les exemplaires de placement des composés `viNsut2`,
  `viNsu1sut2`, `viNsut1su2`, `viNsuu1su2`, `viNsuu2`, `viNsut3`, `viNsu1sut1`, `viNpp2`.
- **Lot virga, décisions de marteo (13 novembre 2026) :** acceptés `ci`, `ciN`, `bvN`, `ciS`,
  `ci1`, `visu1suu1`, `visut1su2`, `visu1sut2`, `visut3`, `viNsuu3`, `viNsu1suu1`, `tvN` ;
  `ciNpp2` = ancienne variante D (390 p. 22), `ciS1` = ancienne variante A (391 p. 88).
  Rejetés comme faux neumes (points du neume voisin, virgas isolées…) et recherchés à nouveau
  avec `motifs.py --serre` et les pages des pièces NR : `sc`, `scS`, `scB`, `bv`, `viNsu1suu2`
  (c'était un `bvNsu1suu2`), `viNsu3` (style), `viNsuu1sut1su2` (c'était un `viNsuu2su2`),
  `vippt1su2` (c'était un `vippu1su2`, repris pour `vippu1su2`), `vippu1su2` (c'était un
  `viN` + `visu2`), `bvNsut2` (à rendre cohérent avec `bvN`), `viNsu2sut1`, `viNsu4`,
  `viNsu1suu1su2` (c'était un `viNsu1suv1su2`, gardé dans `reperes.csv`).
  Nouvelles propositions inscrites, en attente : `sc`, `scS`, `scB`, `bv` (vraies bivirgas
  simples, suivies de deux tractulus : dans Hartker presque toutes les bivirgas sont
  épisémées), `viNsu1suu2`, `viNsu3`, `viNsuu1sut1su2` (391 p. 134, Fundata est domus, source de
  gregall ; NR y transcrit `vi-suu2su2`), `vippu1su2`, `bvNsut2` (classés par cohérence
  mesurée avec `bvN`), `vippt1su2` (tractulus seul au pied de la virga ; la variante C, avec un
  « Ꝛ + tractulus » devant, est sans doute un `ciG` + `ci`), `viNsu1suu1su2` (391 p. 194 et
  232), `viNsu2sut1` (390 p. 46, dernier élément peut-être un uncinus). Toujours sans vrai
  exemplaire dans les 411 pages : `viNsu4`.
  `viNB` : choisi 390 p. 80 (n° 30 de `viNB_c`, la petite `lsi` à sa droite est hors boîte).
- **Restitution :** `restituer.py` sur tous les choix du lot virga (planches
  `restitution_virga_1..3`).
- **Décompositions :** les 414 glyphes utilisés dans NR, tous tranchés ; 145 formes de base
  (71 neumes, 7 modèles d'éléments, 27 lettres dont le c mi-long `lsc_semi`, 34 ligatures,
  3 crochets/vide, 3 sans glyphe propre : `or_salicus`, `or_pi`, `or_couche`).
- **Pages :** les bandes du corps principal des deux volumes (390 p. 16–191, 391 p. 3–239, hors
  pages exclues) sont téléchargées et segmentées ; `sources/pages_examinees.csv` ne liste que
  les pages vérifiées à l'œil.
- **Lot clivis (commencé le 13 novembre 2026) :** `cl` et `clN` gardés, cohérents entre eux
  (`planche.py clivis_1 cl clN clS clM --sur cl`). Proposés : `clS` (pied tourné vers la droite,
  `candidats.py --trait pied`), `clM` (clivis étroite, à confirmer). `clB` : choisi 390 p. 80 (céphalicus trouvé à partir de celui désigné par marteo). Restent `clNB`, `clSN`, `clMN`, les formes rares (`clS1`, `clSN1`,
  `clNB1`, `clSN2` : propositions faites, `clSN1`, `clSN2`, `clNB1` validés), les ligatures (`cl!or_pi`, `cl!po`, `cl!poN1`, `cl!clS`, `cl!vs`) et les
  composés (`ciG`, `ciG1`, `clSsut2`, `clSNsu2`, `clSsuu1su2`, `clN1su2`, `clBppt2`, lettres).
  `reperes.csv` garde des `ciG?` (clS avec tractulus sous le pied) et des salicus.

- **Décisions du 13 novembre 2026 (suite) :** `decision_virga_1..4` validés sauf : `scB` (les
  propositions étaient des `sf` ; `scB` n'est employé que deux fois dans NR, dont *Libera me…
  de morte*, 391 p. 198, *ter*, page trop pâle : toujours sans exemplaire) ; `bv` = 391 p. 68
  (*Exaltare Domine*, *xal*, bivirga isolée, boîte relevée à la main), les `bvsut2` en
  variantes ; `viNsu1suu1su2` = 391 p. 232 ; `viNsu2sut1` = nouvelles propositions (390 p. 148…),
  l'ancien était un `viNsu2suu1` ; `vippt1su2` : aucune proposition n'en était (`viNppt2su2`,
  `viNppt1su2`, `visu1sut1` + `ciN`, `clSsut1` + `ciN`, notés dans `reperes.csv`), toujours sans
  exemplaire ; `cl`, `clN`, `clS` validés ; `clM` : les premiers étaient des `cl`, puis des
  `toM1` (repères) ; nouvelles propositions à jambe droite profonde (`candidats.py --trait
  patte`, pages NR de `clM`).

**Prochaines étapes :**
1. Lot virga : décisions de marteo sur les nouvelles propositions, `viNB`, puis import.
2. Lot clivis : revue de `cl` et `clN`, puis variantes cohérentes avec `cl` (`--sur cl`),
   ligatures et composés.
3. Outil de construction des composés par références (voir plus haut).
4. Lots suivants : pes, torculus, quilisma… ; formes sans glyphe propre (`or_salicus` : de
   nombreux salicus sont apparus dans les recherches de scandicus, `or_pi`, `or_couche`).
5. Licence et demande à la Stiftsbibliothek (`docs/`), auteur à confirmer.
