"""Onglet Synthèses : synthèses spéciales que permettent les monstres de
l'équipe, de la réserve et du ranch, tout de suite ou bientôt (analyse de
dqmj2p_save.syntheses). Un clic sur le nom d'un monstre l'ouvre dans l'onglet
Monstres.

Sous chaque synthèse possible ou bientôt possible, « Ensuite » déplie les
synthèses que son enfant permettra, et ainsi de suite : un arbre qui monte
d'un niveau à chaque dépliage (calculé à la demande)."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
                               QScrollArea, QToolButton, QVBoxLayout, QWidget)

from dqmj2p_save import noms, syntheses
from dqmj2p_save.langue import tr
from dqmj2p_save.syntheses import BIENTOT, INCOMPLETE, POSSIBLE

from . import icones

IGNORER_POLARITE = 'Ignorer la polarité (sexe)'
AIDE_POLARITE = ('Le patch anglais permet de désactiver la polarité pour les '
                 'synthèses : deux parents de même polarité peuvent alors être '
                 'synthétisés.')
MASQUER_DRESSEES = 'Masquer les espèces déjà dressées'
# Synthèses incomplètes montrées : libellé -> nombre maximal d'espèces manquantes.
INCOMPLETES = {
    'Incomplètes : aucune': 0,
    'Incomplètes : il manque 1 monstre': 1,
    'Incomplètes : il manque 1 ou 2 monstres': 2,
    'Incomplètes : toutes': 4,
}
TITRES = {POSSIBLE: 'Possibles maintenant', BIENTOT: 'Bientôt possibles',
          INCOMPLETE: 'Incomplètes'}
AUCUNE = 'Aucune synthèse spéciale à portée avec ces réglages.'
AIDE_SUITES = ("Synthèses que permettra l'enfant de celle-ci, avec les monstres qu'elle "
               "ne consomme pas. L'enfant naît au niveau 1 : il faudra le monter au "
               'niveau 10.')


def _espece(espece: int, gras: bool = False, absent: bool = False) -> QWidget:
    bloc = QWidget()
    disposition = QHBoxLayout(bloc)
    disposition.setContentsMargins(0, 0, 0, 0)
    disposition.setSpacing(4)
    image = QLabel()
    image.setPixmap(icones.icone(espece).pixmap(icones.TAILLE_CASE))
    nom = QLabel(noms.table('especes')[espece])
    if gras:
        nom.setStyleSheet('font-weight: bold')
    disposition.addWidget(image)
    disposition.addWidget(nom)
    if absent:
        bloc.setEnabled(False)          # grisé : espèce à trouver
        bloc.setToolTip(tr('Aucun monstre disponible de cette espèce'))
    return bloc


def _etiquette(texte: str, aide: str) -> QLabel:
    etiquette = QLabel(texte)
    etiquette.setToolTip(aide)
    etiquette.setStyleSheet('color: palette(highlighted-text); background: palette(highlight);'
                            'border-radius: 3px; padding: 1px 4px')
    return etiquette


class PageSyntheses(QWidget):
    selectionner = Signal(int)          # emplacement du monstre cliqué

    def __init__(self):
        super().__init__()
        self.sauvegarde = None
        self._dressees: set[int] = set()
        self.polarite = QCheckBox(tr(IGNORER_POLARITE))
        self.polarite.setChecked(True)
        self.polarite.setToolTip(tr(AIDE_POLARITE))
        self.incompletes = QComboBox()
        for libelle, maximum in INCOMPLETES.items():
            self.incompletes.addItem(tr(libelle), maximum)
        self.incompletes.setCurrentIndex(1)
        self.dressees = QCheckBox(tr(MASQUER_DRESSEES))
        self.resume = QLabel()
        for signal in (self.polarite.toggled, self.dressees.toggled,
                       self.incompletes.currentIndexChanged):
            signal.connect(self.rafraichir)

        options = QHBoxLayout()
        for widget in (self.polarite, self.incompletes, self.dressees):
            options.addWidget(widget)
        options.addStretch()
        options.addWidget(self.resume)
        note = QLabel(tr("Monstres de l'équipe, de la réserve et du ranch. Chaque parent "
                         'doit être au moins au niveau {niveau}. Une synthèse à 4 se fait '
                         "avec deux monstres nés chacun d'une des paires.",
                         niveau=syntheses.NIVEAU_MIN))
        note.setWordWrap(True)
        self.zone = QScrollArea()
        self.zone.setWidgetResizable(True)
        self.zone.setFrameShape(QFrame.NoFrame)
        self.zone.setWidget(QWidget())

        disposition = QVBoxLayout(self)
        disposition.addLayout(options)
        disposition.addWidget(note)
        disposition.addWidget(self.zone, 1)

    def afficher(self, sauvegarde) -> None:
        self.sauvegarde = sauvegarde
        self.rafraichir()

    def rafraichir(self) -> None:
        if self.sauvegarde is None:
            return
        analyses = syntheses.analyser(self.sauvegarde.monstres(), self.polarite.isChecked())
        maximum = self.incompletes.currentData()
        dressees = (self.sauvegarde.bibliotheque.especes_dressees()
                    if self.dressees.isChecked() else set())
        retenues = [a for a in analyses
                    if (a.etat != INCOMPLETE or a.nb_manquants <= maximum)
                    and a.recette.resultat not in dressees]
        par_etat = {etat: [a for a in retenues if a.etat == etat] for etat in syntheses.ETATS}
        self.resume.setText(tr('{possibles} possibles, {bientot} bientôt, '
                               '{incompletes} incomplètes',
                               possibles=len(par_etat[POSSIBLE]),
                               bientot=len(par_etat[BIENTOT]),
                               incompletes=len(par_etat[INCOMPLETE])))

        contenu = QWidget()
        disposition = QVBoxLayout(contenu)
        self._dressees = self.sauvegarde.bibliotheque.especes_dressees()
        monstres = tuple(self.sauvegarde.monstres())
        for etat, liste in par_etat.items():
            if not liste:
                continue
            entete = QLabel(f'{tr(TITRES[etat])} ({len(liste)})')
            entete.setStyleSheet('font-weight: bold; font-size: 110%; margin-top: 8px')
            disposition.addWidget(entete)
            for analyse in liste:
                disposition.addWidget(self._carte(analyse, monstres))
        if not retenues:
            disposition.addWidget(QLabel(tr(AUCUNE)))
        disposition.addStretch()
        position = self.zone.verticalScrollBar().value()
        self.zone.setWidget(contenu)
        self.zone.verticalScrollBar().setValue(position)

    # ── Une synthèse ─────────────────────────────────────────────────────────

    def _carte(self, analyse: syntheses.Analyse, disponibles: tuple) -> QWidget:
        """Une synthèse ; disponibles : monstres dont elle dispose (ceux de la
        sauvegarde, ou ce qu'il en reste plus les enfants à créer)."""
        carte = QFrame()
        carte.setFrameShape(QFrame.StyledPanel)
        colonne = QVBoxLayout(carte)
        colonne.setContentsMargins(6, 4, 6, 4)
        colonne.setSpacing(2)

        ligne = QHBoxLayout()
        ligne.setContentsMargins(0, 0, 0, 0)
        manquants = list(analyse.manquants)
        for i, parent in enumerate(analyse.recette.parents):
            if i:
                ligne.addWidget(QLabel('+'))
            absent = parent in manquants and analyse.monstres[i] is None
            if absent:
                manquants.remove(parent)
            ligne.addWidget(_espece(parent, absent=absent))
        ligne.addWidget(QLabel('→'))
        ligne.addWidget(_espece(analyse.recette.resultat, gras=True))
        if analyse.recette.patch:
            ligne.addWidget(_etiquette(tr('patch'),
                                       tr('Recette ajoutée par le patch de traduction')),
                            0, Qt.AlignVCenter)
        if analyse.recette.resultat in self._dressees:
            ligne.addWidget(_etiquette(tr('déjà dressé'),
                                       tr('Espèce déjà dressée (bibliothèque)')),
                            0, Qt.AlignVCenter)
        ligne.addStretch()
        colonne.addLayout(ligne)

        details = QLabel('<br>'.join(self._details(analyse)))
        details.setTextFormat(Qt.RichText)
        details.setWordWrap(True)
        details.linkActivated.connect(lambda lien: self.selectionner.emit(int(lien)))
        colonne.addWidget(details)
        if analyse.etat != INCOMPLETE:
            self._ajouter_suites(colonne, analyse, disponibles)
        return carte

    def _ajouter_suites(self, colonne: QVBoxLayout, analyse, disponibles) -> None:
        suites = syntheses.suites(analyse, disponibles, self.polarite.isChecked())
        if not suites:
            return
        bouton = QToolButton()
        bouton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        bouton.setArrowType(Qt.RightArrow)
        bouton.setAutoRaise(True)
        bouton.setCheckable(True)
        bouton.setText(tr('Ensuite, avec {espece} : {n} synthèse(s)',
                          espece=noms.table('especes')[analyse.recette.resultat],
                          n=len(suites)))
        bouton.setToolTip(tr(AIDE_SUITES))
        enfants = QWidget()
        disposition = QVBoxLayout(enfants)
        disposition.setContentsMargins(24, 0, 0, 0)
        enfants.hide()

        def basculer(ouvert: bool) -> None:
            if ouvert and not disposition.count():         # construit au premier dépliage
                for suite in suites:
                    disposition.addWidget(self._carte(suite.analyse, suite.disponibles))
            bouton.setArrowType(Qt.DownArrow if ouvert else Qt.RightArrow)
            enfants.setVisible(ouvert)

        bouton.toggled.connect(basculer)
        colonne.addWidget(bouton, 0, Qt.AlignLeft)
        colonne.addWidget(enfants)

    def _lien(self, monstre) -> str:
        from .fenetre import LIBELLES_ROLES
        if isinstance(monstre, syntheses.MonstreAVenir):
            return '<i>' + _html(tr('{espece} (à créer, puis niv. {niveau})',
                                    espece=_nom(monstre), niveau=syntheses.NIVEAU_MIN)) + '</i>'
        role = tr(LIBELLES_ROLES[self.sauvegarde.role(monstre)])
        texte = tr('{surnom} (niv. {niveau}, {role})', surnom=_nom(monstre),
                   niveau=monstre['niveau'], role=role)
        return f'<a href="{monstre.emplacement}">{_html(texte)}</a>'

    def _details(self, analyse: syntheses.Analyse) -> list[str]:
        especes = noms.table('especes')
        lignes = []
        retenus = list({m.emplacement: m for m in analyse.monstres if m}.values())
        if analyse.intermediaires_prets:
            lignes.append(tr('Intermédiaires : {monstres}',
                             monstres=' + '.join(map(self._lien, retenus))))
        elif retenus:
            lignes.append(tr('Avec : {monstres}',
                             monstres=' + '.join(map(self._lien, retenus))))
        for a, b in analyse.a_synthetiser:
            lignes.append(_html(tr("D'abord : synthétiser {a} + {b} (l'enfant garde cette "
                                   'lignée)', a=especes[a], b=especes[b])))
        if analyse.trop_bas:
            lignes.append(_html(tr('Niveau {niveau} requis : {monstres}',
                                   niveau=syntheses.NIVEAU_MIN,
                                   monstres=', '.join(map(_nom, analyse.trop_bas)))))
        if analyse.meme_polarite:
            lignes.append(_html(tr('Même polarité : il faut deux polarités opposées, ou '
                                   'un parent neutre.')))
        if analyse.manquants:
            lignes.append(_html(tr('Manque : {especes}', especes=', '.join(
                especes[e] for e in analyse.manquants))))
        return lignes


def _nom(monstre) -> str:
    """Surnom, ou nom de l'espèce si le surnom est vide."""
    return monstre['surnom'].strip() or noms.table('especes')[monstre['espece']]


def _html(texte: str) -> str:
    return texte.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
