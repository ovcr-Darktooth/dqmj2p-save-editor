"""Vue sur un enregistrement de monstre : lit et écrit directement dans la
copie de la sauvegarde, champ par champ (voir format.CHAMPS_MONSTRE)."""
from . import format as F


class Monstre:
    def __init__(self, sauvegarde, emplacement: int):
        self.sauvegarde = sauvegarde
        self.emplacement = emplacement
        self.base = F.DEBUT_MONSTRES + emplacement * F.TAILLE_MONSTRE

    def __getitem__(self, cle: str):
        return F.CHAMP[cle].lire(self.sauvegarde.copie, self.base)

    def __setitem__(self, cle: str, valeur) -> None:
        champ = F.CHAMP[cle]
        if champ.lecture_seule:
            raise KeyError(f'{cle} est en lecture seule')
        if champ.lire(self.sauvegarde.copie, self.base) == valeur:
            return
        champ.ecrire(self.sauvegarde.copie, self.base, valeur)
        self.sauvegarde.modifiee = True

    @property
    def present(self) -> bool:
        # ID de création nul : emplacement libéré (monstre consommé en synthèse).
        return self['id_creation'] != 0 and self['espece'] != 0

    @property
    def octets(self) -> bytes:
        return bytes(self.sauvegarde.copie[self.base: self.base + F.TAILLE_MONSTRE])

    def competences(self) -> list[tuple[int, int]]:
        """[(id de compétence, points investis)] des emplacements non vides."""
        paires = ((self[f'competence_{j}'], self[f'competence_{j}_points'])
                  for j in range(1, F.NB_COMPETENCES + 1))
        return [p for p in paires if p[0]]

    def __repr__(self) -> str:
        return (f'<Monstre emplacement={self.emplacement} espece={self["espece"]} '
                f'niveau={self["niveau"]}>')
