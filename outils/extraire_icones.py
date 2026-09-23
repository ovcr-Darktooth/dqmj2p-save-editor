#!/usr/bin/env python3
"""Extrait les icônes des monstres d'une ROM de DQMJ2 Professional.

    python outils/extraire_icones.py <rom.nds> [dossier de sortie]

Alternative à importer_synthese.py, sans passer par le projet des synthèses.
Même extraction que le menu Fichier de l'éditeur ; le format est décrit dans
editeur/extraction.py. Nécessite PySide6 (pour écrire les PNG).
"""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
from editeur.extraction import ErreurExtraction, extraire_icones  # noqa: E402

CIBLE = RACINE / 'editeur' / 'icones'


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    cible = Path(sys.argv[2]) if len(sys.argv) == 3 else CIBLE
    try:
        nombre = extraire_icones(Path(sys.argv[1]).read_bytes(), cible)
    except ErreurExtraction as e:
        raise SystemExit(f'ERREUR : {e}')
    print(f'{nombre} icônes écrites dans {cible}')


if __name__ == '__main__':
    main()
