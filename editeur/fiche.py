"""Fiche d'un monstre : un champ de saisie par entrée de format.CHAMPS_MONSTRE,
rangés par onglet. Chaque modification est écrite aussitôt dans la sauvegarde."""
from PySide6.QtCore import Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (QFormLayout, QGridLayout, QLabel, QPlainTextEdit,
                               QSpinBox, QTabWidget, QVBoxLayout, QWidget)

from dqmj2p_save import format as F

ONGLETS = {
    'Identité': ('espece', 'variante', 'polarite', 'plus', 'plus_base',
                 'arme', 'tactique'),
    'Niveau et stats': ('niveau', 'experience', 'experience_suivant',
                        'pv', 'pv_max', 'pm', 'pm_max', 'attaque', 'defense',
                        'agilite', 'sagesse', 'points_libres'),
    'Lignée': ('parent_1', 'parent_1_variante', 'parent_2', 'parent_2_variante',
               'gp_1a', 'gp_1a_variante', 'gp_1b', 'gp_1b_variante',
               'gp_2a', 'gp_2a_variante', 'gp_2b', 'gp_2b_variante'),
}

QSPINBOX_MAX = 2**31 - 1


class Fiche(QTabWidget):
    modifiee = Signal()             # une valeur a été écrite dans la sauvegarde

    def __init__(self):
        super().__init__()
        self.monstre = None
        self.saisies: dict[str, QSpinBox] = {}

        for titre, cles in ONGLETS.items():
            page = QWidget()
            formulaire = QFormLayout(page)
            for cle in cles:
                formulaire.addRow(F.CHAMP[cle].libelle, self._saisie(cle))
            self.addTab(page, titre)

        page = QWidget()
        grille = QGridLayout(page)
        grille.addWidget(QLabel('Compétence (ID)'), 0, 1)
        grille.addWidget(QLabel('Points investis'), 0, 2)
        for j in range(1, F.NB_COMPETENCES + 1):
            grille.addWidget(QLabel(f'{j}'), j, 0)
            grille.addWidget(self._saisie(f'competence_{j}'), j, 1)
            grille.addWidget(self._saisie(f'competence_{j}_points'), j, 2)
        grille.setRowStretch(F.NB_COMPETENCES + 1, 1)
        self.addTab(page, 'Compétences')

        page = QWidget()
        disposition = QVBoxLayout(page)
        disposition.addWidget(QLabel('Enregistrement brut (0x84 octets). '
                                     'Les octets entre [ ] ont un rôle inconnu.'))
        self.hexa = QPlainTextEdit(readOnly=True)
        self.hexa.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        disposition.addWidget(self.hexa)
        self.addTab(page, 'Octets bruts')

        self.setEnabled(False)

    def _saisie(self, cle: str) -> QSpinBox:
        champ = F.CHAMP[cle]
        saisie = QSpinBox()
        saisie.setRange(0, min(champ.maximum, QSPINBOX_MAX))
        saisie.setToolTip(f'+0x{champ.offset:02X}, {champ.type}')
        saisie.valueChanged.connect(lambda v, cle=cle: self._ecrire(cle, v))
        self.saisies[cle] = saisie
        return saisie

    def afficher(self, monstre) -> None:
        self.monstre = None         # coupe l'écriture pendant le remplissage
        for cle, saisie in self.saisies.items():
            saisie.setValue(monstre[cle])
        self.monstre = monstre
        self._afficher_octets()
        self.setEnabled(True)

    def _ecrire(self, cle: str, valeur: int) -> None:
        if self.monstre is None or self.monstre[cle] == valeur:
            return
        self.monstre[cle] = valeur
        self._afficher_octets()
        self.modifiee.emit()

    def _afficher_octets(self) -> None:
        octets = self.monstre.octets
        inconnus = {off + k for off, n in F.INCONNUS_MONSTRE for k in range(n)}
        lignes = []
        for debut in range(0, len(octets), 16):
            cellules = [f'[{octets[i]:02X}]' if i in inconnus else f' {octets[i]:02X} '
                        for i in range(debut, min(debut + 16, len(octets)))]
            lignes.append(f'+{debut:02X}  ' + ''.join(cellules))
        self.hexa.setPlainText('\n'.join(lignes))
