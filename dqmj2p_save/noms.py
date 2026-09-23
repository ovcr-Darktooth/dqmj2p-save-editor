"""Tables de noms (espèces, compétences, attributs, objets), indexées par ID.

Fichiers texte dans noms/<langue>/ : la ligne N est le nom de l'ID N, la ligne
0 correspond à « aucun ». Mise à jour : outils/importer_noms.py.
"""
from functools import cache
from pathlib import Path

DOSSIER = Path(__file__).parent / 'noms'
AUCUN = '(aucun)'
INUTILISE = '(inutilisé)'


class TableNoms:
    def __init__(self, noms: list[str]):
        self.noms = noms

    def __len__(self) -> int:
        return len(self.noms)

    def __getitem__(self, id_: int) -> str:
        if id_ == 0:
            return AUCUN
        if 0 < id_ < len(self.noms):
            return self.noms[id_].strip() or INUTILISE
        return f'#{id_}'

    def choix(self) -> list[tuple[int, str]]:
        """(ID, nom) de toutes les entrées, lignes vides comprises : une
        sauvegarde peut contenir un ID que la traduction n'a pas nommé."""
        return [(i, self[i]) for i in range(len(self.noms))]


# Numéro de carte (sauvegarde, 0x3A68) -> lieu. La table du jeu qui relie
# cartes et régions (msg_map) n'est pas encore localisée : ces entrées sont
# relevées en jeu, une sauvegarde à la fois.
CARTES = {
    14: "L'Arbirynthe",
    17: 'Prairia',
    24: 'Arène',
    33: 'Avablanche (autre zone)',
    35: 'Avablanche (fin de zone)',
    37: 'Escarpic',
    47: 'Engloutîle',
    57: 'Archéopolis',
    85: 'Albatros (extérieur)',
    88: 'Albatros (intérieur, ranch)',
    151: 'Avablanche',
}


# Intempérie propre à chaque carte (une seule par carte), observée en jeu.
# Les cartes absentes n'ont pas de météo connue. Ne jamais forcer l'intempérie
# ailleurs : essayé à Avablanche, il ne pleut pas mais la zone perd ses
# monstres et sa musique, y compris dans les zones voisines.
METEO = {
    14: 'pluie',        # L'Arbirynthe
    17: 'pluie',        # Prairia
    37: 'pluie',        # Escarpic
    47: 'brume',        # Engloutîle
    57: 'pluie',        # Archéopolis (débloquée plus tard dans l'histoire)
}


def carte(numero: int) -> str:
    return CARTES.get(numero, 'lieu inconnu')


# Codes de contrôle des textes du jeu : {315} retour à la ligne, {231} à {233}
# symboles de polarité (+, -, neutre).
_CODES_TEXTE = {'{315}': '\n', '{231}': '⊕', '{232}': '⊖', '{233}': '⊘'}


def _aide(nom_table: str, id_: int, langue: str) -> str:
    lignes = table(nom_table, langue).noms
    texte = lignes[id_] if 0 <= id_ < len(lignes) else ''
    for code, remplacement in _CODES_TEXTE.items():
        texte = texte.replace(code, remplacement)
    return texte


def aide_objet(id_: int, langue: str = 'fr') -> str:
    """Description d'un objet telle que le jeu l'affiche (msg_itemhelp)."""
    return _aide('objets_aide', id_, langue)


def aide_attribut(id_: int, langue: str = 'fr') -> str:
    """Description d'un attribut, celle de la bibliothèque (msg_library)."""
    return _aide('attributs_aide', id_, langue)


@cache
def table(nom: str, langue: str = 'fr') -> TableNoms:
    """nom : 'especes', 'competences', 'attributs', 'objets', 'objets_aide'
    ou 'attributs_aide'."""
    chemin = DOSSIER / langue / f'{nom}.txt'
    return TableNoms(chemin.read_text(encoding='utf-8').splitlines())
