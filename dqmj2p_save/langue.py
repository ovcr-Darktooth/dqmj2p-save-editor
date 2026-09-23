"""Langue de l'éditeur : noms du jeu et textes de l'interface.

Une langue par patch de traduction de la ROM japonaise : 'fr' (patch
français) et 'en' (patch anglais). Choisir la langue du patch installé garde
l'éditeur raccord avec le jeu : mêmes noms d'espèces, de compétences et
d'objets, et mêmes surnoms donnés par défaut (voir Monstre.surnom_complet).

Les textes sont écrits en français dans le code ; tr() les traduit avec le
catalogue de la langue courante (traduction_en.py) et rend le texte français
s'il manque une traduction.
"""
LANGUES = {'fr': 'Français', 'en': 'English'}
PAR_DEFAUT = 'fr'

_courante = PAR_DEFAUT


def courante() -> str:
    return _courante


def choisir(code: str) -> None:
    global _courante
    if code not in LANGUES:
        raise ValueError(f'langue inconnue : {code} (possibles : {", ".join(LANGUES)})')
    _courante = code


def catalogue(code: str) -> dict[str, str]:
    """Traductions du français vers la langue `code` ({} pour le français)."""
    if code == 'en':
        from .traduction_en import TEXTES
        return TEXTES
    return {}


def tr(texte: str, **valeurs) -> str:
    """Texte dans la langue courante ; les {champs} sont remplis par valeurs."""
    texte = catalogue(_courante).get(texte, texte)
    return texte.format(**valeurs) if valeurs else texte


def decimal(valeur: float, chiffres: int = 2) -> str:
    """Nombre à virgule (français) ou à point (anglais)."""
    texte = f'{valeur:.{chiffres}f}'
    return texte.replace('.', ',') if _courante == 'fr' else texte
