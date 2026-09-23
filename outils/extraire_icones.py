#!/usr/bin/env python3
"""Extrait les icônes des monstres d'une ROM de DQMJ2 Professional.

    python outils/extraire_icones.py <rom.nds> [dossier de sortie]

Alternative à importer_synthese.py, sans passer par le projet des synthèses.
Format, relevé par tools/extract_icons.py de dqmj2pro-synthesis :

- MonsterIconDat.NICA (racine de la ROM) est une archive FPK : « FPK\\0 », u32 nombre
  d'entrées, puis des entrées de 0x28 octets (nom sur 32 octets, u32 début,
  u32 taille) ;
- ic_XXXX.NCGR (XXXX : ID interne de l'espèce en hexadécimal) : graphismes
  4 bits par pixel en tuiles 8x8, données à 0x30, taille en 0x28 ;
  ic_XXXX.NCLD : palette brute de 16 couleurs BGR555, couleur 0 transparente ;
- 25 tuiles forment un bloc de 40x40, rangé comme des sprites DS : 32x32
  (4x4 tuiles), bande droite 8x32, bande basse 32x8, coin 8x8. Les monstres
  de taille 2 ou 3 empilent 2 ou 3 blocs (40x80, 40x120).

Nécessite PySide6 (pour écrire les PNG).
"""
import struct
import sys
from pathlib import Path

from PySide6.QtGui import QImage

from rom_nds import couleurs_bgr555, fichier_rom

CIBLE = Path(__file__).resolve().parents[1] / 'editeur' / 'icones'
ARCHIVE = 'MonsterIconDat.NICA'     # à la racine du système de fichiers
BLOC = [(0, 0, 4, 4), (4, 0, 1, 4), (0, 4, 4, 1), (4, 4, 1, 1)]   # x, y, l, h en tuiles


def lire_fpk(donnees: bytes) -> dict[str, bytes]:
    if donnees[:4] != b'FPK\0':
        raise SystemExit(f'{ARCHIVE} : archive FPK attendue')
    fichiers = {}
    for i in range(struct.unpack_from('<I', donnees, 4)[0]):
        o = 8 + i * 0x28
        nom = donnees[o: o + 32].split(b'\0')[0].decode('latin1')
        debut, taille = struct.unpack_from('<II', donnees, o + 32)
        fichiers[nom] = donnees[debut: debut + taille]
    return fichiers


def decoder(ncgr: bytes, ncld: bytes) -> QImage:
    rgba = [bytes((*c, 0 if i == 0 else 255)) for i, c in enumerate(couleurs_bgr555(ncld))]
    taille = struct.unpack_from('<I', ncgr, 0x28)[0]
    donnees = ncgr[0x30: 0x30 + taille]
    blocs = taille // 32 // 25
    largeur, hauteur = 40, 40 * blocs
    pixels = bytearray(largeur * hauteur * 4)
    tuile = 0
    for b in range(blocs):
        for x0, y0, l, h in BLOC:
            for ty in range(h):
                for tx in range(l):
                    octets = donnees[tuile * 32: (tuile + 1) * 32]
                    for p in range(64):
                        valeur = (octets[p // 2] >> (4 if p % 2 else 0)) & 15
                        x = (x0 + tx) * 8 + p % 8
                        y = b * 40 + (y0 + ty) * 8 + p // 8
                        o = (y * largeur + x) * 4
                        pixels[o: o + 4] = rgba[valeur]
                    tuile += 1
    return QImage(bytes(pixels), largeur, hauteur, QImage.Format_RGBA8888).copy()


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    cible = Path(sys.argv[2]) if len(sys.argv) == 3 else CIBLE
    fichiers = lire_fpk(fichier_rom(Path(sys.argv[1]).read_bytes(), ARCHIVE))
    cible.mkdir(parents=True, exist_ok=True)
    nombre = 0
    for nom, ncgr in fichiers.items():
        if not nom.endswith('.NCGR'):
            continue
        cle = nom[3:7]
        espece = int(cle, 16)
        if espece >= 0x1000:            # ic_9995 à ic_9999 : icônes hors bestiaire
            continue
        decoder(ncgr, fichiers[f'ic_{cle}.NCLD']).save(str(cible / f'{espece}.png'))
        nombre += 1
    print(f'{nombre} icônes écrites dans {cible}')


if __name__ == '__main__':
    main()
