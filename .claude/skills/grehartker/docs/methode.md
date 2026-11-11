# grehartker — méthode et état des travaux

> Document de référence du skill `grehartker` (dépôt `tooling` de Nocturnale Romanum).
> Les chemins `scripts/`, `reference/`, `sources/` et `docs/` sont ceux du skill ; `src/grehartker.sfd`
> est dans le dépôt `grehartker`.

Police de neumes sangalliens pour GregorioTeX (NABC), redessinée **uniquement** d'après
l'antiphonaire de Hartker. Elle remplace gregall **en changeant le moins possible la mise en
page** : un document composé avec gregall doit se composer correctement, et presque à
l'identique, avec `\gresetnabcfont{grehartker}{9}`.

## 1. Ce qui doit rester identique à gregall

Tout ce que lisent `gregoriotex-nabc.lua` et le moteur TeX :

| Élément | Valeur gregall | Pourquoi |
|---|---|---|
| em / ascent / descent | 1000 / 800 / 200 | échelle de la police à la taille demandée |
| OS/2 typo (asc/desc/linegap) | 800 / −200 / 90, UseTypoMetrics | métriques de ligne |
| OS/2 win (asc/desc) | 1722 / 1570 | idem |
| hhea (asc/desc/linegap) | 1722 / −1570 / 90 | idem |
| Jeu de glyphes | 607 glyphes NABC + `space` | la Lua ne lit que la plage **U+E400–U+EFFF** et retrouve les glyphes **par leur nom** |
| Noms de glyphes | codage `B` = `>`, `N` = `-`, `E` = `!`, `T` = `~` (`qlEclB1` = `ql!cl>1`) | la Lua reconstruit le nom NABC à partir du nom de glyphe |
| Encodage | identique | pas indispensable (la Lua passe par les noms), mais sans risque |
| **Chasse** (advance width) de chaque glyphe | identique, sauf élargissement de 20 % au plus quand le contour de Hartker dépasse de la chasse plus que celui de gregall (§ 5) ; jamais réduite | espacement horizontal, centrage des lettres significatives |
| **Hauteur de `cl`** (ymax = 573) | identique, exactement | pas de hauteur des descripteurs `h[a-np]` : `baseraise = (h − 5) × cl.height / 4` |
| Bas de chaque glyphe (ymin) | identique (calage bas sur bas), sauf glyphes composés : leur neume de base est à la hauteur du glyphe de base, les points peuvent descendre plus bas que dans gregall | position du neume par rapport aux autres et à la ligne |
| Centre horizontal du contour, par rapport au milieu de la chasse | identique | centrage des lettres significatives |
| Haut de chaque glyphe (ymax) | libre : proportions de Hartker | placement des lettres significatives (positions 1–9) et des pp/su, à vérifier sur document de test |
| `ni`, `ob`, `cb` | repris tels quels | glyphe vide et crochets NABC, rien à détourer |

Le nom de police n'a pas d'importance pour la Lua : elle applique les alias gregall à toute
police sauf `grelaon`. `\gresetnabcfont` charge la police par `name:grehartker`, il faudra donc
l'installer dans l'arbre TeX (comme gregall.ttf) et mettre à jour la base luaotfload.

## 2. État des lieux de gregall

- Source utilisée : `Documents/gregorio-patch/gregall.sfd` (version modifiée pour NR, identique au
  `gregall.ttf` installé dans MiKTeX). Elle part de la branche develop de gregorio et ajoute
  11 glyphes : `pfEpi pisux1 pqSN qlEclB1 qlEclS1 qlNppt1sut2su1 toEclB toEpisu1 toSEcl toSEclN toSEclNlsi8`.
- Contours quadratiques (TrueType), aucune référence ni ancre, aucune table GSUB/GPOS.
- 490 glyphes ont leur image source dans le calque Back. Les échelles d'import varient
  (19,23 unités/px pour la majorité ; ~170 glyphes entre 7,8 et 38,5) : les images de gregall
  viennent de plusieurs manuscrits et ont été mises à la taille glyphe par glyphe.
- 117 glyphes n'ont pas d'image : surtout des combinaisons avec pp/su assemblées à partir
  d'autres glyphes.
- 47 glyphes de lettres significatives (`lsc`, `lst`, `lse`, …).
- Remarque : `nocturnale-romanum/common_headers.tex` charge aujourd'hui `gresgmodern` à 12 pt ;
  c'est `liber-responsorialis/common_headers.tex` qui charge `gregall` à 9 pt.

## 3. Usage réel dans NR (priorités)

Le vrai parseur de `gregoriotex-nabc.lua` (version patchée) a été exécuté sur tous les
`gabc/*_marteo.gabc` et `ORAL2.gabc` (`scripts/nabc_usage.lua`) :

- 1 018 pièces avec NABC, 66 367 segments NABC, 91 891 glyphes posés ;
- **414 glyphes utilisés sur 607** (193 jamais utilisés dans NR) ;
- couverture cumulée : **29 glyphes → 80 %**, 57 → 90 %, 94 → 95 %, 198 → 99 % ;
- les 20 premiers : `ta` 14 708, `vi` 14 394, `clN` 7 283, `pe` 6 207, `to` 3 649, `cl` 3 458,
  `cllsc3` 2 068, `viN` 1 918, `peS` 1 815, `ciN` 1 735, `viB` 1 580, `pr` 1 452, `lsc` 1 129,
  `taB` 1 087, `lse` 987, `ppt2` 903, `ob` 859, `cb` 847, `qlEclppt1` 824, `ciNpp2` 779 ;
- un seul segment donne une erreur : `/////vi-sut2qi!po-1/vi>hj` dans `0121N1R1_marteo.gabc`
  (déjà en erreur avec gregall, sans rapport avec la police).

Liste complète : `reference/usage_nr.tsv`. Le rapport `build/avancement.csv` est trié par usage.

## 4. Source : antiphonaire de Hartker

- St. Gallen, Stiftsbibliothek, **Cod. Sang. 390** (volume d'hiver, 194 p.) et
  **Cod. Sang. 391** (volume d'été, 264 p.), vers 990–1000.
- e-codices : <https://www.e-codices.unifr.ch/fr/list/one/csg/0390> et `/csg/0391`.
- Manifestes IIIF :
  `https://www.e-codices.unifr.ch/metadata/iiif/csg-0390/manifest.json`,
  `https://www.e-codices.unifr.ch/metadata/iiif/csg-0391/manifest.json`.
- Licence des images : **CC BY-NC**.

### Licence proposée (détail : `LICENSE.md` du dépôt `grehartker`)

- **Contours détourés d'après Hartker** : **CC BY-NC-SA 4.0**. Elle est cohérente avec la clause NC
  des images et interdit la vente de la police, y compris groupée avec un logiciel. Une
  **permission additionnelle** autorise les documents produits avec la police (PDF, livres
  imprimés vendus en impression à la demande, police incorporée ou sous-ensemble). Sans elle,
  les éditions KDP du Liber responsorialis tomberaient sous la clause NC.
- **Ce qui vient de gregall** (contours bouche-trou, calque `gregall`) : reste sous **OFL**, que la
  CC BY-NC-SA ne peut pas remplacer. Aucune diffusion publique de la police tant qu'il reste des
  contours gregall au premier plan. La version publiée est générée sans le calque `gregall`.
  Les paramètres, noms et chasses repris de gregall sont des données fonctionnelles de
  compatibilité.
- **Outils** : GPL-3.0, comme NR et Gregorio.
- **Clause NC des images e-codices** : on ne sait pas si des contours redessinés sont une œuvre
  dérivée des photographies. Le plus sûr est de demander l'accord de la Stiftsbibliothek,
  surtout pour les livres vendus. Un brouillon de demande est prêt :
  `docs/demande-autorisation-stiftsbibliothek.md`.

## 5. Méthode proposée

1. **Une seule échelle pour toute la police : 10 unités de police par pixel e-codices**
   (pleine résolution, 6132 × 8176 px par page). Toutes les découpes sont prises à cette
   résolution et importées à cette échelle : les proportions de la main de Hartker sont
   conservées d'un glyphe à l'autre, sans mise à la taille au cas par cas comme dans gregall.
   Voir « Calibration » ci-dessous.
2. **Par glyphe**, dans FontForge, sur `src/grehartker.sfd` :
   - choisir un exemplaire représentatif dans Hartker et relever sa boîte (x, y, w, h) en
     pixels pleine résolution ;
   - `scripts/import_hartker.py` le télécharge, l'importe dans le calque Back à l'échelle 10, le
     cale sur le gabarit `gregall` (centre horizontal ; bas sur bas, ou haut sur haut pour
     `cl`), passe le glyphe en jaune et note la source dans le commentaire ;
   - détourer au premier plan (remplace le contour gregall laissé en bouche-trou) ;
   - **ne jamais mettre à l'échelle** le contour, même pour l'approcher de gregall : tout
     l'intérêt de grehartker est de corriger les différences d'échelle entre glyphes de gregall,
     qui rendent la police inhomogène ;
   - lancer `scripts/caler.py`, qui applique les règles de calage (ci-dessous) ;
   - noter la source dans le commentaire du glyphe (ex. `Hartker 390, p. 45, l. 3`) ;
   - couleur : rouge = à refaire, jaune = en cours, **vert = refait**.
3. **Règles de calage** (`scripts/caler.py`), pour limiter l'impact sur les livres déjà
   composés avec gregall :
   - translation seulement, à l'échelle commune ;
   - **vertical** : bas du contour sur le bas du contour gregall. Exception : `cl`, haut sur
     haut, car son ymax (573) est le pas de hauteur NABC. Glyphes composés : pas de calage
     vertical propre, le neume de base reste à la hauteur du glyphe de base (point 5) ;
   - **horizontal** : le centre du contour est placé par rapport au milieu de la chasse
     exactement comme celui de gregall ;
   - **chasse** : si le contour dépasse de la chasse (à gauche ou à droite) plus que le contour
     gregall, la chasse est élargie juste assez pour ne pas dépasser davantage, dans la limite
     de **+20 %** de la chasse gregall ; le contour est recentré sur la nouvelle chasse. Au-delà
     du plafond, le dépassement restant est signalé. La chasse n'est jamais réduite.
4. **Ordre : par familles**, et non glyphe par glyphe. Un lot couvre tous les glyphes utilisés
   dans NR qui partagent le même neume de base (`to`, `toN`, `toN1`, `toS`, `toS2`, `toppt1`,
   `toSsu2`, `tolsc3`, `toEcl`…), pour que les choix soient cohérents entre eux et surtout que le
   neume de base garde **la même taille** dans tous les glyphes de la famille. gregall ne le
   respecte pas : pour loger les points ou les lettres, il réduit souvent le neume de base
   (`toSsu2` : neume de base à 73 % de la largeur de `toS` ; `toS2su2` : 61 % ; `ciNpp2` : 73 %
   de `ciN`). Ces écarts sont à corriger dans toute la police.
   Les familles sont dans `reference/familles.tsv` (`scripts/familles.py`), avec l'écart de taille
   mesuré dans gregall pour chaque glyphe composé. Les familles sont traitées par usage total
   décroissant : `vi` (43 glyphes), `ta` (5), `cl` (28), `pe` (35), `to` (34), `ql` (54)…
   Les lettres significatives seules (`ls`) et les points seuls (`pp-su`) forment leurs propres
   familles.
   **Lots graphiques.** Le code NABC ne suffit pas à grouper les glyphes qui partagent un
   élément : le climacus (`ci`), le scandicus (`sc`), la bivirga (`bv`) et la trivirga (`tv`)
   sont aussi une virga avec des points ou des traits. Le lot « virga » réunit donc les
   familles `vi`, `ci`, `sc`, `bv` et `tv` ; ses formes qui contiennent un pes ou une clivis
   vont aux lots « pes » (`scM1 = viN + pe`, `scG = ta + pe`…) ou « clivis » (`ciG = clS + ta`,
   `ciG1`). Les autres familles forment chacune leur lot. Mesure du 11 novembre 2026 : le fût
   de la virga a le même angle seule, dans le climacus et dans le scandicus (42–44°) ; il est
   plus long dans le climacus (95 px contre 82–84 px), et les virgas retenues (93 px) sont entre
   les deux.

   **Décomposition de tous les glyphes et inventaire des formes de base.**
   `scripts/decompose.py` décompose les 414 glyphes utilisés dans NR en formes de base
   (`reference/decompositions.tsv`) et en tire l'inventaire des formes à détourer
   (`reference/formes_de_base.tsv`, avec le nombre de glyphes et d'occurrences NABC qui les
   emploient, et l'exemplaire choisi le cas échéant). Une forme de base est un neume à un seul
   tenant (`vi`, `pe`, `clS`, `vs`…), un modèle d'élément pour les points et traits (`pu`,
   `ta`, `taN`, `gr`, `grN`, `stB`), une lettre significative, une ligature (`ql!cl` : les neumes
   liés par `!` se détourent d'un seul tenant ; leurs points et lettres restent à part), ou une
   forme sans glyphe propre dans gregall. Les neumes que gregall dessine en plusieurs morceaux
   sont décomposés d'après ce dessin, qui fait foi : climacus et scandicus, pressus
   (`pr = vs + pu`, `pi = or_couche + pu`), salicus (`sa = pu + or_salicus + vi`), strophae
   répétées (`ts = st + st + st`, `tsB = st + st + stB`), trigonus (`tg = pu + pu + pu`),
   scandicus flexus (`sf = pu + pu + cl`)… État au 11 novembre 2026 :
   - glyphes : 106 sont eux-mêmes une forme de base, 177 se décomposent d'après leur nom,
     74 d'après le dessin de gregall (dont 7 tranchés à la main : `trM = viN + po`,
     `trG = ta + po`, `poGN = clN + viN`, `saM2 = vi + pq`, `saM4 = viN + or_couche + vi`,
     `peG = vi + vi`, `piB = or_pi + stB`), 57 sont des ligatures ;
   - pressus : le pressus minor se compose de l'oriscus `or_pi` et d'un punctum
     (`pi = or_pi + pu`) ; `or_pi` est le pendant court de la virga strata `vs` du pressus
     maior (`pr = vs + pu`). Ce n'est pas l'oriscus couché (`or_couche`) de certains salicus ;
   - ligatures : seuls les morceaux qui se touchent sont liés. Le punctum d'un pressus reste à
     part (`clEpi = cl!or_pi + pu`, `clEpr = cl!vs + pu`) ; la virga d'un salicus lié à une
     clivis se fond dans la clivis, qui n'est donc pas une ligature
     (`saEcl = pu + or_salicus + cl`) ;
   - formes de base : 146, soit 71 neumes, 7 modèles d'éléments, 26 lettres, 34 ligatures,
     3 crochets/vide, et 5 formes sans glyphe propre dans gregall : `or_salicus` (∩, salicus),
     `or_couche` (~, salicus `sa1`, `saN1`, `saB2`, `saM1`, `saNB1`, `saM4`), `or_pi`
     (pressus minor), `pf1` et `clN1` ;
   - les 14 formes qui ont déjà un exemplaire choisi couvrent 76 % des emplois de formes.
5. **Glyphes composés** (neume de base + points ou lettres : `toSsu2`, `ciNpp2`, `cllsc3`…) :
   **le neume de base n'est pas redétouré, il est repris du glyphe de base** (`toS` pour
   `toSsu2`), sous forme de référence FontForge sans décalage vertical. Il a ainsi exactement la
   même taille, la même forme et la même hauteur dans toute la famille, et suit les retouches du
   glyphe de base. Étapes :
   - détourer et caler d'abord le glyphe de base ;
   - `scripts/composer.py` vide le premier plan du composé et y pose la référence ;
   - choisir un exemplaire de Hartker du composé, qui sert à placer points et lettres par
     rapport au neume de base ; `scripts/import_hartker.py … base <bx>,<by>,<bw>,<bh>` l'importe
     calé sur la référence (boîte du seul neume de base dans l'exemplaire) ;
   - détourer au premier plan ce qui s'ajoute (points ; pour une lettre significative, de
     préférence une référence au glyphe `ls…`) ;
   - `scripts/caler.py` : centre horizontal et chasse comme pour les autres glyphes, mais pas de
     calage vertical (la référence reste à la hauteur 0).
   Les ligatures avec `!` (`toEcl`, `qlEclppt1`…) se détourent d'un seul tenant. Le TTF
   transforme les glyphes mêlant contours et références en contours simples.
   **Variantes épisémées ou liquescentes** d'un glyphe de base (`viN`, `clN`, `toN1`, `peB`,
   `clSN1`… : modificateurs `-`, `>`, `~` ; colonne `variante_de` de `reference/familles.tsv`,
   74 glyphes dans NR). Elles ne peuvent pas reprendre le glyphe de base tel quel. Deux voies :
   - fusionner le contour déjà détouré du glyphe de base (copié par
     `scripts/composer.py --copie <variante>`) avec l'épisème ou la liquescence détourés d'un
     exemplaire de la variante ;
   - ou détourer la variante de zéro.
   Dans les deux cas, **l'exemplaire de la variante est choisi pour sa cohérence visuelle avec
   le glyphe de base retenu** (taille, inclinaison, plein et délié de la partie commune), et
   `scripts/import_hartker.py … base <bx>,<by>,<bw>,<bh>` le cale sur la position du glyphe de
   base (boîte de la partie commune, sans l'épisème). Les glyphes composés d'une variante
   (`viNsut2`, `toN1su2`) reprennent ensuite la variante en référence, comme ci-dessus.
6. **Glyphes introuvables dans Hartker** : garder le contour gregall et le signaler (couleur
   jaune + commentaire) ; décision au cas par cas.
7. **Contrôle** après chaque séance : `check_metrics.py`, puis `build.py` et composition d'un
   document de test avec les NABC visibles, comparé au rendu gregall.

### Calibration (10 novembre 2026)

96 neumes repérés sur quatre pages des deux volumes : Cod. Sang. 390 p. 31 et p. 120,
Cod. Sang. 391 p. 100 et p. 180. Il y a des virgas (`vi`), des clivis (`cl`) et des pes (`pe`).
Leurs boîtes sont dans `sources/calibration.csv`. `scripts/calibrate.py` remesure chaque neume
par seuillage à hystérésis, pour ne pas perdre les traits fins et clairs. Il écarte les
6 mesures dont l'encre touche le bord de la découpe (neume voisin fusionné) et compare les
hauteurs médianes à gregall :

| Classe | n | Hauteur Hartker (px, médiane) | Hauteur gregall | Unités/px |
|---|---|---|---|---|
| `vi` | 37 | 59 (51–69) | 589 | 9,99 |
| `cl` | 25 | 61 (50–65) | 586 | 9,61 |
| `pe` | 28 | 70,5 (47–103) | 684 | 9,70 |

L'étalon est la virga : elle n'a qu'une note, donc sa hauteur ne dépend d'aucun intervalle,
contrairement à la clivis et au pes. Elle donne exactement **10 unités/px**, l'échelle retenue.
Les autres classes s'en écartent de moins de 4 %. Avec cette échelle, une virga et une clivis
de Hartker remplissent pratiquement le gabarit gregall (vérifié par superposition). Les
proportions de gregall et de Hartker sont donc proches, et les avertissements de
`check_metrics.py` devraient rester rares.

Remarques :
- un premier seuillage, trop strict, faisait croire à une virga de Hartker plus courte de
  23 % : c'était un artefact (traits fins perdus). Un échantillon classé virga par erreur
  (un pes, 391 p. 100) a aussi été reclassé ;
- la taille de l'écriture varie un peu selon les pages (p. 100 du 391 plus petite) : choisir
  de préférence les exemplaires dans des pages de module courant ;
- `sources/exemplaires.csv` liste, pour les glyphes déjà étudiés, l'exemplaire de Hartker
  choisi et jusqu'à quatre variantes, chacune d'une page différente (boîtes affinées). Ce sont
  des propositions, à valider avant import. Pour un glyphe composé, la colonne `base` donne la
  boîte du seul neume de base dans l'exemplaire, à passer à `import_hartker.py … base` ;
- `sources/reperes.csv` garde les occurrences identifiées en passant (lettres significatives,
  éléments, neumes rares), avec leur boîte : un réservoir pour les lots à venir ;
- strophae (mesure du 11 novembre 2026, tête seule, sans la queue en délié) : dans `ds`/`ts`,
  24,5 × 27,5 px (n = 34) ; dans `sux`, 26 × 24 px (n = 6), même surface. La stropha
  liquescente `sux` a donc la tête d'une stropha ordinaire, prolongée d'une longue queue fine
  vers le bas à gauche. C'est la forme de `st>` (stropha liquescente), qui est aussi le dernier
  élément de `ds>` et `ts>` : même tête, même queue (hauteur totale ≈ 55–60 px pour `sux` et
  `st>`, contre ≈ 36 px pour une stropha à queue courte). Le modèle de `sux` sera donc `stB`
  (`st>`), trouvé sur les pages sources des pièces NR (`sources/reperes.csv`) ;
- `sources/calibration_mesures.csv` donne les boîtes affinées. Ce sont elles qu'il faut passer
  à `import_hartker.py` : une boîte trop serrée décale le calage.

## 6. Outils

La liste des scripts, leurs commandes et l'ordre de travail sont dans `SKILL.md`, à la racine du
skill. Le dépôt `grehartker` ne contient que la police (`src/grehartker.sfd`, avec les extraits de
Hartker retenus en arrière-plan), ses licences et un README court.

## 7. Questions ouvertes

- Licence : proposition à valider, et demande à la Stiftsbibliothek à envoyer (§ 4).
- Mention d'auteur : a priori Matthias Bry, à confirmer. Elle est inscrite dans `LICENSE.md`
  mais pas encore dans la police, où le texte gregall est conservé, précédé d'une mention
  grehartker.
- Seuil de signalement des écarts de haut dans `check_metrics.py` (12 % de la hauteur) à ajuster
  à l'usage.
