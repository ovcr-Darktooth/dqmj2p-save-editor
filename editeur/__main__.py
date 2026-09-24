"""Lance l'éditeur : python -m editeur [sauvegarde.dsv]"""
import sys

from PySide6.QtWidgets import QApplication

from .defilement import MoletteSansSaisie
from .fenetre import Fenetre


def main() -> None:
    app = QApplication(sys.argv)
    molette = MoletteSansSaisie(app)
    app.installEventFilter(molette)
    fenetre = Fenetre()
    fenetre.show()
    if len(sys.argv) > 1:
        fenetre.ouvrir(sys.argv[1])
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
