"""Onglet Joueur : nom, temps de jeu, or et statistiques de partie, plus la
date de sauvegarde, l'emplacement dans le monde et la téléportation vers des
points relevés en jeu, et le déblocage des îles de fin de partie."""
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGridLayout, QGroupBox,
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

        iles = QGroupBox(tr('Zones'))
        formulaire = QFormLayout(iles)
        self.carte_iles = QComboBox()
        self.carte_iles.activated.connect(self._regler_chapitre)
        formulaire.addRow(tr('Carte des îles'), self.carte_iles)
        aide = QLabel(tr("Le jeu y ajoute les îles au fil des chapitres de l'histoire : "
                         "l'avancer peut faire sauter des événements. On ne peut pas "
                         "revenir en deçà du chapitre de la partie."))
        aide.setWordWrap(True)
        aide.setEnabled(False)                      # texte grisé, comme une légende
        formulaire.addRow(aide)
        grille = QGridLayout()
        self.cases_zones = {}
        for rang, zone in enumerate(F.TELEPORTATION):
            case = QCheckBox(tr(zone))
            case.toggled.connect(lambda actif, zone=zone: self._ouvrir_zone(zone, actif))
            grille.addWidget(case, rang // 4, rang % 4)
            self.cases_zones[zone] = case
        grille.setColumnStretch(4, 1)
        formulaire.addRow(tr('Sort Téléportation'), grille)
        aide = QLabel(tr("Une zone cochée entre dans la liste du sort (dans l'ordre du "
                         "jeu), sans changer de chapitre ; une île s'affiche aussi comme "
                         "visitée sur la carte. Les zones déjà visitées restent cochées : "
                         "le jeu les remettrait. Attention, ouvrir Nécropolis, Ténébria ou "
                         "l'Île des Pipits (ou s'y téléporter) avant que l'histoire y mène "
                         "peut causer des soucis : seules l'arrivée et l'exploration ont été "
                         "testées, pas la suite de l'histoire."))
        aide.setWordWrap(True)
        aide.setEnabled(False)
        formulaire.addRow(aide)
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

    def _ouvrir_zone(self, zone: str, actif: bool) -> None:
        self.liaison.vue.sauvegarde.ouvrir_zone(zone, actif)
        self._remplir_points()
        self.liaison.modifiee.emit()

    def _regler_chapitre(self) -> None:
        sauvegarde = self.liaison.vue.sauvegarde
        chapitre = self.carte_iles.currentData()
        if sauvegarde.chapitre != chapitre:
            sauvegarde.chapitre = chapitre
            self.liaison.modifiee.emit()

    def _afficher_iles(self, sauvegarde) -> None:
        # Le chapitre ne descend pas sous celui de la partie, et les îles déjà
        # visitées restent : revenir en arrière n'a pas été essayé en jeu.
        origine = sauvegarde.chapitre
        self.carte_iles.clear()
        paliers = sorted(set(F.CHAPITRE_CARTE.values()) | {origine})
        for chapitre in (c for c in paliers if c >= origine):
            iles = [tr(i) for i, seuil in F.CHAPITRE_CARTE.items() if seuil <= chapitre]
            self.carte_iles.addItem(
                tr('{iles}  (chapitre {n})', iles=', '.join(iles) if iles else tr('Aucune île'),
                   n=chapitre), chapitre)
        self.carte_iles.setEnabled(self.carte_iles.count() > 1)
        # La liste déroulante ne coupe pas le plus long palier.
        largeur = max(self.carte_iles.fontMetrics().horizontalAdvance(
            self.carte_iles.itemText(i)) for i in range(self.carte_iles.count()))
        self.carte_iles.view().setMinimumWidth(largeur + 40)
        for zone, case in self.cases_zones.items():
            visitee = sauvegarde.zone_visitee(zone)
            case.blockSignals(True)
            case.setChecked(visitee)
            case.blockSignals(False)
            case.setEnabled(not visitee)
            case.setToolTip(tr('Déjà visitée dans cette partie.') if visitee else '')

    def _remplir_points(self) -> None:
        """Points de téléportation, sans ceux des îles pas encore ouvertes."""
        sauvegarde = self.liaison.vue.sauvegarde
        choisi = self.points.currentData()
        self.points.clear()
        for point in F.POINTS_TELEPORTATION:
            if point not in F.ILES_FIN_DE_PARTIE or sauvegarde.zone_visitee(point):
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
