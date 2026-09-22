"""Fenêtre principale : liste des monstres à gauche, fiche à droite."""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QAbstractItemView, QFileDialog, QHeaderView,
                               QMainWindow, QMessageBox, QSplitter, QTableWidget,
                               QTableWidgetItem, QTabWidget)

from dqmj2p_save import ErreurSauvegarde, Sauvegarde
from dqmj2p_save import noms

from .fiche import Fiche
from .joueur import PageJoueur

TITRE = 'Éditeur de sauvegardes DQMJ2P'
FILTRE = 'Sauvegardes DS (*.dsv *.sav);;Tous les fichiers (*)'
LIBELLES_ROLES = {'equipe_1': 'Équipe 1', 'equipe_2': 'Équipe 2',
                  'equipe_3': 'Équipe 3', 'reserve_1': 'Réserve 1',
                  'reserve_2': 'Réserve 2', 'reserve_3': 'Réserve 3',
                  'ranch': 'Ranch'}
ORDRE_ROLES = list(LIBELLES_ROLES)
COLONNES = ('Empl.', 'Rôle', 'Espèce', 'Surnom', 'Niveau')


class Fenetre(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sauvegarde: Sauvegarde | None = None
        self.monstres = []

        self.liste = QTableWidget(0, len(COLONNES))
        self.liste.setHorizontalHeaderLabels(COLONNES)
        self.liste.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.liste.setSelectionMode(QAbstractItemView.SingleSelection)
        self.liste.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.liste.verticalHeader().hide()
        self.liste.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.liste.horizontalHeader().setStretchLastSection(True)
        self.liste.itemSelectionChanged.connect(self._selection)

        self.fiche = Fiche()
        self.fiche.liaison.modifiee.connect(self._apres_modification)
        self.page_joueur = PageJoueur()
        self.page_joueur.liaison.modifiee.connect(self._rafraichir_titre)
        for liaison in (self.fiche.liaison, self.page_joueur.liaison):
            liaison.erreur.connect(lambda message: self.statusBar().showMessage(message, 8000))

        separation = QSplitter()
        separation.addWidget(self.liste)
        separation.addWidget(self.fiche)
        separation.setStretchFactor(0, 0)
        separation.setStretchFactor(1, 1)
        separation.setCollapsible(0, False)
        self.liste.setMinimumWidth(400)

        self.onglets = QTabWidget()
        self.onglets.addTab(self.page_joueur, 'Joueur')
        self.onglets.addTab(separation, 'Monstres')
        self.setCentralWidget(self.onglets)

        menu = self.menuBar().addMenu('&Fichier')
        self._action(menu, '&Ouvrir…', QKeySequence.Open, self.ouvrir_dialogue)
        self.action_enregistrer = self._action(
            menu, '&Enregistrer', QKeySequence.Save, self.enregistrer)
        self.action_enregistrer_sous = self._action(
            menu, 'Enregistrer &sous…', QKeySequence.SaveAs, self.enregistrer_sous)
        menu.addSeparator()
        self._action(menu, '&Quitter', QKeySequence.Quit, self.close)

        self.setAcceptDrops(True)
        self.resize(1080, 620)
        self._rafraichir_titre()
        self.statusBar().showMessage('Ouvrez une sauvegarde (Ctrl+O) ou '
                                     'glissez-la dans la fenêtre.')

    def _action(self, menu, texte, raccourci, slot) -> QAction:
        action = QAction(texte, self, shortcut=raccourci, triggered=slot)
        menu.addAction(action)
        return action

    # ── Ouverture ────────────────────────────────────────────────────────────

    def ouvrir_dialogue(self) -> None:
        if not self._confirmer_abandon():
            return
        chemin, _ = QFileDialog.getOpenFileName(self, 'Ouvrir une sauvegarde', '', FILTRE)
        if chemin:
            self.ouvrir(chemin)

    def ouvrir(self, chemin) -> None:
        try:
            sauvegarde = Sauvegarde.ouvrir(chemin)
        except (OSError, ErreurSauvegarde) as e:
            QMessageBox.critical(self, 'Ouverture impossible', f'{chemin}\n\n{e}')
            return
        self.sauvegarde = sauvegarde
        self.monstres = sorted(sauvegarde.monstres(),
                               key=lambda m: (ORDRE_ROLES.index(sauvegarde.role(m)),
                                              m.emplacement))
        self.liste.setRowCount(len(self.monstres))
        for ligne in range(len(self.monstres)):
            self._remplir_ligne(ligne)
        self.liste.selectRow(0)
        self.page_joueur.afficher(sauvegarde.joueur)
        self._rafraichir_titre()
        self.statusBar().showMessage(f'{len(self.monstres)} monstres chargés.')

    def _remplir_ligne(self, ligne: int) -> None:
        m = self.monstres[ligne]
        valeurs = (m.emplacement, LIBELLES_ROLES[self.sauvegarde.role(m)],
                   noms.table('especes')[m['espece']], m['surnom'], m['niveau'])
        for colonne, valeur in enumerate(valeurs):
            cellule = QTableWidgetItem(str(valeur))
            if isinstance(valeur, int):
                cellule.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.liste.setItem(ligne, colonne, cellule)

    def _selection(self) -> None:
        lignes = self.liste.selectionModel().selectedRows()
        if lignes:
            self.fiche.afficher(self.monstres[lignes[0].row()])

    def _apres_modification(self) -> None:
        self._remplir_ligne(self.liste.currentRow())
        self._rafraichir_titre()

    # ── Enregistrement ───────────────────────────────────────────────────────

    def enregistrer(self) -> bool:
        return self._enregistrer_vers(self.sauvegarde.chemin)

    def enregistrer_sous(self) -> bool:
        chemin, _ = QFileDialog.getSaveFileName(
            self, 'Enregistrer sous', str(self.sauvegarde.chemin), FILTRE)
        return bool(chemin) and self._enregistrer_vers(chemin)

    def _enregistrer_vers(self, chemin) -> bool:
        try:
            bak = self.sauvegarde.enregistrer(chemin)
        except OSError as e:
            QMessageBox.critical(self, 'Enregistrement impossible', f'{chemin}\n\n{e}')
            return False
        self._rafraichir_titre()
        message = f'Enregistré : {Path(chemin).name}'
        if bak:
            message += f'  (original gardé dans {bak.name})'
        self.statusBar().showMessage(message)
        return True

    # ── Divers ───────────────────────────────────────────────────────────────

    def _rafraichir_titre(self) -> None:
        ouverte = self.sauvegarde is not None
        self.action_enregistrer.setEnabled(ouverte)
        self.action_enregistrer_sous.setEnabled(ouverte)
        if not ouverte:
            self.setWindowTitle(TITRE)
            return
        marque = ' *' if self.sauvegarde.modifiee else ''
        self.setWindowTitle(f'{self.sauvegarde.chemin.name}{marque} — {TITRE}')

    def _confirmer_abandon(self) -> bool:
        """Vrai si l'on peut abandonner la sauvegarde courante."""
        if not (self.sauvegarde and self.sauvegarde.modifiee):
            return True
        choix = QMessageBox.question(
            self, 'Modifications non enregistrées',
            'Enregistrer les modifications avant de continuer ?',
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if choix == QMessageBox.Save:
            return self.enregistrer()
        return choix == QMessageBox.Discard

    def closeEvent(self, evenement) -> None:
        if self._confirmer_abandon():
            evenement.accept()
        else:
            evenement.ignore()

    def dragEnterEvent(self, evenement) -> None:
        if evenement.mimeData().hasUrls():
            evenement.acceptProposedAction()

    def dropEvent(self, evenement) -> None:
        urls = evenement.mimeData().urls()
        if urls and self._confirmer_abandon():
            self.ouvrir(urls[0].toLocalFile())
