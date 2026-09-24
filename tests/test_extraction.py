"""Tests de l'extraction des icônes (editeur/extraction.py et le menu de
l'éditeur), sur une mini-ROM synthétique (rom_synthetique.py) : aucune ROM
du jeu n'est nécessaire. Demandent PySide6 (sautés sinon)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

from dqmj2p_save import langue

sys.path.insert(0, str(Path(__file__).parent))
import rom_synthetique  # noqa: E402

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PySide6.QtCore import QSettings
    from PySide6.QtGui import QImage
    from PySide6.QtWidgets import QApplication, QFileDialog

    from editeur import extraction, icones
except ImportError:
    extraction = None


@unittest.skipIf(extraction is None, 'PySide6 absent')
class Extraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.rom = rom_synthetique.rom()

    def setUp(self):
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        self.dossier = Path(dossier.name)

    def test_icones_des_monstres(self):
        n = extraction.extraire_icones(self.rom, self.dossier)
        self.assertEqual(n, len(rom_synthetique.ESPECES))     # ic_9999 ignorée
        self.assertEqual(sorted(p.name for p in self.dossier.iterdir()),
                         sorted(f'{e}.png' for e in rom_synthetique.ESPECES))
        petite, grande = QImage(str(self.dossier / '1.png')), QImage(str(self.dossier / '31.png'))
        self.assertEqual((petite.width(), petite.height()), (40, 40))
        self.assertEqual((grande.width(), grande.height()), (40, 120))

    def test_rangement_des_tuiles(self):
        # Tuile 0 en haut à gauche, tuile 16 (bande droite) à x = 32.
        image = QImage(str(self._extraire_icones() / '1.png'))
        ncgr = rom_synthetique._ncgr(1)[0x30:]
        palette = extraction.couleurs_bgr555(rom_synthetique._palette())
        for tuile, (x, y) in ((0, (0, 0)), (16, (32, 0)), (20, (0, 32)), (24, (32, 32))):
            valeur = ncgr[tuile * 32] & 15              # premier pixel de la tuile
            with self.subTest(tuile=tuile):
                pixel = image.pixelColor(x, y)
                if valeur == 0:
                    self.assertEqual(pixel.alpha(), 0)
                else:
                    self.assertEqual((pixel.red(), pixel.green(), pixel.blue()),
                                     palette[valeur])

    def test_icones_des_familles(self):
        n = extraction.extraire_familles(self.rom, self.dossier)
        self.assertEqual(n, 8)
        self.assertIn('inconnue.png', {p.name for p in self.dossier.iterdir()})
        gluant = QImage(str(self.dossier / 'Gluant.png'))
        self.assertEqual((gluant.width(), gluant.height()), (7, 10))   # recadrée

    def test_icones_des_boutons(self):
        n = extraction.extraire_boutons(self.rom, self.dossier)
        self.assertEqual(n, rom_synthetique.NB_BOUTONS)
        image = QImage(str(self.dossier / '3.png'))
        self.assertEqual((image.width(), image.height()), (40, 40))
        # Tuiles rangées ligne par ligne : la 1 à droite de la 0, la 5 dessous.
        tuiles = rom_synthetique.icone_bouton(3)[4:]
        palette = extraction.couleurs_bgr555(rom_synthetique._palette())
        for tuile, (x, y) in ((0, (0, 0)), (1, (8, 0)), (5, (0, 8)), (24, (32, 32))):
            valeur = tuiles[tuile * 32] & 15
            with self.subTest(tuile=tuile):
                pixel = image.pixelColor(x, y)
                if valeur == 0:
                    self.assertEqual(pixel.alpha(), 0)
                else:
                    self.assertEqual((pixel.red(), pixel.green(), pixel.blue()),
                                     palette[valeur])

    def test_pas_une_rom(self):
        with self.assertRaises(extraction.ErreurExtraction):
            extraction.extraire_icones(b'pas une ROM', self.dossier)
        with self.assertRaises(extraction.ErreurExtraction):
            extraction.extraire_icones(bytes(0x1000), self.dossier)

    def test_fichier_absent(self):
        with self.assertRaisesRegex(extraction.ErreurExtraction, 'introuvable'):
            extraction.fichier_rom(self.rom, 'absent.bin')

    def _extraire_icones(self) -> Path:
        extraction.extraire_icones(self.rom, self.dossier)
        return self.dossier


@unittest.skipIf(extraction is None, 'PySide6 absent')
class MenuExtraction(unittest.TestCase):
    """Fichier > Extraire les icônes d'une ROM… dans la vraie fenêtre."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from editeur.fenetre import Fenetre
        self.Fenetre = Fenetre
        self.addCleanup(langue.choisir, langue.courante())
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        self.dossier = Path(dossier.name)
        self.rom = self.dossier / 'jeu.nds'
        self.rom.write_bytes(rom_synthetique.rom())
        # Icônes écrites dans le dossier temporaire, pas dans editeur/icones.
        for nom, valeur in (('DOSSIER', self.dossier / 'icones'),
                            ('FAMILLES', self.dossier / 'icones' / 'familles'),
                            ('BOUTONS', self.dossier / 'icones' / 'boutons')):
            self.addCleanup(setattr, icones, nom, getattr(icones, nom))
            setattr(icones, nom, valeur)
        for fonction in (icones.image, icones.icone, icones.famille, icones.bouton):
            self.addCleanup(fonction.cache_clear)
            fonction.cache_clear()
        self.reglages = QSettings(str(self.dossier / 'reglages.ini'), QSettings.IniFormat)
        self.reglages.setValue('langue', 'fr')

    def tearDown(self):
        if self.Fenetre.active:
            self.Fenetre.active._remplacee = True
            self.Fenetre.active.close()
            self.Fenetre.active = None

    def choisir(self, chemin: str):
        original = QFileDialog.getOpenFileName
        QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: (chemin, ''))
        self.addCleanup(setattr, QFileDialog, 'getOpenFileName', original)

    def test_extraction_depuis_le_menu(self):
        fenetre = self.Fenetre(self.reglages)
        self.assertTrue(icones.icone(1).isNull())
        self.choisir(str(self.rom))
        fenetre.extraire_icones()
        nouvelle = self.Fenetre.active
        self.assertIsNot(nouvelle, fenetre)                 # fenêtre redessinée
        self.assertFalse(icones.icone(1).isNull())
        self.assertFalse(icones.famille('Gluant').isNull())
        self.assertFalse(icones.bouton(8).isNull())
        self.assertIn('3 icônes de monstres, 8 de familles et 12 de boutons',
                      nouvelle.statusBar().currentMessage())

    def test_annulation(self):
        fenetre = self.Fenetre(self.reglages)
        self.choisir('')
        fenetre.extraire_icones()
        self.assertIs(self.Fenetre.active, fenetre)
        self.assertFalse((self.dossier / 'icones').exists())


if __name__ == '__main__':
    unittest.main()
