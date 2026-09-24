"""Tables de noms (espèces, compétences, attributs, objets), indexées par ID.

Fichiers texte dans noms/<langue>/ (un dossier par patch de traduction) : la
ligne N est le nom de l'ID N, la ligne 0 correspond à « aucun ». Sans langue
précisée, c'est celle de langue.courante(). Mise à jour : outils/importer_noms.py.
"""
from functools import cache
from pathlib import Path

from . import langue
from .langue import tr

DOSSIER = Path(__file__).parent / 'noms'
AUCUN = '(aucun)'
INUTILISE = '(inutilisé)'


class TableNoms:
    def __init__(self, noms: list[str], langue_: str = langue.PAR_DEFAUT):
        self.noms = noms
        self.langue = langue_

    def __len__(self) -> int:
        return len(self.noms)

    def __getitem__(self, id_: int) -> str:
        if id_ == 0:
            return self._marque(AUCUN)
        if 0 < id_ < len(self.noms):
            return self.noms[id_].strip() or self._marque(INUTILISE)
        return f'#{id_}'

    def choix(self) -> list[tuple[int, str]]:
        """(ID, nom) de toutes les entrées, lignes vides comprises : une
        sauvegarde peut contenir un ID que la traduction n'a pas nommé."""
        return [(i, self[i]) for i in range(len(self.noms))]

    def inutilise(self, id_: int) -> bool:
        """Vrai pour une entrée sans nom (ID réservé par le jeu)."""
        return 0 < id_ < len(self.noms) and not self.noms[id_].strip()

    def _marque(self, texte: str) -> str:
        return langue.catalogue(self.langue).get(texte, texte)


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
    67: 'Nécropolis',
    79: 'Ténébria',
    85: 'Albatros (extérieur)',
    88: 'Albatros (intérieur, ranch)',
    131: 'Ténébria (autre zone)',
    136: 'Île des Pipits',
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


# Boutons du menu de l'écran du bas (format.BOUTONS) : ID = ligne de msg_menu.
BOUTONS = {
    0x00: 'Sorts et aptitudes',
    0x01: 'Objets',
    0x02: 'Équipement',
    0x03: 'Changer de monstres',
    0x04: 'Changer de tactique',
    0x05: 'Attribuer les compétences',
    0x06: 'Soigner tous',
    0x07: 'Sauvegarder',
    0x08: 'Compétences de dressage',
    0x09: 'Manuel du dresseur',
    0x0A: 'Monstrequinque',
    0x0B: 'Combats tombola',
}


def bouton(id_: int) -> str:
    """Nom du bouton, dans la langue courante (noms des patchs)."""
    return tr(BOUTONS[id_]) if id_ in BOUTONS else tr('Bouton {id:02X}', id=id_)


def carte(numero: int) -> str:
    """Nom du lieu, dans la langue courante (noms du patch anglais : voir
    traduction_en.py)."""
    return tr(CARTES.get(numero, 'lieu inconnu'))


# Codes de contrôle des textes du jeu : {315} retour à la ligne, {231} à {233}
# symboles de polarité (+, -, neutre).
_CODES_TEXTE = {'{315}': '\n', '{231}': '⊕', '{232}': '⊖', '{233}': '⊘'}


def _aide(nom_table: str, id_: int, langue_: str | None) -> str:
    lignes = table(nom_table, langue_).noms
    texte = lignes[id_] if 0 <= id_ < len(lignes) else ''
    for code, remplacement in _CODES_TEXTE.items():
        texte = texte.replace(code, remplacement)
    return texte


def aide_objet(id_: int, langue_: str | None = None) -> str:
    """Description d'un objet telle que le jeu l'affiche (msg_itemhelp)."""
    return _aide('objets_aide', id_, langue_)


def aide_attribut(id_: int, langue_: str | None = None) -> str:
    """Description d'un attribut, celle de la bibliothèque (msg_library)."""
    return _aide('attributs_aide', id_, langue_)


def aide_manuel(id_: int, langue_: str | None = None) -> str:
    """Texte d'une entrée du Manuel du dresseur (msg_traveler)."""
    return _aide('manuel_aide', id_, langue_)


def table(nom: str, langue_: str | None = None) -> TableNoms:
    """nom : 'especes', 'competences', 'attributs', 'objets', 'objets_aide',
    'attributs_aide', 'manuel' ou 'manuel_aide' ; langue_ : 'fr', 'en', ou None pour la courante."""
    return _table(nom, langue_ or langue.courante())


@cache
def _table(nom: str, langue_: str) -> TableNoms:
    chemin = DOSSIER / langue_ / f'{nom}.txt'
    return TableNoms(chemin.read_text(encoding='utf-8').splitlines(), langue_)
