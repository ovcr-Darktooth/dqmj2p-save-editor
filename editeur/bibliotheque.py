"""Onglet Bibliothèque : monstres vus et dressés, attributs et compétences
vus, comme la bibliothèque du jeu. Chaque case se coche ou se décoche ; les
actions « Lignes affichées » s'appliquent à tout ce que laissent passer les
filtres."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QFrame,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMenu,
                               QTableWidget, QTableWidgetItem, QTabWidget,
                               QToolButton, QVBoxLayout, QWidget)

from dqmj2p_save import bestiaire, noms
from dqmj2p_save import format as F
from dqmj2p_save.langue import tr

from . import icones
from .sac import _sans_accents

FAMILLE_INCONNUE = 'Famille inconnue'
# Filtre d'état : libellé -> test (vue, dressée).
ETATS = {
    'Toutes les espèces': lambda vue, dressee: True,
    'Dressées': lambda vue, dressee: dressee,
    'Vues': lambda vue, dressee: vue,
    'Vues, pas dressées': lambda vue, dressee: vue and not dressee,
    'Jamais vues': lambda vue, dressee: not vue,
}


def _cellule(valeur, alignement=Qt.AlignLeft | Qt.AlignVCenter) -> QTableWidgetItem:
    """Cellule triable : un entier se trie comme un nombre."""
    cellule = QTableWidgetItem()
    cellule.setData(Qt.DisplayRole, valeur)
    cellule.setTextAlignment(alignement)
    return cellule


class Case(QTableWidgetItem):
    """Case à cocher, triée selon son état."""

    def __init__(self, cochee: bool):
        super().__init__()
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
        # Toujours explicite : sans état posé, Qt ne dessine pas la case.
        self.setCheckState(Qt.Checked if cochee else Qt.Unchecked)

    def cochee(self) -> bool:
        return self.checkState() == Qt.Checked

    def cocher(self, cochee: bool) -> None:
        if self.checkState() != (etat := Qt.Checked if cochee else Qt.Unchecked):
            self.setCheckState(etat)

    def __lt__(self, autre):
        return self.cochee() < autre.cochee()


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


def _bouton_actions(actions: list[tuple[str, callable]]) -> QToolButton:
    bouton = QToolButton(text=tr('Lignes affichées'), popupMode=QToolButton.InstantPopup)
    menu = QMenu(bouton)
    for texte, slot in actions:
        menu.addAction(texte, slot)
    bouton.setMenu(menu)
    return bouton


class PageMonstres(QWidget):
    modifiee = Signal()
    COLONNES = ('ID', 'Fam.', 'Espèce', 'Rang', 'Vue', 'Dressée')
    VUE, DRESSEE = COLONNES.index('Vue'), COLONNES.index('Dressée')

    def __init__(self):
        super().__init__()
        self.especes = noms.table('especes')
        self.bibliotheque = None
        self.vues: set[int] = set()
        self.dressees: set[int] = set()
        self._remplissage = False

        self.recherche = QLineEdit(placeholderText=tr('Rechercher une espèce…'),
                                   clearButtonEnabled=True)
        # Données : la famille telle que la nomme bestiaire (None : toutes).
        self.famille = QComboBox()
        self.famille.addItem(tr('Toutes les familles'), None)
        familles = {f for i in range(len(self.especes)) if (f := bestiaire.fiche(i).famille)}
        for famille in sorted(familles, key=tr):
            self.famille.addItem(tr(famille), famille)
        self.famille.addItem(tr(FAMILLE_INCONNUE), FAMILLE_INCONNUE)
        self.etat = QComboBox()
        for libelle, test in ETATS.items():
            self.etat.addItem(tr(libelle), test)
        for filtre in (self.recherche.textChanged, self.famille.currentIndexChanged,
                       self.etat.currentIndexChanged):
            filtre.connect(self._filtrer)
        barre = QHBoxLayout()
        barre.addWidget(self.recherche, 1)
        barre.addWidget(self.famille)
        barre.addWidget(self.etat)
        barre.addWidget(_bouton_actions([
            (tr('Marquer comme vues'), lambda: self._marquer_affichees('vue', True)),
            (tr('Marquer comme dressées'), lambda: self._marquer_affichees('dressee', True)),
            (tr('Retirer « dressée »'), lambda: self._marquer_affichees('dressee', False)),
            (tr('Tout décocher (jamais vues)'), lambda: self._marquer_affichees('vue', False)),
        ]))

        self.table = _table(tuple(map(tr, self.COLONNES)), self.COLONNES.index('Espèce'))
        self.table.verticalHeader().setDefaultSectionSize(icones.CASE + 4)
        self.table.setIconSize(icones.TAILLE_CASE)
        self.table.itemChanged.connect(self._case_changee)
        self.compteur = QLabel()

        disposition = QVBoxLayout(self)
        disposition.addLayout(barre)
        disposition.addWidget(self.table)
        disposition.addWidget(self.compteur)

    def afficher(self, bibliotheque) -> None:
        self.bibliotheque = bibliotheque
        self._lire()
        # Espèces sans nom : cachées, sauf si la sauvegarde les a vues. Au-delà
        # des bits de la bibliothèque, les « espèces » X et XY sont des variantes.
        ids = [i for i in range(1, F.NB_BITS_ESPECES)
               if not self.especes.inutilise(i) or i in self.vues]
        self._remplissage = True
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(ids))
        centre = Qt.AlignCenter
        for ligne, id_ in enumerate(ids):
            fiche = bestiaire.fiche(id_)
            numero = _cellule(id_, Qt.AlignRight | Qt.AlignVCenter)
            numero.setData(Qt.UserRole, fiche.famille or FAMILLE_INCONNUE)
            famille = _cellule(tr(fiche.famille) if fiche.famille else '', centre)
            famille.setData(Qt.DecorationRole, icones.famille(fiche.famille))
            famille.setToolTip(tr(fiche.famille or FAMILLE_INCONNUE))
            famille.setForeground(Qt.transparent)    # l'icône suffit, le texte sert au tri
            espece = _cellule(self.especes[id_])
            espece.setIcon(icones.icone(id_))
            cellules = (numero, famille, espece, _cellule(fiche.rang or '', centre),
                        Case(id_ in self.vues), Case(id_ in self.dressees))
            for colonne, cellule in enumerate(cellules):
                self.table.setItem(ligne, colonne, cellule)
        self.table.setSortingEnabled(True)
        self._remplissage = False
        self._filtrer()

    def _lire(self) -> None:
        self.vues = self.bibliotheque.especes_vues()
        self.dressees = self.bibliotheque.especes_dressees()

    def _id(self, ligne: int) -> int:
        return self.table.item(ligne, 0).data(Qt.DisplayRole)

    def _synchroniser(self) -> None:
        """Recoche toutes les cases d'après la sauvegarde (dresser coche aussi
        « vue », oublier décoche aussi « dressée »)."""
        self._lire()
        self._remplissage = True
        self.table.setSortingEnabled(False)       # sinon une ligne cochée bouge
        for ligne in range(self.table.rowCount()):
            id_ = self._id(ligne)
            self.table.item(ligne, self.VUE).cocher(id_ in self.vues)
            self.table.item(ligne, self.DRESSEE).cocher(id_ in self.dressees)
        self.table.setSortingEnabled(True)
        self._remplissage = False
        self._compter()
        self.modifiee.emit()

    def _case_changee(self, cellule: QTableWidgetItem) -> None:
        if self._remplissage or self.bibliotheque is None:
            return
        colonne = cellule.column()
        if colonne not in (self.VUE, self.DRESSEE):
            return
        id_ = self._id(cellule.row())
        if colonne == self.VUE:
            self.bibliotheque.marquer_vue(id_, cellule.cochee())
        else:
            self.bibliotheque.marquer_dressee(id_, cellule.cochee())
        self._synchroniser()

    def _marquer_affichees(self, quoi: str, valeur: bool) -> None:
        marquer = (self.bibliotheque.marquer_vue if quoi == 'vue'
                   else self.bibliotheque.marquer_dressee)
        for ligne in range(self.table.rowCount()):
            if not self.table.isRowHidden(ligne):
                marquer(self._id(ligne), valeur)
        self._synchroniser()

    def _filtrer(self) -> None:
        motif = _sans_accents(self.recherche.text())
        famille = self.famille.currentData()
        etat = self.etat.currentData()
        for ligne in range(self.table.rowCount()):
            numero = self.table.item(ligne, 0)
            id_ = numero.data(Qt.DisplayRole)
            visible = (motif in _sans_accents(self.table.item(ligne, 2).text())
                       and famille in (None, numero.data(Qt.UserRole))
                       and etat(id_ in self.vues, id_ in self.dressees))
            self.table.setRowHidden(ligne, not visible)
        self._compter()

    def _compter(self) -> None:
        affichees = sum(not self.table.isRowHidden(l) for l in range(self.table.rowCount()))
        self.compteur.setText(tr(
            '{vues} espèces vues, {dressees} dressées — {affichees} affichée(s) sur {total}',
            vues=len(self.vues - {0}), dressees=len(self.dressees - {0}),
            affichees=affichees, total=self.table.rowCount()))


class PageListe(QWidget):
    """Attributs ou compétences : un seul état, vu ou non."""
    modifiee = Signal()

    def __init__(self, nom_table: str, singulier: str, lire: str, marquer: str, aide=None):
        super().__init__()
        self.table_noms = noms.table(nom_table)
        self.singulier = singulier
        self.lire, self.marquer = lire, marquer      # méthodes de Bibliotheque
        self.aide = aide
        self.bibliotheque = None
        self.vus: set[int] = set()
        self._remplissage = False

        self.recherche = QLineEdit(placeholderText=tr('Rechercher…'), clearButtonEnabled=True)
        self.recherche.textChanged.connect(self._filtrer)
        self.seulement_vus = QCheckBox(tr('Vus seulement'))
        self.seulement_vus.toggled.connect(self._filtrer)
        barre = QHBoxLayout()
        barre.addWidget(self.recherche, 1)
        barre.addWidget(self.seulement_vus)
        barre.addWidget(_bouton_actions([
            (tr('Marquer comme vus'), lambda: self._marquer_affiches(True)),
            (tr('Tout décocher'), lambda: self._marquer_affiches(False)),
        ]))

        self.table = _table((tr('ID'), tr(singulier), tr('Vu')), 1)
        self.table.itemChanged.connect(self._case_changee)
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

    def afficher(self, bibliotheque) -> None:
        self.bibliotheque = bibliotheque
        self._lire()
        ids = [i for i in range(1, len(self.table_noms))
               if not self.table_noms.inutilise(i) or i in self.vus]
        self._remplissage = True
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(ids))
        for ligne, id_ in enumerate(ids):
            nom = _cellule(self.table_noms[id_])
            if self.aide:
                nom.setToolTip(self.aide(id_))
            cellules = (_cellule(id_, Qt.AlignRight | Qt.AlignVCenter), nom,
                        Case(id_ in self.vus))
            for colonne, cellule in enumerate(cellules):
                self.table.setItem(ligne, colonne, cellule)
        self.table.setSortingEnabled(True)
        self._remplissage = False
        self._filtrer()

    def _lire(self) -> None:
        # Le bit 0 (« aucun ») n'est pas une entrée.
        self.vus = getattr(self.bibliotheque, self.lire)() - {0}

    def _id(self, ligne: int) -> int:
        return self.table.item(ligne, 0).data(Qt.DisplayRole)

    def _synchroniser(self) -> None:
        self._lire()
        self._remplissage = True
        self.table.setSortingEnabled(False)
        for ligne in range(self.table.rowCount()):
            self.table.item(ligne, 2).cocher(self._id(ligne) in self.vus)
        self.table.setSortingEnabled(True)
        self._remplissage = False
        self._compter()
        self.modifiee.emit()

    def _case_changee(self, cellule: QTableWidgetItem) -> None:
        if self._remplissage or self.bibliotheque is None or cellule.column() != 2:
            return
        getattr(self.bibliotheque, self.marquer)(self._id(cellule.row()), cellule.cochee())
        self._synchroniser()

    def _marquer_affiches(self, valeur: bool) -> None:
        marquer = getattr(self.bibliotheque, self.marquer)
        for ligne in range(self.table.rowCount()):
            if not self.table.isRowHidden(ligne):
                marquer(self._id(ligne), valeur)
        self._synchroniser()

    def _afficher_description(self) -> None:
        lignes = self.table.selectionModel().selectedRows()
        if not lignes:
            self.titre_description.setText(tr('Description'))
            self.description.setText(tr('Sélectionnez un attribut pour lire sa description.')
                                     if self.singulier == 'Attribut' else
                                     tr('Sélectionnez une compétence pour lire sa description.'))
            return
        id_ = self._id(lignes[0].row())
        self.titre_description.setText(self.table_noms[id_])
        self.description.setText(self.aide(id_) or tr('(pas de description)'))

    def _filtrer(self) -> None:
        motif = _sans_accents(self.recherche.text())
        for ligne in range(self.table.rowCount()):
            id_ = self._id(ligne)
            texte = self.table.item(ligne, 1).text()
            if self.aide:
                texte += ' ' + self.aide(id_)
            visible = (motif in _sans_accents(texte)
                       and (id_ in self.vus or not self.seulement_vus.isChecked()))
            self.table.setRowHidden(ligne, not visible)
        self._compter()

    def _compter(self) -> None:
        affiches = sum(not self.table.isRowHidden(l) for l in range(self.table.rowCount()))
        self.compteur.setText(tr('{vus} vus — {affiches} affiché(s) sur {total}',
                                 vus=len(self.vus), affiches=affiches,
                                 total=self.table.rowCount()))


class PageBibliotheque(QTabWidget):
    modifiee = Signal()

    def __init__(self):
        super().__init__()
        self.monstres = PageMonstres()
        self.attributs = PageListe('attributs', 'Attribut', 'attributs',
                                   'marquer_attribut', noms.aide_attribut)
        self.competences = PageListe('competences', 'Compétence', 'competences',
                                     'marquer_competence')
        for page, titre in ((self.monstres, 'Monstres'), (self.attributs, 'Attributs'),
                            (self.competences, 'Compétences')):
            self.addTab(page, tr(titre))
            page.modifiee.connect(self.modifiee)
        self.setEnabled(False)

    def afficher(self, bibliotheque) -> None:
        for page in (self.monstres, self.attributs, self.competences):
            page.afficher(bibliotheque)
        self.setEnabled(True)
