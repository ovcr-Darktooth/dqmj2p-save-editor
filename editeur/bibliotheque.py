"""Onglet Bibliothèque : monstres vus et dressés, attributs et compétences
vus, comme la bibliothèque du jeu. Lecture seule tant que l'écriture de ces
champs n'a pas été essayée en jeu."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QFrame,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QTableWidget, QTableWidgetItem, QTabWidget,
                               QVBoxLayout, QWidget)

from dqmj2p_save import bestiaire, noms
from dqmj2p_save import format as F

from . import icones
from .sac import _sans_accents

COCHE = '✓'
FAMILLE_INCONNUE = 'Famille inconnue'
ETATS = ('Toutes les espèces', 'Dressées', 'Vues', 'Vues, pas dressées', 'Jamais vues')


def _cellule(valeur, alignement=Qt.AlignLeft | Qt.AlignVCenter) -> QTableWidgetItem:
    """Cellule triable : un entier se trie comme un nombre."""
    cellule = QTableWidgetItem()
    cellule.setData(Qt.DisplayRole, valeur)
    cellule.setTextAlignment(alignement)
    return cellule


def _table(colonnes: tuple[str, ...], etiree: int) -> QTableWidget:
    table = QTableWidget(0, len(colonnes))
    table.setHorizontalHeaderLabels(colonnes)
    table.verticalHeader().hide()
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.sortByColumn(0, Qt.AscendingOrder)
    entete = table.horizontalHeader()
    entete.setSectionResizeMode(QHeaderView.ResizeToContents)
    entete.setSectionResizeMode(etiree, QHeaderView.Stretch)
    return table


class PageMonstres(QWidget):
    COLONNES = ('ID', 'Fam.', 'Espèce', 'Rang', 'Vue', 'Dressée')

    def __init__(self):
        super().__init__()
        self.especes = noms.table('especes')
        self.vues: set[int] = set()
        self.dressees: set[int] = set()

        self.recherche = QLineEdit(placeholderText='Rechercher une espèce…',
                                   clearButtonEnabled=True)
        self.famille = QComboBox()
        familles = sorted({f for i in range(len(self.especes))
                           if (f := bestiaire.fiche(i).famille)})
        self.famille.addItems(['Toutes les familles', *familles, FAMILLE_INCONNUE])
        self.etat = QComboBox()
        self.etat.addItems(ETATS)
        for filtre in (self.recherche.textChanged, self.famille.currentIndexChanged,
                       self.etat.currentIndexChanged):
            filtre.connect(self._filtrer)
        barre = QHBoxLayout()
        barre.addWidget(self.recherche, 1)
        barre.addWidget(self.famille)
        barre.addWidget(self.etat)

        self.table = _table(self.COLONNES, self.COLONNES.index('Espèce'))
        self.table.verticalHeader().setDefaultSectionSize(icones.CASE + 4)
        self.table.setIconSize(icones.TAILLE_CASE)
        self.compteur = QLabel()

        disposition = QVBoxLayout(self)
        disposition.addLayout(barre)
        disposition.addWidget(self.table)
        disposition.addWidget(self.compteur)

    def afficher(self, bibliotheque) -> None:
        self.vues = bibliotheque.especes_vues()
        self.dressees = bibliotheque.especes_dressees()
        # Espèces sans nom : cachées, sauf si la sauvegarde les a vues. Au-delà
        # des bits de la bibliothèque, les « espèces » X et XY sont des variantes.
        ids = [i for i in range(1, F.NB_BITS_ESPECES)
               if self.especes[i] != noms.INUTILISE or i in self.vues]
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(ids))
        centre = Qt.AlignCenter
        for ligne, id_ in enumerate(ids):
            fiche = bestiaire.fiche(id_)
            numero = _cellule(id_, Qt.AlignRight | Qt.AlignVCenter)
            numero.setData(Qt.UserRole, fiche.famille or FAMILLE_INCONNUE)
            famille = _cellule(fiche.famille or '', centre)
            famille.setData(Qt.DecorationRole, icones.famille(fiche.famille))
            famille.setToolTip(fiche.famille or FAMILLE_INCONNUE)
            famille.setForeground(Qt.transparent)    # l'icône suffit, le texte sert au tri
            espece = _cellule(self.especes[id_])
            espece.setIcon(icones.icone(id_))
            cellules = (numero, famille, espece, _cellule(fiche.rang or '', centre),
                        _cellule(COCHE if id_ in self.vues else '', centre),
                        _cellule(COCHE if id_ in self.dressees else '', centre))
            for colonne, cellule in enumerate(cellules):
                self.table.setItem(ligne, colonne, cellule)
        self.table.setSortingEnabled(True)
        self._filtrer()

    def _filtrer(self) -> None:
        motif = _sans_accents(self.recherche.text())
        famille = self.famille.currentText() if self.famille.currentIndex() else None
        etat = self.etat.currentText()
        affichees = 0
        for ligne in range(self.table.rowCount()):
            numero = self.table.item(ligne, 0)
            id_ = numero.data(Qt.DisplayRole)
            vue, dressee = id_ in self.vues, id_ in self.dressees
            visible = (motif in _sans_accents(self.table.item(ligne, 2).text())
                       and famille in (None, numero.data(Qt.UserRole))
                       and {'Dressées': dressee, 'Vues': vue,
                            'Vues, pas dressées': vue and not dressee,
                            'Jamais vues': not vue}.get(etat, True))
            self.table.setRowHidden(ligne, not visible)
            affichees += visible
        self.compteur.setText(
            f'{len(self.vues)} espèces vues, {len(self.dressees)} dressées'
            f' — {affichees} affichée(s) sur {self.table.rowCount()}')


class PageListe(QWidget):
    """Attributs ou compétences : un seul état, vu ou non."""

    def __init__(self, nom_table: str, singulier: str, aide=None):
        super().__init__()
        self.table_noms = noms.table(nom_table)
        self.singulier = singulier
        self.aide = aide
        self.vus: set[int] = set()

        self.recherche = QLineEdit(placeholderText='Rechercher…', clearButtonEnabled=True)
        self.recherche.textChanged.connect(self._filtrer)
        self.seulement_vus = QCheckBox('Vus seulement')
        self.seulement_vus.toggled.connect(self._filtrer)
        barre = QHBoxLayout()
        barre.addWidget(self.recherche, 1)
        barre.addWidget(self.seulement_vus)

        self.table = _table(('ID', singulier, 'Vu'), 1)
        self.compteur = QLabel()
        disposition = QVBoxLayout(self)
        disposition.addLayout(barre)
        disposition.addWidget(self.table)

        if aide:
            self.table.itemSelectionChanged.connect(self._afficher_description)
            self.titre_description = QLabel(styleSheet='font-weight: bold')
            self.description = QLabel(wordWrap=True)
            self.description.setMinimumHeight(self.description.fontMetrics().lineSpacing() * 3)
            encadre = QFrame(frameShape=QFrame.StyledPanel)
            colonne = QVBoxLayout(encadre)
            colonne.addWidget(self.titre_description)
            colonne.addWidget(self.description)
            disposition.addWidget(encadre)
            self._afficher_description()
        disposition.addWidget(self.compteur)

    def afficher(self, vus: set[int]) -> None:
        self.vus = vus - {0}             # le bit 0 (« aucun ») n'est pas une entrée
        ids = [i for i in range(1, len(self.table_noms))
               if self.table_noms[i] != noms.INUTILISE or i in vus]
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(ids))
        for ligne, id_ in enumerate(ids):
            nom = _cellule(self.table_noms[id_])
            if self.aide:
                nom.setToolTip(self.aide(id_))
            cellules = (_cellule(id_, Qt.AlignRight | Qt.AlignVCenter), nom,
                        _cellule(COCHE if id_ in vus else '', Qt.AlignCenter))
            for colonne, cellule in enumerate(cellules):
                self.table.setItem(ligne, colonne, cellule)
        self.table.setSortingEnabled(True)
        self._filtrer()

    def _afficher_description(self) -> None:
        lignes = self.table.selectionModel().selectedRows()
        if not lignes:
            self.titre_description.setText('Description')
            self.description.setText(f'Sélectionnez un {self.singulier.lower()} '
                                     'pour lire sa description.')
            return
        id_ = self.table.item(lignes[0].row(), 0).data(Qt.DisplayRole)
        self.titre_description.setText(self.table_noms[id_])
        self.description.setText(self.aide(id_) or '(pas de description)')

    def _filtrer(self) -> None:
        motif = _sans_accents(self.recherche.text())
        affiches = 0
        for ligne in range(self.table.rowCount()):
            id_ = self.table.item(ligne, 0).data(Qt.DisplayRole)
            texte = self.table.item(ligne, 1).text()
            if self.aide:
                texte += ' ' + self.aide(id_)
            visible = (motif in _sans_accents(texte)
                       and (id_ in self.vus or not self.seulement_vus.isChecked()))
            self.table.setRowHidden(ligne, not visible)
            affiches += visible
        self.compteur.setText(f'{len(self.vus)} vus — {affiches} affiché(s) '
                              f'sur {self.table.rowCount()}')


class PageBibliotheque(QTabWidget):
    def __init__(self):
        super().__init__()
        self.monstres = PageMonstres()
        self.attributs = PageListe('attributs', 'Attribut', noms.aide_attribut)
        self.competences = PageListe('competences', 'Compétence')
        self.addTab(self.monstres, 'Monstres')
        self.addTab(self.attributs, 'Attributs')
        self.addTab(self.competences, 'Compétences')
        self.setEnabled(False)

    def afficher(self, bibliotheque) -> None:
        self.monstres.afficher(bibliotheque)
        self.attributs.afficher(bibliotheque.attributs())
        self.competences.afficher(bibliotheque.competences())
        self.setEnabled(True)
