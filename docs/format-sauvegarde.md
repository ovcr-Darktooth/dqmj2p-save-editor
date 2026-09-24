# Format de sauvegarde de DQMJ2 Professional

Carte de travail, complétée au fil de la rétro-ingénierie. La source de vérité
pour le code est `dqmj2p_save/format.py`. Ce document explique le contexte et
liste ce qui reste à découvrir.

Offsets de base relevés par **Ceris White** (`save_converter.py`, projet
[DQMJ2Pro Translation](https://github.com/saneezore07/DQMJ2Pro_Translation)).

## Fichier

| Plage | Contenu |
|---|---|
| `0x0000-0x70FF` | Copie 1 |
| `0x7100-0xE1FF` | Copie 2 (identique à la copie 1 dans toutes les sauvegardes observées) |
| `0xE200-0xFFFF` | Zone de queue, rôle inconnu. Nulle ou variable selon les parties. **Ne jamais écraser.** |
| `0x10000-…` | `.dsv` seulement : pied de page DeSmuME/DraStic de 122 octets, terminé par `\|-DESMUME SAVE-\|` |

## Copie (offsets relatifs à son début)

| Offset | Type | Contenu |
|---|---|---|
| `0x00` | 4 o | Magic `SIZ\0` |
| `0x04-0x0B` | | **À cartographier** (constant : `00 00 01 00 D0 70 00 00`) |
| `0x0C` | 7 × u32 | Date de la dernière sauvegarde en jeu : année − 2000, mois, jour, jour de la semaine (0 = dimanche), heure, minute, seconde |
| `0x28` | u32 | Temps de jeu, en 1/30 s (résumé ; copie de `0x90`) |
| `0x2C` | texte 20 o | Nom du joueur (résumé ; copie de `0x98`) |
| `0x40` | 3 × texte 20 o | Surnoms des 3 monstres d'équipe (résumé) |
| `0x7C` | 3 × u16 + 3 × u8 | Espèce puis niveau des 3 monstres d'équipe (résumé) |
| `0x85` | u8 | Nombre de monstres dans l'équipe (résumé) |
| `0x86` | u8 | Carte (résumé ; copie de `0x3A68`), affichée sur l'écran de chargement |
| `0x87` | u8 | Bits d'avancement cumulatifs : 0 en début de partie, 3 bits à 3 h, 6 à 13 h, les 7 après Rapthorne 2 (étapes de l'histoire ?) |
| `0x88` | u32 | Somme data : somme des `0x1C10` mots u32 à partir de `0x90` |
| `0x8C` | u32 | Somme d'en-tête : somme des `0x23` premiers mots (inclut `0x88`, donc à calculer après) |
| `0x90` | u32 | Temps de jeu, en 1/30 s |
| `0x94` | u32 | Dernier ID de création attribué |
| `0x98` | texte 20 o | Nom du joueur |
| `0xAC` | u32 | Or sur soi |
| `0xB0` | u32 | Or en banque |
| `0xB4` | 6 × u32 | ID de création : équipe 1-3, puis réserve 1-3 |
| `0xCC` | 256 × u8 | Sac : quantité possédée de chaque objet, indexée par ID d'objet (armes comprises) |
| `0x1CC` | 12 × u8 | Ordre des boutons de l'écran du bas (grille 4 × 3, ligne par ligne) : ID du bouton, `7F` = case vide (voir « Boutons ») |
| `0x1D8` | 4 × u8 | Sorts du sous-menu Compétences de dressage, mêmes IDs (`0C` à `0F`), `7F` = pas encore appris |
| `0x1DC` | 3 × u16 | Victoires, monstres dressés, monstres synthétisés |
| `0x1E8` | 100 × 0x84 | Enregistrements de monstres |
| `0x3578` | 512 bits | Bibliothèque des monstres, **dressés** : bit n = espèce n (voir ci-dessous) |
| `0x35B8-0x3637` | | **À cartographier** (presque vide : 1 à 8 octets non nuls) |
| `0x3638` | 512 bits | Bibliothèque des monstres, **vus** : bit n = espèce n |
| `0x3678` | 512 bits | Indexé par espèce, rôle inconnu : vide en milieu de jeu, 80 espèces en fin de jeu |
| `0x36B8-0x36F7` | | **À cartographier** (quasi vide) |
| `0x36F8` | 256 bits | Bibliothèque des attributs : bit n = attribut n (`msg_tokusei`) |
| `0x3718` | 256 bits | Bibliothèque des compétences : bit n = compétence n (`noms.competences`) |
| `0x3738-0x3A53` | | Drapeaux d'événements, **à cartographier** (voir « Zones ») ; `0x393C` : avancement de l'histoire ; `0x39A7` bit `0x01` : anneau évolué (voir « Dressage des monstres géants ») |
| `0x3A54` | 64 bits | Manuel du dresseur, entrées **débloquées** : bit n = entrée n + 1 (voir « Manuel du dresseur ») |
| `0x3A5C` | 64 bits | Manuel du dresseur, entrées marquées **« nouveau »** (pas encore lues) |
| `0x3A64-0x3A67` | | **À cartographier** |
| `0x3A68` | u8 | Carte actuelle (table `noms.CARTES`, relevée en jeu : 14 L'Arbirynthe, 17 Prairia, 24 Arène, 37 Escarpic, 47 Engloutîle, 57 Archéopolis, 85 Albatros extérieur, 88 Albatros intérieur, 151 Avablanche) |
| `0x3A6C` | u32 | Horloge jour/nuit, en 1/30 s de jeu en plein air (0 en ville) : nuit à partir de 10 800, retour à 0 à 18 000 |
| `0x3A69` | u8 | Carte précédente : au chargement, le jeu y met la carte du résumé (`0x86`) |
| `0x3A6A` | u8 | Intempérie en cours (1) ou non (0) ; son type dépend de la carte (`noms.METEO` : pluie à l'Arbirynthe, Prairia, Archéopolis ; brume à Engloutîle) |
| `0x3A70` | 3 × i32 | Position X, Y, Z du joueur, en centièmes |
| `0x3A7C` | i32 | Probablement l'orientation, en degrés virgule fixe 20.12 (180°, −88°, 90° observés) |
| `0x3A90` | 4 × u32 | Quatre copies du temps de jeu (rôle inconnu) |
| `0x3AA0-0x70CF` | | **À cartographier** (drapeaux d'histoire ? bibliothèque ?) |
| `0x70D0-0x70FF` | | Hors somme de contrôle, rôle inconnu |

La zone `0x20-0x87` est un **résumé** pour l'écran de chargement : le jeu y
recopie des valeurs tenues ailleurs. L'éditeur écrit le nom et le temps de jeu
aux deux endroits, et recalcule surnoms, espèces et niveaux de l'équipe. Sur
toutes les sauvegardes écrites par le jeu, ce recalcul redonne exactement les
octets d'origine.

Valeurs identifiées sur une partie connue : 13 h 07 min 07 s, joueur « BKK »,
2601 or, 11856 en banque, 245 victoires, 65 dressages, 41 synthèses, et le
contenu complet du sac (28 objets). Les ID d'objets sont ceux de
`msg_itemname` ; le champ « arme » d'un monstre (`+0x31`) utilise les mêmes.

## Texte

Table de caractères de l'ARM9 (`0x020DBC16`, reprise dans `texte.py`) :
un octet par caractère (`01-0A` chiffres, `0D-26` A-Z, `27-40` a-z, puis
accents et kana), ou deux octets avec un préfixe `E0`, `E1` ou `E4`
(ponctuation, symboles, kanji). Le tiret s'écrit `E0 5A`. Le texte s'arrête au
premier `00` ou au marqueur `E3 1B` ; ce qui suit est du résidu d'un nom
précédent, à conserver tel quel. Les noms et surnoms font 8 **caractères** au
plus, dans un champ de 20 octets.

À la capture, le jeu donne comme surnom les 2 premières lettres de l'espèce.
Valider un surnom vide le remplace par le nom de l'espèce coupé à 8
caractères, ce que fait aussi l'action « Surnoms abrégés → nom complet ».

Les monstres vivants occupent toujours les emplacements `0..N-1` (le jeu
compacte le ranch) ; au-delà traînent des monstres consommés en synthèse, ID de
création à 0. Un nouveau monstre prend l'emplacement N et l'ID `0x94 + 1`.

**Validé en jeu le 23/09/2026** (ROM `dqmj2-pro-patchfr-test`) sur une
sauvegarde générée par l'éditeur : or, banque, sac, surnoms complétés, écran
de chargement, et trois monstres dupliqués. Une copie a servi en synthèse et
une autre en combat sans anomalie ; le monstre né de la synthèse a reçu l'ID
suivant celui laissé par l'éditeur en `0x94`. Un monstre synthétisé est nommé
d'après son espèce coupée à 8 caractères, espace final compris.

La date de sauvegarde (`0x0C-0x27`) a été vérifiée contre l'heure d'écriture
des `.dsv` sur la console : elle la précède de quelques secondes, le temps que
DraStic vide sa mémoire de sauvegarde. Location et position ont été relevées en
jeu sur `moitie-jeu` (location 57, position −26,10 / 0 / 589,46).

**Téléportation validée en jeu le 23/09/2026** : en recopiant le bloc
`0x3A68-0x3A83` d'une sauvegarde faite à l'Albatros, une partie sauvegardée à
Archéopolis a démarré sur l'Albatros (bon décor, bonne musique, sortie
normale). Seul l'écran de chargement affichait encore Archéopolis : la carte a
une copie en `0x86`, que le jeu relit aussi au chargement (elle est devenue la
carte précédente). L'éditeur ne téléporte donc que vers des points relevés en
jeu (`POINTS_TELEPORTATION`), en écrivant la carte aux deux endroits.

**Horloge jour/nuit** (23/09/2026, Engloutîle) : une sauvegarde de nuit
(horloge 10 833) remise à 3 599 a démarré de jour, drapeau `0x39A1` inchangé.
Sauvegardes faites quelques secondes après les messages : 10 801 à la tombée
de la nuit, 26 au retour du jour. Le jour dure donc 6 min de jeu en plein air
et la nuit 4 min. Un bit de `0x39A1` (`0x20`) s'est allumé à la première nuit
observée : drapeau d'événement, sans effet sur l'heure.

**Météo** (23/09/2026) : une sauvegarde prise dans la brume à Engloutîle ne
diffère des sauvegardes par temps clair que par `0x3A6A` (1 au lieu de 0) et
`0x3970`. Remettre `0x3970` à sa valeur de temps clair ne change rien ;
remettre `0x3A6A` à 0 fait disparaître la brume au chargement. La capture de
l'Arbirynthe, faite sous la pluie, a aussi `0x3A6A` à 1. Chaque carte n'a
qu'un type d'intempérie. Pluie forcée validée à Archéopolis (avant même que
l'histoire ne la débloque), Prairia et Escarpic. **Forcée à Avablanche, qui
n'a pas de météo, il ne pleut pas mais la zone n'a plus ni monstres ni
musique**, et l'octet reste à 1 dans la sauvegarde suivante : l'éditeur
n'autorise donc la case que sur les cartes à météo connue (on peut toujours la
décocher pour réparer). Réparation validée : la même sauvegarde, intempérie
remise à 0, a retrouvé monstres et musique. `0x3970` (0 à 6 selon les sauvegardes) reste inconnu.

Réglage par l'éditeur validé en jeu le même jour : horloge à 10 800, la partie
démarre de nuit ; à 10 725 (75 unités avant le seuil), de jour, et la nuit
tombe au bout d'environ 3 secondes. À 17 925 (75 avant la fin de la
nuit), la partie démarre de nuit et le jour revient au bout d'environ 3
secondes : la durée du cycle, 18 000, est confirmée par mesure directe. L'horloge avance donc d'environ 25 à 30
unités par seconde en plein air.

Deuxième validation le 23/09/2026, avec la fonction `teleporter()` de
l'éditeur : Archéopolis → Avablanche (zone de plein air). Écran de chargement
correct, arrivée au point de la Téléportation du jeu, décor, musique, combats
et jour normaux, puis déplacement, Téléportation du jeu vers Engloutîle et
sauvegarde sans anomalie.

Un emplacement de monstre est libre si son ID de création (`+0x14`) ou son
espèce (`+0x18`) vaut 0 (monstre consommé en synthèse).

## Enregistrement de monstre (0x84 octets)

Voir `CHAMPS_MONSTRE` dans `format.py` pour la liste complète. En résumé :

| Offset | Contenu |
|---|---|
| `+0x00` | Surnom, texte 20 o |
| `+0x14` | ID de création (u32) |
| `+0x18` | Espèce, variante, polarité, synthèse + |
| `+0x20` | PV, PM, PV max, PM max, ATQ, DEF, AGI, SAG (u16) |
| `+0x30` | Niveau, arme, tactique |
| `+0x34` | Expérience, expérience du niveau suivant (u32) |
| `+0x3C` | Points de compétence non attribués (u16) |
| `+0x40` | Lignée : 2 parents + 4 grands-parents (u16), puis leurs variantes (u8) |
| `+0x52`, `+0x66` | Surnoms des parents, texte 20 o |
| `+0x7A` | 5 × (compétence u8, points investis u8) |

### Octets inconnus

`+0x1D`, `+0x1F`, `+0x33`, `+0x3E` (2 o). Les octets `+0x10`, `+0x62` et
`+0x76`, autrefois inconnus, sont la fin des surnoms sur 20 octets (le
convertisseur d'origine les lisait sur 16).

## Bibliothèque

Trois champs de bits, repérés sur les 18 sauvegardes de test (pas encore validés
en jeu, rien n'est modifiable) :

- **Monstres vus, `0x3638`, et dressés, `0x3578`** : relevé en jeu le
  23/09/2026 sur `moitie-jeu` (bibliothèque, par famille) : 14 Gluants vus,
  et 7 Gluants, 15 Dragons, 12 Nature, 15 Bêtes, 14 Matières, 8 Démons,
  6 Zombies, 0 ??? dressés, soit 77. Les deux champs redonnent exactement ces
  nombres (Butanosaure, espèce 50, compte parmi les Dragons ; il manque à
  `bestiaire.json`, comme 97 autres espèces). « Dressé » veut dire obtenu,
  synthèse comprise : la Phalène géante synthétisée a allumé le bit 110 dans
  les deux champs. Sur les 18 sauvegardes, dressés ⊆ vus, et toute espèce
  possédée est dressée.
- **Attributs, `0x36F8`** : les attributs de chaque espèce possédée
  (`Database_FR/monster_database.csv`) y sont toujours, sauf dans
  `histoire.dsv` (partie randomisée ?). Même synthèse : bits 12 (Défense
  paralysante) et 189 (Pré-Vent contraire), les deux attributs nouveaux de la
  Phalène géante. 97 attributs marqués pour 33 possédés : attributs vus.
- **Compétences, `0x3718`** : les 619 compétences portées par les monstres des
  sauvegardes y sont toutes. Même synthèse : bit 144 (Bonus Attaque Ⅲ).

**Écriture validée en jeu le 23/09/2026** (`biblio-suppr-test`) : ajouts et
retraits dans les quatre champs, y compris une espèce vue retirée et une
espèce dressée ramenée à « vue ». La bibliothèque du jeu les affiche tels
quels, et une sauvegarde faite en jeu les conserve à l'identique.

**Suppression de monstres validée le même jour** : deux monstres retirés du
ranch, le suivant descendu de deux emplacements, les deux derniers vidés. Le
jeu les affiche correctement et réécrit le ranch sans changement.

En appuyant sur la tablette du ranch, le jeu a affiché une seule fois « vous
avez dressé 30 monstres » et annoncé une récompense, sans nouveau monstre dans
la sauvegarde suivante. Octets changés hors temps et position : `0x3966`
(0 → 3, change aussi dans d'autres sessions), `0x399D` bit 4, `0x39B7` bit 6,
`0x3A56` bit 7, `0x3A5E` bit 7. Le drapeau du message est l'un d'eux. Les deux
derniers sont l'entrée 24 du Manuel du dresseur (Favorites), débloquée et
nouvelle : la récompense était cette entrée.

## Dressage des monstres géants

Le droit de dresser les monstres géants (3 places dans l'équipe) est accordé
au chapitre 8 : Lionyx, revenu à la vie, fait évoluer l'anneau de dresseur
(scène `d092` : « À partir d'aujourd'hui, tu seras en mesure de dresser des
monstres géants ! »). Il tient à **deux conditions à la fois** :

- **`0x39A7` bit `0x01`** : l'anneau a évolué ;
- **`0x393C` ≥ `0x0B`** : compteur d'avancement de l'histoire (u8), plus fin
  que le chapitre. Il vaut 1 au début, 2, 4 (chapitre 4), 5, 6, puis :

  | Valeur | Étape |
  |---|---|
  | `07` | arrivée à Archéopolis (`moitie-jeu`, chapitre 7) |
  | `08` | boss d'Archéopolis battu (probable) |
  | `09` | Lionyx maléfique battu à Nécropolis (probable ; partie principale, 14 h 33, toujours chapitre 7) |
  | `0B` | championnat des dresseurs gagné (relevé : partie principale, 15 h 22, toujours chapitre 7) ; l'anneau n'a pas encore évolué |
  | `0C`, `0D` | chapitre 9 et au-delà |

  `0A` n'a jamais été vu : le championnat fait passer de `09` à `0B` d'un
  coup. La scène de l'anneau (`d092`, chapitre 8) vient après, avec
  l'avancement déjà à `0B` : c'est elle qui allume `0x39A7`.

  Chapitre et avancement vont de pair : dans les 1 903 savestates et toutes
  les sauvegardes du jeu, chapitre 8 ↔ `0B`, chapitre 9 ↔ `0C` ou `0D`,
  chapitre 10 ↔ `0D`, et `0B` n'apparaît pas avant la fin du chapitre 7
  (championnat). La carte des îles (chapitre) et le dressage des géants
  (avancement) peuvent casser cette paire : l'éditeur l'affiche alors en
  avertissement (onglet Joueur).

  Les étapes probables viennent de ce qu'a joué le joueur entre `07` et `09`
  (boss d'Archéopolis, Nécropolis, Lionyx maléfique).

**Validé en jeu le 24/09/2026** sur une partie au chapitre 7 (avancement 9),
devant un Vercule (de nuit dans son nid) : les deux ensemble rendent
« Dresser » actif ; le drapeau seul, le compteur seul à `0B`, ou le drapeau
avec le compteur à `0A`, le laissent grisé. Puis, avec le réglage de
l'éditeur : une sauvegarde faite en jeu garde les deux octets, et un second
géant (de jour, dans une grotte d'une sous-zone de Prairia) a été dressé.

Trouvé par dichotomie en jeu, 31 essais. Base : la zone `0x3738-0x3A67`
recopiée d'un savestate DeSmuME (voir ci-dessous) pris juste avant le dressage
d'un Vercule. Recopiée d'un savestate pris juste après, elle faisait disparaître
le Vercule : un drapeau de cette zone retient les géants battus. Allumer
seulement des bits (essais sur les candidats « éteints jusqu'au chapitre 7,
allumés à partir du 9 ») ne marchait pas, justement parce que `0x393C` est un
compteur et non un drapeau.

Un troisième bit, **`0x3996` `0x01`**, rend les **géants utilisables** : sans
lui, un géant dressé occupe ses 3 cases du ranch avec des « ? » et ne peut
pas entrer dans l'équipe ; allumé, il s'affiche et s'équipe normalement
(validé en jeu sur le Vercule dressé dans la partie du randomizer). Un autre
éditeur n'allume que ce bit pour « accorder le droit de dresser », ce qui ne
suffit pas. Il s'allume lui aussi au chapitre 8. Il était resté allumé dans
toutes les sauvegardes de la dichotomie (la première version de l'éditeur
l'allumait), d'où son absence des essais.

L'éditeur (onglet Joueur, cadre « Dressage ») sépare les deux :
- « Dresser les monstres géants » allume l'anneau et monte le compteur à
  `0B` s'il est en dessous ; décocher n'éteint que l'anneau ;
- « Utiliser les monstres géants (3 places) » règle `0x3996` bit `0x01`,
  sans toucher à l'histoire.

**Risque pour l'histoire** (24/09/2026) : sur la partie du randomizer
(chapitre 0, compteur `01`), cocher a permis de dresser le Vercule, mais en
entrant dans le Vercule, où l'histoire fait affronter le boss du cercueil, le
héros a été recraché dès l'entrée (les monstres de l'intérieur restaient
visibles) : la progression est bloquée. En cause, très probablement, le
compteur monté d'un coup à `0B` (le drapeau seul n'a pas été essayé). Cocher
avant d'avoir battu ce boss est donc à éviter ; les autres étapes sautées
(`09` → `0B` sur la partie principale : retour de Lionyx) n'ont pas été
testées.

### Savestates DeSmuME

Un savestate DeSmuME (`.dst`, en-tête `DeSmuME SState` de 32 octets, puis
zlib) contient, une fois décompressé, la mémoire de sauvegarde (copies à
`0x907F34` et `0x90F034`) et la **copie de travail du jeu en RAM** à
`0x1C9B2C`, même disposition que la sauvegarde, à jour même sans sauvegarde
en jeu. 1 928 savestates d'une partie japonaise (2022) ont servi à suivre les
drapeaux dans le temps ; ils n'ont pas d'état entre 12 h 21 et 26 h 46 de jeu.

## Manuel du dresseur

Deux champs de bits de 8 octets, relevés le 24/09/2026 sur trois sauvegardes
de la même partie (`manuel-vide`, `manuel-complet`, `manuel-complet-nouveau`) :
elles ne diffèrent qu'en `0x3A54-0x3A59` et `0x3A5C-0x3A61` (et les sommes).

- **`0x3A54` : entrées débloquées.** Le bit n est l'entrée n + 1, dans l'ordre
  des titres de `msg_traveler` (ligne 0 « ???????? », puis Professionnels,
  Équipe… jusqu'à Mémo 13, ligne 47 ; leurs textes suivent à partir de la
  ligne 51). Manuel complet : bits 0 à 46, soit **47 entrées**.
- **`0x3A5C` : entrées « nouveau »**, même numérotation. La sauvegarde
  « tout nouveau » n'allume que les bits 0 à 44 : Mémo 12 et Mémo 13 n'y
  sont pas marqués.
- Sur toutes les sauvegardes écrites par le jeu, nouvelles ⊆ débloquées. Une
  partie neuve (`random`) a 11 entrées, dont Professionnels et Zoom déjà lues ;
  les sauvegardes de fin de partie en ont 30, avec Monstrequinque (reçu tard)
  encore « nouveau » avant le boss final.
- `0x3A50-0x3A53`, juste avant, vaut `FF FF FF FF` dans toutes les
  sauvegardes : autre champ, non touché.

L'éditeur (onglet Bibliothèque, sous-onglet Manuel du dresseur) coche les deux
états par entrée : marquer « nouveau » débloque, verrouiller retire aussi
« nouveau ».

**Validé en jeu le 24/09/2026.** `manuel-complet-nouveau` : les 47 entrées
affichées, toutes « nouveau » sauf Mémo 12 et 13, comme ses bits. Puis une
sauvegarde écrite par l'éditeur (`manuel-validation`) : entrées 1 à 10,
Répartition, Soigner, Mémo 12 et 13 débloquées, Dresser absente ; « nouveau »
sur Équipe, Répartition, Mémo 12 et 13 (le marqueur s'affiche donc aussi sur
les Mémos). Une sauvegarde faite en jeu ensuite garde les deux champs à
l'identique.

## Zones

Relevé le 24/09/2026 sur `moitie-jeu` (partie arrêtée à Archéopolis) :

- **`0x3951` : chapitre de l'histoire** (u8) : 0 au début, 4, 7 à
  mi-parcours, 9 après Rapthorne 2, 10 en fin de jeu. La carte des îles
  (affichée en sortant d'une zone par son entrée) en dépend, **validé en
  jeu** : au chapitre 8 elle montre Nécropolis, au 9 aussi Ténébria, au 10
  aussi l'Île des Pipits. **Toutes les îles en dépendent**, pas seulement
  celles de fin : sur la partie du randomizer (chapitre 0), passer au
  chapitre 10 affiche toutes les îles sur la carte, sans les ajouter au sort
  Téléportation. Relevé chapitre par chapitre le 24/09/2026 :

  | Chapitre | Île ajoutée à la carte |
  |---|---|
  | 2 (probable) | L'Arbirynthe, Prairia |
  | 3 | Arène |
  | 4 | Avablanche |
  | 5 | Escarpic |
  | 6 | Engloutîle |
  | 7 | Archéopolis |
  | 8 | Nécropolis |
  | 9 | Ténébria |
  | 10 | Île des Pipits |

  Au chapitre 1, la carte n'est accessible qu'après un dressage imposé par
  l'histoire, qui fait lui-même passer au chapitre 2 (et l'avancement de 1 à
  2) : d'où le « probable ».

  **Le chapitre n'ouvre que la carte.** Sur la même partie passée du
  chapitre 2 au 6 (avancement resté à `02`), Engloutîle est accessible mais
  les tentacules qu'il faut battre pour y avancer n'y sont pas : l'histoire
  de l'île n'est pas préparée, la progression y est bloquée. À L'Arbirynthe,
  en revanche, l'histoire reprend normalement (cinématiques, mécano) : elle
  suit l'avancement et des compteurs propres à chaque île (`0x393F` a valu
  1, 4 puis 5 au fil des événements de L'Arbirynthe), jamais le chapitre,
  resté à 6. Les étapes suivantes n'ont pas été jouées. L'éditeur laisse
  donc le choix du chapitre, avec un avertissement. Trouvé d'abord par dichotomie comme un « bit
  `0x08` » : l'allumer faisait passer `moitie-jeu` du chapitre 7 au 15, ce
  qui montrait les trois îles mais sautait tous les chapitres suivants. Il
  faut écrire la valeur voulue, jamais un masque. Avancer le chapitre peut
  faire sauter des événements de l'histoire.
- **Chaque zone dans la liste du sort Téléportation** (`TELEPORTATION`),
  allumé par la première visite, qui fait aussi passer le point d'une île en
  « visité » (moins marqué) sur la carte des îles. La liste en jeu suit
  l'ordre du jeu, pas celui des bits :

  | Zone | Bit |
  |---|---|
  | Albatros (toujours présent) | `0x39A9` `0x04` |
  | L'Arbirynthe | `0x39A9` `0x10` |
  | Prairia | `0x39A9` `0x20` |
  | Arène | `0x39AB` `0x08` |
  | Avablanche | `0x39A9` `0x40` |
  | Escarpic | `0x39A9` `0x80` |
  | Engloutîle | `0x39AA` `0x04` |
  | Archéopolis | `0x39AA` `0x02` |
  | Nécropolis | `0x39AA` `0x08` |
  | Ténébria | `0x39AA` `0x10` |
  | Île des Pipits | `0x39D9` `0x40` |
  | Palais Blanc (pas de point sur la carte des îles) | `0x39D9` `0x80` |

  **Validés en jeu** : les onze allumés ensemble sur la sauvegarde du
  randomizer (chapitre 0, rien que l'Albatros), puis Avablanche, Escarpic,
  Engloutîle et Archéopolis départagés par deux essais de deux bits ; les îles
  de fin allumées seules sur `moitie-jeu`. Un autre éditeur (conçu pour
  Joker 2) les propose comme « zones débloquables » et donne les mêmes bits.
  Éteindre celui d'une zone déjà visitée ne la retire pas : éteint, celui de
  l'Arbirynthe est revenu à la sauvegarde suivante. La première visite de
  l'Île des Pipits allume aussi `0x3950` bit `0x01`, `0x39F2` bit `0x08`,
  `0x3A29` bit `0x20` et `0x3A2A` (`3F`), sans rôle connu ; celle de Ténébria
  `0x39A8` bit `0x08`.
- Cartes : 67 Nécropolis, 79 Ténébria (arrivée de la Téléportation), 131 une
  autre zone de Ténébria, 136 Île des Pipits. Points de téléportation relevés
  sans bouger : arrivée du sort pour Ténébria et l'Île des Pipits, arrivée par
  la carte des îles pour Nécropolis. Pas encore de point pour le Palais Blanc.
- L'éditeur (onglet Joueur, cadre « Zones ») règle séparément la carte des
  îles (choix du chapitre, jamais sous celui de la partie ni au-delà de 10) et
  la liste du sort Téléportation (une case par zone, sans toucher au
  chapitre). Les îles
  déjà visitées restent cochées : retirer ces bits d'une partie avancée n'a
  pas été essayé. La Téléportation seule a été validée pour Ténébria au
  chapitre 7 (l'île apparaît dans la liste sans être sur la carte), et la
  téléportation de l'éditeur vers Ténébria au chapitre 7 donne une zone
  normale, avec ses monstres. **Seules l'arrivée et l'exploration ont été
  testées** : ouvrir Nécropolis, Ténébria ou l'Île des Pipits, ou s'y
  téléporter, avant que l'histoire y mène peut causer des soucis pour la
  suite de l'histoire (non testée).
- Les bits de `0x39C0-0x3A67` allumés en fin de jeu comprennent les sous-cartes
  découvertes : ajoutés à `moitie-jeu`, toutes celles d'Archéopolis se sont
  affichées. Pas encore isolés.

## Boutons

L'écran du bas du menu affiche une grille de 4 × 3 boutons, dont l'ordre est
enregistré en `0x1CC`, ligne par ligne ; `7F` marque une case vide. L'ID d'un
bouton est sa ligne dans `msg_menu` (le titre affiché en haut de l'écran du
bas, pour le bouton sélectionné, l'a confirmé sur deux boutons) :

| ID | Bouton | ID | Bouton |
|---|---|---|---|
| `00` | Sorts et aptitudes | `08` | Compétences de dressage |
| `01` | Objets | `09` | Manuel du dresseur |
| `02` | Équipement | `0A` | Monstrequinque |
| `03` | Changer de monstres | `0B` | Combats tombola |
| `04` | Changer de tactique | `0C` | Téléportation |
| `05` | Attribuer les compétences | `0D` | Téléportaïaut |
| `06` | Soigner tous | `0E` | Détectrésor |
| `07` | Sauvegarder | `0F` | Invisibilité |

Ordre d'une partie neuve (sauvegarde du randomizer) : `01 00 02 03 04 05 07
0B 09 08`, puis deux cases vides ; Soigner tous et Monstrequinque s'obtiennent
plus tard. Les quatre sorts (`0C` à `0F`) sont dans le sous-menu Compétences
de dressage, rangés en `0x1D8`.

**Validé en jeu le 24/09/2026** sur `moitie-jeu` : grille réordonnée, puis
une case vide au milieu et un bouton dans la dernière case ; la grille
s'affiche comme écrit (captures de l'écran du bas) et chaque bouton ouvre son
menu. L'éditeur (onglet Menu) échange les cases par glisser-déposer, sans
ajouter ni retirer de bouton ; il ne touche pas aux sorts. Il affiche les
icônes du jeu, extraites de la ROM (`menu_icon_data.cch` et `.cpl`, une icône
de 40 × 40 par ID, voir `editeur/extraction.py`).

## Méthode pour la suite

Pour identifier un champ : sauvegarder dans le jeu, faire **une seule** action
(dépenser de l'or, gagner un objet…), sauvegarder de nouveau, puis comparer
les deux fichiers. Les tests d'aller-retour garantissent qu'on ne casse rien
entre-temps.
