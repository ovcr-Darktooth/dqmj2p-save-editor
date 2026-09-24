"""Champs du joueur, texte, et cohérence du résumé de l'écran de chargement.
Valeurs de référence relevées en jeu sur moitie-jeu.dsv."""
import unittest

from dqmj2p_save import ErreurSauvegarde, Sauvegarde, noms, texte
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
        self.assertEqual(noms.carte(j['location']), 'Archéopolis')
        self.assertEqual((j['position_x'], j['position_y'], j['position_z']), (-2610, 0, 58946))
        date = tuple(j[f'sauvegarde_{c}'] for c in
                     ('annee', 'mois', 'jour', 'jour_semaine', 'heure', 'minute', 'seconde'))
        self.assertEqual(date, (26, 9, 22, 2, 2, 56, 47))


class Teleportation(unittest.TestCase):
    def test_points_releves_en_jeu(self):
        """Chaque point reproduit exactement le bloc d'une sauvegarde faite sur
        place par le jeu."""
        for fichier, point in (
                ('apres-test-jeu.dsv', 'Albatros (tablette du ranch)'),
                ('arene.dsv', 'Arène'),
                ('captures/01-004857-carte85.dsv', 'Albatros (sortie)'),
                ('captures/02-005012-carte14.dsv', "L'Arbirynthe"),
                ('captures/03-005036-carte17.dsv', 'Prairia'),
                ('captures/04-005058-carte151.dsv', 'Avablanche'),
                ('captures/05-005120-carte37.dsv', 'Escarpic'),
                ('captures/06-005145-carte47.dsv', 'Engloutîle'),
                ('captures/07-005220-carte57.dsv', 'Archéopolis'),
                ('avablanche-warp.dsv', 'Avablanche (fin de zone, sort)')):
            with self.subTest(point):
                reference = Sauvegarde.ouvrir(donnee(fichier))
                bloc = bytearray(F.POINTS_TELEPORTATION[point])
                releve = bytearray(reference.copie[F.BLOC_POSITION:
                                                   F.BLOC_POSITION + len(bloc)])
                releve[2] = 0                               # points sans intempérie
                self.assertEqual(releve, bloc)
                self.assertEqual(reference.copie[0x86], bloc[0])

    def test_teleporter(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        s.teleporter('Arène')
        relue = Sauvegarde(s.en_octets())
        self.assertEqual(noms.carte(relue.joueur['location']), 'Arène')
        self.assertEqual(relue.joueur['location_precedente'], 57)
        self.assertEqual(relue.copie[0x86], 24)      # résumé de l'écran de chargement
        self.assertEqual(relue.joueur['position_x'], 145777)


class Horloge(unittest.TestCase):
    def test_valeurs_relevees_en_jeu(self):
        """Engloutîle : sauvegarde quelques secondes après la tombée de la nuit,
        puis quelques secondes après le retour du jour."""
        nuit = Sauvegarde.ouvrir(donnee('debut-nuit.dsv')).joueur['horloge']
        jour = Sauvegarde.ouvrir(donnee('debut-jour.dsv')).joueur['horloge']
        self.assertTrue(F.DEBUT_NUIT <= nuit < F.DEBUT_NUIT + 30 * 5)
        self.assertTrue(0 <= jour < 30 * 5)

    def test_indicateur_de_nuit_coherent(self):
        """Le bit de nuit suit l'horloge dans toutes les sauvegardes du jeu, et
        regler_horloge() le tient à jour."""
        octet, bit = F.INDICATEUR_NUIT
        for nom in ('debut-nuit.dsv', 'debut-jour.dsv', 'engloutile-nuit.dsv',
                    'engloutile-brume.dsv'):
            s = Sauvegarde.ouvrir(donnee(nom))
            self.assertEqual(bool(s.copie[octet] & bit), s.joueur['horloge'] >= F.DEBUT_NUIT, nom)
        s = Sauvegarde.ouvrir(donnee('debut-jour.dsv'))
        s.regler_horloge(F.DEBUT_NUIT)
        self.assertTrue(s.copie[octet] & bit)
        s.regler_horloge(0)
        self.assertFalse(s.copie[octet] & bit)
        self.assertEqual(Sauvegarde(s.en_octets()).copie[octet],
                         Sauvegarde.ouvrir(donnee('debut-jour.dsv')).copie[octet])


class Meteo(unittest.TestCase):
    def test_intemperie_relevee_en_jeu(self):
        self.assertEqual(Sauvegarde.ouvrir(donnee('engloutile-brume.dsv')).joueur['intemperie'], 1)
        self.assertEqual(Sauvegarde.ouvrir(donnee('debut-jour.dsv')).joueur['intemperie'], 0)
        pluie = Sauvegarde.ouvrir(donnee('captures/02-005012-carte14.dsv')).joueur
        self.assertEqual((pluie['intemperie'], noms.METEO[pluie['location']]), (1, 'pluie'))

    def test_teleportation_sans_intemperie(self):
        s = Sauvegarde.ouvrir(donnee('engloutile-brume.dsv'))
        s.teleporter("L'Arbirynthe")
        self.assertEqual(s.joueur['intemperie'], 0)



class Iles(unittest.TestCase):
    def test_chapitre_releve_en_jeu(self):
        for nom, chapitre in (('histoire.dsv', 4), ('moitie-jeu.dsv', 7),
                              ('en-avant-rapthorne-2.dsv', 9), ('en-fin-de-jeu.dsv', 10)):
            with self.subTest(nom):
                self.assertEqual(Sauvegarde.ouvrir(donnee(nom)).chapitre, chapitre)

    def test_teleportation_relevee_en_jeu(self):
        fin = Sauvegarde.ouvrir(donnee('en-fin-de-jeu.dsv'))
        milieu = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        debut = Sauvegarde.ouvrir(donnee('random.dsv'))     # randomizer, chapitre 0
        for zone in F.TELEPORTATION:
            with self.subTest(zone):
                self.assertTrue(fin.zone_visitee(zone))
                self.assertEqual(milieu.zone_visitee(zone), zone not in F.ILES_FIN_DE_PARTIE)
                self.assertFalse(debut.zone_visitee(zone))

    def test_bits_distincts(self):
        self.assertEqual(len(set(F.TELEPORTATION.values())), len(F.TELEPORTATION))

    def test_ouvrir_une_ile_sans_changer_de_chapitre(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        avant = bytes(s.copie)
        s.ouvrir_zone('Ténébria')
        self.assertEqual(s.chapitre, 7)
        self.assertTrue(s.zone_visitee('Ténébria'))
        self.assertFalse(s.zone_visitee('Nécropolis'))
        self.assertEqual([i for i in range(len(avant)) if avant[i] != s.copie[i]],
                         [F.TELEPORTATION['Ténébria'][0]])
        s.ouvrir_zone('Ténébria', False)
        self.assertEqual(bytes(s.copie), avant)

    def test_chapitre_ne_touche_qu_un_octet(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        avant = bytes(s.copie)
        s.chapitre = F.CHAPITRE_CARTE['Ténébria']
        self.assertEqual([i for i in range(len(avant)) if avant[i] != s.copie[i]],
                         [F.CHAPITRE])
        self.assertEqual(Sauvegarde(s.en_octets()).chapitre, 9)

    def test_fin_de_jeu_deja_ouverte(self):
        s = Sauvegarde.ouvrir(donnee('en-fin-de-jeu.dsv'))
        for zone in F.TELEPORTATION:
            s.ouvrir_zone(zone)
        self.assertEqual(s.chapitre, 10)
        self.assertFalse(s.modifiee)

    def test_dressage_des_geants(self):
        # Accordé au chapitre 8 (scène de Lionyx) : jamais avant, toujours après.
        for nom, attendu in (('random.dsv', False), ('histoire.dsv', False),
                             ('moitie-jeu.dsv', False), ('en-avant-rapthorne-2.dsv', True),
                             ('en-fin-de-jeu.dsv', True)):
            with self.subTest(nom):
                s = Sauvegarde.ouvrir(donnee(nom))
                self.assertEqual(s.dressage_geants, attendu)
                self.assertEqual(s.geants_utilisables, attendu)

    def test_bit_de_l_autre_editeur_ne_suffit_pas(self):
        # manuel-vide-geants : seul 0x3996 bit 0x01 (géants utilisables)
        # allumé par un autre éditeur ; en jeu, « Dresser » restait grisé.
        s = Sauvegarde.ouvrir(donnee('manuel-vide-geants.sav'))
        self.assertTrue(s.geants_utilisables)
        self.assertFalse(s.dressage_geants)

    def test_dresser_et_utiliser_sont_independants(self):
        # random : chapitre 0, avancement 1. Validé en jeu : Vercule dressé
        # (anneau + avancement), puis visible et équipable une fois 0x3996
        # bit 0x01 allumé.
        s = Sauvegarde.ouvrir(donnee('random.dsv'))
        avant = bytes(s.copie)
        diff = lambda: {i: s.copie[i] for i in range(len(avant)) if avant[i] != s.copie[i]}
        s.dressage_geants = True
        self.assertFalse(s.geants_utilisables)
        self.assertEqual(diff(), {F.AVANCEMENT: 0x0B, 0x39A7: avant[0x39A7] | 0x01})
        s.geants_utilisables = True
        self.assertEqual(diff(), {F.AVANCEMENT: 0x0B, 0x39A7: avant[0x39A7] | 0x01,
                                  0x3996: avant[0x3996] | 0x01})
        s.dressage_geants = False
        self.assertTrue(s.geants_utilisables)
        s.geants_utilisables = False
        self.assertEqual(diff(), {F.AVANCEMENT: 0x0B})      # l'avancement ne recule pas

    def test_dressage_des_geants_valide_en_jeu(self):
        # geant-vercule : partie au chapitre 7 (avancement 9), devant un
        # Vercule, géants déjà utilisables (0x3996 bit 0x01). Validé en jeu :
        # ces deux octets seuls rendent « Dresser » actif.
        s = Sauvegarde.ouvrir(donnee('geant-vercule.dsv'))
        avant = bytes(s.copie)
        self.assertFalse(s.dressage_geants)
        s.dressage_geants = True
        self.assertTrue(s.dressage_geants)
        self.assertEqual({i: s.copie[i] for i in range(len(avant)) if avant[i] != s.copie[i]},
                         {F.AVANCEMENT: 0x0B, 0x39A7: 0xC1})
        # Décocher n'éteint que l'anneau : l'avancement ne recule pas.
        s.dressage_geants = False
        self.assertFalse(s.dressage_geants)
        self.assertEqual(s.copie[F.AVANCEMENT], 0x0B)
        self.assertEqual(s.copie[0x39A7], 0xC0)

    def test_avancement_deja_suffisant(self):
        s = Sauvegarde.ouvrir(donnee('en-fin-de-jeu.dsv'))
        s.dressage_geants = False
        s.dressage_geants = True
        self.assertEqual(s.en_octets(), donnee('en-fin-de-jeu.dsv').read_bytes())

    def test_histoire_coherente_dans_les_sauvegardes_du_jeu(self):
        for chemin in ECRITES_PAR_LE_JEU:
            with self.subTest(chemin.name):
                self.assertTrue(Sauvegarde.ouvrir(chemin).histoire_coherente())

    def test_apres_le_championnat(self):
        # Partie principale juste après le championnat des dresseurs :
        # avancement 9 -> 0x0B, toujours au chapitre 7, anneau pas évolué.
        s = Sauvegarde.ouvrir(donnee('apres-championnat.dsv'))
        self.assertEqual((s.chapitre, s.avancement), (7, 0x0B))
        self.assertTrue(s.histoire_coherente())
        self.assertFalse(s.dressage_geants)

    def test_scene_de_lionyx(self):
        # Partie principale juste avant et juste après la scène où Lionyx
        # fait évoluer l'anneau : les deux bits des géants s'allument, rien
        # d'autre ne change pour les géants, chapitre 7 et avancement 0x0B.
        avant = Sauvegarde.ouvrir(donnee('avant-lionyx.dsv'))
        apres = Sauvegarde.ouvrir(donnee('apres-lionyx.dsv'))
        self.assertFalse(avant.dressage_geants or avant.geants_utilisables)
        self.assertTrue(apres.dressage_geants and apres.geants_utilisables)
        for s in (avant, apres):
            self.assertEqual((s.chapitre, s.avancement), (7, 0x0B))
        self.assertEqual(apres.copie[0x39A7], avant.copie[0x39A7] | 0x01)
        self.assertEqual(apres.copie[0x3996], avant.copie[0x3996] | 0x01)
        # L'éditeur, sur la sauvegarde d'avant, écrit les mêmes octets.
        avant.dressage_geants = True
        avant.geants_utilisables = True
        for octet in (0x39A7, 0x3996, F.AVANCEMENT):
            self.assertEqual(avant.copie[octet], apres.copie[octet])

    def test_incoherences_signalees(self):
        s = Sauvegarde.ouvrir(donnee('random.dsv'))          # chapitre 0, avancement 1
        s.dressage_geants = True                             # avancement 0B
        self.assertFalse(s.histoire_coherente())
        s.chapitre = 8
        self.assertTrue(s.histoire_coherente())
        s.chapitre = 10                                      # îles de fin sans l'histoire
        self.assertFalse(s.histoire_coherente())
        m = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))      # chapitre 7, avancement 7
        m.chapitre = 9
        self.assertFalse(m.histoire_coherente())

    def test_points_des_zones(self):
        for zone in F.TELEPORTATION:
            if zone in F.POINTS_TELEPORTATION:
                with self.subTest(zone):
                    self.assertEqual(noms.carte(F.POINTS_TELEPORTATION[zone][0]), zone)


class Boutons(unittest.TestCase):
    def test_releves_en_jeu(self):
        self.assertEqual(Sauvegarde.ouvrir(donnee('random.dsv')).boutons,
                         [*F.ORDRE_BOUTONS_NEUF, F.BOUTON_VIDE, F.BOUTON_VIDE])
        fin = Sauvegarde.ouvrir(donnee('en-fin-de-jeu.dsv')).boutons
        self.assertEqual(sorted(fin), list(range(12)))
        self.assertTrue(all(b in noms.BOUTONS for b in fin))

    def test_echange_ne_touche_que_la_grille(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        avant = bytes(s.copie)
        s.echanger_boutons(0, 11)                   # Objets vers une case vide
        self.assertEqual(s.boutons[11], 0x01)
        self.assertEqual(s.boutons[0], F.BOUTON_VIDE)
        self.assertEqual([i for i in range(len(avant)) if avant[i] != s.copie[i]],
                         [F.BOUTONS, F.BOUTONS + 11])

    def test_essais_valides_en_jeu(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        s.ranger_boutons(list(bytes.fromhex('08090b0705' '7f' '0302' '0001' '7f' '04')))
        self.assertEqual(s.boutons[5], F.BOUTON_VIDE)

    def test_on_ne_change_pas_les_boutons(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        cases = s.boutons
        cases[10] = 0x06                            # Soigner tous, pas encore obtenu
        with self.assertRaises(ErreurSauvegarde):
            s.ranger_boutons(cases)
        self.assertFalse(s.modifiee)

    def test_ordre_du_jeu(self):
        fin = Sauvegarde.ouvrir(donnee('en-fin-de-jeu.dsv'))
        self.assertEqual(F.ordre_boutons_du_jeu(fin.boutons),
                         [*F.ORDRE_BOUTONS_NEUF, 0x06, 0x0A])
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        self.assertEqual(F.ordre_boutons_du_jeu(s.boutons), s.boutons)


class Composition(unittest.TestCase):
    def test_lecture(self):
        s = Sauvegarde.ouvrir(donnee('en-avant-boss-final.dsv'))
        equipe, reserve = s.composition()
        self.assertEqual([s.taille(m) for m in equipe], [3])       # Rhapthorne II
        self.assertEqual(len(reserve), 3)

    def test_echange_et_resume(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        equipe, reserve = s.composition()
        # Tyrantosaure (réserve) prend la place de Magmasse, qui part au ranch
        s.definir_composition([equipe[0], equipe[1], reserve[0]], reserve[1:])
        relue = Sauvegarde(s.en_octets())
        e2, r2 = relue.composition()
        self.assertEqual([m['id_creation'] for m in e2],
                         [equipe[0]['id_creation'], equipe[1]['id_creation'], reserve[0]['id_creation']])
        self.assertEqual(len(r2), 1)
        self.assertEqual(relue.role(relue.monstre(equipe[2].emplacement)), 'ranch')
        self.assertEqual(relue.copie[F.TABLE_EQUIPE + 4], reserve[0]['espece'] & 0xFF)
        self.assertEqual(relue.copie[F.TAILLE_EQUIPE], 3)

    def test_tassement_et_case_vide(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        equipe, reserve = s.composition()
        s.definir_composition([equipe[2]], [])
        relue = Sauvegarde(s.en_octets())
        self.assertEqual(relue.ids_equipe(), [equipe[2]['id_creation'], 0, 0, 0, 0, 0])
        self.assertEqual(relue.copie[F.TAILLE_EQUIPE], 1)
        self.assertEqual(bytes(relue.copie[F.RESUME_SURNOMS + 20: F.RESUME_SURNOMS + 22]),
                         F.SURNOM_VIDE)

    def test_refus(self):
        from dqmj2p_save import ErreurSauvegarde
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        equipe, reserve = s.composition()
        grand = next(m for m in s.monstres() if s.taille(m) == 2)   # Sanglinaire
        with self.assertRaises(ErreurSauvegarde):
            s.definir_composition([], reserve)
        with self.assertRaises(ErreurSauvegarde):
            s.definir_composition(equipe[:2] + [grand], [])          # 1 + 1 + 2 > 3
        with self.assertRaises(ErreurSauvegarde):
            s.definir_composition(equipe, [equipe[0]])
        self.assertFalse(s.modifiee)

    def _noms(self, s):
        E = noms.table('especes')
        e, r = s.composition()
        return [E[m['espece']] for m in e], [E[m['espece']] for m in r]

    def _par_nom(self, s, nom):
        E = noms.table('especes')
        return next(m for m in s.monstres() if E[m['espece']] == nom)

    def test_grand_monstre_echange_plusieurs_cases(self):
        """Cas signalé : Sanglinaire (taille 2) déposé sur Dingodrag. Il couvre
        les cases 2 et 3 : Dingodrag et Magmasse partent ensemble en réserve."""
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        s.deplacer(self._par_nom(s, 'Sanglinaire'), 'equipe', 1)
        self.assertEqual(self._noms(s), (['Nécromante', 'Sanglinaire'],
                                         ['Tyrantosaure', 'Dingodrag', 'Magmasse']))

    def test_echange_dans_la_meme_colonne(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        s.deplacer(self._par_nom(s, 'Nécromante'), 'equipe', 2)
        self.assertEqual(self._noms(s)[0], ['Magmasse', 'Dingodrag', 'Nécromante'])

    def test_depuis_le_ranch_et_case_libre(self):
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        s.deplacer(self._par_nom(s, 'Condor infernal'), 'equipe', 0)   # Nécromante -> ranch
        self.assertEqual(self._noms(s)[0], ['Condor infernal', 'Dingodrag', 'Magmasse'])
        self.assertEqual(s.role(self._par_nom(s, 'Nécromante')), 'ranch')
        s.definir_composition(s.composition()[0], s.composition()[1][:1])  # réserve : 1 place prise
        s.deplacer(self._par_nom(s, 'Slurpierre'), 'reserve', 2)          # case libre -> en fin
        self.assertEqual(self._noms(s)[1], ['Tyrantosaure', 'Slurpierre'])

    def test_grand_monstre_refuse_si_la_place_manque(self):
        from dqmj2p_save import ErreurSauvegarde
        s = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv'))
        with self.assertRaises(ErreurSauvegarde):     # Sanglinaire irait en équipe (4 places)
            s.deplacer(self._par_nom(s, 'Dingodrag'), 'reserve', 1)
        self.assertFalse(s.modifiee)
