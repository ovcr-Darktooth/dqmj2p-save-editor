#!/usr/bin/env python3
"""Extrait les icônes de familles de la police du jeu (font_16x16.NFTR).

    python outils/extraire_familles.py <rom.nds> [dossier de sortie]

Les pictogrammes des familles sont des glyphes de la police, juste après les
kanji : 565 Gluant, 566 Dragon, 567 Nature, 568 Bête, 569 Matière, 570 Démon,
571 Zombie, 572 « ??? ». Glyphes 12x16 en 4 bits par pixel (bloc CGLP du
format NFTR). Chaque valeur est un indice dans la palette des menus (1 contour
noir, 11 bleu, 14 vert…), ici celle de l'écran de statut, main_status_bg.pal
(16 premières couleurs, BGR555) ; 0 est transparent.

Nécessite PySide6 (pour écrire les PNG).
"""
import struct
import sys
from pathlib import Path

from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QImage

from rom_nds import couleurs_bgr555, fichier_rom

CIBLE = Path(__file__).resolve().parents[1] / 'editeur' / 'icones' / 'familles'
GLYPHES = {'Gluant': 565, 'Dragon': 566, 'Nature': 567, 'Bête': 568,
           'Matière': 569, 'Démon': 570, 'Zombie': 571, '???': 572}
FICHIERS = {'???': 'inconnue'}      # « ??? » n'est pas un nom de fichier sûr


def palette(donnees: bytes) -> list[QColor]:
    return [QColor(*rgb) for rgb in couleurs_bgr555(donnees)]


def glyphe(police: bytes, index: int, couleurs: list[QColor]) -> QImage:
    cglp = police.find(b'PLGC')
    largeur, hauteur = police[cglp + 8], police[cglp + 9]
    taille, bpp = struct.unpack_from('<H', police, cglp + 10)[0], police[cglp + 14]
    bits = int.from_bytes(police[cglp + 0x10 + index * taille:
                                 cglp + 0x10 + (index + 1) * taille], 'big')
    image = QImage(largeur, hauteur, QImage.Format_ARGB32)
    image.fill(0)
    masque = (1 << bpp) - 1
    for y in range(hauteur):
        for x in range(largeur):
            decalage = taille * 8 - (y * largeur + x + 1) * bpp
            valeur = (bits >> decalage) & masque
            if valeur:
                image.setPixelColor(x, y, couleurs[valeur])
    # Recadrage sur le dessin (7x10 dans une cellule 12x16)
    return image.copy(image.rect().intersected(_boite(image)))


def _boite(image: QImage):
    xs = [x for x in range(image.width()) for y in range(image.height())
          if image.pixelColor(x, y).alpha()]
    ys = [y for x in range(image.width()) for y in range(image.height())
          if image.pixelColor(x, y).alpha()]
    return QRect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    cible = Path(sys.argv[2]) if len(sys.argv) == 3 else CIBLE
    rom = Path(sys.argv[1]).read_bytes()
    police = fichier_rom(rom, 'font_16x16.NFTR')
    couleurs = palette(fichier_rom(rom, 'main_status_bg.pal'))
    cible.mkdir(parents=True, exist_ok=True)
    for famille, index in GLYPHES.items():
        glyphe(police, index, couleurs).save(str(cible / f'{FICHIERS.get(famille, famille)}.png'))
    print(f'{len(GLYPHES)} icônes de familles écrites dans {cible}')


if __name__ == '__main__':
    main()
