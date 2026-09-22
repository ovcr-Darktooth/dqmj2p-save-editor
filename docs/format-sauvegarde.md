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
| `0x1CC-0x1DB` | 16 o | **À cartographier** (`00 01 00 02 03 04 05 07 0B 09 08 7F…`, ressemble à un ordre ou à des index) |
| `0x1DC` | 3 × u16 | Victoires, monstres dressés, monstres synthétisés |
| `0x1E8` | 100 × 0x84 | Enregistrements de monstres |
| `0x3638-0x3A67` | | **À cartographier** |
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
qu'un type d'intempérie. `0x3970` (0 à 6 selon les sauvegardes) reste inconnu.

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

## Méthode pour la suite

Pour identifier un champ : sauvegarder dans le jeu, faire **une seule** action
(dépenser de l'or, gagner un objet…), sauvegarder de nouveau, puis comparer
les deux fichiers. Les tests d'aller-retour garantissent qu'on ne casse rien
entre-temps.
