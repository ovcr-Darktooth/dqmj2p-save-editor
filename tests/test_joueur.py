"""Champs du joueur, texte, et cohérence du résumé de l'écran de chargement.
Valeurs de référence relevées en jeu sur moitie-jeu.dsv."""
import unittest

from dqmj2p_save import Sauvegarde, texte
from dqmj2p_save import format as F

from test_sauvegarde import ECRITES_PAR_LE_JEU, donnee


class Joueur(unittest.TestCase):
    def test_valeurs_relevees_en_jeu(self):
        j = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv')).joueur
        self.assertEqual(j['nom'], 'BKK')
        self.assertEqual(j['temps_jeu'] // F.IMAGES_PAR_SECONDE, 13 * 3600 + 7 * 60 + 7)
        self.assertEqual((j['or'], j['banque']), (2601, 11856))
        self.assertEqual((j['victoires'], j['dressages'], j['syntheses']), (245, 65, 41))

    def test_nom_et_temps_ecrits_aux_deux_endroits(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        s.joueur['nom'] = 'Élodie'
        s.joueur['temps_jeu'] = 123456
        relue = Sauvegarde(s.en_octets())
        for champ in (F.CHAMP_JOUEUR['nom'], F.CHAMP_JOUEUR['temps_jeu']):
            self.assertEqual(relue.copie[champ.offset: champ.offset + 4],
                             relue.copie[champ.miroir: champ.miroir + 4])
        self.assertEqual(relue.joueur['nom'], 'Élodie')

    def test_surnom_d_equipe_recopie_dans_le_resume(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        chef = next(m for m in s.monstres() if s.role(m) == 'equipe_1')
        chef['surnom'] = 'Bobo'
        relue = Sauvegarde(s.en_octets())
        self.assertEqual(texte.decoder(relue.copie[F.RESUME_SURNOMS: F.RESUME_SURNOMS + 20]),
                         'Bobo')

    def test_resynchroniser_le_resume_ne_change_rien(self):
        """Le résumé recalculé doit être celui que le jeu avait écrit."""
        if not ECRITES_PAR_LE_JEU:
            self.skipTest('aucune sauvegarde écrite par le jeu dans tests/donnees')
        for chemin in ECRITES_PAR_LE_JEU:
            with self.subTest(chemin.name):
                origine = chemin.read_bytes()
                s = Sauvegarde(origine)
                s.modifiee = True
                self.assertEqual(s.en_octets(), origine)


class Texte(unittest.TestCase):
    def test_aller_retour(self):
        for mot in ('BKK', 'Nécroman', 'Œuf 12', 'スライム'):
            self.assertEqual(texte.decoder(texte.encoder(mot, 20)), mot)

    def test_fin_de_texte_et_residu(self):
        self.assertEqual(texte.decoder(bytes.fromhex('0e353b2ee31b1f5d3c2b')), 'Bouh')
        self.assertEqual(texte.decoder(bytes.fromhex('133200272d2b')), 'Gl')

    def test_refus(self):
        with self.assertRaises(ValueError):
            texte.encoder('Neuf lettres', 20)
        with self.assertRaises(ValueError):
            texte.encoder('a#b', 20)
