# Éditeur de sauvegardes DQMJ2 Professional

Éditeur graphique de sauvegardes pour *Dragon Quest Monsters: Joker 2
Professional* (Nintendo DS). Il accepte les `.sav` bruts et les `.dsv` de
DeSmuME et DraStic.

> **État : en construction.** Le cœur (lecture, édition, écriture) fonctionne
> et est testé. L'interface graphique n'existe pas encore.

## Principe

L'éditeur modifie la sauvegarde **en place** : seuls les champs édités
changent. Les sommes de contrôle sont recalculées, et les deux copies ainsi
que le pied de page `.dsv` sont conservés. Les zones dont le rôle est encore
inconnu ne sont jamais touchées. Une sauvegarde ouverte puis enregistrée
sans modification ressort identique octet pour octet.

Avant chaque écriture, une copie horodatée de l'original est gardée
(`partie.dsv.20260922-153000.bak`).

## Utilisation (pour l'instant)

```
python -m dqmj2p_save partie.dsv
```

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
| `editeur/` | Interface graphique (PySide6), à venir |
| `docs/format-sauvegarde.md` | Carte du format, avec ce qui reste inconnu |
| `tests/` | `python -m unittest discover tests` |

Les tests sur sauvegardes réelles lisent `tests/donnees/*.dsv`. Ces fichiers
ne sont pas versionnés : déposez-y vos propres sauvegardes.

## Remerciements

Le format de sauvegarde a été décrypté par **Ceris White** et l'équipe du
projet [DQMJ2 Professional Translation](https://github.com/saneezore07/DQMJ2Pro_Translation).
Ce dépôt n'en reprend pas le code : il réimplémente le format à partir de
leur documentation.

## Avertissement

Gardez toujours une copie de votre sauvegarde. Sous DraStic, fermez le jeu
avant de remplacer le fichier, sinon l'émulateur l'écrase en quittant.
