"""Vue sur un enregistrement de monstre (voir format.CHAMPS_MONSTRE)."""
from . import format as F
from .noms import table
from .texte import LONGUEUR_MAX
from .vue import Vue


class Monstre(Vue):
    def __init__(self, sauvegarde, emplacement: int):
        super().__init__(sauvegarde, F.DEBUT_MONSTRES + emplacement * F.TAILLE_MONSTRE,
                         F.CHAMP)
        self.emplacement = emplacement

    @property
    def present(self) -> bool:
        # ID de création nul : emplacement libéré (monstre consommé en synthèse).
        return self['id_creation'] != 0 and self['espece'] != 0

    @property
    def octets(self) -> bytes:
        return bytes(self.sauvegarde.copie[self.base: self.base + F.TAILLE_MONSTRE])

    def surnom_complet(self) -> str:
        """Nom de l'espèce, coupé à la longueur permise par le jeu : ce que le
        jeu attribue quand on valide un surnom vide."""
        return table('especes')[self['espece']][:LONGUEUR_MAX].rstrip()

    @property
    def surnom_par_defaut(self) -> bool:
        """Vrai si le surnom est encore l'abrégé donné à la capture (les
        premières lettres de l'espèce)."""
        surnom, complet = self['surnom'], self.surnom_complet()
        return bool(surnom) and surnom != complet and complet.startswith(surnom)

    def competences(self) -> list[tuple[int, int]]:
        """[(id de compétence, points investis)] des emplacements non vides."""
        paires = ((self[f'competence_{j}'], self[f'competence_{j}_points'])
                  for j in range(1, F.NB_COMPETENCES + 1))
        return [p for p in paires if p[0]]

    def __repr__(self) -> str:
        return (f'<Monstre emplacement={self.emplacement} espece={self["espece"]} '
                f'niveau={self["niveau"]}>')
