"""Champs de saisie liés à une vue de la sauvegarde (joueur ou monstre).

Chaque saisie expose setValue() et le signal valueChanged, comme QSpinBox ;
Liaison s'occupe du va-et-vient entre les saisies et la vue."""
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import (QComboBox, QCompleter, QHBoxLayout, QLineEdit,
                               QSpinBox, QWidget)

from dqmj2p_save import format as F
from dqmj2p_save import noms, texte

from . import icones

QSPINBOX_MAX = 2**31 - 1


class ChoixNom(QComboBox):
    """Liste déroulante « ID — nom », avec recherche par morceau de nom."""
    valueChanged = Signal(int)

    def __init__(self, table: noms.TableNoms, avec_icones: bool = False):
        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setMaxVisibleItems(20)
        if avec_icones:
            self.setIconSize(icones.TAILLE_CASE / 2)
        aide = noms.aide_objet if table is noms.table('objets') else None
        for id_, nom in table.choix():
            self.addItem(f'{id_} — {nom}', id_)
            if aide:
                self.setItemData(self.count() - 1, aide(id_), Qt.ToolTipRole)
            if avec_icones:
                self.setItemIcon(self.count() - 1, icones.icone(id_))
        self.completer().setFilterMode(Qt.MatchContains)
        self.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.currentIndexChanged.connect(
            lambda i: self.valueChanged.emit(self.itemData(i)))
        self.currentIndexChanged.connect(self._majInfobulle)

    def setValue(self, valeur: int) -> None:
        index = self.findData(valeur)
        if index < 0:               # ID hors de la table : on le garde visible
            self.addItem(f'{valeur} — #{valeur}', valeur)
            index = self.count() - 1
        self.setCurrentIndex(index)

    def _majInfobulle(self) -> None:
        self.setToolTip(self.itemData(self.currentIndex(), Qt.ToolTipRole) or '')

    def focusOutEvent(self, evenement) -> None:
        # Texte tapé sans correspondance : on réaffiche la valeur en cours.
        super().focusOutEvent(evenement)
        self.setEditText(self.itemText(self.currentIndex()))


class _ValidateurTexte(QValidator):
    def validate(self, saisie, position):
        if texte.caracteres_invalides(saisie):
            return QValidator.Invalid, saisie, position
        return QValidator.Acceptable, saisie, position


class ChampTexte(QLineEdit):
    """Nom ou surnom : 8 caractères, seulement ceux de la police du jeu."""
    valueChanged = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMaxLength(texte.LONGUEUR_MAX)
        self.setValidator(_ValidateurTexte(self))
        self.textEdited.connect(self.valueChanged.emit)

    def setValue(self, valeur: str) -> None:
        self.setText(valeur)


class TempsJeu(QWidget):
    """Temps de jeu en heures / minutes / secondes. La fraction de seconde
    d'origine est conservée."""
    valueChanged = Signal(int)

    def __init__(self):
        super().__init__()
        self._images = 0
        disposition = QHBoxLayout(self)
        disposition.setContentsMargins(0, 0, 0, 0)
        maximum_heures = QSPINBOX_MAX // (3600 * F.IMAGES_PAR_SECONDE)
        self.unites = []
        for suffixe, maximum in ((' h', maximum_heures), (' min', 59), (' s', 59)):
            saisie = QSpinBox(suffix=suffixe, maximum=maximum)
            saisie.valueChanged.connect(self._changement)
            disposition.addWidget(saisie)
            self.unites.append(saisie)
        disposition.addStretch()

    def setValue(self, images: int) -> None:
        self._images = images
        secondes = images // F.IMAGES_PAR_SECONDE
        for saisie, valeur in zip(self.unites, (secondes // 3600, secondes // 60 % 60,
                                                secondes % 60)):
            saisie.blockSignals(True)
            saisie.setValue(valeur)
            saisie.blockSignals(False)

    def _changement(self) -> None:
        h, m, s = (u.value() for u in self.unites)
        fraction = self._images % F.IMAGES_PAR_SECONDE
        self._images = (h * 3600 + m * 60 + s) * F.IMAGES_PAR_SECONDE + fraction
        self.valueChanged.emit(self._images)


def creer_saisie(champ: F.Champ) -> QWidget:
    if champ.noms:
        return ChoixNom(noms.table(champ.noms), avec_icones=champ.noms == 'especes')
    if champ.type == 'texte':
        return ChampTexte()
    if champ.cle == 'temps_jeu':
        return TempsJeu()
    saisie = QSpinBox()
    saisie.setRange(max(champ.minimum, -QSPINBOX_MAX), min(champ.maximum, QSPINBOX_MAX))
    saisie.setGroupSeparatorShown(champ.maximum > 0xFFFF)
    saisie.setReadOnly(champ.lecture_seule)
    if champ.lecture_seule:
        saisie.setButtonSymbols(QSpinBox.NoButtons)
    return saisie


class Liaison(QObject):
    """Relie des saisies aux champs d'une vue : afficher() remplit les
    saisies, et toute saisie modifiée est aussitôt écrite dans la vue."""
    modifiee = Signal()
    erreur = Signal(str)

    def __init__(self, champs: dict[str, F.Champ]):
        super().__init__()
        self.champs = champs
        self.vue = None
        self.saisies: dict[str, QWidget] = {}

    def saisie(self, cle: str) -> QWidget:
        champ = self.champs[cle]
        widget = creer_saisie(champ)
        widget.setToolTip(f'+0x{champ.offset:02X}, {champ.type}')
        if not champ.lecture_seule:
            widget.valueChanged.connect(lambda v, cle=cle: self._ecrire(cle, v))
        self.saisies[cle] = widget
        return widget

    def afficher(self, vue) -> None:
        self.vue = None             # coupe l'écriture pendant le remplissage
        for cle, widget in self.saisies.items():
            widget.setValue(vue[cle])
        self.vue = vue

    def _ecrire(self, cle: str, valeur) -> None:
        if self.vue is None or self.vue[cle] == valeur:
            return
        try:
            self.vue[cle] = valeur
        except ValueError as e:
            self.erreur.emit(str(e))
            return
        self.modifiee.emit()
