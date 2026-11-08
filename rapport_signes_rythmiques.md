# Signes rythmiques déduits du NABC : rapport, version 2

Cette version intègre tes remarques sur la version 1. Le champ est désormais celui des **répons** ; les hymnes sont laissés de côté.

Corpus : 1 013 pièces `_marteo` avec NABC et signes, sections `ob`/`cb` comprises, dont 709 pour l'apprentissage et 304 pour la vérification (215 répons).

**Réserve sur la vérification.** Ces 304 pièces en sont à leur deuxième usage. J'ai écrit la version 2 sur l'apprentissage seul, mais j'avais vu les totaux et les types d'écarts de la version 1 sur ces pièces. Le score reste indicatif plutôt que strictement indépendant.

## 1. Résultats

### Répons de vérification (215 pièces, 48 428 notes)

| Mesure | Résultat |
|---|---:|
| Notes exactes, version 2 | **98,67 %** |
| Notes exactes, version 1 | 98,64 % |
| Sections synthétiques | 99,07 % |
| Sections authentiques | 98,38 % |
| Avec le NABC de dcrochu (46 441 notes) | 98,29 % |
| Écarts par pièce | 3,0 notes en moyenne |
| Pièces sans aucun écart | 32 sur 215 |

| Signe | Précision | Rappel |
|---|---:|---:|
| Épisème `_` | 96,5 % | 97,1 % |
| Point `.` | 95,9 % | 96,5 % |

Le gain global est faible : tes corrections rendent surtout les règles justes sur des cas ciblés (`ppt`, reprises, `ql!vs`), qui pèsent peu dans le total. Sur l'ensemble du corpus (tous genres), sans aucun signe, le score serait de 76,8 %.

### Placement de l'épisème
Mesuré sur les notes où le signe est juste : 97,6 % de placements exacts, contre 94,1 % sans aucun chiffre.

| Chiffre | Précision | Rappel | Effectif |
|---|---:|---:|---:|
| `_0` | 87 % | 78 % | 464 |
| `_1` | 37 % | 30 % | 23 |
| `_2` | 60 % | 19 % | 32 |

Avec le NABC de dcrochu, `_0` descend à 81 % de précision et 77 % de rappel.

## 2. Tes points, un par un

### Virga strata : tu avais raison
`vs` isolée suivie de `su` est très rare : 4 cas en apprentissage (`vssu3`, `vssut1`). Mon « `vs` + `su` » recouvrait en réalité **`ql!vs`** (ou `qi!vs`), avec environ 250 cas : `ql!vssu2` (182) et `ql!vsppt1sut2` (70).

- **`ql!vs` ou `qi!vs` :** épisème sur les deux notes de `vs` (99,6 %, 224 notes). Exemple : `h_f!gwhG__FEf`.
- **`vs` isolée :** aucun signe (98,6 %, 210 notes).
- **Ce qui suit :** `su` ne reçoit rien et `sut` reçoit un épisème, comme ailleurs.

### LST et LSC selon la position : hypothèse confirmée seulement en partie
Pour `lst`, seuls les chiffres 2 et 3 sont présents (177 neumes en apprentissage). Part de notes épisémées :

| Neume | `lst2` | `lst3` |
|---|---|---|
| 2 notes | 1re 91 %, 2e 18 % | 1re 50 %, 2e 36 % |
| 3 notes | 1re 26 %, **médiane 71 %**, dernière 4 % | 1re 23 %, médiane 54 %, dernière 15 % |
| 4 notes et plus | toutes environ 81 % | médianes 24 %, 1re 0 %, dernière 10 % |

- **`lst2` :** il vise bien le milieu, c'est-à-dire le sommet du neume (première note d'une clivis, médiane d'un torculus ou d'un pressus). `pflst2` épisème les quatre notes (100 %).
- **`lst3` :** il **ne vise pas la dernière note**, qui n'est jamais la plus marquée. `cllst3` ne reçoit presque rien (3 notes sur 46), alors que `cllst2` en reçoit plus d'une fois sur deux (14 sur 24).
- **Règle appliquée :** sommet du neume, toutes les notes pour `pf`, rien pour `cllst3`. Accord de 81,9 % (144 notes) : c'est l'un des points les moins sûrs.

Pour `lsc` :
- **Aucun effet de position mesurable.** Sur un neume sans épisème, `lsc` à gauche, au milieu ou à droite n'en crée jamais (99 à 100 %).
- **Annulation éventuelle :** `lsc` coexiste rarement avec un neume épisémé. Seul `clS` montre une annulation (10 notes), que j'ai retenue. `sut` et `suu` gardent leur épisème avec `lsc2` (94 à 100 %).

### Point et proposition grammaticale : hypothèse non confirmée par ma lecture
**La barre reste le meilleur critère**, avec la ponctuation du texte :

| Devant | Avec ponctuation | Sans ponctuation |
|---|---:|---:|
| `:` et `::` | 99 % de points | |
| `;` | 96,4 % | 62,9 % |
| `,` | 21 % | 2,7 % |

**Test à l'aveugle.** J'ai classé 280 segments, sans voir leurs signes, selon que la proposition s'y termine ou non, puis j'ai comparé aux points. Part de points :

| Cas | Proposition finie | Proposition non finie |
|---|---:|---:|
| `,` avec virgule, tous neumes | 15 % (60) | 17 % (30) |
| `,` avec virgule, `cl-` ou `pr` | 39 % (36) | 26 % (19) |
| `;` avec ponctuation | 97 % (39) | 100 % (8) |
| `;` sans ponctuation (deux échantillons) | **100 % (8)** | 64 % (50) |

- **Devant `;` sans ponctuation :** une proposition finie reçoit toujours son point. C'est le seul cas qui va clairement dans ton sens, sur 8 segments seulement.
- **Devant `,` :** ma lecture ne distingue presque rien. Il y a des points sur de simples groupes nominaux (*Lúcia virgo,* ; *Dies illa, dies iræ,* ; *ex sémine Abrahæ,*) et aucun sur des propositions complètes (*Sepívi te,* ; *Ego sum qui peccávi,*).
- **Autres critères testés sans succès :** finale du mode, mouvement mélodique, et mot suivant (coordination ou subordination). Le meilleur croisement, `,` avec virgule, neume cadentiel et coordination, plafonne à 41 %.

Il se peut aussi que la répartition entre `,` et `;` reflète déjà ta lecture : la barre porterait alors l'information. Le classement est de moi seul, à vérifier. Je ne génère donc aucun point devant `,` : environ 10 % des notes à cette place sont manquées, dont 21 % quand le texte porte une ponctuation.

### Clivis `cl-` devant une barre : appliqué
- `..` si la règle du point s'applique, soit devant `;`, `:` et `::` : 96,8 % (1 042 notes).
- `__` sinon, soit devant `,` : 91,9 % (248 notes).

### Reprises : ta règle est confirmée
Sur 912 reprises de répons, **899 recopient exactement le corps**. La règle est donc désormais de copier les signes de la note correspondante du corps : 99,2 % d'accord (2 013 notes), sur des signes eux-mêmes prédits.

Les 13 reprises en écart sont dans la section 5.

### `ppt` : le critère est la place dans la chaîne
Le neume suivant semblait compter, mais il suivait surtout la longueur de la chaîne de `ppt`.

- **`ppt` seul ou non dernier de sa chaîne :** épisème (96,5 %, 375 notes).
- **Dernier `ppt` d'une chaîne d'au moins deux :** rien (92,6 %, 68 notes).
- **`ppt` juste avant un quilisma :** rien, par la règle générale.

Ainsi, `ppt` en tête devant `to` a 96 % d'épisèmes, et un dernier `ppt` de chaîne devant `cl` en a 2 %. Quelques exceptions restent (`ppt` en tête devant `cl` : 5 cas).

### Réglages `_0`, `_1`, `_2`

**`_0` : règle fiable (87 % de précision).** La note épisémée est suivie d'une montée, d'un séparateur (`/`, `//`), et la note suivante n'a pas d'épisème. Elle appartient alors à un neume d'une note (`ta-` 97 %, `ta` 100 %, `vi` 100 %, `ppt` 94 %, `ppu` 95 %, `vi-` 77 %, `sut` 57 %) ou elle ouvre un neume qui continue au-delà du séparateur (`scM1` 100 %). Ton « début de montée » est donc bien confirmé.

Je ne retrouve pas **« note très haute »** : sans montée, `_0` reste à 2 ou 3 % sur les notes hautes (`j` à `m`).

**`_1` : pas de vraie règle.** Il se concentre sur la 1re note de `pr-`, surtout sur `f` (`f_1foe`, 27 cas). La pratique semble varier selon les lots de pièces (91 % sur les pièces en `10…`, bien moins ailleurs). Les notes `c`, `d`, `e` n'ont presque jamais `_1`. Je l'applique à `pr-` sur `f` ou plus bas, avec seulement 37 % de précision ; aucune des 76 pièces n'en reçoit.

**`_2` : non identifié.** Il suit presque toujours une note épisémée suivie d'une autre, dans un autre neume (77 cas sur 85), mais ce contexte ne donne que 1 à 9 % de `_2`. Seul `tr-3` devant `vi-` est net (10 sur 10). Viennent ensuite `vi-` devant `toS` (57 %, 7 cas), `ds-` devant `ci-` (50 %, 8 cas) et `cl-` devant `pe-1` (27 %, 33 cas). Je n'applique que le premier ; les 76 pièces en reçoivent 10.

## 3. `..` ou `__` en fin d'incise : synthèse des hypothèses

Cette section rassemble ce que nous savons de ce choix, surtout sur `cl-`, où il est le plus visible. **Aucune règle ne le tranche à elle seule** : marteo précise lui-même que ce n'est pas déterministe.

### Ce que disent les signes (marteo)
- **Le point** est un allongement avec **retombée du son**.
- **L'épisème** est un allongement moindre, en **soutenant le son** pour enchaîner.

Le choix porte donc sur une question de chant : la voix peut-elle retomber ici ? La longueur de la barre est un autre choix, lié à la pause voulue. Une proposition peut finir sur un quart de barre et garder son point, comme dans [Q6F3R1](https://nocturnale.marteo.fr/chant/Q6F3R1), où la suite (*dicéntes:*) doit arriver vite.

### Tableau des hypothèses

Part de `..` ou de points, sur les répons (apprentissage, sauf H4, mesurée sur la vérification). Les effectifs sont entre parenthèses.

| Hypothèse | Mesure | Verdict |
|---|---|---|
| **H1. La barre décide** | `cl-` : 99 % devant `:`, 96 % devant `;` avec virgule, 33 % devant `,` avec virgule | Critère principal, déjà en règle |
| **H2. La ponctuation du texte compte** | Devant `,` : `cl-` 33 % avec virgule, 4 % sans. Devant `;` : 96 % avec virgule, 71 % sans | Oui, en complément de la barre ; à elle seule, elle ne tranche pas devant `,` |
| **H3. Point si la proposition finit** | Lecture à l'aveugle, devant `,` avec virgule : 15 % (60) si elle finit, 17 % (30) sinon. Sur `cl-` et `pr` : 39 % (36) contre 26 % (19) | Trop faible, formulée ainsi |
| **H4. Point si la proposition finit et si la voix peut retomber**, la suite n'étant ni nécessaire au sens, ni étroitement liée (`nonne… nonne…`) | Lecture à l'aveugle sur 220 segments devant `,` : **30 % (73) contre 13 % (120)** ; `cl-` : **42 % (19) contre 17 % (23)** ; `ta`, `vi` : 21 % (34) contre 5 % (58) | **Vrai signal, le meilleur trouvé**, mais insuffisant pour générer : 22 points justes pour 51 faux |
| **H5. Énumération : point contestable, non fautif** | Membres parallèles et appositions : 30 % (27), autant que H4 | Cohérent : ces cas restent libres |
| **H6. Fin d'incipit (avant `*`) : pas systématique, mais plus facile** | `cl-` avec ponctuation : 41 % (29), sans : 5 % (65). Devant `;` : 55 % (20), contre 91 % ailleurs. Devant `,` : 15 % (153), contre 10 % ailleurs | Confirmé, sur de petits effectifs |
| **H7. Point à l'incise précédente : on préfère l'épisème** | Devant `;` : 91-96 % sans point avant, 76-82 % avec. Devant `,` : 16 % sans, 24 % avec | Confirmé devant `;`, pas devant `,` |
| **H8. Incise courte juste après une pause longue : épisème** | Devant `;` après pause longue : 92 % (9 syllabes ou plus), 76 % (5 à 8), **56 % (4 ou moins, 16 cas)**. Après pause brève : 92 à 98 %. Devant `,` : aucun effet | Confirmé devant `;`, pas devant `,` |

**Pistes testées sans résultat utile (de ma part) :**
- **Finale du mode :** 7 % de points sur la finale, 11 % ailleurs, devant `,`.
- **Mouvement mélodique suivant :** 9 à 11 % quel qu'il soit.
- **Mot suivant :** sur neume cadentiel avec virgule, 41 % devant une coordination, 36 % devant une subordination.
- **Longueur seule :** une incise courte n'a pas moins de points qu'une moyenne, hors contexte de H8.

**Le neume final joue :** devant `,` avec virgule, `pr` 43 %, `cl-` 33 %, `to` 26 %, `vi` 15 %, `ta` 9 %. Ce n'est pas un critère de sens, mais il indique où le choix se pose vraiment.

### Exemples commentés par marteo

| Pièce | Incise | Corpus | Explication |
|---|---|---|---|
| [0908N2R1](https://nocturnale.marteo.fr/chant/0908N2R1) | *ortæ de tribu Juda,* | `..` | Contestable, pas fautif : énumération (*ex… ortæ… ex…*), le choriste peut laisser retomber légèrement |
| [Q6F3R1](https://nocturnale.marteo.fr/chant/Q6F3R1) | *et custodiéntes latus meum,* | `..` | Fin de proposition, *dicéntes* se rapporte à *eis*. Barre courte, car une pause longue viendra avant la citation |
| [Q3F2R1](https://nocturnale.marteo.fr/chant/Q3F2R1) | *Tóllite hinc vobíscum múnera,* | `..` | Fin de proposition |
| [09H3N2R1](https://nocturnale.marteo.fr/chant/09H3N2R1) | *numquam fuísset pecúnia ipsa,* | `__` | La proposition finit, mais la suite est nécessaire au sens |
| [09H1N1R2](https://nocturnale.marteo.fr/chant/09H1N1R2) | *Nonne dissimulávi,* | `__` | Les deux parties (*nonne… nonne…*) sont dépendantes : la voix ne retombe pas |
| [1024N2R3](https://nocturnale.marteo.fr/chant/1024N2R3) | *et, grátias agens ei,* | `__` | Pas de fin de proposition |
| [1024N1R3](https://nocturnale.marteo.fr/chant/1024N1R3) | *Forti ánimo esto,* | `__` | Incise courte juste après une pause longue : inutile de faire déjà retomber la voix |
| [0829N1R3](https://nocturnale.marteo.fr/chant/0829N1R3) | *Nihil áliud petas,* | `..` | **À corriger en `__`** |
| [1226N2R1](https://nocturnale.marteo.fr/chant/1226N2R1) | *Dómine Jesu Christe,* | `..` | **À corriger en `__`** : déjà des points à l'incise précédente, et incise courte |
| [1224R2](https://nocturnale.marteo.fr/chant/1224R2) | *Constántes estóte:* | `__` | **À corriger en `..`** |

### Ce que cela change pour les règles
- **Devant `:` et `::` :** `..` sans réserve.
- **Devant `;` :** `..`, mais à marquer comme moins sûr en fin d'incipit et après une pause longue, surtout sur une incise courte.
- **Devant `,` :** `__` par défaut, aucun point généré. C'est là que la relecture humaine est la plus utile.

**Le corpus lui-même hésite.** Sur 4 désaccords examinés entre ma lecture et le corpus, tous sur `cl-`, marteo a corrigé le corpus 3 fois et lui a donné raison une fois. L'échantillon est trop petit pour conclure, mais il suggère que le plafond mesuré vient en partie de signes à revoir, et non des seules règles.

**Corrections retenues à ce jour** (non appliquées) : [0829N1R3](https://nocturnale.marteo.fr/chant/0829N1R3) `tas,(gf..|cl-)` → `gf__` ; [1226N2R1](https://nocturnale.marteo.fr/chant/1226N2R1) `te,(fe..|cl-)` → `fe__` ; [1224R2](https://nocturnale.marteo.fr/chant/1224R2) `te:(ixhg/higgf__|////cltoS2cl-)` → `higgf..`.

**Pour la suite :** si l'on prépare une liste à arbitrer, H4 donnerait les candidats, H7 et H8 les placeraient plus bas, et le neume final les ordonnerait. Ce classement n'existe pas encore.

## 4. Les règles, dans l'ordre

Les pourcentages sont mesurés sur les répons de vérification.

1. **Table des neumes** (inchangée, version 1). Un neume sans modificateur ne reçoit rien ; le modificateur désigne les notes. Exemples : `cl-` `EE`, `ci-` `E··`, `peS` `E·`, `pe-` `·E`, `pe-1` `EE`, `toS` `EEE`, `toS2` `··E`, `toS3` `·E·`, `to-1` `··E`, `ql-` `·E`, `vi-` `E`, `ta-` `E`, `pr-` `E··`, `ds-` `·E`, `bv-` `EE`. La liste complète est dans `rules.py` et `model.pkl`.
2. **Subpunctis et prépunctis.** `su`, `pp` : rien. `sut`, `suu`, `ppu` : épisème. `ppt` : selon sa place dans la chaîne.
3. **`ql!vs` :** deux épisèmes. `vs` isolée : rien.
4. **`lst` :** sommet du neume, toutes les notes pour `pf`, rien pour `cllst3`.
5. **Note avant un quilisma :** jamais d'épisème (99,7 %). Cette règle l'emporte sur les précédentes.
6. **Point :** dernière note de syllabe devant `;`, `:` ou `::`.
7. **`cl`, `cl-`, `pe`, fin de `sf-` devant ces barres :** `..`. Sinon, épisèmes selon la table.
8. **Syllabe accentuée à l'unisson avant la finale :** point, comme dans `nos(g.|ta)ter.(g.|ta)`.
9. **Reprises (`+`, `‡`) :** copie exacte du corps. Si le corps est introuvable, pas de point final.
10. **Chiffres :** `_0`, `_1` et `_2` comme ci-dessus.
11. **Règles faibles, gardées :** `ta` ou `vi` en mélisme avant une montée (épisème) ; `clS`, `clS-`, `toS2` avant un unisson (rien).

## 5. Reprises à vérifier

Ces cas sont à signaler ; je n'ai pas contrôlé chacun, et certains peuvent être de fausses alertes de ma comparaison.

**Signes différents du corps**
| Pièce | Syllabe | Reprise | Corps |
|---|---|---|---|
| [09H1N2R1](https://nocturnale.marteo.fr/chant/09H1N2R1) | mén | `gh!iwj/jk>` | `g_h!iwj/jk>` |
| [A2N2R1](https://nocturnale.marteo.fr/chant/A2N2R1) | ró | `i_h/i!jwk_kl` | `ih__/i!jwk_kl` |
| [P4N1R1](https://nocturnale.marteo.fr/chant/P4N1R1) | Ad | `g_0` | `g` |
| [H2F6N1R2](https://nocturnale.marteo.fr/chant/H2F6N1R2) | Tu, ve | `h_0//ij`, `jvIH__G/hwi_HGFg` | `h@ioj`, `jvIH__G/hwiH__GFg` |

Dans [H2F6N1R2](https://nocturnale.marteo.fr/chant/H2F6N1R2), les neumes diffèrent aussi.

**Notes ou texte différents**
| Pièce | Syllabe | Reprise | Corps |
|---|---|---|---|
| [H1F5N1R2](https://nocturnale.marteo.fr/chant/H1F5N1R2) | est | `hvGF` (`ci`) | `hvGFfo` (`cior`) |
| [Q4N1R1](https://nocturnale.marteo.fr/chant/Q4N1R1) | Ut | `e` | `d` |
| [APTPN3R2](https://nocturnale.marteo.fr/chant/APTPN3R2) | si, cut (2 reprises) | identiques en notes | le texte diffère : à regarder |

**Corps introuvable :** [0829N1R2](https://nocturnale.marteo.fr/chant/0829N1R2) (Pro), [09H4N2R2](https://nocturnale.marteo.fr/chant/09H4N2R2) (E), [09H5N1R3](https://nocturnale.marteo.fr/chant/09H5N1R3) (Qui), [CONPN3R1](https://nocturnale.marteo.fr/chant/CONPN3R1) (I), [COPON2R3](https://nocturnale.marteo.fr/chant/COPON2R3) (I).

**Dans les 76 pièces générées :** [Q5F6N3R2](https://nocturnale.marteo.fr/chant/Q5F6N3R2) (« cæ. », 2 notes) n'a pas de correspondance dans le corps.

La liste complète est dans `reprises_ecarts.tsv`.

## 6. Points à arbitrer

1. **Point devant `,` :** voir la synthèse de la section 3. Le critère de marteo donne un vrai signal, mais il n'est pas assez sûr pour générer les points automatiquement.
2. **`lst3` :** `cllst3` sans signe te semble-t-il juste ? Il contredit l'idée que le chiffre 3 vise la dernière note.
3. **`_1` et `_2` :** y a-t-il une raison visuelle que je ne peux pas lire dans le code (collision avec une note ou le texte) ? Si oui, il faudrait l'examiner sur le rendu, pas seulement sur le GABC.
4. **`_0` sur note très haute :** as-tu un exemple ? Je ne le retrouve pas.
5. **Règles faibles de la section 4 (règle 11) :** faut-il les garder, ou laisser ces notes sans signe ?
6. **`ta` ou `vi` épisémés sans `-`, `vi-` ou `ta-` sans signe :** ces écarts sont à relire, car il peut s'agir de coquilles. Ils sont dans `ecarts.tsv`.

## 7. Pièces générées

- **76 répons** : tous les répons qui ont un `_dcrochu` avec NABC et pas de `_marteo`.
- **16 559 notes** ont reçu une décision : 3 026 épisèmes (dont 129 `_0` et 10 `_2`) et 920 points. **159 notes** (1 %) n'ont pas pu être alignées et restent sans signe. La plus touchée est [1208N1R3](https://nocturnale.marteo.fr/chant/1208N1R3) (30 notes).
- **88 % des notes** sont en section synthétique.
- **Contrôles :** les 76 fichiers passent `gregorio` sans erreur. Sur 250 pièces, un aller-retour d'écriture retrouve signes et chiffres de 48 053 notes sans différence, et rien d'autre ne change dans le fichier.
- **Échantillon :** recompilé avec `gregall` (3 pièces). J'en ai regardé la première page. Les `???` de la version 1 étaient les crochets `ob`/`cb`, que `gresgmodern` n'affichait pas.
- **Non vérifié :** aucune pièce n'a été relue note à note. La qualité réelle reste à établir par ta relecture.
- **En-têtes provisoires :** j'ai gardé le premier bloc de dcrochu, avec `submitter:marteo`.

## 8. Fichiers

Seul ce rapport est versé ici. Les fichiers ci-dessous sont restés dans le dossier temporaire de la session d'analyse (08/11/2026) et ne sont pas conservés dans ce dépôt.

- `nrparse.py`, `build.py` : lecture et alignement.
- `rules.py` : les règles. `final2.py` : les évaluations. `gen2.py` : l'écriture des signes et la génération.
- `split.json` : tirage. `model.pkl` : table et longueurs apprises.
- `seg_labels.py`, `seg_cmp2.py` : mes lectures à l'aveugle du latin.
- `ecarts.tsv` : notes en écart (2 366). `reprises_ecarts.tsv` : reprises en écart.
- `generes/` : les 76 fichiers `<ID>_marteo.gabc` et `echantillon.pdf`.
