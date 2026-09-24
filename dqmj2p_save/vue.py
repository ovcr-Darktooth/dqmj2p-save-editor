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


class Bibliotheque:
    """Bibliothèque du jeu : monstres vus et dressés, attributs et compétences
    vus, sous forme d'ensembles d'ID dont le bit est allumé.

    Une espèce dressée est toujours vue (vrai dans toutes les sauvegardes
    écrites par le jeu) : dresser allume aussi « vu », oublier une espèce
    éteint aussi « dressé ». L'ID 0 (« aucun ») n'est jamais modifié."""
    CHAMPS = {
        'vues': (F.BIBLIO_VUS, F.NB_BITS_ESPECES),
        'dressees': (F.BIBLIO_DRESSES, F.NB_BITS_ESPECES),
        'attributs': (F.BIBLIO_ATTRIBUTS, F.NB_BITS_ATTRIBUTS),
        'competences': (F.BIBLIO_COMPETENCES, F.NB_BITS_COMPETENCES),
    }

    def __init__(self, sauvegarde):
        self.sauvegarde = sauvegarde

    def _bits(self, champ: str) -> set[int]:
        debut, nombre = self.CHAMPS[champ]
        octets = self.sauvegarde.copie[debut: debut + nombre // 8]
        return {i for i in range(nombre) if octets[i // 8] >> (i % 8) & 1}

    def _ecrire(self, champ: str, id_: int, allume: bool) -> None:
        debut, nombre = self.CHAMPS[champ]
        if not 0 < id_ < nombre:
            raise ValueError(f'{champ} : ID {id_} hors de 1..{nombre - 1}')
        octet, masque = debut + id_ // 8, 1 << (id_ % 8)
        avant = self.sauvegarde.copie[octet]
        apres = avant | masque if allume else avant & ~masque
        if apres != avant:
            self.sauvegarde.copie[octet] = apres
            self.sauvegarde.modifiee = True

    def especes_vues(self) -> set[int]:
        return self._bits('vues')

    def especes_dressees(self) -> set[int]:
        return self._bits('dressees')

    def attributs(self) -> set[int]:
        return self._bits('attributs')

    def competences(self) -> set[int]:
        return self._bits('competences')

    def marquer_vue(self, espece: int, vue: bool = True) -> None:
        if not vue:
            self._ecrire('dressees', espece, False)
        self._ecrire('vues', espece, vue)

    def marquer_dressee(self, espece: int, dressee: bool = True) -> None:
        if dressee:
            self._ecrire('vues', espece, True)
        self._ecrire('dressees', espece, dressee)

    def marquer_attribut(self, id_: int, vu: bool = True) -> None:
        self._ecrire('attributs', id_, vu)

    def marquer_competence(self, id_: int, vue: bool = True) -> None:
        self._ecrire('competences', id_, vue)


class Manuel:
    """Manuel du dresseur : entrées débloquées et marquées « nouveau », sous
    forme d'ensembles de numéros d'entrée (1 à F.NB_ENTREES_MANUEL, ligne de
    noms.table('manuel')). Une entrée nouvelle est toujours débloquée :
    marquer nouvelle débloque, verrouiller retire aussi « nouveau »."""
    CHAMPS = {'debloquees': F.MANUEL_DEBLOQUEES, 'nouvelles': F.MANUEL_NOUVELLES}

    def __init__(self, sauvegarde):
        self.sauvegarde = sauvegarde

    def _entrees(self, champ: str) -> set[int]:
        debut = self.CHAMPS[champ]
        octets = self.sauvegarde.copie[debut: debut + 8]
        return {n + 1 for n in range(F.NB_ENTREES_MANUEL) if octets[n // 8] >> (n % 8) & 1}

    def _ecrire(self, champ: str, entree: int, allume: bool) -> None:
        if not 1 <= entree <= F.NB_ENTREES_MANUEL:
            raise ValueError(f'manuel : entrée {entree} hors de 1..{F.NB_ENTREES_MANUEL}')
        n = entree - 1
        octet, masque = self.CHAMPS[champ] + n // 8, 1 << (n % 8)
        avant = self.sauvegarde.copie[octet]
        apres = avant | masque if allume else avant & ~masque
        if apres != avant:
            self.sauvegarde.copie[octet] = apres
            self.sauvegarde.modifiee = True

    def debloquees(self) -> set[int]:
        return self._entrees('debloquees')

    def nouvelles(self) -> set[int]:
        return self._entrees('nouvelles')

    def debloquer(self, entree: int, debloquee: bool = True) -> None:
        if not debloquee:
            self._ecrire('nouvelles', entree, False)
        self._ecrire('debloquees', entree, debloquee)

    def marquer_nouvelle(self, entree: int, nouvelle: bool = True) -> None:
        if nouvelle:
            self._ecrire('debloquees', entree, True)
        self._ecrire('nouvelles', entree, nouvelle)
