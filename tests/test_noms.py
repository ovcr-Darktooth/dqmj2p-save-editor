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
