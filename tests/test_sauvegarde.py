"""Tests du cœur. Lancer depuis la racine du dépôt :

    python -m unittest discover tests

Les sauvegardes réelles de tests/donnees/ ne sont pas versionnées (elles
contiennent des données de partie personnelles) : les tests qui en ont besoin
sont sautés si elles manquent.
"""
import tempfile
import unittest
from pathlib import Path

from dqmj2p_save import ErreurSauvegarde, Sauvegarde
from dqmj2p_save import format as F
from dqmj2p_save.sauvegarde import copie_valide

DONNEES = Path(__file__).parent / 'donnees'
REELLES = sorted(DONNEES.glob('*.dsv'))
# Éditées avec l'ancienne chaîne save_converter, qui laissait le résumé
# d'équipe incohérent : elles ne reflètent pas ce qu'écrit le jeu.
EDITEES_HORS_JEU = {'random-edit.dsv', 'random-lvl50.dsv'}
ECRITES_PAR_LE_JEU = [p for p in REELLES if p.name not in EDITEES_HORS_JEU]


def donnee(nom: str) -> Path:
    chemin = DONNEES / nom
    if not chemin.exists():
        raise unittest.SkipTest(f'{chemin} absent')
    return chemin


def octets_differents(a: bytes, b: bytes) -> set[int]:
    return {i for i in range(min(len(a), len(b))) if a[i] != b[i]}


SOMMES = {debut + off + k for debut in F.COPIES
          for off in (F.SOMME_DATA, F.SOMME_ENTETE) for k in range(4)}


class AllerRetour(unittest.TestCase):
    def test_sans_modification_le_fichier_est_identique(self):
        if not REELLES:
            self.skipTest('aucune sauvegarde réelle dans tests/donnees')
        for chemin in REELLES:
            with self.subTest(chemin.name):
                origine = chemin.read_bytes()
                self.assertEqual(Sauvegarde(origine).en_octets(), origine)

    def test_modifier_puis_remettre_redonne_l_original(self):
        origine = donnee('histoire.dsv').read_bytes()
        s = Sauvegarde(origine)
        m = s.monstres()[0]
        niveau = m['niveau']
        m['niveau'] = niveau + 1
        m['niveau'] = niveau
        self.assertEqual(s.en_octets(), origine)


class Edition(unittest.TestCase):
    def test_edition_relue_et_sommes_valides(self):
        origine = donnee('histoire.dsv').read_bytes()
        s = Sauvegarde(origine)
        m = s.monstres()[3]
        m['attaque'] = 999
        m['competence_1_points'] = 50
        sortie = s.en_octets()

        relue = Sauvegarde(sortie).monstre(m.emplacement)
        self.assertEqual(relue['attaque'], 999)
        self.assertEqual(relue['competence_1_points'], 50)
        for debut in F.COPIES:
            self.assertTrue(copie_valide(sortie[debut: debut + F.TAILLE_COPIE]))
        # Hors des deux copies (zone de queue, pied de page), rien ne bouge.
        self.assertEqual(sortie[2 * F.TAILLE_COPIE:], origine[2 * F.TAILLE_COPIE:])

    def test_reproduit_l_edition_niveau_50(self):
        """random-lvl50.dsv = random.dsv dont le monstre 0 a été passé au
        niveau 50 avec l'ancienne chaîne d'outils. On refait la même édition."""
        cible = Sauvegarde.ouvrir(donnee('random-lvl50.dsv'))
        s = Sauvegarde.ouvrir(donnee('random.dsv'))
        for cle in ('pv', 'pm', 'pv_max', 'pm_max', 'attaque', 'defense',
                    'agilite', 'sagesse', 'niveau'):
            s.monstre(0)[cle] = cible.monstre(0)[cle]
        sortie = s.en_octets()

        # Seul écart permis : l'ancienne chaîne ne mettait pas à jour le niveau
        # dans la table compacte d'équipe (0x7C + 6), nous si.
        niveau_equipe = {debut + F.TABLE_EQUIPE + 6 for debut in F.COPIES}
        ecarts = octets_differents(sortie, cible.en_octets())
        self.assertLessEqual(ecarts, niveau_equipe | SOMMES)
        self.assertEqual(sortie[F.TABLE_EQUIPE + 6], 50)

    def test_role_des_monstres(self):
        s = Sauvegarde.ouvrir(donnee('histoire.dsv'))
        roles = {m.emplacement: s.role(m) for m in s.monstres()}
        self.assertEqual(roles[11], 'equipe_1')
        self.assertEqual(roles[21], 'reserve_3')
        self.assertEqual(roles[0], 'ranch')

    def test_valeur_hors_bornes_refusee(self):
        s = Sauvegarde.ouvrir(donnee('histoire.dsv'))
        with self.assertRaises(ValueError):
            s.monstres()[0]['niveau'] = 256
        self.assertFalse(s.modifiee)

    def test_id_de_creation_en_lecture_seule(self):
        s = Sauvegarde.ouvrir(donnee('histoire.dsv'))
        with self.assertRaises(KeyError):
            s.monstres()[0]['id_creation'] = 1


class Fichiers(unittest.TestCase):
    def test_sav_brut_accepte(self):
        origine = donnee('histoire.dsv').read_bytes()[:F.TAILLE_BRUTE]
        self.assertEqual(Sauvegarde(origine).en_octets(), origine)

    def test_fichier_invalide_refuse(self):
        for contenu in (b'', bytes(F.TAILLE_BRUTE), b'\xff' * 100):
            with self.assertRaises(ErreurSauvegarde):
                Sauvegarde(contenu)

    def test_enregistrer_garde_une_copie_de_l_original(self):
        origine = donnee('histoire.dsv').read_bytes()
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / 'partie.dsv'
            chemin.write_bytes(origine)
            s = Sauvegarde.ouvrir(chemin)
            s.monstres()[0]['niveau'] = 42
            bak = s.enregistrer()

            self.assertEqual(bak.read_bytes(), origine)
            self.assertEqual(Sauvegarde.ouvrir(chemin).monstres()[0]['niveau'], 42)
            self.assertFalse(s.modifiee)


class Bibliotheque(unittest.TestCase):
    def test_moitie_jeu_comme_en_jeu(self):
        # Relevé dans la bibliothèque du jeu le 23/09/2026, par famille.
        from collections import Counter
        from dqmj2p_save import bestiaire
        biblio = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv')).bibliotheque
        famille = lambda e: bestiaire.fiche(e).famille
        self.assertEqual(Counter(map(famille, biblio.especes_dressees())),
                         {'Gluant': 7, 'Dragon': 15, 'Nature': 12, 'Bête': 15,
                          'Matière': 14, 'Démon': 8, 'Zombie': 6})
        vues = Counter(map(famille, biblio.especes_vues()))
        self.assertEqual((vues['Gluant'], vues['Dragon'], vues['Démon']), (14, 22, 19))

    def test_dressees_vues_et_possedees(self):
        for chemin in ECRITES_PAR_LE_JEU:
            with self.subTest(chemin.name):
                s = Sauvegarde.ouvrir(chemin)
                dressees = s.bibliotheque.especes_dressees()
                self.assertLessEqual(dressees, s.bibliotheque.especes_vues())
                self.assertLessEqual({m['espece'] for m in s.monstres()}, dressees)

    def test_synthese_d_une_phalene_geante(self):
        # Entre moitie-jeu et apres-test-jeu : espèce 110 synthétisée, avec
        # deux attributs nouveaux et la compétence Bonus Attaque III.
        avant = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv')).bibliotheque
        apres = Sauvegarde.ouvrir(donnee('apres-test-jeu.dsv')).bibliotheque
        self.assertEqual(apres.especes_dressees() - avant.especes_dressees(), {110})
        self.assertEqual(apres.especes_vues() - avant.especes_vues(), {110})
        self.assertEqual(apres.attributs() - avant.attributs(), {12, 189})
        self.assertEqual(apres.competences() - avant.competences(), {144})


if __name__ == '__main__':
    unittest.main()
