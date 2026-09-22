"""Cartographie du format de sauvegarde de DQMJ2 Professional.

Tout ce qui est connu du format vit ici, sous forme de tables. Un champ
nouvellement identifié s'ajoute en une ligne dans CHAMPS_MONSTRE (ou dans une
future table d'en-tête), sans toucher au reste du code.

Offsets relevés par Ceris White (save_converter.py du projet DQMJ2Pro
Translation), vérifiés sur des sauvegardes réelles. Voir docs/format-sauvegarde.md.
"""
import struct
from dataclasses import dataclass

from . import texte

# ── Fichier ──────────────────────────────────────────────────────────────────

TAILLE_BRUTE = 0x10000              # mémoire de sauvegarde de la cartouche
TAILLE_COPIE = 0x7100               # le jeu écrit deux copies identiques
COPIES = (0x0000, 0x7100)
MAGIC = b'SIZ\x00'
MARQUEUR_DSV = b'|-DESMUME SAVE-|'  # fin du pied de page DeSmuME / DraStic

# ── Sommes de contrôle (relatives au début d'une copie) ──────────────────────
# L'ordre compte : la somme d'en-tête couvre le mot où est rangée la somme data.

SOMME_DATA = 0x88                   # u32 : somme de MOTS_DATA mots dès DEBUT_DATA
DEBUT_DATA = 0x90
MOTS_DATA = 0x1C10
SOMME_ENTETE = 0x8C                 # u32 : somme des MOTS_ENTETE premiers mots
MOTS_ENTETE = 0x23

# ── Équipe ───────────────────────────────────────────────────────────────────

# Résumé pour l'écran de chargement : copie de données tenues ailleurs.
RESUME_SURNOMS = 0x40               # 3 × 20 o : surnoms des monstres d'équipe
TABLE_EQUIPE = 0x7C                 # 3 × u16 espèce, puis 3 × u8 niveau
EQUIPE_IDS = 0xB4                   # 6 × u32 : ID de création des monstres
ROLES = ('equipe_1', 'equipe_2', 'equipe_3',
         'reserve_1', 'reserve_2', 'reserve_3')

# ── Monstres ─────────────────────────────────────────────────────────────────

DEBUT_MONSTRES = 0x1E8
TAILLE_MONSTRE = 0x84
NB_MONSTRES = 100
NB_COMPETENCES = 5

_FORMATS = {'u8': '<B', 'u16': '<H', 'u32': '<I', 'i32': '<i'}


@dataclass(frozen=True)
class Champ:
    cle: str
    offset: int
    type: str                       # 'u8', 'u16', 'u32', 'i32', 'texte' ou 'octets'
    libelle: str
    taille: int = 0                 # seulement pour 'texte' et 'octets'
    lecture_seule: bool = False
    noms: str | None = None         # table de noms associée (voir noms.py)
    miroir: int | None = None       # second offset où la même valeur est rangée

    @property
    def minimum(self) -> int:
        return -(1 << 31) if self.type == 'i32' else 0

    @property
    def maximum(self) -> int:
        bits = 8 * struct.calcsize(_FORMATS[self.type])
        return (1 << (bits - 1)) - 1 if self.type == 'i32' else (1 << bits) - 1

    def lire(self, buf, base: int):
        debut = base + self.offset
        if self.type == 'octets':
            return bytes(buf[debut: debut + self.taille])
        if self.type == 'texte':
            return texte.decoder(bytes(buf[debut: debut + self.taille]))
        return struct.unpack_from(_FORMATS[self.type], buf, debut)[0]

    def ecrire(self, buf, base: int, valeur) -> None:
        brut = self.en_octets(valeur)
        for offset in (self.offset, self.miroir):
            if offset is not None:
                buf[base + offset: base + offset + len(brut)] = brut

    def en_octets(self, valeur) -> bytes:
        if self.type == 'texte':
            try:
                return texte.encoder(valeur, self.taille)
            except ValueError as e:
                raise ValueError(f'{self.cle} : {e}') from None
        if self.type == 'octets':
            if len(valeur) != self.taille:
                raise ValueError(f'{self.cle} : {self.taille} octets attendus, '
                                 f'{len(valeur)} reçus')
            return bytes(valeur)
        if not self.minimum <= valeur <= self.maximum:
            raise ValueError(f'{self.cle} : {valeur} hors de {self.minimum}..{self.maximum}')
        return struct.pack(_FORMATS[self.type], valeur)


def _competences():
    for j in range(NB_COMPETENCES):
        yield Champ(f'competence_{j + 1}', 0x7A + 2 * j, 'u8', f'Compétence {j + 1}',
                    noms='competences')
        yield Champ(f'competence_{j + 1}_points', 0x7B + 2 * j, 'u8',
                    f'Compétence {j + 1} : points investis')


CHAMPS_MONSTRE = (
    Champ('surnom', 0x00, 'texte', 'Surnom', 20),
    Champ('id_creation', 0x14, 'u32', 'ID de création', lecture_seule=True),
    Champ('espece', 0x18, 'u16', 'Espèce', noms='especes'),
    Champ('variante', 0x1A, 'u8', 'Variante (0 normal, 1 X, 2 XY)'),
    Champ('polarite', 0x1B, 'u8', 'Polarité'),
    Champ('plus', 0x1C, 'u8', 'Synthèse +'),
    Champ('plus_base', 0x1E, 'u8', 'Synthèse + (base)'),
    Champ('pv', 0x20, 'u16', 'PV'),
    Champ('pm', 0x22, 'u16', 'PM'),
    Champ('pv_max', 0x24, 'u16', 'PV max'),
    Champ('pm_max', 0x26, 'u16', 'PM max'),
    Champ('attaque', 0x28, 'u16', 'Attaque'),
    Champ('defense', 0x2A, 'u16', 'Défense'),
    Champ('agilite', 0x2C, 'u16', 'Agilité'),
    Champ('sagesse', 0x2E, 'u16', 'Sagesse'),
    Champ('niveau', 0x30, 'u8', 'Niveau'),
    Champ('arme', 0x31, 'u8', 'Arme équipée', noms='objets'),
    Champ('tactique', 0x32, 'u8', 'Tactique'),
    Champ('experience', 0x34, 'u32', 'Expérience'),
    Champ('experience_suivant', 0x38, 'u32', 'Expérience du niveau suivant'),
    Champ('points_libres', 0x3C, 'u16', 'Points de compétence non attribués'),
    # Lignée : les grands-parents sont entrelacés (1a, 2a, 1b, 2b).
    Champ('parent_1', 0x40, 'u16', 'Parent 1', noms='especes'),
    Champ('parent_2', 0x42, 'u16', 'Parent 2', noms='especes'),
    Champ('gp_1a', 0x44, 'u16', 'Grand-parent 1a', noms='especes'),
    Champ('gp_2a', 0x46, 'u16', 'Grand-parent 2a', noms='especes'),
    Champ('gp_1b', 0x48, 'u16', 'Grand-parent 1b', noms='especes'),
    Champ('gp_2b', 0x4A, 'u16', 'Grand-parent 2b', noms='especes'),
    Champ('parent_1_variante', 0x4C, 'u8', 'Parent 1 : variante'),
    Champ('parent_2_variante', 0x4D, 'u8', 'Parent 2 : variante'),
    Champ('gp_1a_variante', 0x4E, 'u8', 'Grand-parent 1a : variante'),
    Champ('gp_2a_variante', 0x4F, 'u8', 'Grand-parent 2a : variante'),
    Champ('gp_1b_variante', 0x50, 'u8', 'Grand-parent 1b : variante'),
    Champ('gp_2b_variante', 0x51, 'u8', 'Grand-parent 2b : variante'),
    Champ('parent_1_surnom', 0x52, 'texte', 'Parent 1 : surnom', 20),
    Champ('parent_2_surnom', 0x66, 'texte', 'Parent 2 : surnom', 20),
    *_competences(),
)

CHAMP = {c.cle: c for c in CHAMPS_MONSTRE}

# Octets de l'enregistrement dont le rôle est inconnu : (offset, taille).
# Ils ne sont jamais réécrits, donc toujours préservés.
INCONNUS_MONSTRE = ((0x1D, 1), (0x1F, 1), (0x33, 1), (0x3E, 2))

# ── Joueur (offsets relatifs au début de la copie) ───────────────────────────
# Valeurs relevées sur une partie connue (13 h 07 min 07 s, « BKK », 2601 or,
# 11856 en banque, 245 victoires, 65 dressages, 41 synthèses). Nom et temps de
# jeu existent en double : résumé de l'écran de chargement (0x20-0x87) et
# données de partie (0x90+).

IMAGES_PAR_SECONDE = 30             # unité du temps de jeu

CHAMPS_JOUEUR = (
    # Date et heure de la dernière sauvegarde en jeu (horloge de la console),
    # vérifiées contre l'heure d'écriture des .dsv.
    Champ('sauvegarde_annee', 0x0C, 'u32', 'Année (depuis 2000)', lecture_seule=True),
    Champ('sauvegarde_mois', 0x10, 'u32', 'Mois', lecture_seule=True),
    Champ('sauvegarde_jour', 0x14, 'u32', 'Jour', lecture_seule=True),
    Champ('sauvegarde_jour_semaine', 0x18, 'u32', 'Jour de la semaine (0 = dimanche)',
          lecture_seule=True),
    Champ('sauvegarde_heure', 0x1C, 'u32', 'Heure', lecture_seule=True),
    Champ('sauvegarde_minute', 0x20, 'u32', 'Minute', lecture_seule=True),
    Champ('sauvegarde_seconde', 0x24, 'u32', 'Seconde', lecture_seule=True),
    Champ('temps_jeu', 0x28, 'u32', 'Temps de jeu', miroir=0x90),  # en 1/30 s
    Champ('nom', 0x2C, 'texte', 'Nom', 20, miroir=0x98),
    Champ('dernier_id_creation', 0x94, 'u32', 'Dernier ID de création attribué',
          lecture_seule=True),
    Champ('or', 0xAC, 'u32', 'Or sur soi'),
    Champ('banque', 0xB0, 'u32', 'Or en banque'),
    Champ('victoires', 0x1DC, 'u16', 'Victoires'),
    Champ('dressages', 0x1DE, 'u16', 'Monstres dressés'),
    Champ('syntheses', 0x1E0, 'u16', 'Monstres synthétisés'),
    # Emplacement dans le monde, relevé en jeu (location 57, -26,10 / 0 / 589,46).
    # Lecture seule : on ne le change qu'en bloc, vers un point relevé en jeu
    # (voir POINTS_TELEPORTATION). La carte a une copie dans le résumé, que le
    # jeu relit au chargement (elle devient la « location précédente »).
    Champ('location', 0x3A68, 'u8', 'Location', lecture_seule=True, miroir=0x86),
    Champ('location_precedente', 0x3A69, 'u8', 'Location précédente (?)', lecture_seule=True),
    Champ('position_x', 0x3A70, 'i32', 'Position X (centièmes)', lecture_seule=True),
    Champ('position_y', 0x3A74, 'i32', 'Position Y (centièmes)', lecture_seule=True),
    Champ('position_z', 0x3A78, 'i32', 'Position Z (centièmes)', lecture_seule=True),
)
CHAMP_JOUEUR = {c.cle: c for c in CHAMPS_JOUEUR}

# Bloc de position complet (0x3A68-0x3A83 : carte, carte précédente, X, Y, Z,
# orientation et deux champs inconnus), recopié de sauvegardes faites en jeu.
# Téléportation validée en jeu le 23/09/2026 (Archéopolis -> Albatros).
BLOC_POSITION = 0x3A68
POINTS_TELEPORTATION = {
    'Archéopolis': bytes.fromhex('3939000000000000cef5ffff0000000042e6000000400b00bc000000'),
    'Albatros (tablette du ranch)':
        bytes.fromhex('58580000a805000051fefeff00a000006dfeffff0080faffa0000000'),
    'Arène': bytes.fromhex('1839000000000000713902000e5b00005c3f030000b0f8ffa4000000'),
}

# ── Sac ──────────────────────────────────────────────────────────────────────
# Quantité possédée de chaque objet, indexée par son ID (armes comprises).
# Relevé sur une partie dont le contenu du sac était connu.

SAC = 0xCC
NB_OBJETS = 256
QUANTITE_MAX = 99                   # plafond du jeu (le format permettrait 255)

CHAMPS_SAC = {i: Champ(f'objet_{i}', SAC + i, 'u8', f'Objet {i}', noms='objets')
              for i in range(1, NB_OBJETS)}
