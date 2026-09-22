"""Tables de noms (espèces, compétences), indexées par ID.

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


@cache
def table(nom: str, langue: str = 'fr') -> TableNoms:
    """nom : 'especes', 'competences' ou 'objets'."""
    chemin = DOSSIER / langue / f'{nom}.txt'
    return TableNoms(chemin.read_text(encoding='utf-8').splitlines())
