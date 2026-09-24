"""Icônes des monstres (icones/<id espèce>.png, voir outils/importer_icones.py).

Les icônes font 40 px de large et 40, 80 ou 120 px de haut selon la taille du
monstre. Une icône absente n'est pas une erreur : on affiche une case vide.
"""
import sys
from functools import cache
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap

# Exe Windows (PyInstaller) : icones/ à côté de l'exe, où l'on peut les déposer.
DOSSIER = (Path(sys.executable).parent if getattr(sys, 'frozen', False)
           else Path(__file__).parent) / 'icones'
CASE = 40                           # côté de la case dans les listes


@cache
def image(espece: int) -> QPixmap:
    """Icône en taille réelle (pixmap nulle si absente)."""
    return QPixmap(str(DOSSIER / f'{espece}.png'))


@cache
def icone(espece: int) -> QIcon:
    """Icône tenant dans une case carrée, pour les listes et menus."""
    source = image(espece)
    if source.isNull():
        return QIcon()
    reduite = source.scaled(CASE, CASE, Qt.KeepAspectRatio, Qt.FastTransformation)
    case = QPixmap(CASE, CASE)
    case.fill(Qt.transparent)
    peintre = QPainter(case)
    peintre.drawPixmap((CASE - reduite.width()) // 2, (CASE - reduite.height()) // 2, reduite)
    peintre.end()
    return QIcon(case)


def agrandie(espece: int, hauteur_mini: int = 2 * CASE) -> QPixmap:
    """Icône agrandie d'un facteur entier, sans lissage (pixel art net), jusqu'à
    atteindre hauteur_mini ; les grands monstres restent en taille réelle."""
    source = image(espece)
    if source.isNull():
        return source
    facteur = max(1, hauteur_mini // source.height())
    return source.scaled(source.size() * facteur, Qt.IgnoreAspectRatio,
                         Qt.FastTransformation)


TAILLE_CASE = QSize(CASE, CASE)

FAMILLES = DOSSIER / 'familles'     # glyphes de la police du jeu (outils/extraire_familles.py)


def chemin_famille(famille: str | None) -> Path | None:
    """Fichier de l'icône d'une famille (« ??? » -> inconnue.png), ou None."""
    if not famille:
        return None
    chemin = FAMILLES / f"{'inconnue' if famille == '???' else famille}.png"
    return chemin if chemin.exists() else None


@cache
def famille(nom: str | None, facteur: int = 2) -> QPixmap:
    chemin = chemin_famille(nom)
    if chemin is None:
        return QPixmap()
    source = QPixmap(str(chemin))
    return source.scaled(source.size() * facteur, Qt.IgnoreAspectRatio, Qt.FastTransformation)


BOUTONS = DOSSIER / 'boutons'       # boutons du menu (outils/extraire_boutons.py)


@cache
def bouton(id_: int, facteur: int = 2) -> QPixmap:
    """Icône du bouton de menu, agrandie sans lissage (nulle si absente)."""
    source = QPixmap(str(BOUTONS / f'{id_}.png'))
    if source.isNull():
        return source
    return source.scaled(source.size() * facteur, Qt.IgnoreAspectRatio, Qt.FastTransformation)
