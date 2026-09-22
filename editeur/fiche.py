"""Fiche d'un monstre : un champ de saisie par entrée de format.CHAMPS_MONSTRE,
rangés par onglet. Chaque modification est écrite aussitôt dans la sauvegarde."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (QFormLayout, QGridLayout, QHBoxLayout, QLabel,
                               QPlainTextEdit, QTabWidget, QVBoxLayout, QWidget)

from dqmj2p_save import format as F
from dqmj2p_save import bestiaire, noms

from . import icones

from .saisies import Liaison
from .synthese import PageSynthese

ONGLETS = {
    'Identité': ('surnom', 'espece', 'variante', 'polarite', 'plus', 'plus_base',
                 'arme', 'tactique'),
    'Niveau et stats': ('niveau', 'experience', 'experience_suivant',
                        'pv', 'pv_max', 'pm', 'pm_max', 'attaque', 'defense',
                        'agilite', 'sagesse', 'points_libres'),
    'Lignée': ('parent_1', 'parent_1_surnom', 'parent_1_variante',
               'parent_2', 'parent_2_surnom', 'parent_2_variante',
               'gp_1a', 'gp_1a_variante', 'gp_1b', 'gp_1b_variante',
               'gp_2a', 'gp_2a_variante', 'gp_2b', 'gp_2b_variante'),
}


class Fiche(QWidget):
    """En-tête (icône, surnom, espèce, niveau) au-dessus des onglets."""

    def __init__(self):
        super().__init__()
        self.onglets = _Onglets()
        self.liaison = self.onglets.liaison
        self._espece_affichee = None
        self.liaison.modifiee.connect(self._afficher_entete)

        self.image = QLabel(alignment=Qt.AlignCenter)
        self.image.setFixedWidth(icones.CASE * 2 + 8)
        self.titre = QLabel()
        police = QFont(self.titre.font())
        police.setPointSizeF(police.pointSizeF() * 1.5)
        police.setBold(True)
        self.titre.setFont(police)
        self.sous_titre = QLabel()
        textes = QVBoxLayout()
        textes.addStretch()
        textes.addWidget(self.titre)
        textes.addWidget(self.sous_titre)
        textes.addStretch()
        entete = QHBoxLayout()
        entete.addWidget(self.image)
        entete.addLayout(textes, 1)

        disposition = QVBoxLayout(self)
        disposition.setContentsMargins(0, 0, 0, 0)
        disposition.addLayout(entete)
        disposition.addWidget(self.onglets, 1)
        self.setEnabled(False)

    @property
    def monstre(self):
        return self.liaison.vue

    def afficher(self, monstre) -> None:
        self.onglets.afficher(monstre)
        self._afficher_entete()
        self.setEnabled(True)

    def _afficher_entete(self) -> None:
        m = self.monstre
        espece = m['espece']
        self.image.setPixmap(icones.agrandie(espece))
        self.titre.setText(m['surnom'] or noms.table('especes')[espece])
        infos = bestiaire.fiche(espece)
        details = [noms.table('especes')[espece]]
        if infos.rang:
            details.append(f'rang {infos.rang}')
        if infos.famille:
            chemin = icones.chemin_famille(infos.famille)
            image = (f'<img src="{chemin.as_uri()}" width="14" height="20" '
                     f'style="vertical-align: middle"> ' if chemin else '')
            details.append(image + infos.famille)
        if infos.taille and infos.taille > 1:
            details.append(f'taille {infos.taille}')
        details += [f"niveau {m['niveau']}", f'emplacement {m.emplacement}']
        self.sous_titre.setText('  —  '.join(details))
        if espece != self._espece_affichee:
            self._espece_affichee = espece
            self.onglets.synthese.afficher(espece)


class _Onglets(QTabWidget):
    def __init__(self):
        super().__init__()
        self.liaison = Liaison(F.CHAMP)
        self.liaison.modifiee.connect(self._afficher_octets)

        for titre, cles in ONGLETS.items():
            page = QWidget()
            formulaire = QFormLayout(page)
            for cle in cles:
                formulaire.addRow(F.CHAMP[cle].libelle, self.liaison.saisie(cle))
            self.addTab(page, titre)

        page = QWidget()
        grille = QGridLayout(page)
        grille.addWidget(QLabel('Compétence'), 0, 1)
        grille.addWidget(QLabel('Points investis'), 0, 2)
        for j in range(1, F.NB_COMPETENCES + 1):
            grille.addWidget(QLabel(f'{j}'), j, 0)
            grille.addWidget(self.liaison.saisie(f'competence_{j}'), j, 1)
            grille.addWidget(self.liaison.saisie(f'competence_{j}_points'), j, 2)
        grille.setColumnStretch(1, 1)
        grille.setRowStretch(F.NB_COMPETENCES + 1, 1)
        self.addTab(page, 'Compétences')

        self.synthese = PageSynthese()
        self.addTab(self.synthese, 'Synthèse')

        page = QWidget()
        disposition = QVBoxLayout(page)
        disposition.addWidget(QLabel('Enregistrement brut (0x84 octets). '
                                     'Les octets entre [ ] ont un rôle inconnu.'))
        self.hexa = QPlainTextEdit(readOnly=True)
        self.hexa.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        disposition.addWidget(self.hexa)
        self.addTab(page, 'Octets bruts')

    def afficher(self, monstre) -> None:
        self.liaison.afficher(monstre)
        self._afficher_octets()

    def _afficher_octets(self) -> None:
        octets = self.liaison.vue.octets
        inconnus = {off + k for off, n in F.INCONNUS_MONSTRE for k in range(n)}
        lignes = []
        for debut in range(0, len(octets), 16):
            cellules = [f'[{octets[i]:02X}]' if i in inconnus else f' {octets[i]:02X} '
                        for i in range(debut, min(debut + 16, len(octets)))]
            lignes.append(f'+{debut:02X}  ' + ''.join(cellules))
        self.hexa.setPlainText('\n'.join(lignes))
