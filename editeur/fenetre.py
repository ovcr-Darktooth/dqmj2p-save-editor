"""Fenêtre principale : liste des monstres à gauche, fiche à droite."""
from pathlib import Path

from PySide6.QtCore import QLocale, QSettings, Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFileDialog, QHeaderView,
                               QMainWindow, QMenu, QMessageBox, QSplitter, QTableWidget,
                               QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget)

from dqmj2p_save import ErreurSauvegarde, Sauvegarde
from dqmj2p_save import bestiaire, langue, noms
from dqmj2p_save.langue import tr

from . import extraction, icones
from .bibliotheque import PageBibliotheque
from .equipe import PanneauEquipe, TYPE_MIME, emplacement_depuis, glisser
from .fiche import Fiche
from .joueur import PageJoueur
from .sac import PageSac

# Textes traduits à l'affichage (tr) : la langue peut changer en cours de route.
TITRE = 'Éditeur de sauvegardes DQMJ2P'
FILTRE = 'Sauvegardes DS (*.dsv *.sav);;Tous les fichiers (*)'
FILTRE_ROM = 'ROM DS (*.nds);;Tous les fichiers (*)'
LIBELLES_ROLES = {'equipe_1': 'Équipe 1', 'equipe_2': 'Équipe 2',
                  'equipe_3': 'Équipe 3', 'reserve_1': 'Réserve 1',
                  'reserve_2': 'Réserve 2', 'reserve_3': 'Réserve 3',
                  'ranch': 'Ranch'}
ORDRE_ROLES = list(LIBELLES_ROLES)
COLONNES = ('Empl.', 'Rôle', 'Fam.', 'Espèce', 'Surnom', 'Niveau')
COLONNE_FAMILLE, COLONNE_ESPECE = COLONNES.index('Fam.'), COLONNES.index('Espèce')
CLE_RECENTS = 'fichiers_recents'
CLE_LANGUE = 'langue'
NB_RECENTS = 8


def langue_systeme() -> str:
    """Français si le système l'est, anglais sinon."""
    return 'fr' if QLocale.system().language() == QLocale.French else 'en'


def langue_enregistree(reglages: QSettings) -> str:
    code = reglages.value(CLE_LANGUE, '')
    return code if code in langue.LANGUES else langue_systeme()


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
    # Fenêtre affichée : une fenêtre sans parent doit rester référencée, et
    # changer de langue en construit une nouvelle (voir _changer_langue).
    active: 'Fenetre | None' = None

    def __init__(self, reglages: QSettings | None = None):
        super().__init__()
        Fenetre.active = self
        self.reglages = reglages or QSettings('ovcr-Darktooth', 'dqmj2p-save-editor')
        langue.choisir(langue_enregistree(self.reglages))
        self.sauvegarde: Sauvegarde | None = None
        self.monstres = []
        self._remplacee = False

        self.liste = ListeMonstres(self)
        self.liste.setHorizontalHeaderLabels([tr(c) for c in COLONNES])
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
        self.onglets.addTab(self.page_joueur, tr('Joueur'))
        self.onglets.addTab(separation, tr('Monstres'))
        self.onglets.addTab(self.page_sac, tr('Sac'))
        self.onglets.addTab(self.page_bibliotheque, tr('Bibliothèque'))
        self.setCentralWidget(self.onglets)

        menu = self.menuBar().addMenu(tr('&Fichier'))
        self._action(menu, tr('&Ouvrir…'), QKeySequence.Open, self.ouvrir_dialogue)
        self.menu_recents = menu.addMenu(tr('Fichiers &récents'))
        self.menu_recents.aboutToShow.connect(self._remplir_recents)
        self.menu_recents.setToolTipsVisible(True)
        self.action_enregistrer = self._action(
            menu, tr('&Enregistrer'), QKeySequence.Save, self.enregistrer)
        self.action_enregistrer_sous = self._action(
            menu, tr('Enregistrer &sous…'), QKeySequence.SaveAs, self.enregistrer_sous)
        menu.addSeparator()
        self._action(menu, tr("Extraire les &icônes d'une ROM…"), None, self.extraire_icones)
        menu.addSeparator()
        self._action(menu, tr('&Quitter'), QKeySequence.Quit, self.close)

        menu = self.menuBar().addMenu(tr('&Monstres'))
        self.actions_sauvegarde = [
            self._action(menu, tr('&Dupliquer le monstre sélectionné'), 'Ctrl+D',
                         self.dupliquer),
            self._action(menu, tr("Surnoms abrégés → &nom complet de l'espèce"), None,
                         self.restaurer_surnoms),
        ]
        self.action_supprimer = self._action(menu, tr('&Supprimer le monstre sélectionné…'),
                                             None, self.supprimer)
        self.actions_sauvegarde.append(self.action_supprimer)
        # Suppr n'agit que dans la liste (pas dans un champ de saisie).
        self.action_supprimer.setShortcut(QKeySequence.Delete)
        self.action_supprimer.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self.liste.addAction(self.action_supprimer)
        self.liste.setContextMenuPolicy(Qt.CustomContextMenu)
        self.liste.customContextMenuRequested.connect(self._menu_liste)

        # Libellé bilingue : on retrouve le menu quelle que soit la langue.
        menu = self.menuBar().addMenu('&Langue / Language')
        groupe = QActionGroup(self)
        for code, nom in langue.LANGUES.items():
            action = menu.addAction(nom, lambda c=code: self._changer_langue(c))
            action.setCheckable(True)
            action.setChecked(code == langue.courante())
            groupe.addAction(action)
        menu.addSeparator()
        menu.addAction(tr('Choisir la langue du patch installé : noms des monstres, '
                          'des compétences et des objets identiques au jeu.')
                       ).setEnabled(False)

        self.setAcceptDrops(True)
        self.resize(1080, 620)
        self._remplir_recents()
        self._rafraichir_titre()
        self.statusBar().showMessage(tr('Ouvrez une sauvegarde (Ctrl+O) ou '
                                        'glissez-la dans la fenêtre.'))

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
        chemin, _ = QFileDialog.getOpenFileName(self, tr('Ouvrir une sauvegarde'), dossier,
                                                tr(FILTRE))
        if chemin:
            self.ouvrir(chemin)

    def ouvrir_recent(self, chemin: str) -> None:
        if not Path(chemin).is_file():
            QMessageBox.warning(self, tr('Fichier introuvable'),
                                tr('{chemin}\n\nIl est retiré des fichiers récents.',
                                   chemin=chemin))
            self._enregistrer_recents([c for c in self.recents() if c != chemin])
            return
        if self._confirmer_abandon():
            self.ouvrir(chemin)

    def ouvrir(self, chemin) -> None:
        try:
            sauvegarde = Sauvegarde.ouvrir(chemin)
        except (OSError, ErreurSauvegarde) as e:
            QMessageBox.critical(self, tr('Ouverture impossible'), f'{chemin}\n\n{e}')
            return
        self.afficher(sauvegarde)
        self._ajouter_recent(sauvegarde.chemin)
        self.statusBar().showMessage(tr('{n} monstres chargés.', n=len(self.monstres)))

    def afficher(self, sauvegarde: Sauvegarde, emplacement: int | None = None) -> None:
        """Affiche une sauvegarde déjà ouverte, modifications comprises."""
        self.sauvegarde = sauvegarde
        self._remplir_liste(emplacement)
        self.panneau_equipe.afficher(sauvegarde)
        self.page_joueur.afficher(sauvegarde.joueur)
        self.page_sac.afficher(sauvegarde.sac)
        self.page_bibliotheque.afficher(sauvegarde.bibliotheque)
        self._rafraichir_titre()

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
        self.menu_recents.addAction(tr('&Vider la liste'), lambda: self._enregistrer_recents([])
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
        valeurs = (m.emplacement, tr(LIBELLES_ROLES[self.sauvegarde.role(m)]), '',
                   noms.table('especes')[m['espece']], m['surnom'], m['niveau'])
        for colonne, valeur in enumerate(valeurs):
            cellule = QTableWidgetItem(str(valeur))
            if isinstance(valeur, int):
                cellule.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if colonne == COLONNE_ESPECE:
                cellule.setIcon(icones.icone(m['espece']))
            if colonne == COLONNE_FAMILLE:
                cellule.setData(Qt.DecorationRole, icones.famille(famille))
                cellule.setToolTip(tr(famille) if famille else '')
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
            QMessageBox.warning(self, tr('Duplication impossible'), str(e))
            return
        self._remplir_liste(copie.emplacement)
        self.panneau_equipe.update_colonnes()
        self._rafraichir_titre()
        self.statusBar().showMessage(
            tr('{surnom} dupliqué dans le ranch (emplacement {n}).',
               surnom=copie['surnom'], n=copie.emplacement))

    def _menu_liste(self, position) -> None:
        if self.sauvegarde is None or self.liste.itemAt(position) is None:
            return
        menu = QMenu(self)
        menu.addAction(self.actions_sauvegarde[0])          # Dupliquer
        menu.addAction(self.action_supprimer)
        menu.exec(self.liste.viewport().mapToGlobal(position))

    def supprimer(self) -> None:
        monstre = self.fiche.monstre
        if monstre is None:
            return
        role = self.sauvegarde.role(monstre)
        description = tr('{surnom} ({espece}, niveau {niveau}, {role})',
                         surnom=monstre['surnom'],
                         espece=noms.table('especes')[monstre['espece']],
                         niveau=monstre['niveau'], role=tr(LIBELLES_ROLES[role]).lower())
        avertissement = ('' if role == 'ranch' else
                         tr("\n\nIl quittera aussi l'équipe.") if role.startswith('equipe')
                         else tr('\n\nIl quittera aussi la réserve.'))
        choix = QMessageBox.warning(
            self, tr('Supprimer un monstre'),
            tr('Supprimer définitivement {description} ?', description=description)
            + avertissement + '\n\n'
            + tr("La sauvegarde n'est modifiée sur le disque qu'à l'enregistrement."),
            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if choix != QMessageBox.Yes:
            return
        try:
            self.sauvegarde.supprimer(monstre)
        except ErreurSauvegarde as e:
            QMessageBox.warning(self, tr('Suppression impossible'), str(e))
            return
        emplacement = min(monstre.emplacement, len(self.sauvegarde.monstres()) - 1)
        self.panneau_equipe.afficher(self.sauvegarde)
        self._remplir_liste(emplacement)
        self._rafraichir_titre()
        self.statusBar().showMessage(tr('{description} supprimé.', description=description))

    def restaurer_surnoms(self) -> None:
        renommes = self.sauvegarde.restaurer_surnoms()
        self._remplir_liste(self.fiche.monstre.emplacement)
        self._rafraichir_titre()
        self.statusBar().showMessage(tr('{n} surnom(s) complété(s).', n=len(renommes)))

    # ── Enregistrement ───────────────────────────────────────────────────────

    def enregistrer(self) -> bool:
        return self._enregistrer_vers(self.sauvegarde.chemin)

    def enregistrer_sous(self) -> bool:
        chemin, _ = QFileDialog.getSaveFileName(
            self, tr('Enregistrer sous'), str(self.sauvegarde.chemin), tr(FILTRE))
        return bool(chemin) and self._enregistrer_vers(chemin)

    def _enregistrer_vers(self, chemin) -> bool:
        try:
            bak = self.sauvegarde.enregistrer(chemin)
        except OSError as e:
            QMessageBox.critical(self, tr('Enregistrement impossible'), f'{chemin}\n\n{e}')
            return False
        self._ajouter_recent(chemin)
        self._rafraichir_titre()
        message = tr('Enregistré : {nom}', nom=Path(chemin).name)
        if bak:
            message += tr('  (original gardé dans {nom})', nom=bak.name)
        self.statusBar().showMessage(message)
        return True

    # ── Icônes ───────────────────────────────────────────────────────────────

    def extraire_icones(self) -> None:
        """Extrait les icônes des monstres et des familles d'une ROM choisie par
        l'utilisateur, dans le dossier où l'éditeur les cherche."""
        chemin, _ = QFileDialog.getOpenFileName(
            self, tr('Choisir la ROM du jeu (japonaise ou patchée)'), '', tr(FILTRE_ROM))
        if not chemin:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            rom = Path(chemin).read_bytes()
            monstres = extraction.extraire_icones(rom, icones.DOSSIER)
            familles = extraction.extraire_familles(rom, icones.FAMILLES)
        except (OSError, extraction.ErreurExtraction) as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, tr('Extraction impossible'), f'{chemin}\n\n{e}')
            return
        QApplication.restoreOverrideCursor()
        for fonction in (icones.image, icones.icone, icones.famille):
            fonction.cache_clear()
        self._reconstruire().statusBar().showMessage(tr(
            '{monstres} icônes de monstres et {familles} de familles extraites dans {dossier}.',
            monstres=monstres, familles=familles, dossier=icones.DOSSIER))

    # ── Langue ───────────────────────────────────────────────────────────────

    def _changer_langue(self, code: str) -> None:
        """Enregistre la langue et reconstruit la fenêtre dans cette langue."""
        if code == langue.courante():
            return
        self.reglages.setValue(CLE_LANGUE, code)
        self._reconstruire()

    def _reconstruire(self) -> 'Fenetre':
        """Remplace cette fenêtre par une nouvelle (langue ou icônes changées).
        La sauvegarde ouverte passe telle quelle, modifications non
        enregistrées comprises."""
        nouvelle = Fenetre(self.reglages)
        nouvelle.restoreGeometry(self.saveGeometry())
        if self.sauvegarde is not None:
            nouvelle.afficher(self.sauvegarde,
                              self.fiche.monstre.emplacement if self.fiche.monstre else None)
        nouvelle.onglets.setCurrentIndex(self.onglets.currentIndex())
        nouvelle.show()
        self._remplacee = True
        self.close()
        self.deleteLater()
        return nouvelle

    # ── Divers ───────────────────────────────────────────────────────────────

    def _rafraichir_titre(self) -> None:
        ouverte = self.sauvegarde is not None
        for action in (self.action_enregistrer, self.action_enregistrer_sous,
                       *self.actions_sauvegarde):
            action.setEnabled(ouverte)
        if not ouverte:
            self.setWindowTitle(tr(TITRE))
            return
        marque = ' *' if self.sauvegarde.modifiee else ''
        self.setWindowTitle(f'{self.sauvegarde.chemin.name}{marque} — {tr(TITRE)}')

    def _confirmer_abandon(self) -> bool:
        """Vrai si l'on peut abandonner la sauvegarde courante."""
        if self._remplacee or not (self.sauvegarde and self.sauvegarde.modifiee):
            return True
        choix = QMessageBox.question(
            self, tr('Modifications non enregistrées'),
            tr('Enregistrer les modifications avant de continuer ?'),
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
