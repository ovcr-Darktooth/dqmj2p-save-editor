"""Onglet Joueur : nom, temps de jeu, or et statistiques de partie, plus la
date de sauvegarde, l'emplacement dans le monde et la téléportation vers des
points relevés en jeu."""
from PySide6.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout,
                               QLabel, QPushButton, QVBoxLayout, QWidget)

from dqmj2p_save import format as F
from dqmj2p_save import noms

from .cadran import CadranHoraire
from .saisies import Liaison

CHAMPS = ('nom', 'temps_jeu', 'or', 'banque', 'victoires', 'dressages',
          'syntheses', 'dernier_id_creation')
JOURS = ('dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi')


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

        infos = QGroupBox('Dernière sauvegarde en jeu')
        formulaire = QFormLayout(infos)
        self.date = QLabel()
        self.lieu = QLabel()
        self.position = QLabel()
        formulaire.addRow('Date', self.date)
        formulaire.addRow('Location', self.lieu)
        formulaire.addRow('Position X / Y / Z', self.position)
        self.cadran = CadranHoraire()
        self.cadran.valueChanged.connect(self._regler_horloge)
        jour = QPushButton('Lever du jour')
        jour.clicked.connect(lambda: self._regler_horloge(0))
        nuit = QPushButton('Tombée de la nuit')
        nuit.clicked.connect(lambda: self._regler_horloge(F.DEBUT_NUIT))
        boutons = QVBoxLayout()
        boutons.addStretch()
        boutons.addWidget(jour)
        boutons.addWidget(nuit)
        boutons.addStretch()
        ligne_horloge = QHBoxLayout()
        ligne_horloge.addWidget(self.cadran)
        ligne_horloge.addLayout(boutons)
        ligne_horloge.addStretch()
        formulaire.addRow('Moment de la journée', ligne_horloge)
        self.points = QComboBox()
        self.points.addItems(F.POINTS_TELEPORTATION)
        bouton = QPushButton('Téléporter')
        bouton.clicked.connect(self._teleporter)
        ligne = QHBoxLayout()
        ligne.addWidget(self.points, 1)
        ligne.addWidget(bouton)
        formulaire.addRow('Téléporter vers', ligne)
        aide = QLabel('Points relevés dans des sauvegardes faites sur place : la '
                      "position, l'orientation et la carte du résumé sont recopiées.")
        aide.setWordWrap(True)
        formulaire.addRow(aide)
        disposition.addWidget(infos)
        disposition.addStretch()
        self.setEnabled(False)

    def afficher(self, joueur) -> None:
        self.liaison.afficher(joueur)
        self._afficher_emplacement()
        self.setEnabled(True)

    def _teleporter(self) -> None:
        joueur = self.liaison.vue
        joueur.sauvegarde.teleporter(self.points.currentText())
        self._afficher_emplacement()
        self.liaison.modifiee.emit()

    def _regler_horloge(self, valeur: int) -> None:
        if self.liaison.vue['horloge'] == valeur:
            return
        self.liaison.vue['horloge'] = valeur
        self.cadran.setValue(valeur)
        self.liaison.modifiee.emit()

    def _afficher_emplacement(self) -> None:
        joueur = self.liaison.vue
        j = {c: joueur[c] for c in F.CHAMP_JOUEUR}
        jour = JOURS[j['sauvegarde_jour_semaine']] if j['sauvegarde_jour_semaine'] < 7 else '?'
        self.date.setText(f"{jour} {j['sauvegarde_jour']:02}/{j['sauvegarde_mois']:02}/"
                          f"{2000 + j['sauvegarde_annee']} à {j['sauvegarde_heure']:02}:"
                          f"{j['sauvegarde_minute']:02}:{j['sauvegarde_seconde']:02}")
        self.lieu.setText(f"{j['location']} — {noms.carte(j['location'])}   "
                          f"(précédente : {j['location_precedente']} — "
                          f"{noms.carte(j['location_precedente'])})")
        self.position.setText(' / '.join(f"{j[f'position_{a}'] / 100:.2f}".replace('.', ',')
                                         for a in 'xyz'))
        self.cadran.setValue(j['horloge'])
