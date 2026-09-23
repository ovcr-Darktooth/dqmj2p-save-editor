"""Fenêtre principale : liste des monstres à gauche, fiche à droite."""
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QAbstractItemView, QFileDialog, QHeaderView,
                               QMainWindow, QMessageBox, QSplitter, QTableWidget,
                               QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)

from dqmj2p_save import ErreurSauvegarde, Sauvegarde
from dqmj2p_save import bestiaire, noms

from . import icones
from .bibliotheque import PageBibliotheque
from .equipe import PanneauEquipe, TYPE_MIME, emplacement_depuis, glisser
from .fiche import Fiche
from .joueur import PageJoueur
from .sac import PageSac

TITRE = 'Éditeur de sauvegardes DQMJ2P'
FILTRE = 'Sauvegardes DS (*.dsv *.sav);;Tous les fichiers (*)'
LIBELLES_ROLES = {'equipe_1': 'Équipe 1', 'equipe_2': 'Équipe 2',
                  'equipe_3': 'Équipe 3', 'reserve_1': 'Réserve 1',
                  'reserve_2': 'Réserve 2', 'reserve_3': 'Réserve 3',
                  'ranch': 'Ranch'}
ORDRE_ROLES = list(LIBELLES_ROLES)
COLONNES = ('Empl.', 'Rôle', 'Fam.', 'Espèce', 'Surnom', 'Niveau')
CLE_RECENTS = 'fichiers_recents'
NB_RECENTS = 8


class ListeMonstres(QTableWidget):
    """Liste des monstres : on en glisse un vers le panneau d'équipe, et on y
    dépose un monstre du panneau pour le renvoyer au ranch."""

    def __init__(self, fenetre: 'Fenetre'):
        super().__init__(0, len(COLONNES))
        self.fenetre = fenetre
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)

    def startDrag(self, _actions):
        ligne = self.currentRow()
        if 0 <= ligne < len(self.fenetre.monstres):
            glisser(self, self.fenetre.monstres[ligne])

    def dragEnterEvent(self, evenement):
        if evenement.mimeData().hasFormat(TYPE_MIME) and evenement.source() is not self:
            evenement.acceptProposedAction()
        else:
            evenement.ignore()

    def dragMoveEvent(self, evenement):
        self.dragEnterEvent(evenement)

    def dropEvent(self, evenement):
        emplacement = emplacement_depuis(evenement.mimeData())
        if emplacement is not None and evenement.source() is not self:
            self.fenetre.panneau_equipe.renvoyer_au_ranch(emplacement)
            evenement.acceptProposedAction()


class Fenetre(QMainWindow):
    def __init__(self, reglages: QSettings | None = None):
        super().__init__()
        self.reglages = reglages or QSettings('ovcr-Darktooth', 'dqmj2p-save-editor')
        self.sauvegarde: Sauvegarde | None = None
        self.monstres = []

        self.liste = ListeMonstres(self)
        self.liste.setHorizontalHeaderLabels(COLONNES)
        self.liste.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.liste.setSelectionMode(QAbstractItemView.SingleSelection)
        self.liste.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.liste.verticalHeader().hide()
        self.liste.verticalHeader().setDefaultSectionSize(icones.CASE + 4)
        self.liste.setIconSize(icones.TAILLE_CASE)
        self.liste.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.liste.horizontalHeader().setStretchLastSection(True)
        self.liste.itemSelectionChanged.connect(self._selection)

        self.fiche = Fiche()
        self.fiche.liaison.modifiee.connect(self._apres_modification)
        self.page_joueur = PageJoueur()
        self.page_joueur.liaison.modifiee.connect(self._rafraichir_titre)
        self.page_sac = PageSac()
        self.page_sac.modifiee.connect(self._rafraichir_titre)
        self.page_bibliotheque = PageBibliotheque()
        self.page_bibliotheque.modifiee.connect(self._rafraichir_titre)
        for liaison in (self.fiche.liaison, self.page_joueur.liaison):
            liaison.erreur.connect(lambda message: self.statusBar().showMessage(message, 8000))

        self.panneau_equipe = PanneauEquipe()
        self.panneau_equipe.modifiee.connect(self._apres_changement_equipe)
        self.panneau_equipe.selectionner.connect(self._selectionner_emplacement)
        self.panneau_equipe.message.connect(lambda texte: self.statusBar().showMessage(texte, 8000))
        gauche = QWidget()
        colonne_gauche = QVBoxLayout(gauche)
        colonne_gauche.setContentsMargins(0, 0, 0, 0)
        colonne_gauche.addWidget(self.panneau_equipe)
        colonne_gauche.addWidget(self.liste, 1)

        separation = QSplitter()
        separation.addWidget(gauche)
        separation.addWidget(self.fiche)
        separation.setStretchFactor(0, 0)
        separation.setStretchFactor(1, 1)
        separation.setCollapsible(0, False)
        self.liste.setMinimumWidth(480)

        self.onglets = QTabWidget()
        self.onglets.addTab(self.page_joueur, 'Joueur')
        self.onglets.addTab(separation, 'Monstres')
        self.onglets.addTab(self.page_sac, 'Sac')
        self.onglets.addTab(self.page_bibliotheque, 'Bibliothèque')
        self.setCentralWidget(self.onglets)

        menu = self.menuBar().addMenu('&Fichier')
        self._action(menu, '&Ouvrir…', QKeySequence.Open, self.ouvrir_dialogue)
        self.menu_recents = menu.addMenu('Fichiers &récents')
        self.menu_recents.aboutToShow.connect(self._remplir_recents)
        self.menu_recents.setToolTipsVisible(True)
        self.action_enregistrer = self._action(
            menu, '&Enregistrer', QKeySequence.Save, self.enregistrer)
        self.action_enregistrer_sous = self._action(
            menu, 'Enregistrer &sous…', QKeySequence.SaveAs, self.enregistrer_sous)
        menu.addSeparator()
        self._action(menu, '&Quitter', QKeySequence.Quit, self.close)

        menu = self.menuBar().addMenu('&Monstres')
        self.actions_sauvegarde = [
            self._action(menu, '&Dupliquer le monstre sélectionné', 'Ctrl+D',
                         self.dupliquer),
            self._action(menu, "Surnoms abrégés → &nom complet de l'espèce", None,
                         self.restaurer_surnoms),
        ]

        self.setAcceptDrops(True)
        self.resize(1080, 620)
        self._remplir_recents()
        self._rafraichir_titre()
        self.statusBar().showMessage('Ouvrez une sauvegarde (Ctrl+O) ou '
                                     'glissez-la dans la fenêtre.')

    def _action(self, menu, texte, raccourci, slot) -> QAction:
        action = QAction(texte, self, triggered=slot)
        if raccourci:
            action.setShortcut(raccourci)
        menu.addAction(action)
        return action

    # ── Ouverture ────────────────────────────────────────────────────────────

    def ouvrir_dialogue(self) -> None:
        if not self._confirmer_abandon():
            return
        recents = self.recents()
        dossier = str(Path(recents[0]).parent) if recents else ''
        chemin, _ = QFileDialog.getOpenFileName(self, 'Ouvrir une sauvegarde', dossier, FILTRE)
        if chemin:
            self.ouvrir(chemin)

    def ouvrir_recent(self, chemin: str) -> None:
        if not Path(chemin).is_file():
            QMessageBox.warning(self, 'Fichier introuvable',
                                f'{chemin}\n\nIl est retiré des fichiers récents.')
            self._enregistrer_recents([c for c in self.recents() if c != chemin])
            return
        if self._confirmer_abandon():
            self.ouvrir(chemin)

    def ouvrir(self, chemin) -> None:
        try:
            sauvegarde = Sauvegarde.ouvrir(chemin)
        except (OSError, ErreurSauvegarde) as e:
            QMessageBox.critical(self, 'Ouverture impossible', f'{chemin}\n\n{e}')
            return
        self.sauvegarde = sauvegarde
        self._remplir_liste()
        self.panneau_equipe.afficher(sauvegarde)
        self.page_joueur.afficher(sauvegarde.joueur)
        self.page_sac.afficher(sauvegarde.sac)
        self.page_bibliotheque.afficher(sauvegarde.bibliotheque)
        self._ajouter_recent(sauvegarde.chemin)
        self._rafraichir_titre()
        self.statusBar().showMessage(f'{len(self.monstres)} monstres chargés.')

    # ── Fichiers récents ─────────────────────────────────────────────────────

    def recents(self) -> list[str]:
        valeur = self.reglages.value(CLE_RECENTS, [])
        if isinstance(valeur, str):     # un seul élément : le registre rend une chaîne
            valeur = [valeur]
        return [str(c) for c in valeur or []]

    def _enregistrer_recents(self, chemins: list[str]) -> None:
        self.reglages.setValue(CLE_RECENTS, chemins[:NB_RECENTS])
        self._remplir_recents()

    def _ajouter_recent(self, chemin) -> None:
        chemin = str(Path(chemin).resolve())
        autres = [c for c in self.recents() if Path(c) != Path(chemin)]
        self._enregistrer_recents([chemin, *autres])

    def _remplir_recents(self) -> None:
        self.menu_recents.clear()
        recents = self.recents()
        for numero, chemin in enumerate(recents, 1):
            action = self.menu_recents.addAction(f'&{numero}  {Path(chemin).name}')
            action.setToolTip(chemin)
            action.setStatusTip(chemin)
            action.triggered.connect(lambda _=False, c=chemin: self.ouvrir_recent(c))
        if recents:
            self.menu_recents.addSeparator()
        self.menu_recents.addAction('&Vider la liste', lambda: self._enregistrer_recents([])
                                    ).setEnabled(bool(recents))
        self.menu_recents.setEnabled(bool(recents))

    def _remplir_liste(self, emplacement_choisi: int | None = None) -> None:
        sauvegarde = self.sauvegarde
        self.monstres = sorted(sauvegarde.monstres(),
                               key=lambda m: (ORDRE_ROLES.index(sauvegarde.role(m)),
                                              m.emplacement))
        self.liste.setRowCount(len(self.monstres))
        for ligne in range(len(self.monstres)):
            self._remplir_ligne(ligne)
        emplacements = [m.emplacement for m in self.monstres]
        self.liste.selectRow(emplacements.index(emplacement_choisi)
                             if emplacement_choisi in emplacements else 0)

    def _remplir_ligne(self, ligne: int) -> None:
        m = self.monstres[ligne]
        famille = bestiaire.fiche(m['espece']).famille
        valeurs = (m.emplacement, LIBELLES_ROLES[self.sauvegarde.role(m)], '',
                   noms.table('especes')[m['espece']], m['surnom'], m['niveau'])
        for colonne, valeur in enumerate(valeurs):
            cellule = QTableWidgetItem(str(valeur))
            if isinstance(valeur, int):
                cellule.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if colonne == COLONNES.index('Espèce'):
                cellule.setIcon(icones.icone(m['espece']))
            if colonne == COLONNES.index('Fam.'):
                cellule.setData(Qt.DecorationRole, icones.famille(famille))
                cellule.setToolTip(famille or '')
                cellule.setTextAlignment(Qt.AlignCenter)
            self.liste.setItem(ligne, colonne, cellule)

    def _selection(self) -> None:
        lignes = self.liste.selectionModel().selectedRows()
        if lignes:
            monstre = self.monstres[lignes[0].row()]
            self.fiche.afficher(monstre)
            self.panneau_equipe.marquer(monstre.emplacement)

    def _selectionner_emplacement(self, emplacement: int) -> None:
        emplacements = [m.emplacement for m in self.monstres]
        if emplacement in emplacements:
            self.liste.selectRow(emplacements.index(emplacement))

    def _apres_changement_equipe(self) -> None:
        self._remplir_liste(self.fiche.monstre.emplacement if self.fiche.monstre else None)
        self._rafraichir_titre()

    def _apres_modification(self) -> None:
        self._remplir_ligne(self.liste.currentRow())
        self.panneau_equipe.update_colonnes()   # espèce changée : taille et icône
        self._rafraichir_titre()

    # ── Actions sur les monstres ─────────────────────────────────────────────

    def dupliquer(self) -> None:
        modele = self.fiche.monstre
        try:
            copie = self.sauvegarde.dupliquer(modele)
        except ErreurSauvegarde as e:
            QMessageBox.warning(self, 'Duplication impossible', str(e))
            return
        self._remplir_liste(copie.emplacement)
        self.panneau_equipe.update_colonnes()
        self._rafraichir_titre()
        self.statusBar().showMessage(
            f'{copie["surnom"]} dupliqué dans le ranch (emplacement {copie.emplacement}).')

    def restaurer_surnoms(self) -> None:
        renommes = self.sauvegarde.restaurer_surnoms()
        self._remplir_liste(self.fiche.monstre.emplacement)
        self._rafraichir_titre()
        self.statusBar().showMessage(f'{len(renommes)} surnom(s) complété(s).')

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
        self._ajouter_recent(chemin)
        self._rafraichir_titre()
        message = f'Enregistré : {Path(chemin).name}'
        if bak:
            message += f'  (original gardé dans {bak.name})'
        self.statusBar().showMessage(message)
        return True

    # ── Divers ───────────────────────────────────────────────────────────────

    def _rafraichir_titre(self) -> None:
        ouverte = self.sauvegarde is not None
        for action in (self.action_enregistrer, self.action_enregistrer_sous,
                       *self.actions_sauvegarde):
            action.setEnabled(ouverte)
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
