"""Lecture et écriture d'une sauvegarde DQMJ2P, en place.

Principe : les octets d'origine restent la source de vérité. On ne modifie que
les champs édités, puis on recalcule les sommes de contrôle et on recopie la
copie active dans les deux emplacements. Tout octet dont on ignore le rôle
(champs inconnus, zone après 0xE200, pied de page .dsv) est donc préservé.

Formats acceptés :
  .sav  mémoire brute de 65536 octets ;
  .dsv  la même chose suivie du pied de page DeSmuME / DraStic (122 octets).
"""
import os
import shutil
import struct
from datetime import datetime
from pathlib import Path

from . import format as F
from .monstre import Monstre
from .vue import Joueur, Sac


class ErreurSauvegarde(Exception):
    pass


def calculer_sommes(copie) -> tuple[int, int]:
    """Renvoie (somme data, somme en-tête) d'une copie, telle qu'elle serait
    une fois la somme data rangée à sa place."""
    data = sum(struct.unpack_from(f'<{F.MOTS_DATA}I', copie, F.DEBUT_DATA)) & 0xFFFFFFFF
    entete = bytearray(copie[:4 * F.MOTS_ENTETE])
    struct.pack_into('<I', entete, F.SOMME_DATA, data)
    return data, sum(struct.unpack(f'<{F.MOTS_ENTETE}I', entete)) & 0xFFFFFFFF


def copie_valide(copie) -> bool:
    if bytes(copie[:4]) != F.MAGIC:
        return False
    stockees = struct.unpack_from('<2I', copie, F.SOMME_DATA)
    return stockees == calculer_sommes(copie)


class Sauvegarde:
    def __init__(self, contenu: bytes, chemin: Path | None = None):
        if len(contenu) == F.TAILLE_BRUTE:
            self.pied = b''
        elif len(contenu) > F.TAILLE_BRUTE and contenu.endswith(F.MARQUEUR_DSV):
            self.pied = bytes(contenu[F.TAILLE_BRUTE:])
        else:
            raise ErreurSauvegarde(
                f'{len(contenu)} octets : ni un .sav brut ({F.TAILLE_BRUTE} octets) '
                f'ni un .dsv (pied de page {F.MARQUEUR_DSV.decode()}).')

        self.chemin = chemin
        self.brut = bytearray(contenu[:F.TAILLE_BRUTE])
        valides = [i for i, off in enumerate(F.COPIES)
                   if copie_valide(self.brut[off: off + F.TAILLE_COPIE])]
        if not valides:
            raise ErreurSauvegarde(
                'Aucune des deux copies n\'est valide (en-tête SIZ ou sommes de '
                'contrôle incorrects) : ce n\'est pas une sauvegarde DQMJ2P, ou '
                'elle est vide ou corrompue.')
        # Les deux copies sont identiques dans les sauvegardes réelles ; si
        # elles divergent, la première valide fait foi.
        self.index_copie = valides[0]
        debut = F.COPIES[self.index_copie]
        self.copie = bytearray(self.brut[debut: debut + F.TAILLE_COPIE])
        self.modifiee = False
        self.joueur = Joueur(self)
        self.sac = Sac(self)

    @classmethod
    def ouvrir(cls, chemin) -> 'Sauvegarde':
        chemin = Path(chemin)
        return cls(chemin.read_bytes(), chemin)

    # ── Monstres ─────────────────────────────────────────────────────────────

    def monstre(self, emplacement: int) -> Monstre:
        if not 0 <= emplacement < F.NB_MONSTRES:
            raise IndexError(emplacement)
        return Monstre(self, emplacement)

    def monstres(self) -> list[Monstre]:
        """Monstres présents, dans l'ordre des emplacements."""
        return [m for m in map(self.monstre, range(F.NB_MONSTRES)) if m.present]

    def restaurer_surnoms(self) -> list[Monstre]:
        """Donne le nom complet de l'espèce aux monstres qui portent encore le
        surnom abrégé de la capture. Renvoie les monstres renommés."""
        renommes = [m for m in self.monstres() if m.surnom_par_defaut]
        for m in renommes:
            m['surnom'] = m.surnom_complet()
        return renommes

    def dupliquer(self, modele: Monstre) -> Monstre:
        """Copie un monstre dans le premier emplacement libre du ranch, avec un
        nouvel ID de création. Le jeu range les monstres vivants dans les
        emplacements 0..N-1 : la copie va en N."""
        emplacement = len(self.monstres())
        if emplacement >= F.NB_MONSTRES:
            raise ErreurSauvegarde(f'ranch plein ({F.NB_MONSTRES} monstres)')
        copie = self.monstre(emplacement)
        self.copie[copie.base: copie.base + F.TAILLE_MONSTRE] = modele.octets
        # Champs en lecture seule pour l'utilisateur : écriture directe.
        nouvel_id = self.joueur['dernier_id_creation'] + 1
        F.CHAMP['id_creation'].ecrire(self.copie, copie.base, nouvel_id)
        F.CHAMP_JOUEUR['dernier_id_creation'].ecrire(self.copie, 0, nouvel_id)
        self.modifiee = True
        return copie

    def teleporter(self, point: str) -> None:
        """Place le joueur sur un point de F.POINTS_TELEPORTATION, relevé en
        jeu, et met à jour la carte du résumé de l'écran de chargement."""
        bloc = F.POINTS_TELEPORTATION[point]
        self.copie[F.BLOC_POSITION: F.BLOC_POSITION + len(bloc)] = bloc
        champ = F.CHAMP_JOUEUR['location']
        self.copie[champ.miroir] = bloc[0]
        self.modifiee = True

    def regler_horloge(self, valeur: int) -> None:
        """Règle l'horloge jour/nuit et l'indicateur de nuit qui l'accompagne."""
        valeur %= F.DUREE_CYCLE
        self.joueur['horloge'] = valeur
        octet, bit = F.INDICATEUR_NUIT
        avant = self.copie[octet]
        self.copie[octet] = avant | bit if valeur >= F.DEBUT_NUIT else avant & ~bit
        if self.copie[octet] != avant:
            self.modifiee = True

    def ids_equipe(self) -> list[int]:
        return list(struct.unpack_from('<6I', self.copie, F.EQUIPE_IDS))

    def role(self, monstre: Monstre) -> str:
        """'equipe_1'..'reserve_3', ou 'ranch'."""
        ids = self.ids_equipe()
        cid = monstre['id_creation']
        return F.ROLES[ids.index(cid)] if cid in ids else 'ranch'

    def _synchroniser_resume_equipe(self) -> None:
        """Recopie surnom, espèce et niveau des 3 monstres d'équipe dans le
        résumé de l'écran de chargement, que le jeu tient à jour de son côté."""
        par_id = {m['id_creation']: m for m in self.monstres()}
        surnom = F.CHAMP['surnom']
        self.copie[F.TAILLE_EQUIPE] = sum(cid in par_id for cid in self.ids_equipe()[:3])
        for i, cid in enumerate(self.ids_equipe()[:3]):
            m = par_id.get(cid)
            struct.pack_into('<H', self.copie, F.TABLE_EQUIPE + 2 * i,
                             m['espece'] if m else 0)
            self.copie[F.TABLE_EQUIPE + 6 + i] = m['niveau'] if m else 0
            if m:
                debut = F.RESUME_SURNOMS + i * surnom.taille
                source = m.base + surnom.offset
                self.copie[debut: debut + surnom.taille] = \
                    self.copie[source: source + surnom.taille]

    # ── Écriture ─────────────────────────────────────────────────────────────

    def en_octets(self) -> bytes:
        """Contenu complet du fichier. Sans modification, c'est exactement le
        fichier d'origine (si ses deux copies étaient valides)."""
        if self.modifiee:
            self._synchroniser_resume_equipe()
            struct.pack_into('<2I', self.copie, F.SOMME_DATA, *calculer_sommes(self.copie))
        brut = bytearray(self.brut)
        for debut in F.COPIES:
            brut[debut: debut + F.TAILLE_COPIE] = self.copie
        return bytes(brut) + self.pied

    def enregistrer(self, chemin=None, garder_original: bool = True) -> Path | None:
        """Écrit la sauvegarde. Si le fichier cible existe et garder_original
        est vrai, il est d'abord copié en <nom>.<horodatage>.bak, dont le
        chemin est renvoyé."""
        chemin = Path(chemin or self.chemin)
        contenu = self.en_octets()
        copie_bak = None
        if garder_original and chemin.exists():
            horodatage = datetime.now().strftime('%Y%m%d-%H%M%S')
            copie_bak = chemin.with_name(f'{chemin.name}.{horodatage}.bak')
            shutil.copy2(chemin, copie_bak)
        temporaire = chemin.with_name(chemin.name + '.tmp')
        temporaire.write_bytes(contenu)
        os.replace(temporaire, chemin)
        self.chemin = chemin
        self.modifiee = False
        return copie_bak
