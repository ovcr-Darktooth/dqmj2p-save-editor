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


    def test_supprimer_un_monstre_du_ranch(self):
        s = Sauvegarde(donnee('moitie-jeu.dsv').read_bytes())
        avant = s.monstres()
        ids = [m['id_creation'] for m in avant]
        equipe = s.ids_equipe()
        victime = next(m for m in avant if s.role(m) == 'ranch')
        cid = victime['id_creation']      # après, l'emplacement contient le suivant
        s.supprimer(victime)
        apres = s.monstres()
        attendus = [i for i in ids if i != cid]
        self.assertEqual([m['id_creation'] for m in apres], attendus)
        self.assertEqual([m.emplacement for m in apres], list(range(len(attendus))))
        self.assertEqual(s.monstre(len(attendus)).octets, bytes(F.TAILLE_MONSTRE))
        self.assertEqual(s.ids_equipe(), equipe)
        self.assertTrue(copie_valide(Sauvegarde(s.en_octets()).copie))

    def test_supprimer_un_monstre_d_equipe_ou_de_reserve(self):
        s = Sauvegarde(donnee('moitie-jeu.dsv').read_bytes())
        equipe, reserve = s.composition()
        membre = (reserve or equipe)[0]
        cid = membre['id_creation']
        s.supprimer(membre)
        self.assertNotIn(cid, s.ids_equipe())
        self.assertEqual(sum(1 for c in s.ids_equipe() if c), len(equipe) + len(reserve) - 1)
        relu = Sauvegarde(s.en_octets())
        self.assertEqual(len(relu.monstres()), 24)

    def test_dernier_monstre_d_equipe_protege(self):
        s = Sauvegarde(donnee('moitie-jeu.dsv').read_bytes())
        while len(s.composition()[0]) > 1:
            s.supprimer(s.composition()[0][-1])
        with self.assertRaises(ErreurSauvegarde):
            s.supprimer(s.composition()[0][0])


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


    def test_ecriture_et_contrainte_vue_dressee(self):
        origine = donnee('moitie-jeu.dsv').read_bytes()
        s = Sauvegarde(origine)
        b = s.bibliotheque
        self.assertNotIn(2, b.especes_vues())               # Gluanbulle
        b.marquer_dressee(2)
        self.assertIn(2, b.especes_dressees())
        self.assertIn(2, b.especes_vues())                  # dressée => vue
        b.marquer_vue(1, False)                             # Gluant, dressé
        self.assertNotIn(1, b.especes_dressees() | b.especes_vues())
        b.marquer_attribut(200); b.marquer_competence(200)
        relu = Sauvegarde(s.en_octets()).bibliotheque       # sommes recalculées
        self.assertEqual(relu.especes_dressees(), b.especes_dressees())
        self.assertIn(200, relu.attributs() & relu.competences())
        # Retour en arrière : fichier identique à l'original.
        b.marquer_dressee(2, False); b.marquer_vue(2, False)
        b.marquer_dressee(1)
        b.marquer_attribut(200, False); b.marquer_competence(200, False)
        self.assertEqual(s.en_octets(), origine)

    def test_id_hors_limites_refuse(self):
        b = Sauvegarde.ouvrir(donnee('moitie-jeu.dsv')).bibliotheque
        for ecrire, id_ in ((b.marquer_vue, 0), (b.marquer_vue, 512),
                            (b.marquer_attribut, 256), (b.marquer_competence, -1)):
            with self.assertRaises(ValueError):
                ecrire(id_)


if __name__ == '__main__':
    unittest.main()
