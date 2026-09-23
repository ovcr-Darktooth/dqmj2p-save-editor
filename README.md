# Éditeur de sauvegardes DQMJ2 Professional

Éditeur graphique de sauvegardes pour *Dragon Quest Monsters: Joker 2
Professional* (Nintendo DS). Il accepte les `.sav` bruts et les `.dsv` de
DeSmuME et DraStic.

> **État : en construction.** Édition du joueur (nom, temps de jeu, or,
> statistiques), du sac et des monstres (surnom, espèce, stats, lignée,
> compétences, arme), avec les noms français. Consultation de la
> bibliothèque (monstres vus et dressés, attributs, compétences).

## Principe

L'éditeur modifie la sauvegarde **en place** : seuls les champs édités
changent. Les sommes de contrôle sont recalculées, et les deux copies ainsi
que le pied de page `.dsv` sont conservés. Les zones dont le rôle est encore
inconnu ne sont jamais touchées. Une sauvegarde ouverte puis enregistrée
sans modification ressort identique octet pour octet.

Avant chaque écriture, une copie horodatée de l'original est gardée
(`partie.dsv.20260922-153000.bak`).

## Lancer l'éditeur

Double-cliquer sur `Lancer-Editeur.bat`. La première fois, il crée un
environnement `.venv` et y installe PySide6. On peut aussi glisser une
sauvegarde sur la fenêtre, ou lancer :

```
python -m editeur partie.dsv
```

### Icônes (facultatif)

Les icônes des monstres et des familles sont des graphismes du jeu : elles ne
sont pas dans ce dépôt. Sans elles, l'éditeur fonctionne et affiche des cases
vides. Pour les extraire de votre ROM (japonaise d'origine ou patchée, en
moins d'une seconde) :

```
python outils/extraire_icones.py <votre ROM .nds>
python outils/extraire_familles.py <votre ROM .nds>
```

Les icônes des monstres peuvent aussi venir d'un clone du projet
[dqmj2pro-synthesis](https://github.com/ovcr-Darktooth/dqmj2pro-synthesis),
qui les publie déjà : `python outils/importer_synthese.py <clone>`.

## Utilisation en Python

Inspection rapide : `python -m dqmj2p_save partie.dsv`

```python
from dqmj2p_save import Sauvegarde

s = Sauvegarde.ouvrir('partie.dsv')
for m in s.monstres():
    print(m.emplacement, s.role(m), m['espece'], m['niveau'])

s.monstre(11)['attaque'] = 500
s.enregistrer()
```

## Structure

| Dossier | Rôle |
|---|---|
| `dqmj2p_save/` | Cœur, sans interface, bibliothèque standard uniquement |
| `editeur/` | Interface graphique (PySide6) |
| `dqmj2p_save/noms/fr/` | Noms des espèces et compétences (ligne N = ID N) |
| `outils/importer_noms.py` | Resynchronise ces noms depuis le dépôt de traduction |
| `editeur/icones/` | Icônes des monstres (`<id>.png`), à extraire (non versionnées) |
| `outils/extraire_icones.py` | Les extrait d'une ROM (`MonsterIconDat.NICA`) |
| `outils/rom_nds.py` | Lecture des fichiers d'une ROM DS, pour les extracteurs |
| `dqmj2p_save/donnees/bestiaire.json` | Rang, famille, taille et synthèses spéciales |
| `outils/importer_synthese.py` | Recopie icônes et bestiaire depuis le projet des synthèses |
| `editeur/icones/familles/` | Icônes des familles, glyphes de la police du jeu (non versionnées) |
| `outils/extraire_familles.py` | Les extrait d'une ROM (`font_16x16.NFTR` + palette des menus) |
| `docs/format-sauvegarde.md` | Carte du format, avec ce qui reste inconnu |
| `tests/` | `python -m unittest discover tests` |

Les tests sur sauvegardes réelles lisent `tests/donnees/*.dsv`. Ces fichiers
ne sont pas versionnés : déposez-y vos propres sauvegardes.

## Remerciements

Le format de sauvegarde a été décrypté par **Ceris White** et l'équipe du
projet [DQMJ2 Professional Translation](https://github.com/saneezore07/DQMJ2Pro_Translation).
Ce dépôt n'en reprend pas le code : il réimplémente le format à partir de
leur documentation.

Les noms français viennent de la traduction
[DQMJ2Pro_Translation_FR](https://github.com/ovcr-Darktooth/DQMJ2Pro_Translation_FR),
les synthèses du projet [dqmj2pro-synthesis](https://github.com/ovcr-Darktooth/dqmj2pro-synthesis),
dont `tools/extract_icons.py` a décodé le format des icônes (`MonsterIconDat.NICA`)
repris par `outils/extraire_icones.py`.

## Avertissement

Gardez toujours une copie de votre sauvegarde. Sous DraStic, fermez le jeu
avant de remplacer le fichier, sinon l'émulateur l'écrase en quittant.
