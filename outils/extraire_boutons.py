#!/usr/bin/env python3
"""Extrait les icônes des boutons du menu (menu_icon_data.cch et .cpl).

    python outils/extraire_boutons.py <rom.nds> [dossier de sortie]

Même extraction que le menu Fichier de l'éditeur ; le format est décrit dans
editeur/extraction.py. Nécessite PySide6 (pour écrire les PNG).
"""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
from editeur.extraction import ErreurExtraction, extraire_boutons  # noqa: E402

CIBLE = RACINE / 'editeur' / 'icones' / 'boutons'


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    cible = Path(sys.argv[2]) if len(sys.argv) == 3 else CIBLE
    try:
        nombre = extraire_boutons(Path(sys.argv[1]).read_bytes(), cible)
    except ErreurExtraction as e:
        raise SystemExit(f'ERREUR : {e}')
    print(f'{nombre} icônes de boutons écrites dans {cible}')


if __name__ == '__main__':
    main()
