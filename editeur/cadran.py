"""Cadran rond de l'horloge jour/nuit : soleil en haut (milieu du jour), lune en
bas (milieu de la nuit). On règle l'heure en faisant glisser la poignée ou avec
la molette.

Le jour dure 6 min et la nuit 4 : leurs milieux (5 400 et 14 400) sont à un
demi-cycle d'écart, d'où un soleil pile en haut et une lune pile en bas.
"""
import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from dqmj2p_save import format as F
from dqmj2p_save.langue import decimal, tr

MILIEU_JOUR = F.DEBUT_NUIT // 2
PAS_MOLETTE = 5 * 30                # 5 secondes
CIEL_JOUR = QColor('#f5c542')
CIEL_NUIT = QColor('#243a73')


class CadranHoraire(QWidget):
    valueChanged = Signal(int)

    def __init__(self):
        super().__init__()
        self._valeur = 0
        self.setMinimumSize(170, 170)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tr("Faire glisser la poignée, ou la molette (5 s par cran). "
                           "L'horloge ne tourne qu'en plein air."))

    def sizeHint(self):
        return self.minimumSize()

    # ── Valeur ───────────────────────────────────────────────────────────────

    def value(self) -> int:
        return self._valeur

    def setValue(self, valeur: int) -> None:
        valeur %= F.DUREE_CYCLE
        if valeur != self._valeur:
            self._valeur = valeur
            self.update()

    def _changer(self, valeur: int) -> None:
        valeur %= F.DUREE_CYCLE
        if valeur != self._valeur:
            self._valeur = valeur
            self.update()
            self.valueChanged.emit(valeur)

    # ── Géométrie : angle 0 en haut, sens horaire ────────────────────────────

    @staticmethod
    def _angle(valeur: float) -> float:
        return (valeur - MILIEU_JOUR) / F.DUREE_CYCLE * 360

    def _centre_rayon(self) -> tuple[QPointF, float]:
        cote = min(self.width(), self.height())
        return QPointF(self.width() / 2, self.height() / 2), cote / 2 - 12

    def _point(self, angle: float, rayon: float) -> QPointF:
        centre, _ = self._centre_rayon()
        rad = math.radians(angle)
        return QPointF(centre.x() + rayon * math.sin(rad), centre.y() - rayon * math.cos(rad))

    # ── Dessin ───────────────────────────────────────────────────────────────

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        centre, rayon = self._centre_rayon()
        anneau = QRectF(centre.x() - rayon, centre.y() - rayon, 2 * rayon, 2 * rayon)
        epaisseur = 14

        # Arcs jour / nuit (Qt : angles en 1/16 de degré, 0 à 3 h, sens direct)
        def arc(debut: float, fin: float, couleur: QColor) -> None:
            p.setPen(QPen(couleur, epaisseur, Qt.SolidLine, Qt.FlatCap))
            a0, a1 = self._angle(debut), self._angle(fin)
            p.drawArc(anneau, int((90 - a0) * 16), int(-(a1 - a0) * 16))
        arc(0, F.DEBUT_NUIT, CIEL_JOUR)
        arc(F.DEBUT_NUIT, F.DUREE_CYCLE, CIEL_NUIT)

        # Repères du lever et du coucher
        p.setPen(QPen(self.palette().windowText().color(), 2))
        for seuil in (0, F.DEBUT_NUIT):
            a = self._angle(seuil)
            p.drawLine(self._point(a, rayon - epaisseur / 2 - 3),
                       self._point(a, rayon + epaisseur / 2 + 3))

        self._soleil(p, self._point(0, rayon - 30), 11)
        self._lune(p, self._point(180, rayon - 30), 11)

        # Texte central
        jour = self._valeur < F.DEBUT_NUIT
        reste = (F.DEBUT_NUIT if jour else F.DUREE_CYCLE) - self._valeur
        p.setPen(self.palette().windowText().color())
        police = QFont(self.font())
        police.setBold(True)
        p.setFont(police)
        p.drawText(QRectF(centre.x() - 50, centre.y() - 20, 100, 20), Qt.AlignCenter,
                   tr('Jour') if jour else tr('Nuit'))
        p.setFont(self.font())
        minutes = decimal(reste / 30 / 60, 1)
        p.drawText(QRectF(centre.x() - 60, centre.y(), 120, 18), Qt.AlignCenter,
                   tr('nuit dans {n} min', n=minutes) if jour
                   else tr('jour dans {n} min', n=minutes))

        # Poignée
        poignee = self._point(self._angle(self._valeur), rayon)
        p.setPen(QPen(QColor('#202020'), 2))
        p.setBrush(QColor('white'))
        p.drawEllipse(poignee, 8, 8)
        p.end()

    @staticmethod
    def _soleil(p: QPainter, c: QPointF, r: float) -> None:
        p.setPen(QPen(QColor('#e39a10'), 2))
        for k in range(8):
            a = math.radians(k * 45)
            p.drawLine(QPointF(c.x() + (r * 0.75) * math.cos(a), c.y() + (r * 0.75) * math.sin(a)),
                       QPointF(c.x() + (r + 4) * math.cos(a), c.y() + (r + 4) * math.sin(a)))
        p.setBrush(CIEL_JOUR)
        p.drawEllipse(c, r * 0.6, r * 0.6)

    @staticmethod
    def _lune(p: QPainter, c: QPointF, r: float) -> None:
        disque = QPainterPath()
        disque.addEllipse(c, r, r)
        ombre = QPainterPath()
        ombre.addEllipse(QPointF(c.x() + r * 0.55, c.y() - r * 0.3), r, r)
        p.setPen(QPen(QColor('#8f97b8'), 1))
        p.setBrush(QColor('#e8e4c8'))
        p.drawPath(disque.subtracted(ombre))

    # ── Souris et molette ────────────────────────────────────────────────────

    def _depuis_souris(self, position: QPointF) -> None:
        centre, _ = self._centre_rayon()
        angle = math.degrees(math.atan2(position.x() - centre.x(), centre.y() - position.y()))
        self._changer(round(MILIEU_JOUR + angle / 360 * F.DUREE_CYCLE))

    def mousePressEvent(self, evenement):
        if evenement.button() == Qt.LeftButton:
            self._depuis_souris(evenement.position())

    def mouseMoveEvent(self, evenement):
        if evenement.buttons() & Qt.LeftButton:
            self._depuis_souris(evenement.position())

    def wheelEvent(self, evenement):
        crans = evenement.angleDelta().y() // 120
        if crans:
            self._changer(self._valeur + crans * PAS_MOLETTE)
