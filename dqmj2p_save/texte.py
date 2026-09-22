"""Codage du texte du jeu (noms du joueur et des monstres).

Table de caractères de l'ARM9 (adresse 0x020DBC16, relevée par msgtool.py du
projet de traduction) :
  - un octet 00-DF ou E5-FF : le caractère TABLE[octet] ;
  - un préfixe E0, E1 ou E4 suivi d'un octet n : TABLE[base du préfixe + n]
    (ponctuation, symboles, katakana, kanji ; le tiret s'écrit E0 5A).

Le texte se termine par 0x00 ou par le marqueur E3 1B ; ce qui suit est du
résidu. La limite du jeu compte des caractères, pas des octets.
"""

# '\0' = entrée sans caractère.
TABLE = (
    '\x000123456789 \u3000ABCDEFGHIJKLMNOPQRS'  # 0x000
    'TUVWXYZabcdefghijklmnopqrstuvwxy'  # 0x020
    'zÀÁÂÄÇÈÉÊËÌÍÎÏÑÒÓÔÖŒÙÚÛÜàáâäçèéê'  # 0x040
    'ëìíîïñòóôöœùúûüあぁいぃうぅえぇおぉかきくけこさし'  # 0x060
    'すせそたちつってとなにぬねのはひふへほまみむめもやゃゆゅよょらり'  # 0x080
    'るれろわをんアァイィウゥエェオォカキクケコサシスセソタチツッテト'  # 0x0A0
    'ナニヌネノハヒフヘホマミムメモヤャユュヨョラリルレロワヲン012'  # 0x0C0
    '3456789がぎぐげござじずぜぞだぢづでどばびぶべぼガギグゲゴ'  # 0x0E0
    'ザジズゼゾダヂヅデドバビブベボぱぴぷぺぽパピプペポß¿¡ß¿¡!'  # 0x100
    '?_←↑→↓☆★※△▲▽▼□■○●°++＝//⇔⇒ⅠⅡⅢⅤⅩ;°'  # 0x120
    '-""""\'\'`\'\'～♪*・*()“%.&×:„！》《-,,？。'  # 0x140
    '「」『』”“?!、・ー-～/*()+:…→i%.＆゛゜：％ｧｨｩ'  # 0x160
    'ｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉ'  # 0x180
    'ﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝＡＢＣ\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # 0x1A0
    '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # 0x1C0
    '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # 0x1E0
    '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # 0x200
    '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # 0x220
    '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # 0x240
    '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # 0x260
    '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # 0x280
    '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00遺員雨炎王下果火我会回海界崖換間'  # 0x2A0
    '関岸器機気技客休級巨強金具空系経撃剣験原減言古後交光功効攻行合最'  # 0x2C0
    '作山斬仕使士死私試事時自失室守手種呪修出所勝賞上乗場済信心新汝神'  # 0x2E0
    '親人図吹水世性成整生聖跡雪戦船前全相装増息族体対耐代大探断値知地'  # 0x300
    '着中仲調長鳥通定敵闘動道特謎日入年敗配買売箱発半販飛備不負武復分'  # 0x320
    '文平編宝方北本魔味密無名命明予預用踊利理竜力林令話壁画練証者優伝'  # 0x340
    '説決参加品選権位獣男点結第態思活真老師兵島邪化身将軍天馬黒騎暗皇'  # 0x360
    '帝勇車霧破裂病城冥少旅町風数高連友目木差月階封計'  # 0x380
)

BASES = {0xE0: 0xE6, 0xE1: 0x118, 0xE4: 0x2AF}
PREFIXES = range(0xE0, 0xE5)        # E2 et E3 : préfixes de codes non textuels
FIN = b'\xe3\x1b'
LONGUEUR_MAX = 8                    # limite du jeu pour les noms et surnoms


def _construire_encodage() -> dict[str, bytes]:
    # Un octet quand c'est possible, sinon E0 (le choix du jeu pour le tiret).
    # Les plages E1 et E4 (kanji…) ne servent qu'au décodage.
    encodage = {}
    for octet in range(0x100):
        if octet not in PREFIXES and TABLE[octet] != '\0':
            encodage.setdefault(TABLE[octet], bytes([octet]))
    for n in range(0x100):
        car = TABLE[BASES[0xE0] + n]
        if car != '\0':
            encodage.setdefault(car, bytes([0xE0, n]))
    return encodage


_ENCODAGE = _construire_encodage()


def decoder(brut: bytes) -> str:
    """Octets -> texte. Un code sans caractère devient {XX} ou {XXYY}."""
    brut = brut.split(FIN)[0]
    sortie, i = [], 0
    while i < len(brut) and brut[i]:
        octet = brut[i]
        if octet in PREFIXES and i + 1 < len(brut):
            n = brut[i + 1]
            index = BASES.get(octet, len(TABLE)) + n
            car = TABLE[index] if index < len(TABLE) else '\0'
            sortie.append(car if car != '\0' else f'{{{octet:02X}{n:02X}}}')
            i += 2
        else:
            car = TABLE[octet] if octet not in PREFIXES else '\0'
            sortie.append(car if car != '\0' else f'{{{octet:02X}}}')
            i += 1
    return ''.join(sortie)


def caracteres_invalides(texte: str) -> str:
    return ''.join(sorted({c for c in texte if c not in _ENCODAGE}))


def encoder(texte: str, taille: int) -> bytes:
    """Texte -> octets, complété par des 0 jusqu'à taille."""
    if len(texte) > LONGUEUR_MAX:
        raise ValueError(f'{LONGUEUR_MAX} caractères au plus')
    invalides = caracteres_invalides(texte)
    if invalides:
        raise ValueError(f'caractères absents de la police du jeu : {invalides}')
    brut = b''.join(_ENCODAGE[c] for c in texte)
    if len(brut) >= taille:
        raise ValueError(f'trop long une fois codé ({len(brut)} octets)')
    return brut.ljust(taille, b'\0')
