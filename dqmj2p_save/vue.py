"""Accès par nom aux champs d'une zone de la sauvegarde : v['niveau'] lit,
v['niveau'] = 50 écrit directement dans la copie en mémoire."""
from . import format as F


class Vue:
    def __init__(self, sauvegarde, base: int, champs: dict[str, F.Champ]):
        self.sauvegarde = sauvegarde
        self.base = base
        self.champs = champs

    def __getitem__(self, cle: str):
        return self.champs[cle].lire(self.sauvegarde.copie, self.base)

    def __setitem__(self, cle: str, valeur) -> None:
        champ = self.champs[cle]
        if champ.lecture_seule:
            raise KeyError(f'{cle} est en lecture seule')
        if self[cle] == valeur:
            return
        champ.ecrire(self.sauvegarde.copie, self.base, valeur)
        self.sauvegarde.modifiee = True


class Joueur(Vue):
    def __init__(self, sauvegarde):
        super().__init__(sauvegarde, 0, F.CHAMP_JOUEUR)


class Sac(Vue):
    """sac[id_objet] : quantité possédée."""
    def __init__(self, sauvegarde):
        super().__init__(sauvegarde, 0, F.CHAMPS_SAC)

    def contenu(self) -> dict[int, int]:
        """{id: quantité} des objets possédés."""
        return {i: q for i in self.champs if (q := self[i])}
