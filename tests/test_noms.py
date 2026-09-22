import unittest

from dqmj2p_save import format as F
from dqmj2p_save import noms


class Noms(unittest.TestCase):
    def test_tables_couvrent_les_ids_possibles(self):
        self.assertEqual(len(noms.table('competences')), 256)   # ID sur u8
        self.assertGreater(len(noms.table('especes')), 500)

    def test_noms_connus(self):
        especes = noms.table('especes')
        self.assertEqual(especes[49], 'Komodor')
        self.assertEqual(especes[0], noms.AUCUN)
        self.assertEqual(especes[30], noms.INUTILISE)
        self.assertEqual(especes[9999], '#9999')

    def test_chaque_champ_nomme_a_sa_table(self):
        for champ in F.CHAMPS_MONSTRE:
            if champ.noms:
                with self.subTest(champ.cle):
                    self.assertTrue(len(noms.table(champ.noms)))


class Bestiaire(unittest.TestCase):
    def test_fiches(self):
        from dqmj2p_save import bestiaire
        gluant = bestiaire.fiche(1)
        self.assertEqual((gluant.rang, gluant.famille, gluant.taille), ('F', 'Gluant', 1))
        self.assertEqual(bestiaire.fiche(31).taille, 3)             # Famille gluant
        self.assertEqual(bestiaire.fiche(9999), bestiaire.Fiche(None, None, None))

    def test_recettes(self):
        from dqmj2p_save import bestiaire
        self.assertEqual(bestiaire.obtenu_par(110), [])              # Phalène géante
        self.assertIn(bestiaire.Recette(379, (1, 17), False), bestiaire.obtenu_par(379))
        self.assertTrue(all(1 in r.parents for r in bestiaire.sert_a(1)))
        # Toute espèce citée dans une recette a un nom
        from dqmj2p_save.bestiaire import _donnees
        for r in _donnees()[1]:
            for espece in (r.resultat, *r.parents):
                self.assertNotIn(noms.table('especes')[espece], (noms.INUTILISE, noms.AUCUN))
