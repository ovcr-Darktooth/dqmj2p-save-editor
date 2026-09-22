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
| `0x04-0x7B` | | En-tête, **à cartographier** (nom du joueur, temps de jeu, or…) |
| `0x7C` | 3 × u16 + 3 × u8 | Table compacte d'équipe : espèce puis niveau des 3 monstres actifs. Le jeu la tient à jour ; l'éditeur la resynchronise. |
| `0x88` | u32 | Somme data : somme des `0x1C10` mots u32 à partir de `0x90` |
| `0x8C` | u32 | Somme d'en-tête : somme des `0x23` premiers mots (inclut `0x88`, donc à calculer après) |
| `0xB4` | 6 × u32 | ID de création : équipe 1-3, puis réserve 1-3 |
| `0xCC-0x1E7` | | **À cartographier** |
| `0x1E8` | 100 × 0x84 | Enregistrements de monstres |
| `0x3638-0x70CF` | | Après les monstres, couvert par la somme data. **À cartographier** (inventaire ? drapeaux ?) |
| `0x70D0-0x70FF` | | Hors somme de contrôle, rôle inconnu |

Un emplacement de monstre est libre si son ID de création (`+0x14`) ou son
espèce (`+0x18`) vaut 0 (monstre consommé en synthèse).

## Enregistrement de monstre (0x84 octets)

Voir `CHAMPS_MONSTRE` dans `format.py` pour la liste complète. En résumé :

| Offset | Contenu |
|---|---|
| `+0x00` | Surnom, 16 o, codage du jeu (table de caractères de l'ARM9) |
| `+0x14` | ID de création (u32) |
| `+0x18` | Espèce, variante, polarité, synthèse + |
| `+0x20` | PV, PM, PV max, PM max, ATQ, DEF, AGI, SAG (u16) |
| `+0x30` | Niveau, arme, tactique |
| `+0x34` | Expérience, expérience du niveau suivant (u32) |
| `+0x3C` | Points de compétence non attribués (u16) |
| `+0x40` | Lignée : 2 parents + 4 grands-parents (u16), puis leurs variantes (u8) |
| `+0x52`, `+0x66` | Surnoms des parents |
| `+0x7A` | 5 × (compétence u8, points investis u8) |

### Octets inconnus

`+0x10` (4 o), `+0x1D`, `+0x1F`, `+0x33`, `+0x3E` (2 o), `+0x62` (4 o),
`+0x76` (4 o). Observé : `+0x10` et `+0x62` valent parfois `e31be31b`, qui
ressemble à du texte codé.

## Méthode pour la suite

Pour identifier un champ : sauvegarder dans le jeu, faire **une seule** action
(dépenser de l'or, gagner un objet…), sauvegarder de nouveau, puis comparer
les deux fichiers. Les tests d'aller-retour garantissent qu'on ne casse rien
entre-temps.
