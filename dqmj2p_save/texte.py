"""Codage du texte du jeu (noms du joueur et des monstres).

Un octet = un caractère, via la table de l'ARM9 (adresse 0x020DBC16, 256
premières entrées, relevée par msgtool.py du projet de traduction). Le texte se
termine par 0x00 ou par le marqueur E3 1B ; ce qui suit est du résidu.
"""

# Caractère de chaque octet ; '\0' = octet sans caractère.
TABLE = (
    '\x000123456789 　ABCDEFGHIJKLMNOPQRS'  # 0x00
    'TUVWXYZabcdefghijklmnopqrstuvwxy'  # 0x20
    'zÀÁÂÄÇÈÉÊËÌÍÎÏÑÒÓÔÖŒÙÚÛÜàáâäçèéê'  # 0x40
    'ëìíîïñòóôöœùúûüあぁいぃうぅえぇおぉかきくけこさし'  # 0x60
    'すせそたちつってとなにぬねのはひふへほまみむめもやゃゆゅよょらり'  # 0x80
    'るれろわをんアァイィウゥエェオォカキクケコサシスセソタチツッテト'  # 0xA0
    'ナニヌネノハヒフヘホマミムメモヤャユュヨョラリルレロワヲン012'  # 0xC0
    '3456789がぎぐげござじずぜぞだぢづでどばびぶべぼガギグゲゴ'  # 0xE0
)
assert len(TABLE) == 256

FIN = b'\xe3\x1b'
LONGUEUR_MAX = 8                    # limite du jeu pour les noms et surnoms
PREFIXES = range(0xE0, 0xE5)        # début d'un caractère sur deux octets

_OCTET = {}
for _octet, _car in enumerate(TABLE):
    if _car != '\0' and _octet not in PREFIXES:
        _OCTET.setdefault(_car, _octet)


def decoder(brut: bytes) -> str:
    """Octets -> texte. Un octet sans caractère devient {XX}."""
    brut = brut.split(b'\0')[0].split(FIN)[0]
    return ''.join(TABLE[b] if TABLE[b] != '\0' and b not in PREFIXES
                   else f'{{{b:02X}}}' for b in brut)


def caracteres_invalides(texte: str) -> str:
    return ''.join(sorted({c for c in texte if c not in _OCTET}))


def encoder(texte: str, taille: int) -> bytes:
    """Texte -> octets, complété par des 0 jusqu'à taille."""
    if len(texte) > LONGUEUR_MAX:
        raise ValueError(f'{LONGUEUR_MAX} caractères au plus')
    invalides = caracteres_invalides(texte)
    if invalides:
        raise ValueError(f'caractères absents de la police du jeu : {invalides}')
    return bytes(_OCTET[c] for c in texte).ljust(taille, b'\0')
