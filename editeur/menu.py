"""Onglet Menu : ordre des boutons de l'écran du bas, grille de 4 × 3 cases
comme dans le jeu. Glisser un bouton sur une autre case échange les deux ;
une case vide peut rester au milieu de la grille (validé en jeu)."""
from PySide6.QtCore import QMimeData, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from dqmj2p_save import format as F
from dqmj2p_save import noms
from dqmj2p_save.langue import tr

from .equipe import FOND_CASE, FOND_CASE_SURVOL, OR

TYPE_MIME = 'application/x-dqmj2p-bouton'      # contenu : numéro de la case
LARGEUR, HAUTEUR = 150, 64
FOND_VIDE = QColor('#2a2f3a')


class GrilleBoutons(QWidget):
    """Les 12 cases ; source et cible de glisser-déposer."""
    echange = Signal(int, int)

    def __init__(self):
        super().__init__()
        self.cases: list[int] = []
        self.survol: int | None = None
        self.depart: QPoint | None = None
        self.setAcceptDrops(True)
        self.setFixedSize(F.COLONNES_BOUTONS * LARGEUR + 8, F.LIGNES_BOUTONS * HAUTEUR + 8)

    def afficher(self, cases: list[int]) -> None:
        self.cases = cases
        self.update()

    def rect_case(self, case: int) -> QRect:
        ligne, colonne = divmod(case, F.COLONNES_BOUTONS)
        return QRect(4 + colonne * LARGEUR, 4 + ligne * HAUTEUR,
                     LARGEUR, HAUTEUR).adjusted(3, 3, -3, -3)

    def case_sous(self, point: QPoint) -> int | None:
        colonne, ligne = (point.x() - 4) // LARGEUR, (point.y() - 4) // HAUTEUR
        if 0 <= colonne < F.COLONNES_BOUTONS and 0 <= ligne < F.LIGNES_BOUTONS:
            return ligne * F.COLONNES_BOUTONS + colonne
        return None

    def paintEvent(self, _):
        p = QPainter(self)
        for case, bouton in enumerate(self.cases):
            rect = self.rect_case(case)
            vide = bouton == F.BOUTON_VIDE
            p.setPen(QPen(QColor('#555c6b') if vide else OR, 2,
                          Qt.DashLine if vide else Qt.SolidLine))
            p.setBrush(FOND_CASE_SURVOL if case == self.survol else
                       FOND_VIDE if vide else FOND_CASE)
            p.drawRoundedRect(rect, 6, 6)
            if not vide:
                p.setPen(QColor('white'))
                p.drawText(rect.adjusted(6, 4, -6, -4), Qt.AlignCenter | Qt.TextWordWrap,
                           noms.bouton(bouton))
        p.end()

    def event(self, evenement):
        if evenement.type() == evenement.Type.ToolTip:
            case = self.case_sous(evenement.pos())
            if case is not None and self.cases[case] != F.BOUTON_VIDE:
                self.setToolTip(tr('Bouton {id:02X} — glisser pour le déplacer',
                                   id=self.cases[case]))
            else:
                self.setToolTip(tr('Case vide'))
        return super().event(evenement)

    # ── Souris ───────────────────────────────────────────────────────────────

    def mousePressEvent(self, evenement):
        case = self.case_sous(evenement.position().toPoint())
        vide = case is None or self.cases[case] == F.BOUTON_VIDE
        self.depart = None if vide else evenement.position().toPoint()

    def mouseMoveEvent(self, evenement):
        if self.depart is None or not evenement.buttons() & Qt.LeftButton:
            return
        if (evenement.position().toPoint() - self.depart).manhattanLength() < 6:
            return
        case = self.case_sous(self.depart)
        self.depart = None
        donnees = QMimeData()
        donnees.setData(TYPE_MIME, str(case).encode())
        glisse = QDrag(self)
        glisse.setMimeData(donnees)
        rect = self.rect_case(case)
        glisse.setPixmap(self.grab(rect))
        glisse.setHotSpot(QPoint(rect.width() // 2, rect.height() // 2))
        glisse.exec(Qt.MoveAction)

    def dragEnterEvent(self, evenement):
        if evenement.mimeData().hasFormat(TYPE_MIME):
            evenement.acceptProposedAction()

    def dragMoveEvent(self, evenement):
        if evenement.mimeData().hasFormat(TYPE_MIME):
            self.survol = self.case_sous(evenement.position().toPoint())
            self.update()
            evenement.acceptProposedAction()

    def dragLeaveEvent(self, _):
        self.survol = None
        self.update()

    def dropEvent(self, evenement):
        self.survol = None
        source = int(bytes(evenement.mimeData().data(TYPE_MIME)).decode())
        cible = self.case_sous(evenement.position().toPoint())
        if cible is not None and cible != source:
            self.echange.emit(source, cible)
        evenement.acceptProposedAction()
        self.update()


class PageMenu(QWidget):
    modifiee = Signal()

    def __init__(self):
        super().__init__()
        self.sauvegarde = None
        self.grille = GrilleBoutons()
        self.grille.echange.connect(self._echanger)
        intro = QLabel(tr("Boutons de l'écran du bas, disposés comme dans le jeu."))
        aide = QLabel(tr("Glisser un bouton sur une autre case pour les échanger ; une case "
                         "vide peut rester au milieu de la grille. Seuls les boutons déjà "
                         "obtenus dans la partie sont là. Les sorts du sous-menu "
                         "Compétences de dressage ne sont pas modifiés."))
        aide.setWordWrap(True)
        aide.setEnabled(False)                      # texte grisé, comme une légende
        self.ordre_du_jeu = QPushButton(tr("Ordre d'une partie neuve"))
        self.ordre_du_jeu.setToolTip(tr('Les boutons obtenus plus tard (Soigner tous, '
                                        'Monstrequinque) suivent, dans les cases vides.'))
        self.ordre_du_jeu.clicked.connect(self._ordre_du_jeu)

        centre = QHBoxLayout()
        centre.addWidget(self.grille)
        centre.addStretch()
        boutons = QHBoxLayout()
        boutons.addWidget(self.ordre_du_jeu)
        boutons.addStretch()
        disposition = QVBoxLayout(self)
        disposition.addWidget(intro)
        disposition.addLayout(centre)
        disposition.addLayout(boutons)
        disposition.addWidget(aide)
        disposition.addStretch()
        self.setEnabled(False)

    def afficher(self, sauvegarde) -> None:
        self.sauvegarde = sauvegarde
        self.grille.afficher(sauvegarde.boutons)
        self.setEnabled(True)

    def _echanger(self, a: int, b: int) -> None:
        self.sauvegarde.echanger_boutons(a, b)
        self.grille.afficher(self.sauvegarde.boutons)
        self.modifiee.emit()

    def _ordre_du_jeu(self) -> None:
        avant = self.sauvegarde.boutons
        self.sauvegarde.ranger_boutons(F.ordre_boutons_du_jeu(avant))
        if self.sauvegarde.boutons != avant:
            self.grille.afficher(self.sauvegarde.boutons)
            self.modifiee.emit()
