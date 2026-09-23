"""Onglet Sac : quantité de chaque objet, avec recherche, filtre et la
description du jeu (au survol du nom, et sous la liste pour l'objet choisi)."""
import unicodedata

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QFrame, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QSpinBox,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from dqmj2p_save import format as F
from dqmj2p_save import noms
from dqmj2p_save.langue import tr


def _sans_accents(texte: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', texte.casefold())
                   if unicodedata.category(c) != 'Mn')


class PageSac(QWidget):
    modifiee = Signal()

    def __init__(self):
        super().__init__()
        self.sac = None
        self.table_noms = noms.table('objets')
        self.quantites: dict[int, QSpinBox] = {}

        self.recherche = QLineEdit(placeholderText=tr('Rechercher dans les noms et descriptions…'),
                                   clearButtonEnabled=True)
        self.recherche.textChanged.connect(self._filtrer)
        self.possedes = QCheckBox(tr('Objets possédés seulement'))
        self.possedes.toggled.connect(self._filtrer)
        barre = QHBoxLayout()
        barre.addWidget(self.recherche)
        barre.addWidget(self.possedes)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels((tr('ID'), tr('Objet'), tr('Quantité')))
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.itemSelectionChanged.connect(self._afficher_description)
        entete = self.table.horizontalHeader()
        entete.setSectionResizeMode(QHeaderView.ResizeToContents)
        entete.setSectionResizeMode(1, QHeaderView.Stretch)
        entete.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 90)

        self.titre_description = QLabel()
        self.titre_description.setStyleSheet('font-weight: bold')
        self.description = QLabel(wordWrap=True)
        self.description.setMinimumHeight(self.description.fontMetrics().lineSpacing() * 2)
        encadre = QFrame(frameShape=QFrame.StyledPanel)
        colonne = QVBoxLayout(encadre)
        colonne.addWidget(self.titre_description)
        colonne.addWidget(self.description)

        disposition = QVBoxLayout(self)
        disposition.addLayout(barre)
        disposition.addWidget(self.table)
        disposition.addWidget(encadre)
        self.setEnabled(False)

    def afficher(self, sac) -> None:
        self.sac = None             # coupe l'écriture pendant le remplissage
        # Objets sans nom : cachés, sauf si la sauvegarde en contient.
        ids = [i for i in F.CHAMPS_SAC if not self.table_noms.inutilise(i) or sac[i]]
        self.table.setRowCount(len(ids))
        self.quantites = {}
        for ligne, id_ in enumerate(ids):
            cellule = QTableWidgetItem(str(id_))
            cellule.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(ligne, 0, cellule)
            nom = QTableWidgetItem(self.table_noms[id_])
            nom.setToolTip(noms.aide_objet(id_))
            self.table.setItem(ligne, 1, nom)
            quantite = QSpinBox(maximum=max(F.QUANTITE_MAX, sac[id_]))
            quantite.setValue(sac[id_])
            quantite.valueChanged.connect(lambda v, id_=id_: self._ecrire(id_, v))
            self.table.setCellWidget(ligne, 2, quantite)
            self.quantites[id_] = quantite
        self.sac = sac
        self._filtrer()
        self._afficher_description()
        self.setEnabled(True)

    def _afficher_description(self) -> None:
        lignes = self.table.selectionModel().selectedRows()
        if not lignes:
            self.titre_description.setText(tr('Description'))
            self.description.setText(tr('Sélectionnez un objet pour lire sa description.'))
            return
        id_ = int(self.table.item(lignes[0].row(), 0).text())
        self.titre_description.setText(self.table_noms[id_])
        self.description.setText(noms.aide_objet(id_) or tr('(pas de description)'))

    def _ecrire(self, id_: int, quantite: int) -> None:
        if self.sac is None:
            return
        self.sac[id_] = quantite
        self.modifiee.emit()

    def _filtrer(self) -> None:
        motif = _sans_accents(self.recherche.text())
        for ligne in range(self.table.rowCount()):
            id_ = int(self.table.item(ligne, 0).text())
            texte = self.table.item(ligne, 1).text() + ' ' + noms.aide_objet(id_)
            visible = (motif in _sans_accents(texte)
                       and (not self.possedes.isChecked() or self.quantites[id_].value()))
            self.table.setRowHidden(ligne, not visible)
