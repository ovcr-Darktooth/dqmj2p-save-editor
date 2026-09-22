"""Onglet Joueur : nom, temps de jeu, or et statistiques de partie, plus la
date de sauvegarde et l'emplacement dans le monde (lecture seule)."""
from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QVBoxLayout, QWidget

from dqmj2p_save import format as F

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

        infos = QGroupBox('Dernière sauvegarde en jeu (lecture seule)')
        formulaire = QFormLayout(infos)
        self.date = QLabel()
        self.lieu = QLabel()
        self.position = QLabel()
        formulaire.addRow('Date', self.date)
        formulaire.addRow('Location', self.lieu)
        formulaire.addRow('Position X / Y / Z', self.position)
        disposition.addWidget(infos)
        disposition.addStretch()
        self.setEnabled(False)

    def afficher(self, joueur) -> None:
        self.liaison.afficher(joueur)
        j = {c: joueur[c] for c in F.CHAMP_JOUEUR}
        jour = JOURS[j['sauvegarde_jour_semaine']] if j['sauvegarde_jour_semaine'] < 7 else '?'
        self.date.setText(f"{jour} {j['sauvegarde_jour']:02}/{j['sauvegarde_mois']:02}/"
                          f"{2000 + j['sauvegarde_annee']} à {j['sauvegarde_heure']:02}:"
                          f"{j['sauvegarde_minute']:02}:{j['sauvegarde_seconde']:02}")
        self.lieu.setText(f"{j['location']} (précédente : {j['location_precedente']})")
        self.position.setText(' / '.join(f"{j[f'position_{a}'] / 100:.2f}".replace('.', ',')
                                         for a in 'xyz'))
        self.setEnabled(True)
