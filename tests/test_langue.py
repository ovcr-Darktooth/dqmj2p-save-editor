"""Tests du choix de langue : tables de noms du patch anglais, catalogue de
l'interface et surnoms par défaut raccord avec le patch choisi.

Les tests de l'interface demandent PySide6 (sautés sinon) et tournent sans
écran (QT_QPA_PLATFORM=offscreen).
"""
import ast
import os
import string
import struct
import tempfile
import unittest
from pathlib import Path

from dqmj2p_save import ErreurSauvegarde, Sauvegarde, bestiaire, langue, noms
from dqmj2p_save import format as F
from dqmj2p_save import texte
from dqmj2p_save.sauvegarde import calculer_sommes
from dqmj2p_save.traduction_en import TEXTES

RACINE = Path(__file__).resolve().parents[1]
TABLES = ('especes', 'competences', 'objets', 'objets_aide', 'attributs', 'attributs_aide')


class EnAnglais(unittest.TestCase):
    """Passe en anglais le temps d'un test."""

    def setUp(self):
        self.addCleanup(langue.choisir, langue.courante())
        langue.choisir('en')


def sauvegarde_synthetique(monstres: list[tuple[int, str]]) -> bytes:
    """Sauvegarde .sav minimale et valide : les monstres (espèce, surnom) dans
    les premiers emplacements, le premier seul en équipe."""
    copie = bytearray(F.TAILLE_COPIE)
    copie[:4] = F.MAGIC
    for emplacement, (espece, surnom) in enumerate(monstres):
        base = F.DEBUT_MONSTRES + emplacement * F.TAILLE_MONSTRE
        F.CHAMP['id_creation'].ecrire(copie, base, emplacement + 1)
        F.CHAMP['espece'].ecrire(copie, base, espece)
        F.CHAMP['niveau'].ecrire(copie, base, 1)
        F.CHAMP['surnom'].ecrire(copie, base, surnom)
    F.CHAMP_JOUEUR['dernier_id_creation'].ecrire(copie, 0, len(monstres))
    struct.pack_into('<I', copie, F.EQUIPE_IDS, 1)
    struct.pack_into('<2I', copie, F.SOMME_DATA, *calculer_sommes(copie))
    brut = bytearray(F.TAILLE_BRUTE)
    for debut in F.COPIES:
        brut[debut: debut + F.TAILLE_COPIE] = copie
    return bytes(brut)


class TablesAnglaises(unittest.TestCase):
    def test_alignees_sur_les_tables_francaises(self):
        # Même ID, même entrée : une ligne décalée donnerait le mauvais nom.
        for nom in TABLES:
            with self.subTest(nom):
                fr, en = noms.table(nom, 'fr'), noms.table(nom, 'en')
                self.assertEqual(len(fr), len(en))
                self.assertEqual([i for i in range(len(fr)) if fr.inutilise(i)],
                                 [i for i in range(len(en)) if en.inutilise(i)])

    def test_noms_connus(self):
        especes = noms.table('especes', 'en')
        self.assertEqual(especes[1], 'Slime')
        self.assertEqual(especes[49], 'Komodo')
        self.assertEqual(especes[0], '(none)')
        self.assertEqual(especes[30], '(unused)')
        self.assertTrue(especes.inutilise(30))
        self.assertEqual(noms.aide_attribut(1, 'en'), 'Doubles the chance of evading\n'
                                                      'enemy attacks.')

    def test_noms_du_patch_ecrivables(self):
        # Le surnom par défaut d'un monstre est son nom d'espèce : il doit
        # pouvoir s'écrire avec la police du jeu.
        for i, nom in noms.table('especes', 'en').choix()[1:]:
            if not noms.table('especes', 'en').inutilise(i):
                with self.subTest(nom):
                    self.assertEqual(texte.caracteres_invalides(nom[:texte.LONGUEUR_MAX]), '')


class LangueCourante(EnAnglais):
    def test_table_suit_la_langue(self):
        self.assertEqual(noms.table('especes')[1], 'Slime')
        langue.choisir('fr')
        self.assertEqual(noms.table('especes')[1], 'Gluant')

    def test_lieux_et_erreurs(self):
        self.assertEqual(noms.carte(57), 'Bemusoleum')
        self.assertEqual(noms.carte(999), 'unknown place')
        with self.assertRaisesRegex(ErreurSauvegarde, 'neither a raw .sav'):
            Sauvegarde(b'')
        with self.assertRaisesRegex(ValueError, 'characters at most'):
            texte.encoder('Beaucoup trop long', 20)

    def test_nombres(self):
        self.assertEqual(langue.decimal(1.5, 1), '1.5')
        langue.choisir('fr')
        self.assertEqual(langue.decimal(1.5, 1), '1,5')

    def test_langue_inconnue(self):
        with self.assertRaises(ValueError):
            langue.choisir('de')


class SurnomsParDefaut(EnAnglais):
    """Le jeu abrège le nom de l'espèce dans la langue du patch : l'éditeur
    doit comparer et compléter avec les noms de cette langue."""

    def test_surnoms_du_patch_anglais(self):
        # Slime (1) capturé « Sli », Komodo (49) renommé « Gluant ».
        s = Sauvegarde(sauvegarde_synthetique([(1, 'Sli'), (49, 'Gluant')]))
        slime, komodo = s.monstres()
        self.assertTrue(slime.surnom_par_defaut)
        self.assertFalse(komodo.surnom_par_defaut)
        self.assertEqual([m.emplacement for m in s.restaurer_surnoms()], [0])
        self.assertEqual(slime['surnom'], 'Slime')

    def test_surnoms_du_patch_francais(self):
        langue.choisir('fr')
        s = Sauvegarde(sauvegarde_synthetique([(1, 'Glu'), (1, 'Sli')]))
        s.restaurer_surnoms()
        self.assertEqual([m['surnom'] for m in s.monstres()], ['Gluant', 'Sli'])


def _textes_du_code() -> set[str]:
    """Textes littéraux passés à tr() dans le cœur et l'éditeur."""
    textes = set()
    for dossier in ('dqmj2p_save', 'editeur'):
        for fichier in (RACINE / dossier).glob('*.py'):
            for noeud in ast.walk(ast.parse(fichier.read_text(encoding='utf-8'))):
                if (isinstance(noeud, ast.Call) and getattr(noeud.func, 'id', None) == 'tr'
                        and noeud.args and isinstance(noeud.args[0], ast.Constant)):
                    textes.add(noeud.args[0].value)
    return textes


def _constantes_traduites() -> set[str]:
    """Textes rangés dans des tables et traduits à l'affichage."""
    textes = {noms.AUCUN, noms.INUTILISE, 'lieu inconnu', *noms.CARTES.values(),
              *noms.METEO.values(), *F.POINTS_TELEPORTATION,
              *(c.libelle for c in F.CHAMPS_MONSTRE + F.CHAMPS_JOUEUR)}
    textes |= {bestiaire.fiche(i).famille for i in range(F.NB_BITS_ESPECES)} - {None}
    return textes


def _constantes_editeur() -> set[str]:
    from editeur import bibliotheque, fenetre, fiche, joueur, synthese
    return {fenetre.TITRE, fenetre.FILTRE, fenetre.FILTRE_ROM, *fenetre.LIBELLES_ROLES.values(),
            *fenetre.COLONNES, *fiche.ONGLETS, *joueur.JOURS,
            bibliotheque.FAMILLE_INCONNUE, *bibliotheque.ETATS,
            *bibliotheque.PageMonstres.COLONNES, 'Attribut', 'Attributs', 'Compétences',
            'Équipe', 'Réserve', 'Obtenu par', 'Sert à créer',
            synthese.AUCUNE_RECETTE, synthese.AUCUN_USAGE}


def _champs(modele: str) -> set[str]:
    return {nom for _, nom, _, _ in string.Formatter().parse(modele) if nom}


class Catalogue(unittest.TestCase):
    def verifier(self, textes: set[str]) -> None:
        manquants = sorted(textes - TEXTES.keys())
        self.assertEqual(manquants, [], 'textes sans traduction anglaise')

    def test_textes_du_code_traduits(self):
        self.verifier(_textes_du_code() | _constantes_traduites())

    def test_textes_de_l_editeur_traduits(self):
        try:
            self.verifier(_constantes_editeur())
        except ImportError:
            self.skipTest('PySide6 absent')

    def test_memes_champs(self):
        for francais, anglais in TEXTES.items():
            with self.subTest(francais):
                self.assertEqual(_champs(francais), _champs(anglais))

    def test_raccourcis_clavier(self):
        # Un « & » perdu ou ajouté change le comportement du menu.
        for francais, anglais in TEXTES.items():
            with self.subTest(francais):
                self.assertEqual(francais.count('&'), anglais.count('&'))


class Interface(unittest.TestCase):
    """Fenêtre construite pour de bon, sans écran."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError:
            raise unittest.SkipTest('PySide6 absent')
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from PySide6.QtCore import QSettings
        from editeur.fenetre import Fenetre
        self.addCleanup(langue.choisir, langue.courante())
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        self.reglages = QSettings(str(Path(dossier.name) / 'reglages.ini'), QSettings.IniFormat)
        self.chemin = Path(dossier.name) / 'partie.sav'
        self.chemin.write_bytes(sauvegarde_synthetique([(1, 'Sli'), (49, 'Komo')]))
        self.Fenetre = Fenetre

    def tearDown(self):
        from editeur.fenetre import Fenetre
        if Fenetre.active:
            Fenetre.active._remplacee = True        # pas de question à la fermeture
            Fenetre.active.close()
            Fenetre.active = None

    def test_langue_enregistree(self):
        self.reglages.setValue('langue', 'en')
        fenetre = self.Fenetre(self.reglages)
        fenetre.ouvrir(self.chemin)
        self.assertEqual(langue.courante(), 'en')
        self.assertEqual(fenetre.onglets.tabText(3), 'Library')
        self.assertEqual(fenetre.liste.item(0, 3).text(), 'Slime')
        self.assertEqual(fenetre.liste.item(0, 1).text(), 'Party 1')

    def test_changer_de_langue_garde_les_modifications(self):
        self.reglages.setValue('langue', 'fr')
        fenetre = self.Fenetre(self.reglages)
        fenetre.ouvrir(self.chemin)
        self.assertEqual(fenetre.liste.item(0, 3).text(), 'Gluant')
        fenetre.sauvegarde.joueur['or'] = 1234
        fenetre.onglets.setCurrentIndex(2)
        fenetre._changer_langue('en')
        nouvelle = self.Fenetre.active
        self.assertIsNot(nouvelle, fenetre)
        self.assertEqual(self.reglages.value('langue'), 'en')
        self.assertIs(nouvelle.sauvegarde, fenetre.sauvegarde)
        self.assertTrue(nouvelle.sauvegarde.modifiee)
        self.assertEqual(nouvelle.sauvegarde.joueur['or'], 1234)
        self.assertEqual(nouvelle.onglets.currentIndex(), 2)
        self.assertEqual(nouvelle.liste.item(0, 3).text(), 'Slime')
        self.assertTrue(nouvelle.windowTitle().endswith('DQMJ2P Save Editor'))

    def test_filtres_de_la_bibliotheque(self):
        self.reglages.setValue('langue', 'en')
        fenetre = self.Fenetre(self.reglages)
        fenetre.ouvrir(self.chemin)
        page = fenetre.page_bibliotheque.monstres
        page.famille.setCurrentIndex(page.famille.findData('Gluant'))
        self.assertEqual(page.famille.currentText(), 'Slime')
        visibles = [page._id(l) for l in range(page.table.rowCount())
                    if not page.table.isRowHidden(l)]
        self.assertIn(1, visibles)
        self.assertTrue(all(bestiaire.fiche(i).famille == 'Gluant' for i in visibles))
        page.etat.setCurrentIndex(page.etat.findText('Never seen'))
        self.assertTrue(page.compteur.text().startswith('0 species seen'))

    def test_teleportation_par_cle(self):
        self.reglages.setValue('langue', 'en')
        fenetre = self.Fenetre(self.reglages)
        fenetre.ouvrir(self.chemin)
        points = fenetre.page_joueur.points
        points.setCurrentIndex(points.findText('Bemusoleum'))
        fenetre.page_joueur._teleporter()
        self.assertEqual(fenetre.sauvegarde.joueur['location'], 57)
        self.assertIn('Bemusoleum', fenetre.page_joueur.lieu.text())


if __name__ == '__main__':
    unittest.main()
