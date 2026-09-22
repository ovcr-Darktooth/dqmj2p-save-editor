"""Cartographie du format de sauvegarde de DQMJ2 Professional.

Tout ce qui est connu du format vit ici, sous forme de tables. Un champ
nouvellement identifié s'ajoute en une ligne dans CHAMPS_MONSTRE (ou dans une
future table d'en-tête), sans toucher au reste du code.

Offsets relevés par Ceris White (save_converter.py du projet DQMJ2Pro
Translation), vérifiés sur des sauvegardes réelles. Voir docs/format-sauvegarde.md.
"""
import struct
from dataclasses import dataclass

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

TABLE_EQUIPE = 0x7C                 # 3 × u16 espèce, puis 3 × u8 niveau
EQUIPE_IDS = 0xB4                   # 6 × u32 : ID de création des monstres
ROLES = ('equipe_1', 'equipe_2', 'equipe_3',
         'reserve_1', 'reserve_2', 'reserve_3')

# ── Monstres ─────────────────────────────────────────────────────────────────

DEBUT_MONSTRES = 0x1E8
TAILLE_MONSTRE = 0x84
NB_MONSTRES = 100
NB_COMPETENCES = 5

_FORMATS = {'u8': '<B', 'u16': '<H', 'u32': '<I'}


@dataclass(frozen=True)
class Champ:
    cle: str
    offset: int
    type: str                       # 'u8', 'u16', 'u32' ou 'octets'
    libelle: str
    taille: int = 0                 # seulement pour 'octets'
    lecture_seule: bool = False
    noms: str | None = None         # table de noms associée (voir noms.py)

    @property
    def maximum(self) -> int:
        return (1 << (8 * struct.calcsize(_FORMATS[self.type]))) - 1

    def lire(self, buf, base: int):
        if self.type == 'octets':
            return bytes(buf[base + self.offset: base + self.offset + self.taille])
        return struct.unpack_from(_FORMATS[self.type], buf, base + self.offset)[0]

    def ecrire(self, buf, base: int, valeur) -> None:
        if self.type == 'octets':
            valeur = bytes(valeur)
            if len(valeur) != self.taille:
                raise ValueError(f'{self.cle} : {self.taille} octets attendus, '
                                 f'{len(valeur)} reçus')
            buf[base + self.offset: base + self.offset + self.taille] = valeur
            return
        if not 0 <= valeur <= self.maximum:
            raise ValueError(f'{self.cle} : {valeur} hors de 0..{self.maximum}')
        struct.pack_into(_FORMATS[self.type], buf, base + self.offset, valeur)


def _competences():
    for j in range(NB_COMPETENCES):
        yield Champ(f'competence_{j + 1}', 0x7A + 2 * j, 'u8', f'Compétence {j + 1}',
                    noms='competences')
        yield Champ(f'competence_{j + 1}_points', 0x7B + 2 * j, 'u8',
                    f'Compétence {j + 1} : points investis')


CHAMPS_MONSTRE = (
    Champ('surnom', 0x00, 'octets', 'Surnom (codage du jeu)', 16),
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
    Champ('arme', 0x31, 'u8', 'Arme équipée'),
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
    Champ('parent_1_surnom', 0x52, 'octets', 'Parent 1 : surnom', 16),
    Champ('parent_2_surnom', 0x66, 'octets', 'Parent 2 : surnom', 16),
    *_competences(),
)

CHAMP = {c.cle: c for c in CHAMPS_MONSTRE}

# Octets de l'enregistrement dont le rôle est inconnu : (offset, taille).
# Ils ne sont jamais réécrits, donc toujours préservés.
INCONNUS_MONSTRE = (
    (0x10, 4), (0x1D, 1), (0x1F, 1), (0x33, 1), (0x3E, 2),
    (0x62, 4), (0x76, 4),
)
