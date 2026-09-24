"""Mini-ROM DS pour les tests d'extraction : juste ce que lisent les extracteurs
(NitroFS à plat avec MonsterIconDat.NICA, font_16x16.NFTR, main_status_bg.pal
et menu_icon_data.cch/.cpl), rempli de motifs connus. Aucune donnée du jeu."""
import struct

ESPECES = (1, 49, 31)               # 31 : monstre de taille 3 (trois blocs)
TAILLES = {31: 3}
NB_GLYPHES = 580                    # familles : glyphes 565 à 572
NB_BOUTONS = 12


def _palette() -> bytes:
    # 16 couleurs BGR555 distinctes, la 0 étant la transparence.
    return struct.pack('<16H', *((i * 2) | (i << 5) | ((31 - i) << 10) for i in range(16)))


def _ncgr(espece: int) -> bytes:
    blocs = TAILLES.get(espece, 1)
    taille = blocs * 25 * 32
    # Chaque tuile a son motif : un mauvais rangement des tuiles se voit.
    donnees = bytes((t * 7 + espece + o) & 0xFF for t in range(blocs * 25) for o in range(32))
    entete = bytearray(0x30)
    struct.pack_into('<I', entete, 0x28, taille)
    return bytes(entete) + donnees


def _fpk(fichiers: dict[str, bytes]) -> bytes:
    debut = 8 + 0x28 * len(fichiers)
    entetes, corps = bytearray(), bytearray()
    for nom, contenu in fichiers.items():
        entetes += nom.encode('latin1').ljust(32, b'\0')
        entetes += struct.pack('<II', debut + len(corps), len(contenu))
        corps += contenu
    return b'FPK\0' + struct.pack('<I', len(fichiers)) + bytes(entetes) + bytes(corps)


def _police() -> bytes:
    # Bloc CGLP : cellule 12x16, 4 bits par pixel, 96 octets par glyphe.
    largeur, hauteur, bpp = 12, 16, 4
    taille = largeur * hauteur * bpp // 8
    glyphes = bytearray()
    for index in range(NB_GLYPHES):
        pixels = [0] * (largeur * hauteur)
        for y in range(3, 13):              # dessin 7x10, décalé dans la cellule
            for x in range(2, 9):
                pixels[y * largeur + x] = (x + y + index) % 15 + 1
        valeur = 0
        for p in pixels:
            valeur = (valeur << bpp) | p
        glyphes += valeur.to_bytes(taille, 'big')
    cglp = b'PLGC' + struct.pack('<I', 0x10 + len(glyphes)) + bytes([largeur, hauteur])
    cglp += struct.pack('<H', taille) + bytes([0, 0, bpp, 0]) + bytes(glyphes)
    return b'RTFN' + bytes(12) + cglp


def icone_bouton(bouton: int) -> bytes:
    """5 x 5 tuiles, chacune avec son motif (u16 largeur, u16 hauteur, tuiles)."""
    return struct.pack('<HH', 5, 5) + bytes((t * 11 + bouton + o) & 0xFF
                                            for t in range(25) for o in range(32))


def _table(magie: bytes, zero: bool, entrees: list[bytes]) -> bytes:
    entete = magie + (bytes(4) if zero else b'') + struct.pack('<I', len(entrees))
    debut = len(entete) + 4 * len(entrees)
    debuts, corps = [], bytearray()
    for entree in entrees:
        debuts.append(debut + len(corps))
        corps += entree
    return entete + struct.pack(f'<{len(debuts)}I', *debuts) + bytes(corps)


def rom() -> bytes:
    icones = {}
    for espece in ESPECES:
        icones[f'ic_{espece:04x}.NCGR'] = _ncgr(espece)
        icones[f'ic_{espece:04x}.NCLD'] = _palette()
    icones['ic_9999.NCGR'] = _ncgr(1)           # icône hors bestiaire, ignorée
    icones['ic_9999.NCLD'] = _palette()
    fichiers = {'MonsterIconDat.NICA': _fpk(icones), 'font_16x16.NFTR': _police(),
                'main_status_bg.pal': _palette() * 4,
                'menu_icon_data.cch': _table(b'FHCC', True, [icone_bouton(b) for b in
                                                             range(NB_BOUTONS)]),
                'menu_icon_data.cpl': _table(b'FLPC', False, [b'\x10\x01\0\0' + _palette()]
                                             * NB_BOUTONS)}

    # FNT : un seul dossier (la racine), ses fichiers numérotés à partir de 0.
    liste = b''.join(bytes([len(n)]) + n.encode('latin1') for n in fichiers) + b'\0'
    fnt = struct.pack('<IHH', 8, 0, 1) + liste
    donnees, fat = bytearray(), bytearray()
    debut_donnees = 0x200 + len(fnt) + 8 * len(fichiers)
    for contenu in fichiers.values():
        a = debut_donnees + len(donnees)
        fat += struct.pack('<II', a, a + len(contenu))
        donnees += contenu
    entete = bytearray(0x200)
    struct.pack_into('<4I', entete, 0x40, 0x200, len(fnt), 0x200 + len(fnt), len(fat))
    return bytes(entete) + fnt + bytes(fat) + bytes(donnees)
