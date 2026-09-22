"""Onglet Joueur : nom, temps de jeu, or et statistiques de partie."""
from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from dqmj2p_save import format as F

from .saisies import Liaison

CHAMPS = ('nom', 'temps_jeu', 'or', 'banque', 'victoires', 'dressages',
          'syntheses', 'dernier_id_creation')


class PageJoueur(QWidget):
    def __init__(self):
        super().__init__()
        self.liaison = Liaison(F.CHAMP_JOUEUR)
        disposition = QVBoxLayout(self)
        formulaire = QFormLayout()
        for cle in CHAMPS:
            formulaire.addRow(F.CHAMP_JOUEUR[cle].libelle, self.liaison.saisie(cle))
        disposition.addLayout(formulaire)
        note = QLabel('Le nom et les surnoms sont limités à 8 caractères, pris '
                      'dans la police du jeu.')
        note.setWordWrap(True)
        disposition.addWidget(note)
        disposition.addStretch()
        self.setEnabled(False)

    def afficher(self, joueur) -> None:
        self.liaison.afficher(joueur)
        self.setEnabled(True)
