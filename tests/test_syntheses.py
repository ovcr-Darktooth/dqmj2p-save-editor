"""Tests de l'analyse des synthèses à portée (dqmj2p_save/syntheses.py), sur
des sauvegardes synthétiques."""
import struct
import unittest

from dqmj2p_save import Sauvegarde, bestiaire, syntheses
from dqmj2p_save import format as F
from dqmj2p_save.sauvegarde import calculer_sommes
from dqmj2p_save.syntheses import BIENTOT, INCOMPLETE, NEGATIF, NEUTRE, POSITIF, POSSIBLE

# Recettes de bestiaire.json utilisées ici : Gluant + Gluante -> Gluant
# moucheté ; Gluant moucheté × 4 -> Roi gluant moucheté.
GLUANT, GLUANTE, GLUANT_MOUCHETE, ROI_GLUANT_MOUCHETE = 1, 17, 379, 29


def sauvegarde(*monstres: dict) -> Sauvegarde:
    """Monstres : dict(espece, niveau=10, polarite=POSITIF, parents=(0, 0))."""
    copie = bytearray(F.TAILLE_COPIE)
    copie[:4] = F.MAGIC
    for emplacement, m in enumerate(monstres):
        base = F.DEBUT_MONSTRES + emplacement * F.TAILLE_MONSTRE
        F.CHAMP['id_creation'].ecrire(copie, base, emplacement + 1)
        F.CHAMP['espece'].ecrire(copie, base, m['espece'])
        F.CHAMP['niveau'].ecrire(copie, base, m.get('niveau', 10))
        F.CHAMP['polarite'].ecrire(copie, base, m.get('polarite', POSITIF))
        p1, p2 = m.get('parents', (0, 0))
        F.CHAMP['parent_1'].ecrire(copie, base, p1)
        F.CHAMP['parent_2'].ecrire(copie, base, p2)
    struct.pack_into('<I', copie, F.EQUIPE_IDS, 1)
    struct.pack_into('<2I', copie, F.SOMME_DATA, *calculer_sommes(copie))
    brut = bytearray(F.TAILLE_BRUTE)
    for debut in F.COPIES:
        brut[debut: debut + F.TAILLE_COPIE] = copie
    return Sauvegarde(bytes(brut))


def recette(resultat: int, parents: tuple[int, ...]) -> bestiaire.Recette:
    return next(r for r in bestiaire.obtenu_par(resultat) if r.parents == parents)


def analyse(s: Sauvegarde, r: bestiaire.Recette, **options):
    return syntheses.analyser_recette(r, s.monstres(), **options)


class DeuxParents(unittest.TestCase):
    R = property(lambda self: recette(GLUANT_MOUCHETE, (GLUANT, GLUANTE)))

    def test_possible(self):
        s = sauvegarde({'espece': GLUANT}, {'espece': GLUANTE})
        a = analyse(s, self.R)
        self.assertEqual(a.etat, POSSIBLE)
        self.assertEqual([m['espece'] for m in a.monstres], [GLUANT, GLUANTE])

    def test_niveau_trop_bas(self):
        s = sauvegarde({'espece': GLUANT, 'niveau': 7}, {'espece': GLUANTE})
        a = analyse(s, self.R)
        self.assertEqual(a.etat, BIENTOT)
        self.assertEqual([m['niveau'] for m in a.trop_bas], [7])

    def test_prend_le_monstre_le_plus_avance(self):
        s = sauvegarde({'espece': GLUANT, 'niveau': 7}, {'espece': GLUANT, 'niveau': 12},
                       {'espece': GLUANTE})
        self.assertEqual(analyse(s, self.R).etat, POSSIBLE)

    def test_polarite_ignoree_par_defaut(self):
        s = sauvegarde({'espece': GLUANT}, {'espece': GLUANTE})
        self.assertEqual(analyse(s, self.R).etat, POSSIBLE)
        a = analyse(s, self.R, ignorer_polarite=False)
        self.assertEqual(a.etat, BIENTOT)
        self.assertTrue(a.meme_polarite)

    def test_polarites_opposees_ou_neutre(self):
        for autre in (NEGATIF, NEUTRE):
            s = sauvegarde({'espece': GLUANT}, {'espece': GLUANTE, 'polarite': autre})
            self.assertEqual(analyse(s, self.R, ignorer_polarite=False).etat, POSSIBLE)

    def test_parent_manquant(self):
        a = analyse(sauvegarde({'espece': GLUANT}), self.R)
        self.assertEqual(a.etat, INCOMPLETE)
        self.assertEqual(a.manquants, (GLUANTE,))

    def test_aucun_parent(self):
        self.assertIsNone(analyse(sauvegarde({'espece': 48}), self.R))

    def test_un_monstre_ne_sert_pas_deux_fois(self):
        r = next(r for r in bestiaire.recettes()
                 if len(r.parents) == 2 and r.parents[0] == r.parents[1])
        a = analyse(sauvegarde({'espece': r.parents[0]}), r)
        self.assertEqual(a.etat, INCOMPLETE)
        self.assertEqual(a.manquants, (r.parents[0],))


class QuatreParents(unittest.TestCase):
    R = property(lambda self: recette(ROI_GLUANT_MOUCHETE, (GLUANT_MOUCHETE,) * 4))

    def test_intermediaires_prets(self):
        # Deux monstres nés chacun de deux Gluants B : la synthèse est possible,
        # quelle que soit leur espèce.
        s = sauvegarde({'espece': 48, 'parents': (GLUANT_MOUCHETE, GLUANT_MOUCHETE)},
                       {'espece': 49, 'parents': (GLUANT_MOUCHETE, GLUANT_MOUCHETE)})
        a = analyse(s, self.R)
        self.assertEqual(a.etat, POSSIBLE)
        self.assertTrue(a.intermediaires_prets)

    def test_quatre_parents_a_synthetiser(self):
        s = sauvegarde(*[{'espece': GLUANT_MOUCHETE}] * 4)
        a = analyse(s, self.R)
        self.assertEqual(a.etat, BIENTOT)
        self.assertEqual(a.a_synthetiser, ((GLUANT_MOUCHETE, GLUANT_MOUCHETE),) * 2)

    def test_un_intermediaire_et_deux_parents(self):
        s = sauvegarde({'espece': 48, 'parents': (GLUANT_MOUCHETE, GLUANT_MOUCHETE)},
                       {'espece': GLUANT_MOUCHETE}, {'espece': GLUANT_MOUCHETE})
        a = analyse(s, self.R)
        self.assertEqual(a.etat, BIENTOT)
        self.assertEqual(a.a_synthetiser, ((GLUANT_MOUCHETE, GLUANT_MOUCHETE),))

    def test_il_en_manque(self):
        s = sauvegarde(*[{'espece': GLUANT_MOUCHETE}] * 3)
        a = analyse(s, self.R)
        self.assertEqual(a.etat, INCOMPLETE)
        self.assertEqual(a.manquants, (GLUANT_MOUCHETE,))
        self.assertEqual(a.possedes, 3)


class Tri(unittest.TestCase):
    def test_les_plus_proches_d_abord(self):
        s = sauvegarde({'espece': GLUANT}, {'espece': GLUANTE, 'niveau': 5},
                       {'espece': GLUANT_MOUCHETE})
        etats = [a.etat for a in syntheses.analyser(s.monstres())]
        self.assertEqual(etats, sorted(etats, key=syntheses.ETATS.index))
        self.assertIn(BIENTOT, etats)



class Onglet(unittest.TestCase):
    """Onglet Synthèses de l'éditeur, sans écran."""

    @classmethod
    def setUpClass(cls):
        import os
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError:
            raise unittest.SkipTest('PySide6 absent')
        cls.app = QApplication.instance() or QApplication([])

    def test_polarite_ignoree_par_defaut(self):
        from editeur.syntheses import PageSyntheses
        page = PageSyntheses()
        self.assertTrue(page.polarite.isChecked())
        s = sauvegarde({'espece': GLUANT}, {'espece': GLUANTE})
        page.afficher(s)
        self.assertTrue(page.resume.text().startswith('1 '))
        page.polarite.setChecked(False)          # même polarité : plus possible
        self.assertTrue(page.resume.text().startswith('0 '))


if __name__ == '__main__':
    unittest.main()
