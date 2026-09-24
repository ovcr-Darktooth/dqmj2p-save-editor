"""Rang, famille, taille et synthèses spéciales des espèces.

Données de donnees/bestiaire.json, importées du projet des synthèses par
outils/importer_synthese.py. Une espèce absente (ou « ??? ») n'est pas une
erreur : les champs valent alors None.
"""
import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

FICHIER = Path(__file__).parent / 'donnees' / 'bestiaire.json'
# Familles et rangs manquants, repris de la base de la traduction
# (outils/completer_bestiaire.py) ; ne remplace aucune valeur de FICHIER.
COMPLEMENT = Path(__file__).parent / 'donnees' / 'complement_bestiaire.json'


@dataclass(frozen=True)
class Fiche:
    rang: str | None
    famille: str | None
    taille: int | None


@dataclass(frozen=True)
class Recette:
    resultat: int
    parents: tuple[int, ...]        # 2 ou 4 espèces, dans l'ordre du jeu
    patch: bool                     # ajoutée par le patch de traduction


@cache
def _donnees() -> tuple[dict[int, Fiche], tuple[Recette, ...]]:
    brut = json.loads(FICHIER.read_text(encoding='utf-8'))
    monstres = brut['monstres']
    if COMPLEMENT.exists():
        for i, valeurs in json.loads(COMPLEMENT.read_text(encoding='utf-8')).items():
            fiche = monstres.setdefault(i, {'rang': None, 'famille': None, 'taille': None})
            for cle, valeur in valeurs.items():
                if fiche.get(cle) is None:
                    fiche[cle] = valeur
    fiches = {int(i): Fiche(m['rang'], m['famille'], m['taille'])
              for i, m in monstres.items()}
    recettes = tuple(Recette(r['resultat'], tuple(r['parents']), r['patch'])
                     for r in brut['recettes'])
    return fiches, recettes


def fiche(espece: int) -> Fiche:
    return _donnees()[0].get(espece, Fiche(None, None, None))


def recettes() -> tuple[Recette, ...]:
    """Toutes les synthèses spéciales."""
    return _donnees()[1]


def obtenu_par(espece: int) -> list[Recette]:
    """Synthèses spéciales qui donnent cette espèce."""
    return [r for r in _donnees()[1] if r.resultat == espece]


def sert_a(espece: int) -> list[Recette]:
    """Synthèses spéciales où cette espèce est l'un des parents."""
    return [r for r in _donnees()[1] if espece in r.parents]
