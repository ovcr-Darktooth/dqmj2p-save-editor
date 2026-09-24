"""Zone de défilement pour les pages hautes (Joueur, Synthèses) : la fenêtre
se redimensionne librement, la page défile quand elle ne tient plus."""
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QFrame, QScrollArea


class ZoneDefilante(QScrollArea):
    """QScrollArea qui tient compte du retour à la ligne des textes.

    QScrollArea ne réserve que la hauteur minimale du contenu, calculée par Qt
    sans retour à la ligne : réduire la largeur tassait les rangées et les
    textes se chevauchaient. On réserve la hauteur réelle pour la largeur
    affichée, à chaque redimensionnement comme à chaque contenu qui change."""

    def __init__(self, contenu=None):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        if contenu is not None:
            self.setWidget(contenu)

    def setWidget(self, contenu) -> None:
        super().setWidget(contenu)
        contenu.installEventFilter(self)
        self._ajuster()

    def eventFilter(self, objet, evenement) -> bool:
        if objet is self.widget() and evenement.type() == QEvent.LayoutRequest:
            self._ajuster()
        return super().eventFilter(objet, evenement)

    def resizeEvent(self, evenement) -> None:
        super().resizeEvent(evenement)
        self._ajuster()

    def _ajuster(self) -> None:
        contenu = self.widget()
        disposition = contenu.layout() if contenu else None
        if disposition is None or not disposition.hasHeightForWidth():
            return
        largeur = max(self.viewport().width(), disposition.minimumSize().width())
        contenu.setMinimumHeight(disposition.heightForWidth(largeur))
