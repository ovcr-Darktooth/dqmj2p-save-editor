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


class Sac(unittest.TestCase):
    # Contenu relevé en jeu (onglet objets ; les armes sont rangées à part).
    OBJETS = {
        'Herbe médicinale': 25, 'Remède puissant': 15, 'Remède spécial': 1,
        "Feuille d'Yggdrasil": 1, 'Graine de Compétence': 5, 'Graine de Vie': 3,
        'Graine de Magie': 1, 'Graine de Défense': 1, "Graine d'Agilité": 2,
        'Ticket de métal': 5, 'Herbe curative': 11, 'Botryche lunaire': 6,
        'Sels de choc': 1, 'Panacée': 1, 'Maxi Isolacto': 1, 'Poudre Décuplo': 1,
        'Simpletiol': 1, 'Crottin de monstre': 3, 'Bout de caillou': 8,
        'Pelotox': 6, 'Eclat de bombe': 6, 'Brisure de bronze': 8,
        "Eclat d'argent": 2, 'Anneau de dresseur': 1, "Clef d'Archéopolis": 1,
        'Médaille mystérieuse': 1, 'Plaque des cimes enneigées': 1,
        'Plaque de la côte': 1,
    }

    def test_contenu_releve_en_jeu(self):
        from dqmj2p_save import noms
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        par_nom = {noms.table('objets')[i]: q for i, q in s.sac.contenu().items()}
        for nom, quantite in self.OBJETS.items():
            self.assertEqual(par_nom.pop(nom), quantite, nom)
        # Le reste : uniquement des armes (ID 112 à 191 environ).
        armes = {i for i in s.sac.contenu() if noms.table('objets')[i] in par_nom}
        self.assertTrue(all(100 <= i < 200 for i in armes), armes)

    def test_modifier_une_quantite(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        s.sac[1] = 99
        self.assertEqual(Sauvegarde(s.en_octets()).sac[1], 99)


class Monstres(unittest.TestCase):
    def test_surnoms_par_defaut_restaures(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        renommes = {m.emplacement: m['surnom'] for m in s.restaurer_surnoms()}
        self.assertEqual(renommes[1], 'Slurpier')          # était « Sl »
        self.assertNotIn(21, renommes)                      # « Nécroman » déjà complet
        relue = Sauvegarde(s.en_octets())
        self.assertEqual(relue.monstre(1)['surnom'], 'Slurpier')
        self.assertFalse(any(m.surnom_par_defaut for m in relue.monstres()))

    def test_surnom_complet_identique_a_celui_du_jeu(self):
        """Phalène géante née d'une synthèse en jeu : le jeu l'a nommée
        « Phalène » suivi d'un espace (8 caractères)."""
        s = Sauvegarde.ouvrir(donnee('apres-test-jeu.dsv'))
        phalene = next(m for m in s.monstres() if m['id_creation'] == 111)
        self.assertEqual(phalene['surnom'], 'Phalène ')
        self.assertEqual(phalene.surnom_complet(), phalene['surnom'])
        self.assertFalse(phalene.surnom_par_defaut)

    def test_surnom_avec_tiret_sur_deux_octets(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        mort_vivant = next(m for m in s.monstres() if m['surnom'] == 'Mort-viv')
        champ = F.CHAMP['surnom']
        self.assertEqual(champ.en_octets('Mort-viv')[:9],
                         mort_vivant.octets[:9])            # tiret = E0 5A

    def test_dupliquer(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        avant = len(s.monstres())
        modele = s.monstre(21)
        copie = s.dupliquer(modele)
        relue = Sauvegarde(s.en_octets())
        self.assertEqual(copie.emplacement, avant)
        self.assertEqual(len(relue.monstres()), avant + 1)
        self.assertEqual(relue.monstre(avant)['id_creation'], 108)
        self.assertEqual(relue.joueur['dernier_id_creation'], 108)
        self.assertEqual(relue.role(relue.monstre(avant)), 'ranch')
        self.assertEqual(relue.monstre(avant).octets[0x18:], modele.octets[0x18:])


class Emplacement(unittest.TestCase):
    def test_valeurs_relevees_en_jeu(self):
        """moitie-jeu : location 57, position -26,10 / 0 / 589,46, sauvegardée
        le mardi 22/09/2026 à 02:56:47 (fichier écrit à 02:56:55)."""
        j = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv')).joueur
        self.assertEqual(j['location'], 57)
        self.assertEqual((j['position_x'], j['position_y'], j['position_z']), (-2610, 0, 58946))
        date = tuple(j[f'sauvegarde_{c}'] for c in
                     ('annee', 'mois', 'jour', 'jour_semaine', 'heure', 'minute', 'seconde'))
        self.assertEqual(date, (26, 9, 22, 2, 2, 56, 47))
