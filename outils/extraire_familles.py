#!/usr/bin/env python3
"""Extrait les icônes de familles de la police du jeu (font_16x16.NFTR).

    python outils/extraire_familles.py <rom.nds> [dossier de sortie]

Même extraction que le menu Fichier de l'éditeur ; le format est décrit dans
editeur/extraction.py. Nécessite PySide6 (pour écrire les PNG).
"""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
from editeur.extraction import ErreurExtraction, extraire_familles  # noqa: E402

CIBLE = RACINE / 'editeur' / 'icones' / 'familles'


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    cible = Path(sys.argv[2]) if len(sys.argv) == 3 else CIBLE
    try:
        nombre = extraire_familles(Path(sys.argv[1]).read_bytes(), cible)
    except ErreurExtraction as e:
        raise SystemExit(f'ERREUR : {e}')
    print(f'{nombre} icônes de familles écrites dans {cible}')


if __name__ == '__main__':
    main()
