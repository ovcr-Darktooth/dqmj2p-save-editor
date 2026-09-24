"""Extraction des icônes depuis une ROM de DQMJ2 Professional (japonaise
d'origine ou patchée), pour le menu de l'éditeur et outils/extraire_*.py.

Icônes des monstres. Format relevé par tools/extract_icons.py de
dqmj2pro-synthesis :

- MonsterIconDat.NICA (racine de la ROM) est une archive FPK : « FPK\\0 », u32 nombre
  d'entrées, puis des entrées de 0x28 octets (nom sur 32 octets, u32 début,
  u32 taille) ;
- ic_XXXX.NCGR (XXXX : ID interne de l'espèce en hexadécimal) : graphismes
  4 bits par pixel en tuiles 8x8, données à 0x30, taille en 0x28 ;
  ic_XXXX.NCLD : palette brute de 16 couleurs BGR555, couleur 0 transparente ;
- 25 tuiles forment un bloc de 40x40, rangé comme des sprites DS : 32x32
  (4x4 tuiles), bande droite 8x32, bande basse 32x8, coin 8x8. Les monstres
  de taille 2 ou 3 empilent 2 ou 3 blocs (40x80, 40x120).

Icônes des familles : glyphes de la police du jeu (font_16x16.NFTR), juste
après les kanji : 565 Gluant, 566 Dragon, 567 Nature, 568 Bête, 569 Matière,
570 Démon, 571 Zombie, 572 « ??? ». Glyphes 12x16 en 4 bits par pixel (bloc
CGLP du format NFTR). Chaque valeur est un indice dans la palette des menus
(1 contour noir, 11 bleu, 14 vert…), ici celle de l'écran de statut,
main_status_bg.pal (16 premières couleurs, BGR555) ; 0 est transparent.

Icônes des boutons du menu (écran du bas), dans l'ordre des ID de boutons
(noms.BOUTONS) :

- menu_icon_data.cch : « FHCC », u32 0, u32 nombre d'icônes (12), puis leurs
  débuts (u32). Chaque icône : u16 largeur, u16 hauteur en tuiles (5 x 5),
  puis les tuiles 4 bits par pixel, ligne par ligne (pas de rangement en
  sprites comme les monstres) ;
- menu_icon_data.cpl : « FLPC », u32 nombre de palettes, leurs débuts (u32) ;
  chacune : 4 octets d'en-tête puis 16 couleurs BGR555, la 0 transparente.
"""
import struct
from pathlib import Path

from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QImage

from dqmj2p_save.langue import tr

ARCHIVE = 'MonsterIconDat.NICA'     # à la racine du système de fichiers
BLOC = [(0, 0, 4, 4), (4, 0, 1, 4), (0, 4, 4, 1), (4, 4, 1, 1)]   # x, y, l, h en tuiles
ICONES_BOUTONS = 'menu_icon_data.cch'
PALETTES_BOUTONS = 'menu_icon_data.cpl'
GLYPHES = {'Gluant': 565, 'Dragon': 566, 'Nature': 567, 'Bête': 568,
           'Matière': 569, 'Démon': 570, 'Zombie': 571, '???': 572}
FICHIERS = {'???': 'inconnue'}      # « ??? » n'est pas un nom de fichier sûr


class ErreurExtraction(ValueError):
    """Le fichier n'est pas une ROM de DQMJ2P, ou un fichier attendu y manque."""


# ── ROM Nintendo DS (système de fichiers NitroFS) ────────────────────────────

def fichier_rom(rom: bytes, chemin: str) -> bytes:
    """Contenu du fichier `chemin` (« MonsterIconDat.NICA », « dwc/utility.bin »,
    « font_16x16.NFTR »…). Table des noms (FNT) : une entrée de 8 octets par
    dossier (u32 début de sa liste, u16 ID du premier fichier), puis la liste :
    octet longueur (bit 7 = sous-dossier), nom, et pour un sous-dossier son
    numéro sur u16 (12 bits bas). La FAT donne début et fin de chaque fichier."""
    try:
        return _fichier_rom(rom, chemin)
    except (struct.error, IndexError):
        raise ErreurExtraction(tr('{chemin} illisible : ce fichier est-il une ROM DS ?',
                                  chemin=chemin)) from None


def _fichier_rom(rom: bytes, chemin: str) -> bytes:
    fnt, _, fat, _ = struct.unpack_from('<4I', rom, 0x40)
    parties = chemin.split('/')
    dossier = 0
    for rang, cherche in enumerate(parties):
        dernier = rang == len(parties) - 1
        debut, fid = struct.unpack_from('<IH', rom, fnt + 8 * dossier)
        i, suivant = fnt + debut, None
        while (longueur := rom[i]) != 0:
            nom = rom[i + 1: i + 1 + (longueur & 0x7F)].decode('latin1')
            i += 1 + (longueur & 0x7F)
            if longueur & 0x80:
                numero = struct.unpack_from('<H', rom, i)[0] & 0xFFF
                i += 2
                if nom == cherche and not dernier:
                    suivant = numero
                    break
                continue
            if nom == cherche and dernier:
                a, b = struct.unpack_from('<II', rom, fat + fid * 8)
                return rom[a:b]
            fid += 1
        if suivant is None:
            raise ErreurExtraction(tr('{chemin} introuvable dans la ROM', chemin=chemin))
        dossier = suivant
    raise ErreurExtraction(tr('{chemin} introuvable dans la ROM', chemin=chemin))


def couleurs_bgr555(donnees: bytes, nombre: int = 16) -> list[tuple[int, int, int]]:
    """Palette DS : `nombre` couleurs BGR555 -> (r, g, b) sur 8 bits."""
    c5 = lambda x: (x << 3) | (x >> 2)
    return [(c5(v & 31), c5((v >> 5) & 31), c5((v >> 10) & 31))
            for v in struct.unpack_from(f'<{nombre}H', donnees)]


# ── Icônes des monstres ──────────────────────────────────────────────────────

def lire_fpk(donnees: bytes) -> dict[str, bytes]:
    if donnees[:4] != b'FPK\0':
        raise ErreurExtraction(tr('{archive} : archive FPK attendue', archive=ARCHIVE))
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


def extraire_icones(rom: bytes, cible: Path) -> int:
    """Écrit <id espèce>.png dans cible ; renvoie le nombre d'icônes."""
    fichiers = lire_fpk(fichier_rom(rom, ARCHIVE))
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
    return nombre


# ── Icônes des familles ──────────────────────────────────────────────────────

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
    if not xs:
        raise ErreurExtraction(tr('glyphe de famille vide : police inattendue'))
    return QRect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def extraire_familles(rom: bytes, cible: Path) -> int:
    """Écrit <famille>.png dans cible ; renvoie le nombre d'icônes."""
    police = fichier_rom(rom, 'font_16x16.NFTR')
    couleurs = palette(fichier_rom(rom, 'main_status_bg.pal'))
    if police.find(b'PLGC') < 0:
        raise ErreurExtraction(tr('font_16x16.NFTR : bloc CGLP introuvable'))
    cible.mkdir(parents=True, exist_ok=True)
    for famille, index in GLYPHES.items():
        glyphe(police, index, couleurs).save(str(cible / f'{FICHIERS.get(famille, famille)}.png'))
    return len(GLYPHES)


# ── Icônes des boutons du menu ───────────────────────────────────────────────

def _table(donnees: bytes, magie: bytes, debut_compte: int) -> list[int]:
    if donnees[:4] != magie:
        raise ErreurExtraction(tr('{magie} attendu en tête de fichier',
                                  magie=magie.decode('latin1')))
    nombre = struct.unpack_from('<I', donnees, debut_compte)[0]
    return list(struct.unpack_from(f'<{nombre}I', donnees, debut_compte + 4))


def decoder_bouton(icone: bytes, couleurs: list[tuple[int, int, int]]) -> QImage:
    """Icône de bouton : u16 largeur, u16 hauteur en tuiles, tuiles 4 bits par
    pixel rangées ligne par ligne."""
    largeur, hauteur = struct.unpack_from('<HH', icone)
    rgba = [bytes((*c, 0 if i == 0 else 255)) for i, c in enumerate(couleurs)]
    image = bytearray(largeur * 8 * hauteur * 8 * 4)
    for tuile in range(largeur * hauteur):
        octets = icone[4 + tuile * 32: 4 + (tuile + 1) * 32]
        for p in range(64):
            valeur = (octets[p // 2] >> (4 if p % 2 else 0)) & 15
            x = (tuile % largeur) * 8 + p % 8
            y = (tuile // largeur) * 8 + p // 8
            o = (y * largeur * 8 + x) * 4
            image[o: o + 4] = rgba[valeur]
    return QImage(bytes(image), largeur * 8, hauteur * 8, QImage.Format_RGBA8888).copy()


def extraire_boutons(rom: bytes, cible: Path) -> int:
    """Écrit <id bouton>.png dans cible ; renvoie le nombre d'icônes."""
    cch, cpl = fichier_rom(rom, ICONES_BOUTONS), fichier_rom(rom, PALETTES_BOUTONS)
    icones, palettes = _table(cch, b'FHCC', 8), _table(cpl, b'FLPC', 4)
    if len(icones) != len(palettes):
        raise ErreurExtraction(tr("{a} icônes pour {b} palettes : ce n'est pas le "
                                  'menu attendu', a=len(icones), b=len(palettes)))
    cible.mkdir(parents=True, exist_ok=True)
    for bouton, (debut, debut_palette) in enumerate(zip(icones, palettes)):
        couleurs = couleurs_bgr555(cpl[debut_palette + 4:])
        decoder_bouton(cch[debut:], couleurs).save(str(cible / f'{bouton}.png'))
    return len(icones)
