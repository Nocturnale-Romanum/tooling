---
name: signes-rythmiques
description: Ajouter des signes rythmiques GABC (points `.`, épisèmes `_`, `_0` `_1` `_2`) à une partition neumée en NABC, d'après les règles déduites des `_marteo.gabc` de Nocturnale Romanum ; générer un par un les `_marteo` des répons qui n'ont qu'un `_dcrochu`, élever le NABC sous les épisèmes, réentraîner et vérifier les règles. À utiliser dès qu'il est question de signes rythmiques, de points mora, d'épisèmes déduits du NABC, ou de générer un `_marteo` depuis un `_dcrochu`.
---

# Signes rythmiques depuis le NABC

**Objet :** une partition GABC neumée en NABC mais sans signes rythmiques reçoit des points et des épisèmes, d'après des règles déduites des `gabc/*_marteo.gabc` de Nocturnale Romanum (NR). L'usage principal est de produire les `_marteo` des répons qui n'ont qu'un `_dcrochu`.

**Champ :** les répons seulement, sans les hymnes.

**Arbitre :** marteo (compte GitHub `xmarteo`). Il relit et retravaille chaque pièce, puis la commite lui-même.

**Rapport complet :** `rapport_signes_rythmiques.md`, à la racine du dépôt `tooling`. Il contient la méthode, les mesures, la synthèse `..` ou `__` en fin d'incise et les points à arbitrer. Ce skill en reprend l'essentiel pour travailler.

## Prérequis

- **Python 3 :** bibliothèque standard seulement.
- **Une copie de travail de `nocturnale-romanum` :** les scripts lisent `gabc/` dans le dossier passé en `--repo`, par défaut le dossier courant.
- **Pour le rendu, seulement si marteo le demande :** `lualatex` avec gregoriotex 6.1, la police NABC `gregall`, et `pdftoppm` (poppler).
- **Notation :** pour les noms des neumes et la syntaxe, voir `GregorioRef.pdf` et `GregorioNabcRef.pdf` (section « Références Gregorio » du skill `fusion-repons` de NR).

## Travail un par un

Ci-dessous, `S` désigne le dossier `scripts/` de ce skill. Lancer Python avec `-I` et `PYTHONIOENCODING=utf-8`.

1. **Mettre NR à jour :** `git pull --ff-only`. marteo a pu commiter la pièce précédente entre-temps. Si le pull bloque sur la pièce générée, restée non suivie, vérifier qu'elle est identique à la copie de `--samples` avant de la retirer : marteo commite sa propre version de ce fichier.
2. **Apprendre de sa relecture :** si marteo a commité la pièce précédente, la comparer à la version générée.
   ```
   python -I S/compare_one.py <ID> --repo <NR> --samples <dossier>
   ```
   Le script classe chaque syllabe qui diffère : signes, hauteurs NABC, notes ou neumes, texte. Si le `_dcrochu` a changé depuis la génération, régénérer d'abord la pièce en mémoire depuis la version actuelle, pour ne garder que les retouches de marteo. Rapporter brièvement ce qui a changé et en tirer les consignes nouvelles.
3. **Générer la pièce suivante**, sans rendu :
   ```
   python -I S/gen_one.py --next --repo <NR> --samples <dossier>
   ```
   Le script :
   - écrit `gabc/<ID>_marteo.gabc` dans la copie de travail, **sans commit**, et refuse d'écraser un `_marteo` existant ;
   - affiche les syllabes dont le NABC a été élevé, les notes non alignées et les fins d'incise avec les cas à revoir ;
   - garde une copie du fichier dans `--samples`, hors du dépôt, pour `compare_one.py`.

   Les pièces viennent dans l'ordre alphabétique. On peut aussi donner un `<ID>` à la place de `--next`.

   **Rendu :** marteo compile et regarde lui-même les pièces, donc ne pas compiler ni regarder le rendu. `--pdf` (lualatex puis `pdftoppm`, avec `gregall`) ne sert que s'il le demande. Les collisions entre épisèmes et NABC ne se vérifient que sur le rendu.
4. **Présenter la pièce à marteo**, avec :
   - le lien de la pièce (`https://nocturnale.marteo.fr/chant/<ID>`) ;
   - un lien vers le fichier généré (`gabc/<ID>_marteo.gabc`) ;
   - les notes non alignées, restées sans signe, avec leur neume : ce peut être une coquille du NABC ;
   - les contrôles : notes alignées, et seuls les signes et les hauteurs NABC diffèrent de dcrochu ;
   - les syllabes élevées, en signalant celles qui sont tassées ;
   - les fins d'incise à regarder en priorité : `,` après une virgule, `;` sans ponctuation, `;` après une pause longue, fin d'incipit, reprise.

   **Ne jamais commiter la pièce :** marteo la retravaille et la commite. Attendre qu'il demande la suivante.

## Génération en lot (plan de marteo depuis le 11/11/2026)

marteo peut demander de générer tous les répons restants d'un coup, sans commit, puis de faire le pull de temps en temps pour analyser ses corrections et ajuster le reste.

- **Générer :** `python -I S/gen_all.py S <dossier>`, depuis la racine de NR. Le script :
  - lance `gen_one.py` sur chaque cible ;
  - garde les journaux dans `<dossier>/logs/` ;
  - tient un manifeste `<dossier>/manifest.json`, avec le sha256 de chaque fichier écrit ;
  - affiche une ligne de résumé par pièce.
- **Résumer :** `python -I S/summarize.py <dossier> <revue.md>` écrit la liste à revoir, pièce par pièce. Donner à marteo les liens de chaque pièce et de chaque fichier.
- **Avant chaque pull :** retirer seulement les fichiers générés que marteo a commités et dont la copie de travail correspond encore au manifeste.
- **Après un changement de règle :** `python -I S/regen_intact.py S <dossier> [--dry]` régénère seulement les fichiers intacts, c'est-à-dire non suivis par git et conformes au manifeste. Il ne touche jamais un fichier commité ou retouché, puis met le manifeste à jour. Relancer ensuite `check_all.py` sur les pièces du manifeste.

Le manifeste vit dans le dossier de travail de la session. S'il est perdu, comparer chaque fichier non suivi à une régénération en mémoire avant d'y toucher.

**Corrections du corpus :** les écarts trouvés dans le corpus `_marteo`, comme une reprise qui diffère du corps ou un signe que marteo juge faux, sont à **signaler** et à tenir en liste. Ne jamais les corriger de soi-même : tout changement dans NR passe par une PR, ou par marteo. Le skill `fusion-repons` de NR décrit ce circuit.

## Consignes de marteo

### Origine et sens des signes
- **Origine des signes :** seuls marteo et quelques contributeurs occasionnels mettent des signes. dcrochu et sandhofe n'en mettent pas, donc il n'y a rien à hériter de leurs fichiers.
- **Origine des neumes :** ceux de marteo viennent parfois de Hartker, très rarement d'un autre manuscrit. Entre `ob` et `cb` (sections synthétiques), ils ont été reconstruits à partir des signes. Ces sections servent à l'apprentissage, où la correspondance entre signes et NABC y est même plus nette.
- **Le point** est un allongement avec **retombée du son**.
- **L'épisème** est un allongement moindre, en **soutenant le son** pour enchaîner.
- **Où mettre le point :** en fin de proposition grammaticale, sauf si la suite est nécessaire au sens ou si les deux parties dépendent l'une de l'autre (`nonne… nonne…`).
- **Énumération :** le point y est contestable, sans être fautif.
- **Longueur de la barre :** c'est un choix indépendant, qui dépend de la pause voulue.

### Fin d'incise (rien de tout cela n'est déterministe)
- **Devant `:` et `::` :** point.
- **Devant `;` :** point. Il est moins sûr à la fin de l'incipit (avant `*`) et quand l'incise précédente avait déjà des points. Quand l'incise est courte et suit immédiatement une pause longue, on privilégie les épisèmes : inutile de faire déjà retomber la voix.
- **Devant `,` :** épisèmes par défaut, sans point généré. Le critère de proposition donne un signal réel, mais trop faible pour générer : c'est à la relecture de trancher.
- **`cl-` devant une barre :** `..` si la règle du point s'applique, sinon `__`.

### Reprises
Une reprise (`+`, `‡`) recopie exactement le corps du répons. Tout écart dans le corpus est une erreur humaine à signaler.

### Placement de l'épisème
- **`_0` :** sous la note, au début d'une montée ou sur une note très haute.
- **`_1` :** au-dessus, rare, sur une note très basse, pour éviter le texte.
- **`_2` :** détaché de l'épisème suivant.
- **Pas de chiffre de position (`_0`, `_1`) là où Gregorio n'a qu'une place :**
  - sur une **virga** (`gv_`), l'épisème ne peut aller qu'au-dessus ;
  - dans un groupe de **deux notes ascendantes, et seulement deux** (`gh_`, `g_h`), il va toujours au-dessus de la deuxième note et en dessous de la première. `dh_0` est donc une faute.

### Lettres significatives et neumes
- **`lst` :** se lit avec sa position (1 à gauche, 2 au milieu, 3 à droite) et allonge. `vilst` est à épisémer.
- **`lsc` :** indique une note rapide.
- **`pp` :** en NABC, il s'écrit après le glyphe de base, mais ses notes GABC viennent avant celles du glyphe.
- **Liquescence NABC `>` (`or>`, `vi>`, `pe>1`…) :** elle correspond soit aux notes du glyphe de base dont la dernière porte une liquescence augmentative (GABC `>`), soit à une note de plus, diminuée (GABC `~`). Exemple : `cum(hggof~|cllsc3`or>)`, où `or>` couvre `go` et `f~`. L'alignement (`lenprob` dans `build.py`) admet toujours les deux nombres de notes.
- **Ce qu'il faut regarder :** la barre suivante, la nature syllabique ou mélismatique de la note, et le neume suivant (pour le quilisma).

### Élévation du NABC sous les épisèmes
Les épisèmes entrent souvent en collision avec le NABC de dcrochu. Quand une note haute reçoit un épisème, on élève le NABC (`raise_nabc.py`) :
- **Hauteur minimale de toute la syllabe :** `i_` → `hh`, `j_` → `hj`, `k_` et au-dessus → `hl`.
- **Notes qui ne comptent pas :** `_0` et la première note d'un pes (`i_j`), car leur épisème est sous la note.
- **Facteur :** toute la syllabe monte du même facteur. Un neume sans hauteur compte pour `hf`.
- **Plafond `hl` :** si ce facteur ferait dépasser `hl`, on le tasse harmonieusement. Les neumes les plus bas montent un peu plus, les plus hauts un peu moins, pour arriver au plus haut à `hl`.
- **Neume déjà au-dessus de `hl` :** s'il est ainsi chez dcrochu, il reste tel quel.

### Écriture
- **Raccourcis :** toujours développer les strophas et virgas multiples (`fss` → `fsfs`, `fsss` → `fsfsfs`, `fvv` → `fvfv`), dans la partie GABC seulement. `fss_` est ambigu : Gregorio 6.1 l'épisème comme `fs_fs`, alors que seul `fsfs_` est correct. Le NABC a ses propres `ss` (`lss2`), qu'il ne faut pas toucher.
- **Inclinatum suivi d'une stropha liquescente :** quand dcrochu écrit deux notes losangées consécutives dont la deuxième est une stropha liquescente (`H!Gs<`, `H!Gs>`, `HGs<`, `HGs>`), supprimer la stropha et le `!`, et mettre une liquescence ordinaire : `HG>`. Le corpus `_marteo` écrit toujours ces paires sans `!`.
- **En-tête :** premier bloc d'en-tête de dcrochu, avec `submitter:marteo;` et `nabc-lines:1;`. Les fins de ligne CRLF sont conservées.
- **Échantillons :** les compiler avec la police NABC `gregall` (`\gresetnabcfont{gregall}{12}`), et non `gresgmodern`, même si `common_headers.tex` l'indique.
- **Codes de pièce :** tout code cité (`P3F4R1`, `0202N1R2`) est un lien vers `https://nocturnale.marteo.fr/chant/<code>`.

## Les règles dans le code

`rules.py` contient les règles, et `model.json` la table des neumes apprise.

- **Table :** clé (neume, nombre de notes, place de la note), plus « après quilisma » pour `vs`. Repli sur (neume, position). Le modificateur `-`, `S` ou `1` désigne les notes épisémées.
- **`ppt` :** épisème s'il est seul ou s'il n'est pas le dernier de sa chaîne. `su` et `pp` : rien. `sut`, `suu` et `ppu` : épisème.
- **`ql!vs` :** épisème sur les deux notes de `vs`. `vs` isolée : rien.
- **`lst` :** `pf` reçoit toutes ses notes, `cl` ses deux notes s'il porte `lst2` sans `lsc` (rien avec `lst3`), et les autres neumes leur sommet.
- **`ta` ou `vi` au milieu d'un mélisme :** épisème avant une montée.
- **`clS`, `clS-`, `toS2` :** rien sur la dernière note devant un unisson.
- **Avant un quilisma :** jamais d'épisème. Cette règle l'emporte sur les autres.
- **Point (`dot`) :** dernière note de syllabe devant `;`, `:` ou `::`, hors reprise. `cl`, `cl-`, `pe` et `sf-` y prennent `..`. Une syllabe accentuée à l'unisson avant une finale d'une seule note prend aussi un point.
- **Reprise :** copie du corps, par `cue_src`.
- **Chiffres (`digits_piece`) :** `_0` en début de montée suivie d'un séparateur, `_1` sur la première note de `pr-` à `f` ou plus bas, `_2` sur la dernière note de `tr-3` devant `vi-` épisémé. Jamais `_0` ni `_1` sur une virga ni dans un glyphe GABC de deux notes ascendantes (trait `two_up` de `build.py`).

## Scripts (`scripts/`)

| Fichier | Rôle |
|---|---|
| `gen_all.py`, `summarize.py`, `regen_intact.py` | Génération en lot avec manifeste, liste à revoir, régénération des seuls fichiers intacts |
| `gen_one.py` | Génère une pièce dans la copie de travail et l'affiche avec les points à revoir ; prépare le `.tex` et compile le PDF avec `--pdf`, seulement si marteo le demande |
| `compare_one.py` | Compare la version générée, copiée dans `--samples`, à celle que marteo a commitée |
| `check_all.py` | Génère toutes les cibles en mémoire et vérifie les invariants : notes inchangées, plus aucun raccourci, élévation cohérente |
| `train.py` | Réapprend la table sur le lot d'apprentissage et mesure le lot de vérification ; écrit `model.json` seulement avec `--write` |
| `generate.py` | Chaîne complète d'une pièce, en mémoire, et liste des cibles |
| `nrparse.py` | Lecture du GABC (notes, signes) et du NABC (atomes dans l'ordre des notes : `pp`, glyphes, `su`) |
| `build.py` | Alignement des notes sur le NABC (programmation dynamique) et traits de contexte de chaque note |
| `rules.py` | Règles, prédiction par pièce, chiffres, scores |
| `writer.py` | Écriture des signes dans le GABC et développement des raccourcis |
| `raise_nabc.py` | Élévation du NABC, utilisable seule : `python raise_nabc.py <fichier> [--write]` |
| `model.py`, `model.json` | Table des neumes et longueurs des glyphes |
| `split.json` | Tirage du 08/11/2026, graine 20261108 : 709 pièces pour l'apprentissage, 304 pour la vérification |

### Pour modifier une règle
1. **Modifier** `rules.py` ou `raise_nabc.py`.
2. **Mesurer avec `train.py`**, sans `--write`. Le lot de vérification a déjà servi deux fois : ses scores restent indicatifs.
3. **Vérifier avec `check_all.py`**, qui doit finir par `INVARIANTS VIOLES {}`.
4. **Consigner** la consigne de marteo dans ce fichier.

**À propos de `model.json` :** c'est la table qui a servi pour générer jusqu'ici. Le corpus évolue : au 11/11/2026, `train.py` retrouve la même table de neumes, mais des longueurs de glyphes légèrement différentes. Ne remplacer le modèle (`--write`) qu'après avoir comparé les scores. `--resplit` refait le tirage sur le corpus actuel, mais les scores ne sont alors plus comparables aux anciens.

## Résultats (version 2, répons de vérification)

| Mesure | Résultat |
|---|---:|
| Notes exactes | **98,67 %** (215 pièces, 48 428 notes) |
| Sections synthétiques | 99,07 % |
| Sections authentiques | 98,38 % |
| Avec le NABC de dcrochu | 98,29 % |

| Signe | Précision | Rappel |
|---|---:|---:|
| Épisème | 96,5 % | 97,1 % |
| Point | 95,9 % | 96,5 % |

| Placement de l'épisème | Précision | Rappel |
|---|---:|---:|
| `_0` | 96 % | 78 % |
| `_1` | 37 % | 30 % |
| `_2` | 60 % | 19 % |

**Placement exact :** 98,0 % des épisèmes justes, contre 94,1 % sans aucun chiffre. Avant la règle sur la virga et le groupe de deux notes ascendantes (12/11/2026), `_0` était à 87 % de précision et le placement à 97,6 %.

**Variabilité du corpus :** 1,3 % des contextes identiques y portent des signes différents. Le plafond vient donc en partie du corpus lui-même.

**Limites :**
- aucun point n'est généré devant `,` ;
- `_1` et `_2` sont peu fiables ;
- environ 1 % des notes ne s'alignent pas et restent sans signe.

## État au 11/11/2026

- **[0202N1R1](https://nocturnale.marteo.fr/chant/0202N1R1) :** générée, retravaillée et commitée par marteo. Il n'a changé aucun signe, seulement 7 hauteurs NABC.
- **[0202N1R2](https://nocturnale.marteo.fr/chant/0202N1R2) :** générée, retravaillée et commitée par marteo. Ses retouches :
  - point retiré devant un `;` sans ponctuation dont la suite est nécessaire au sens (*purgatiónis ejus ; secúndum legem Móysi*) ;
  - reprise raccourcie à *Sicut.* ;
  - séparateurs ajustés (`!` → `/`, `/` → `//`, `` ` `` dans le NABC).
- **[0202N1R3](https://nocturnale.marteo.fr/chant/0202N1R3) :** générée, en attente de la relecture de marteo. `no(fe|pr)` (un `pr` sur 2 notes) n'a pas pu être aligné.
- **0202N1R3 :** commitée par marteo, sans aucun signe changé. Il a corrigé `no(fe|pr)` en `ffoe` et passé la clé en `f3`.
- **Répons restants :** les 73 répons restants (de 0202N2R1 à Q5F6N3R2) sont tous générés, non commités, dans la copie de travail de marteo. Au moment de l'export (74 cibles après 0202N1R2), `check_all.py` donnait 74 pièces, 16 095 notes, 159 non alignées et 486 syllabes élevées, dont 81 tassées, sans invariant violé.
- **Corrections signalées dans le corpus**, à vérifier avant d'en reparler :
  - [0829N1R3](https://nocturnale.marteo.fr/chant/0829N1R3) : `tas,(gf..|cl-)` → `gf__` ;
  - [1226N2R1](https://nocturnale.marteo.fr/chant/1226N2R1) : `te,(fe..|cl-)` → `fe__` ;
  - [1224R2](https://nocturnale.marteo.fr/chant/1224R2) : `te:(ixhg/higgf__|////cltoS2cl-)` → `higgf..` ;
  - les deux `fss_` ou `fvv_` du corpus ([08H1N3R1](https://nocturnale.marteo.fr/chant/08H1N3R1), [N1F1N3R2](https://nocturnale.marteo.fr/chant/N1F1N3R2)) ont été corrigés par marteo.
## État au 12/11/2026

- **Lot du 11/11 :** il n'est plus dans la copie de travail de NR. Il reste 66 cibles, de 0319N1R1 à Q5F6N3R2, et le manifeste est perdu.
- **Relectures de [Q5F6N1R2](https://nocturnale.marteo.fr/chant/Q5F6N1R2) et [Q5F6N1R3](https://nocturnale.marteo.fr/chant/Q5F6N1R3) :**
  - point retiré trois fois devant un `;` sans ponctuation dont la suite est nécessaire au sens ;
  - NABC `hm` de dcrochu baissé à `hl` une fois ;
  - le reste suit l'alignement sur 1227N2R2.
  Pas de décision de marteo sur les fins d'incise pour l'instant : ne pas changer la règle du point.
- **Règles ajoutées :** liquescence NABC `>` (une ou deux notes) et pas de chiffre de position sur une virga ni sur un groupe de deux notes ascendantes. Sur les 66 cibles, les notes non alignées passent de 157 à 143, et aucun invariant n'est violé.
- **[0319N1R1](https://nocturnale.marteo.fr/chant/0319N1R1) :** générée avec ces règles, sans note non alignée. En attente de la relecture de marteo.

- **Questions ouvertes :** la liste des points devant `,` à arbitrer n'existe pas encore (voir la section 3 du rapport). Les autres questions sont à la section 6 du rapport.
