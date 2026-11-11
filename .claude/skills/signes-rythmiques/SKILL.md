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
- **Pour le rendu :** `lualatex` avec gregoriotex 6.1, la police NABC `gregall`, et `pdftoppm` (poppler).
- **Notation :** pour les noms des neumes et la syntaxe, voir `GregorioRef.pdf` et `GregorioNabcRef.pdf` (section « Références Gregorio » du skill `fusion-repons` de NR).

## Travail un par un

Ci-dessous, `S` désigne le dossier `scripts/` de ce skill. Lancer Python avec `-I` et `PYTHONIOENCODING=utf-8`.

1. **Mettre NR à jour :** `git pull --ff-only`. marteo a pu commiter la pièce précédente entre-temps.
2. **Apprendre de sa relecture :** si marteo a commité la pièce précédente, la comparer à la version générée.
   ```
   python -I S/compare_one.py <ID> --repo <NR> --samples <dossier>
   ```
   Le script classe chaque syllabe qui diffère : signes, hauteurs NABC, notes ou neumes, texte. Rapporter brièvement ce qui a changé et en tirer les consignes nouvelles.
3. **Générer la pièce suivante :**
   ```
   python -I S/gen_one.py --next --repo <NR> --samples <dossier> --pdf
   ```
   Le script :
   - écrit `gabc/<ID>_marteo.gabc` dans la copie de travail, **sans commit**, et refuse d'écraser un `_marteo` existant ;
   - affiche les syllabes dont le NABC a été élevé et les fins d'incise avec les cas à revoir ;
   - produit `<ID>.pdf` et `<ID>-1.png` dans `--samples`, à garder hors du dépôt.

   Les pièces viennent dans l'ordre alphabétique. On peut aussi donner un `<ID>` à la place de `--next`.
4. **Regarder le rendu :** lire le PNG pour repérer les collisions entre épisèmes et NABC. Seule une vérification graphique permet de s'en assurer.
5. **Présenter la pièce à marteo**, avec :
   - le lien de la pièce (`https://nocturnale.marteo.fr/chant/<ID>`) ;
   - le chemin du fichier et du PDF ;
   - les contrôles : notes alignées, et seuls les signes et les hauteurs NABC diffèrent de dcrochu ;
   - les syllabes élevées, en signalant celles qui sont tassées ;
   - les fins d'incise à regarder en priorité : `,` après une virgule, `;` sans ponctuation, `;` après une pause longue, fin d'incipit, reprise.

   **Ne jamais commiter la pièce :** marteo la retravaille et la commite. Attendre qu'il demande la suivante.

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

### Lettres significatives et neumes
- **`lst` :** se lit avec sa position (1 à gauche, 2 au milieu, 3 à droite) et allonge. `vilst` est à épisémer.
- **`lsc` :** indique une note rapide.
- **`pp` :** en NABC, il s'écrit après le glyphe de base, mais ses notes GABC viennent avant celles du glyphe.
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
- **Chiffres (`digits_piece`) :** `_0` en début de montée suivie d'un séparateur, `_1` sur la première note de `pr-` à `f` ou plus bas, `_2` sur la dernière note de `tr-3` devant `vi-` épisémé.

## Scripts (`scripts/`)

| Fichier | Rôle |
|---|---|
| `gen_one.py` | Génère une pièce dans la copie de travail, l'affiche avec les points à revoir, prépare le `.tex` et peut compiler le PDF |
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
| `_0` | 87 % | 78 % |
| `_1` | 37 % | 30 % |
| `_2` | 60 % | 19 % |

**Placement exact :** 97,6 % des épisèmes justes, contre 94,1 % sans aucun chiffre.

**Variabilité du corpus :** 1,3 % des contextes identiques y portent des signes différents. Le plafond vient donc en partie du corpus lui-même.

**Limites :**
- aucun point n'est généré devant `,` ;
- `_1` et `_2` sont peu fiables ;
- environ 1 % des notes ne s'alignent pas et restent sans signe.

## État au 11/11/2026

- **[0202N1R1](https://nocturnale.marteo.fr/chant/0202N1R1) :** générée, retravaillée et commitée par marteo. Il n'a changé aucun signe, seulement 7 hauteurs NABC.
- **[0202N1R2](https://nocturnale.marteo.fr/chant/0202N1R2) :** générée, dans la copie de travail de marteo, en attente de sa relecture.
- **Répons restants :** 74 cibles après 0202N1R2. `check_all.py` donne 74 pièces, 16 095 notes, 159 non alignées et 486 syllabes élevées, dont 81 tassées, sans invariant violé.
- **Corrections signalées dans le corpus**, à vérifier avant d'en reparler :
  - [0829N1R3](https://nocturnale.marteo.fr/chant/0829N1R3) : `tas,(gf..|cl-)` → `gf__` ;
  - [1226N2R1](https://nocturnale.marteo.fr/chant/1226N2R1) : `te,(fe..|cl-)` → `fe__` ;
  - [1224R2](https://nocturnale.marteo.fr/chant/1224R2) : `te:(ixhg/higgf__|////cltoS2cl-)` → `higgf..` ;
  - les deux `fss_` ou `fvv_` du corpus ([08H1N3R1](https://nocturnale.marteo.fr/chant/08H1N3R1), [N1F1N3R2](https://nocturnale.marteo.fr/chant/N1F1N3R2)) ont été corrigés par marteo.
- **Questions ouvertes :** la liste des points devant `,` à arbitrer n'existe pas encore (voir la section 3 du rapport). Les autres questions sont à la section 6 du rapport.
