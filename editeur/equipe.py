"""Panneau Équipe / Réserve, dans le style de l'écran « Changer de monstres » du
jeu : deux colonnes de 3 cases, un grand monstre couvrant 2 ou 3 cases.

Glisser-déposer (règles dans Sauvegarde.deplacer, en raisonnant par cases) :
  - d'une case à une autre : le monstre couvre autant de cases que sa taille et
    tous leurs occupants prennent sa place d'origine (case libre : déplacement) ;
  - depuis la liste du ranch vers une case : même chose, les délogés retournant
    au ranch ;
  - d'une case vers la liste : le monstre retourne au ranch.
Chaque opération passe par Sauvegarde.definir_composition(), qui tasse les
colonnes et refuse une colonne de plus de 3 places ou une équipe vide.
"""
from PySide6.QtCore import QMargins, QMimeData, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from dqmj2p_save import ErreurSauvegarde
from dqmj2p_save import format as F
from dqmj2p_save.langue import tr

from . import icones

TYPE_MIME = 'application/x-dqmj2p-monstre'     # contenu : emplacement du monstre
CASE = icones.CASE + 8
OR = QColor('#d8b64e')
FOND_CASE = QColor('#33508f')
FOND_CASE_SURVOL = QColor('#4f73c2')


def mime_monstre(emplacement: int) -> QMimeData:
    donnees = QMimeData()
    donnees.setData(TYPE_MIME, str(emplacement).encode())
    return donnees


def emplacement_depuis(mime: QMimeData) -> int | None:
    return int(bytes(mime.data(TYPE_MIME)).decode()) if mime.hasFormat(TYPE_MIME) else None


class Colonne(QWidget):
    """Trois cases ; source et cible de glisser-déposer."""

    def __init__(self, panneau: 'PanneauEquipe', nom: str):
        super().__init__()
        self.panneau = panneau
        self.nom = nom                          # 'equipe' ou 'reserve'
        self.survol: int | None = None          # case survolée pendant un dépôt
        self.depart = None
        self.setAcceptDrops(True)
        self.setFixedSize(CASE + 8, CASE * F.PLACES_PAR_COLONNE + 8)

    def monstres(self):
        return self.panneau.colonnes()[self.nom]

    def occupation(self) -> list[tuple[int, int, object]]:
        """[(première case, nombre de cases, monstre)]."""
        cases, debut = [], 0
        for m in self.monstres():
            n = self.panneau.sauvegarde.taille(m)
            cases.append((debut, n, m))
            debut += n
        return cases

    def case_sous(self, point: QPoint) -> int:
        return max(0, min(F.PLACES_PAR_COLONNE - 1, (point.y() - 4) // CASE))

    def monstre_sous(self, point: QPoint):
        case = self.case_sous(point)
        for debut, n, m in self.occupation():
            if debut <= case < debut + n:
                return m
        return None

    def paintEvent(self, _):
        p = QPainter(self)
        for case in range(F.PLACES_PAR_COLONNE):
            rect = QRect(4, 4 + case * CASE, CASE, CASE).adjusted(2, 2, -2, -2)
            p.setPen(QPen(OR, 2))
            p.setBrush(FOND_CASE_SURVOL if case == self.survol else FOND_CASE)
            p.drawRoundedRect(rect, 4, 4)
        selection = self.panneau.emplacement_selectionne
        for debut, n, m in self.occupation():
            zone = QRect(4, 4 + debut * CASE, CASE, n * CASE).adjusted(2, 2, -2, -2)
            if n > 1:                            # grand monstre : une seule case haute
                p.setPen(QPen(OR, 2))
                p.setBrush(FOND_CASE)
                p.drawRoundedRect(zone, 4, 4)
            if m.emplacement == selection:
                p.setPen(QPen(QColor('white'), 3))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(zone.adjusted(1, 1, -1, -1), 4, 4)
            image = icones.image(m['espece'])
            if not image.isNull():
                reduite = image.scaled(zone.size().shrunkBy(QMargins(2, 2, 2, 2)),
                                       Qt.KeepAspectRatio, Qt.FastTransformation)
                p.drawPixmap(zone.center().x() - reduite.width() // 2 + 1,
                             zone.center().y() - reduite.height() // 2 + 1, reduite)
        p.end()

    # ── Souris ───────────────────────────────────────────────────────────────

    def mousePressEvent(self, evenement):
        m = self.monstre_sous(evenement.position().toPoint())
        self.depart = evenement.position().toPoint() if m else None
        if m:
            self.panneau.clic(m)

    def mouseMoveEvent(self, evenement):
        if self.depart is None or not evenement.buttons() & Qt.LeftButton:
            return
        if (evenement.position().toPoint() - self.depart).manhattanLength() < 6:
            return
        m = self.monstre_sous(self.depart)
        self.depart = None
        if m:
            glisser(self, m)

    def dragEnterEvent(self, evenement):
        if evenement.mimeData().hasFormat(TYPE_MIME):
            evenement.acceptProposedAction()

    def dragMoveEvent(self, evenement):
        self.survol = self.case_sous(evenement.position().toPoint())
        self.update()
        evenement.acceptProposedAction()

    def dragLeaveEvent(self, _):
        self.survol = None
        self.update()

    def dropEvent(self, evenement):
        case = self.case_sous(evenement.position().toPoint())
        self.survol = None
        emplacement = emplacement_depuis(evenement.mimeData())
        if emplacement is not None:
            self.panneau.deposer(emplacement, self.nom, case)
            evenement.acceptProposedAction()
        self.update()


def glisser(source: QWidget, monstre) -> None:
    drag = QDrag(source)
    drag.setMimeData(mime_monstre(monstre.emplacement))
    image = icones.icone(monstre['espece']).pixmap(icones.TAILLE_CASE)
    drag.setPixmap(image)
    drag.setHotSpot(QPoint(image.width() // 2, image.height() // 2))
    drag.exec(Qt.MoveAction)


class PanneauEquipe(QFrame):
    """Signaux : modifiee (la composition a changé), selectionner(emplacement),
    message(texte) pour la barre d'état."""
    modifiee = Signal()
    selectionner = Signal(int)
    message = Signal(str)

    def __init__(self):
        super().__init__()
        self.sauvegarde = None
        self.emplacement_selectionne = None
        self.setObjectName('panneauEquipe')
        self.setStyleSheet(
            '#panneauEquipe { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, '
            'stop:0 #2b4684, stop:1 #16264f); border: 2px solid #d8b64e; border-radius: 8px; }'
            ' QLabel { color: white; font-weight: bold; }')
        self.equipe = Colonne(self, 'equipe')
        self.reserve = Colonne(self, 'reserve')
        disposition = QHBoxLayout(self)
        for titre, couleur, colonne in (('Équipe', '#c8322f', self.equipe),
                                        ('Réserve', '#2f6fc8', self.reserve)):
            bloc = QVBoxLayout()
            entete = QLabel(tr(titre), alignment=Qt.AlignCenter)
            entete.setStyleSheet(f'background: {couleur}; border: 1px solid #d8b64e; '
                                 'border-radius: 4px; padding: 1px 6px;')
            bloc.addWidget(entete)
            bloc.addWidget(colonne, 0, Qt.AlignHCenter)
            disposition.addLayout(bloc)
        aide = QLabel(tr('Glisser pour réorganiser.\nDepuis la liste : prendre\nla place. '
                         'Vers la liste :\nrenvoyer au ranch.'))
        aide.setStyleSheet('color: #dfe6f5; font-weight: normal;')
        disposition.addWidget(aide, 1, Qt.AlignVCenter)
        self.setEnabled(False)

    def afficher(self, sauvegarde) -> None:
        self.sauvegarde = sauvegarde
        self.setEnabled(True)
        self.update_colonnes()

    def update_colonnes(self) -> None:
        self.equipe.update()
        self.reserve.update()

    def colonnes(self) -> dict:
        if self.sauvegarde is None:
            return {'equipe': [], 'reserve': []}
        equipe, reserve = self.sauvegarde.composition()
        return {'equipe': equipe, 'reserve': reserve}

    def clic(self, monstre) -> None:
        self.selectionner.emit(monstre.emplacement)

    def marquer(self, emplacement: int | None) -> None:
        self.emplacement_selectionne = emplacement
        self.update_colonnes()

    # ── Opérations ───────────────────────────────────────────────────────────

    def deposer(self, emplacement: int, cible: str, case: int) -> None:
        """Dépose le monstre `emplacement` sur la case `case` de la colonne
        `cible` (voir Sauvegarde.deplacer : un grand monstre couvre plusieurs
        cases et en déloge tous les occupants)."""
        monstre = self.sauvegarde.monstre(emplacement)
        avant = self.sauvegarde.ids_equipe()
        try:
            self.sauvegarde.deplacer(monstre, cible, case)
        except ErreurSauvegarde as e:
            self.message.emit(tr('Impossible : {erreur}.', erreur=e))
            return
        if self.sauvegarde.ids_equipe() == avant:
            return
        self.update_colonnes()
        surnom = monstre['surnom'] or tr('Monstre')
        self.message.emit(tr('{surnom} placé en équipe.', surnom=surnom) if cible == 'equipe'
                          else tr('{surnom} placé en réserve.', surnom=surnom))
        self.modifiee.emit()

    def renvoyer_au_ranch(self, emplacement: int) -> None:
        colonnes = self.colonnes()
        nouvelle = {nom: [m for m in liste if m.emplacement != emplacement]
                    for nom, liste in colonnes.items()}
        if nouvelle == colonnes:
            return
        self._appliquer(nouvelle, tr('Monstre renvoyé au ranch.'))

    def _appliquer(self, colonnes: dict, message: str) -> None:
        try:
            self.sauvegarde.definir_composition(colonnes['equipe'], colonnes['reserve'])
        except ErreurSauvegarde as e:
            self.message.emit(tr('Impossible : {erreur}.', erreur=e))
            return
        self.update_colonnes()
        self.message.emit(message)
        self.modifiee.emit()
