"""Synthèses spéciales à portée : ce que les monstres possédés (équipe, réserve
et ranch) permettent de faire tout de suite, ou bientôt.

Règles du jeu prises en compte :
  - les deux parents doivent être au moins au niveau NIVEAU_MIN ;
  - ils doivent être de polarités opposées, un parent neutre allant avec
    tout. Le patch anglais permet de désactiver cette règle : l'analyse peut
    donc l'ignorer (c'est le choix par défaut de l'éditeur) ;
  - une synthèse à 4 parents (A + B + C + D) se fait avec deux monstres
    intermédiaires, l'un né de A + B et l'autre de C + D : c'est la lignée
    (parent_1, parent_2) des monstres qui compte, pas leur espèce.

Chaque recette de bestiaire reçoit un état :
  POSSIBLE    les parents sont là et remplissent les conditions ;
  BIENTOT     tous les monstres nécessaires sont là, mais il faut monter un
              niveau, trouver la bonne polarité ou synthétiser d'abord les
              intermédiaires d'une synthèse à 4 ;
  INCOMPLETE  il manque des espèces (Analyse.manquants), au moins un parent
              étant possédé.
Les recettes dont on ne possède aucun parent ne sont pas renvoyées.

suites() fait monter d'un niveau dans l'arbre des synthèses : l'enfant d'une
synthèse prend la place des parents qu'elle consomme, et l'on cherche ce
qu'il permet à son tour. Pour une synthèse incomplète, on suppose ses espèces
manquantes trouvées. En descendant de suite en suite, on suit une lignée
jusqu'aux espèces les plus hautes.
"""
from collections import Counter
from dataclasses import dataclass
from itertools import count, product

from . import bestiaire
from .monstre import Monstre

NIVEAU_MIN = 10
# Valeurs du champ « polarite » : deux polarités opposées, et le neutre.
POSITIF, NEGATIF, NEUTRE = 0, 1, 2

POSSIBLE, BIENTOT, INCOMPLETE = 'possible', 'bientot', 'incomplete'
ETATS = (POSSIBLE, BIENTOT, INCOMPLETE)


def polarites_compatibles(a: Monstre, b: Monstre) -> bool:
    pa, pb = a['polarite'], b['polarite']
    return NEUTRE in (pa, pb) or pa != pb


@dataclass(frozen=True)
class Analyse:
    recette: bestiaire.Recette
    etat: str
    # Monstres retenus, dans l'ordre des parents de la recette ; None pour une
    # espèce manquante. Pour une synthèse à 4 faite directement, ce sont les
    # deux intermédiaires (voir intermediaires_prets).
    monstres: tuple[Monstre | None, ...]
    manquants: tuple[int, ...] = ()
    trop_bas: tuple[Monstre, ...] = ()       # sous NIVEAU_MIN
    meme_polarite: bool = False              # parents retenus incompatibles
    # Synthèse à 4 : paires de la recette dont l'intermédiaire reste à créer.
    a_synthetiser: tuple[tuple[int, int], ...] = ()
    intermediaires_prets: bool = False
    possedes: int = 0                        # parents de la recette couverts

    @property
    def nb_manquants(self) -> int:
        return len(self.manquants)


def _meilleure_paire(candidats_a, candidats_b, ignorer_polarite: bool):
    """Paire de monstres distincts la plus proche d'être utilisable, ou None."""
    meilleure, cle_meilleure = None, None
    for a, b in product(candidats_a, candidats_b):
        if a.emplacement == b.emplacement:
            continue
        compatibles = ignorer_polarite or polarites_compatibles(a, b)
        assez_hauts = (a['niveau'] >= NIVEAU_MIN) + (b['niveau'] >= NIVEAU_MIN)
        cle = (compatibles, assez_hauts, a['niveau'] + b['niveau'])
        if cle_meilleure is None or cle > cle_meilleure:
            meilleure, cle_meilleure = (a, b), cle
    return meilleure


def _evaluer_paire(recette, paire, ignorer_polarite: bool, **autres) -> Analyse:
    a, b = paire
    trop_bas = tuple(m for m in paire if m['niveau'] < NIVEAU_MIN)
    meme = not ignorer_polarite and not polarites_compatibles(a, b)
    etat = BIENTOT if trop_bas or meme else POSSIBLE
    return Analyse(recette, etat, paire, trop_bas=trop_bas, meme_polarite=meme,
                   possedes=len(recette.parents), **autres)


def _allouer(especes, monstres, utilises: set[int]):
    """Un monstre distinct par espèce voulue, le plus haut niveau d'abord.
    Renvoie (monstres ou None, espèces manquantes)."""
    choisis, manquants = [], []
    for espece in especes:
        libres = [m for m in monstres
                  if m['espece'] == espece and m.emplacement not in utilises]
        if libres:
            m = max(libres, key=lambda m: m['niveau'])
            utilises.add(m.emplacement)
            choisis.append(m)
        else:
            choisis.append(None)
            manquants.append(espece)
    return choisis, manquants


def _lignee(m: Monstre) -> Counter:
    return Counter((m['parent_1'], m['parent_2']))


def analyser_recette(recette: bestiaire.Recette, monstres: list[Monstre],
                     ignorer_polarite: bool = True) -> Analyse | None:
    parents = recette.parents
    if len(parents) == 2:
        a, b = parents
        paire = _meilleure_paire([m for m in monstres if m['espece'] == a],
                                 [m for m in monstres if m['espece'] == b],
                                 ignorer_polarite)
        if paire:
            return _evaluer_paire(recette, paire, ignorer_polarite)
        choisis, manquants = _allouer(parents, monstres, set())
        possedes = len(parents) - len(manquants)
        if not possedes:
            return None
        return Analyse(recette, INCOMPLETE, tuple(choisis), tuple(manquants),
                       possedes=possedes)

    # Synthèse à 4 : deux intermédiaires nés de chaque paire de la recette.
    paires = (parents[:2], parents[2:])
    nes_de = [[m for m in monstres if _lignee(m) == Counter(p)] for p in paires]
    paire = _meilleure_paire(nes_de[0], nes_de[1], ignorer_polarite)
    if paire:
        return _evaluer_paire(recette, paire, ignorer_polarite, intermediaires_prets=True)

    utilises: set[int] = set()
    choisis, manquants, a_synthetiser, possedes = [], [], [], 0
    for p, candidats in zip(paires, nes_de):
        libres = [m for m in candidats if m.emplacement not in utilises]
        if libres:          # intermédiaire déjà né : il couvre ses deux parents
            m = max(libres, key=lambda m: m['niveau'])
            utilises.add(m.emplacement)
            choisis += [m, m]
            possedes += 2
            continue
        pris, absents = _allouer(p, monstres, utilises)
        choisis += pris
        manquants += absents
        possedes += len(p) - len(absents)
        a_synthetiser.append(tuple(p))
    if not possedes:
        return None
    retenus = {m.emplacement: m for m in choisis if m}.values()
    trop_bas = tuple(m for m in retenus if m['niveau'] < NIVEAU_MIN)
    etat = INCOMPLETE if manquants else BIENTOT
    return Analyse(recette, etat, tuple(choisis), tuple(manquants), trop_bas=trop_bas,
                   a_synthetiser=tuple(a_synthetiser), possedes=possedes)


class MonstreAVenir:
    """Enfant d'une synthèse pas encore faite, utilisable comme parent dans
    analyser_recette. Il naît au niveau 1 : on le compte au niveau NIVEAU_MIN
    (il faudra l'y monter) et neutre (sa polarité n'est pas encore tirée)."""
    _numeros = count(1)

    def __init__(self, analyse: Analyse):
        self.analyse = analyse
        self.emplacement = -next(self._numeros)     # distinct des emplacements réels
        # Lignée : les parents de la recette, ou pour une synthèse à 4 les
        # intermédiaires déjà nés (sinon leur espèce n'est pas encore connue).
        if len(analyse.recette.parents) == 2:
            lignee = list(analyse.recette.parents)
        elif analyse.intermediaires_prets:
            lignee = [m['espece'] for m in analyse.monstres]
        else:
            lignee = [0, 0]
        self._champs = {'espece': analyse.recette.resultat, 'niveau': NIVEAU_MIN,
                        'polarite': NEUTRE, 'parent_1': lignee[0], 'parent_2': lignee[1],
                        'surnom': ''}

    def __getitem__(self, cle: str):
        return self._champs[cle]


@dataclass(frozen=True)
class Suite:
    """Synthèse rendue possible par l'enfant d'une synthèse précédente.
    disponibles : monstres restants après cette suite, pour aller plus haut."""
    analyse: Analyse
    enfant: MonstreAVenir
    disponibles: tuple


def consommes(analyse: Analyse) -> set[int]:
    """Emplacements des monstres qu'une synthèse fait disparaître."""
    return {m.emplacement for m in analyse.monstres if m}


def suites(analyse: Analyse, disponibles, ignorer_polarite: bool = True) -> list[Suite]:
    """Synthèses (possibles ou bientôt possibles) qui utilisent l'enfant de
    `analyse`, avec les monstres de `disponibles` qu'elle ne consomme pas."""
    utilises = consommes(analyse)
    enfant = MonstreAVenir(analyse)
    reste = [m for m in disponibles if m.emplacement not in utilises] + [enfant]
    resultat = []
    for recette in dict.fromkeys(bestiaire.sert_a(enfant['espece'])):
        a = analyser_recette(recette, reste, ignorer_polarite)
        if a and a.etat != INCOMPLETE and any(m is enfant for m in a.monstres):
            apres = consommes(a)
            resultat.append(Suite(a, enfant, tuple(m for m in reste
                                                   if m.emplacement not in apres)))
    return sorted(resultat, key=lambda s: ETATS.index(s.analyse.etat))


def analyser(monstres: list[Monstre], ignorer_polarite: bool = True) -> list[Analyse]:
    """Recettes à portée, les plus proches d'abord : possibles, puis bientôt,
    puis incomplètes par nombre croissant d'espèces manquantes."""
    analyses = [a for r in bestiaire.recettes()
                if (a := analyser_recette(r, monstres, ignorer_polarite))]
    return sorted(analyses, key=lambda a: (ETATS.index(a.etat), a.nb_manquants,
                                           -a.possedes / len(a.recette.parents)))
