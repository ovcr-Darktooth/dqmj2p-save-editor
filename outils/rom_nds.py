"""Lecture de fichiers dans une ROM Nintendo DS (système de fichiers NitroFS),
pour les scripts d'extraction. Bibliothèque standard uniquement."""
import struct


def fichier_rom(rom: bytes, chemin: str) -> bytes:
    """Contenu du fichier `chemin` (« MonsterIconDat.NICA », « dwc/utility.bin »,
    « font_16x16.NFTR »…). Table des noms (FNT) : une entrée de 8 octets par
    dossier (u32 début de sa liste, u16 ID du premier fichier), puis la liste :
    octet longueur (bit 7 = sous-dossier), nom, et pour un sous-dossier son
    numéro sur u16 (12 bits bas). La FAT donne début et fin de chaque fichier."""
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
            raise SystemExit(f'{chemin} introuvable dans la ROM')
        dossier = suivant
    raise SystemExit(f'{chemin} introuvable dans la ROM')


def couleurs_bgr555(donnees: bytes, nombre: int = 16) -> list[tuple[int, int, int]]:
    """Palette DS : `nombre` couleurs BGR555 -> (r, g, b) sur 8 bits."""
    c5 = lambda x: (x << 3) | (x >> 2)
    return [(c5(v & 31), c5((v >> 5) & 31), c5((v >> 10) & 31))
            for v in struct.unpack_from(f'<{nombre}H', donnees)]
