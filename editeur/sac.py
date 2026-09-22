"""Onglet Sac : quantité de chaque objet, avec recherche et filtre."""
import unicodedata

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QHBoxLayout,
                               QHeaderView, QLineEdit, QSpinBox, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from dqmj2p_save import format as F
from dqmj2p_save import noms


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

        self.recherche = QLineEdit(placeholderText='Rechercher un objet…', clearButtonEnabled=True)
        self.recherche.textChanged.connect(self._filtrer)
        self.possedes = QCheckBox('Objets possédés seulement')
        self.possedes.toggled.connect(self._filtrer)
        barre = QHBoxLayout()
        barre.addWidget(self.recherche)
        barre.addWidget(self.possedes)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(('ID', 'Objet', 'Quantité'))
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        entete = self.table.horizontalHeader()
        entete.setSectionResizeMode(QHeaderView.ResizeToContents)
        entete.setSectionResizeMode(1, QHeaderView.Stretch)
        entete.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 90)

        disposition = QVBoxLayout(self)
        disposition.addLayout(barre)
        disposition.addWidget(self.table)
        self.setEnabled(False)

    def afficher(self, sac) -> None:
        self.sac = None             # coupe l'écriture pendant le remplissage
        # Objets sans nom : cachés, sauf si la sauvegarde en contient.
        ids = [i for i in F.CHAMPS_SAC if self.table_noms[i] != noms.INUTILISE or sac[i]]
        self.table.setRowCount(len(ids))
        self.quantites = {}
        for ligne, id_ in enumerate(ids):
            cellule = QTableWidgetItem(str(id_))
            cellule.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(ligne, 0, cellule)
            self.table.setItem(ligne, 1, QTableWidgetItem(self.table_noms[id_]))
            quantite = QSpinBox(maximum=max(F.QUANTITE_MAX, sac[id_]))
            quantite.setValue(sac[id_])
            quantite.valueChanged.connect(lambda v, id_=id_: self._ecrire(id_, v))
            self.table.setCellWidget(ligne, 2, quantite)
            self.quantites[id_] = quantite
        self.sac = sac
        self._filtrer()
        self.setEnabled(True)

    def _ecrire(self, id_: int, quantite: int) -> None:
        if self.sac is None:
            return
        self.sac[id_] = quantite
        self.modifiee.emit()

    def _filtrer(self) -> None:
        motif = _sans_accents(self.recherche.text())
        for ligne in range(self.table.rowCount()):
            id_ = int(self.table.item(ligne, 0).text())
            visible = (motif in _sans_accents(self.table.item(ligne, 1).text())
                       and (not self.possedes.isChecked() or self.quantites[id_].value()))
            self.table.setRowHidden(ligne, not visible)
