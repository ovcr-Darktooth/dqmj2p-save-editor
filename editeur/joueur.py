"""Onglet Joueur : nom, temps de jeu, or et statistiques de partie, plus la
date de sauvegarde, l'emplacement dans le monde et la téléportation vers des
points relevés en jeu, et le déblocage des îles de fin de partie."""
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGroupBox,
                               QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget)

from dqmj2p_save import format as F
from dqmj2p_save import noms
from dqmj2p_save.langue import decimal, tr

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
            formulaire.addRow(tr(F.CHAMP_JOUEUR[cle].libelle), self.liaison.saisie(cle))
        disposition.addLayout(formulaire)
        note = QLabel(tr('Le nom et les surnoms sont limités à 8 caractères, pris '
                         'dans la police du jeu.'))
        note.setWordWrap(True)
        disposition.addWidget(note)

        infos = QGroupBox(tr('Dernière sauvegarde en jeu'))
        formulaire = QFormLayout(infos)
        self.date = QLabel()
        self.lieu = QLabel()
        self.position = QLabel()
        formulaire.addRow(tr('Date'), self.date)
        formulaire.addRow(tr('Location'), self.lieu)
        formulaire.addRow(tr('Position X / Y / Z'), self.position)
        self.cadran = CadranHoraire()
        self.cadran.valueChanged.connect(self._regler_horloge)
        jour = QPushButton(tr('Lever du jour'))
        jour.clicked.connect(lambda: self._regler_horloge(0))
        nuit = QPushButton(tr('Tombée de la nuit'))
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
        formulaire.addRow(tr('Moment de la journée'), ligne_horloge)
        self.intemperie = QCheckBox()
        self.intemperie.setToolTip(tr("Seulement sur les cartes où le jeu prévoit une "
                                      "intempérie : forcée ailleurs, la zone perd ses "
                                      "monstres et sa musique."))
        self.intemperie.toggled.connect(self._regler_intemperie)
        formulaire.addRow(tr('Météo'), self.intemperie)
        self.points = QComboBox()
        bouton = QPushButton(tr('Téléporter'))
        bouton.clicked.connect(self._teleporter)
        ligne = QHBoxLayout()
        ligne.addWidget(self.points, 1)
        ligne.addWidget(bouton)
        formulaire.addRow(tr('Téléporter vers'), ligne)
        aide = QLabel(tr('Points relevés dans des sauvegardes faites sur place : la '
                         "position, l'orientation et la carte du résumé sont recopiées."))
        aide.setWordWrap(True)
        formulaire.addRow(aide)
        disposition.addWidget(infos)

        iles = QGroupBox(tr('Îles de fin de partie'))
        colonne = QVBoxLayout(iles)
        ligne = QHBoxLayout()
        self.cases_iles = {}
        for ile in F.TELEPORTATION_ILES:
            case = QCheckBox(tr(ile))
            case.toggled.connect(lambda actif, ile=ile: self._ouvrir_ile(ile, actif))
            ligne.addWidget(case)
            self.cases_iles[ile] = case
        ligne.addStretch()
        colonne.addLayout(ligne)
        self.chapitre = QLabel()
        colonne.addWidget(self.chapitre)
        aide = QLabel(tr("Une île cochée entre dans la liste du sort Téléportation et "
                         "s'affiche comme visitée. Pour la montrer sur la carte des îles, "
                         "l'histoire avance au chapitre où le jeu la débloque (Nécropolis "
                         "8, Ténébria 9, Île des Pipits 10) : les îles des chapitres "
                         "précédents apparaissent aussi, et des événements de l'histoire "
                         "peuvent être sautés. Les îles déjà visitées restent cochées."))
        aide.setWordWrap(True)
        aide.setEnabled(False)                      # texte grisé, comme une légende
        colonne.addWidget(aide)
        disposition.addWidget(iles)
        disposition.addStretch()
        self.setEnabled(False)

    def afficher(self, joueur) -> None:
        self.liaison.afficher(joueur)
        self._afficher_emplacement()
        self._afficher_iles(joueur.sauvegarde)
        self._remplir_points()
        self.setEnabled(True)

    def _teleporter(self) -> None:
        joueur = self.liaison.vue
        joueur.sauvegarde.teleporter(self.points.currentData())
        self._afficher_emplacement()
        self.liaison.modifiee.emit()

    def _regler_horloge(self, valeur: int) -> None:
        if self.liaison.vue['horloge'] == valeur:
            return
        self.liaison.vue.sauvegarde.regler_horloge(valeur)
        self.cadran.setValue(valeur)
        self.liaison.modifiee.emit()

    def _regler_intemperie(self, active: bool) -> None:
        joueur = self.liaison.vue
        if joueur is None or bool(joueur['intemperie']) == active:
            return
        joueur['intemperie'] = int(active)
        self.liaison.modifiee.emit()

    def _ouvrir_ile(self, ile: str, actif: bool) -> None:
        sauvegarde = self.liaison.vue.sauvegarde
        sauvegarde.ouvrir_ile(ile, actif)
        # Une île décochée rend le chapitre qu'elle avait fait avancer.
        sauvegarde.chapitre = max([self._chapitre_d_origine] + [
            seuil for i, seuil in F.CHAPITRE_CARTE.items() if sauvegarde.ile_visitee(i)])
        self._afficher_chapitre(sauvegarde)
        self._remplir_points()
        self.liaison.modifiee.emit()

    def _afficher_iles(self, sauvegarde) -> None:
        # Les îles déjà visitées restent : retirer leurs drapeaux d'une partie
        # avancée n'a pas été essayé en jeu.
        self._chapitre_d_origine = sauvegarde.chapitre
        self._afficher_chapitre(sauvegarde)
        for ile, case in self.cases_iles.items():
            visitee = sauvegarde.ile_visitee(ile)
            case.blockSignals(True)
            case.setChecked(visitee)
            case.blockSignals(False)
            case.setEnabled(not visitee)
            case.setToolTip(tr('Déjà visitée dans cette partie.') if visitee else '')

    def _afficher_chapitre(self, sauvegarde) -> None:
        texte = tr("Chapitre de l'histoire : {n}", n=sauvegarde.chapitre)
        if sauvegarde.chapitre != self._chapitre_d_origine:
            texte += tr('  (au lieu de {n})', n=self._chapitre_d_origine)
        self.chapitre.setText(texte)

    def _remplir_points(self) -> None:
        """Points de téléportation, sans ceux des îles pas encore ouvertes."""
        sauvegarde = self.liaison.vue.sauvegarde
        choisi = self.points.currentData()
        self.points.clear()
        for point in F.POINTS_TELEPORTATION:
            if point not in F.TELEPORTATION_ILES or sauvegarde.ile_visitee(point):
                self.points.addItem(tr(point), point)
        self.points.setCurrentIndex(max(0, self.points.findData(choisi)))

    def _afficher_emplacement(self) -> None:
        joueur = self.liaison.vue
        j = {c: joueur[c] for c in F.CHAMP_JOUEUR}
        jour = (tr(JOURS[j['sauvegarde_jour_semaine']]) if j['sauvegarde_jour_semaine'] < 7
                else '?')
        self.date.setText(tr('{jour} {j:02}/{m:02}/{a} à {h:02}:{min:02}:{s:02}',
                             jour=jour, j=j['sauvegarde_jour'], m=j['sauvegarde_mois'],
                             a=2000 + j['sauvegarde_annee'], h=j['sauvegarde_heure'],
                             min=j['sauvegarde_minute'], s=j['sauvegarde_seconde']))
        self.lieu.setText(tr('{n} — {lieu}   (précédente : {n_avant} — {lieu_avant})',
                             n=j['location'], lieu=noms.carte(j['location']),
                             n_avant=j['location_precedente'],
                             lieu_avant=noms.carte(j['location_precedente'])))
        self.position.setText(' / '.join(decimal(j[f'position_{a}'] / 100) for a in 'xyz'))
        self.cadran.setValue(j['horloge'])
        meteo = noms.METEO.get(j['location'])
        self.intemperie.blockSignals(True)
        self.intemperie.setChecked(bool(j['intemperie']))
        self.intemperie.blockSignals(False)
        # Sur une carte sans météo connue, on laisse décocher mais pas cocher.
        self.intemperie.setEnabled(meteo is not None or bool(j['intemperie']))
        self.intemperie.setText(tr('{meteo} en cours', meteo=tr(meteo).capitalize()) if meteo
                                else tr('Aucune intempérie connue sur cette carte'))
