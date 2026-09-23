# Éditeur de sauvegardes DQMJ2 Professional

*[English version](README_en.md)*

Éditeur graphique de sauvegardes pour *Dragon Quest Monsters: Joker 2
Professional* (Nintendo DS). Il accepte les `.sav` bruts et les `.dsv` de
DeSmuME et DraStic.

> **État : en construction.** Édition du joueur (nom, temps de jeu, or,
> statistiques), du sac et des monstres (surnom, espèce, stats, lignée,
> compétences, arme), avec les noms du patch français ou anglais. Consultation
> de la bibliothèque (monstres vus et dressés, attributs, compétences).

## Principe

L'éditeur modifie la sauvegarde **en place** : seuls les champs édités
changent. Les sommes de contrôle sont recalculées, et les deux copies ainsi
que le pied de page `.dsv` sont conservés. Les zones dont le rôle est encore
inconnu ne sont jamais touchées. Une sauvegarde ouverte puis enregistrée
sans modification ressort identique octet pour octet.

Avant chaque écriture, une copie horodatée de l'original est gardée
(`partie.dsv.20260922-153000.bak`).

## Télécharger (Windows)

Prenez le zip de la dernière version dans les
[Releases](https://github.com/ovcr-Darktooth/dqmj2p-save-editor/releases),
décompressez-le et lancez `Editeur-DQMJ2P.exe` : Python n'est pas nécessaire.
Windows peut afficher un avertissement SmartScreen (exe non signé) :
« Informations complémentaires », puis « Exécuter quand même ».

## Lancer l'éditeur depuis le code

Double-cliquer sur `Lancer-Editeur.bat`. La première fois, il crée un
environnement `.venv` et y installe PySide6. On peut aussi glisser une
sauvegarde sur la fenêtre, ou lancer :

```
python -m editeur partie.dsv
```

### Langue

Menu **Langue / Language** : français ou anglais. Choisissez la langue du patch
installé sur votre ROM : l'interface et les noms des monstres, compétences,
attributs et objets sont alors ceux du jeu. Le choix compte aussi pour
« Surnoms abrégés → nom complet de l'espèce », qui compare les surnoms aux noms
d'espèce de cette langue. Changer de langue garde la sauvegarde ouverte et ses
modifications non enregistrées.

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

Avec l'exe, les icônes se rangent dans le dossier `icones` à côté de
`Editeur-DQMJ2P.exe` : copiez-y les PNG de `site/icons` de dqmj2pro-synthesis,
ou donnez ce dossier aux outils d'extraction
(`python outils/extraire_icones.py <ROM> <dossier de l'exe>\icones`, et
`…\icones\familles` pour `extraire_familles.py`).

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
| `dqmj2p_save/noms/fr/`, `noms/en/` | Noms des espèces et compétences de chaque patch (ligne N = ID N) |
| `outils/importer_noms.py` | Resynchronise ces noms depuis le dépôt de traduction (`… <dépôt> en` pour l'anglais) |
| `dqmj2p_save/langue.py` | Langue courante ; textes de l'interface traduits par `traduction_en.py` |
| `editeur/icones/` | Icônes des monstres (`<id>.png`), à extraire (non versionnées) |
| `outils/extraire_icones.py` | Les extrait d'une ROM (`MonsterIconDat.NICA`) |
| `outils/rom_nds.py` | Lecture des fichiers d'une ROM DS, pour les extracteurs |
| `dqmj2p_save/donnees/bestiaire.json` | Rang, famille, taille et synthèses spéciales |
| `outils/importer_synthese.py` | Recopie icônes et bestiaire depuis le projet des synthèses |
| `editeur/icones/familles/` | Icônes des familles, glyphes de la police du jeu (non versionnées) |
| `outils/extraire_familles.py` | Les extrait d'une ROM (`font_16x16.NFTR` + palette des menus) |
| `docs/format-sauvegarde.md` | Carte du format, avec ce qui reste inconnu |
| `outils/construire_exe.py` | Construit l'exe (PyInstaller) |
| `.github/workflows/release.yml` | Exe Windows à chaque PR ; release au push d'un tag `vX.Y.Z` (notes : `docs/notes-de-version/vX.Y.Z.md`) |
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
les noms anglais de [DQMJ2Pro_Translation](https://github.com/saneezore07/DQMJ2Pro_Translation),
les synthèses du projet [dqmj2pro-synthesis](https://github.com/ovcr-Darktooth/dqmj2pro-synthesis),
dont `tools/extract_icons.py` a décodé le format des icônes (`MonsterIconDat.NICA`)
repris par `outils/extraire_icones.py`.

## Avertissement

Gardez toujours une copie de votre sauvegarde. Sous DraStic, fermez le jeu
avant de remplacer le fichier, sinon l'émulateur l'écrase en quittant.
