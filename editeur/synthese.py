"""Onglet Synthèse de la fiche : synthèses spéciales qui donnent l'espèce du
monstre, et celles où elle sert de parent."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QScrollArea,
                               QVBoxLayout, QWidget)

from dqmj2p_save import bestiaire, noms
from dqmj2p_save.langue import tr

from . import icones

AUCUNE_RECETTE = ('Aucune synthèse spéciale : à obtenir par recrutement ou '
                  'synthèse de familles.')
AUCUN_USAGE = "N'apparaît dans aucune synthèse spéciale."


def _monstre(espece: int, surligne: bool = False) -> QWidget:
    """Icône + nom, en gras pour l'espèce de la fiche."""
    bloc = QWidget()
    disposition = QHBoxLayout(bloc)
    disposition.setContentsMargins(0, 0, 0, 0)
    disposition.setSpacing(4)
    image = QLabel()
    image.setPixmap(icones.icone(espece).pixmap(icones.TAILLE_CASE))
    nom = QLabel(noms.table('especes')[espece])
    if surligne:
        nom.setStyleSheet('font-weight: bold')
    disposition.addWidget(image)
    disposition.addWidget(nom)
    return bloc


def _ligne(recette: bestiaire.Recette, espece: int, montrer_resultat: bool) -> QWidget:
    ligne = QWidget()
    disposition = QHBoxLayout(ligne)
    disposition.setContentsMargins(4, 2, 4, 2)
    for i, parent in enumerate(recette.parents):
        if i:
            disposition.addWidget(QLabel('+'))
        disposition.addWidget(_monstre(parent, surligne=parent == espece))
    if montrer_resultat:
        disposition.addWidget(QLabel('→'))
        disposition.addWidget(_monstre(recette.resultat))
    if recette.patch:
        etiquette = QLabel(tr('patch'))
        etiquette.setToolTip(tr('Recette ajoutée par le patch de traduction'))
        etiquette.setStyleSheet('color: palette(highlighted-text); background: palette(highlight);'
                                'border-radius: 3px; padding: 1px 4px')
        disposition.addWidget(etiquette, 0, Qt.AlignVCenter)
    disposition.addStretch()
    return ligne


class PageSynthese(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setWidget(QWidget())

    def afficher(self, espece: int) -> None:
        contenu = QWidget()
        disposition = QVBoxLayout(contenu)
        for titre, recettes, montrer_resultat, vide in (
                ('Obtenu par', bestiaire.obtenu_par(espece), False, AUCUNE_RECETTE),
                ('Sert à créer', bestiaire.sert_a(espece), True, AUCUN_USAGE)):
            entete = QLabel(f'{tr(titre)} ({len(recettes)})')
            entete.setStyleSheet('font-weight: bold; margin-top: 6px')
            disposition.addWidget(entete)
            if not recettes:
                note = QLabel(tr(vide))
                note.setWordWrap(True)
                disposition.addWidget(note)
            for recette in recettes:
                disposition.addWidget(_ligne(recette, espece, montrer_resultat))
        disposition.addStretch()
        self.setWidget(contenu)
        self.verticalScrollBar().setValue(0)
