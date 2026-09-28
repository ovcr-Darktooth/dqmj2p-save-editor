#!/usr/bin/env python3
"""Construit l'éditeur en un seul exécutable (PyInstaller).

    pip install pyinstaller PySide6
    python outils/construire_exe.py

Résultat : dist/Editeur-DQMJ2P.exe sous Windows (dist/Editeur-DQMJ2P
ailleurs). Les tables de noms et le bestiaire sont embarqués ; les icônes,
graphismes du jeu, ne le sont pas : l'exe les cherche dans un dossier icones/
posé à côté de lui (voir editeur/icones.py). Utilisé tel quel par
.github/workflows/release.yml, et par outils/construire_appimage.py.
"""
import os
import sys
from pathlib import Path

import PyInstaller.__main__

RACINE = Path(__file__).resolve().parents[1]
NOM = 'Editeur-DQMJ2P'
DONNEES = ('dqmj2p_save/noms', 'dqmj2p_save/donnees')


def construire(*options: str) -> None:
    """Lance PyInstaller avec les options communes, plus celles données."""
    os.chdir(RACINE)
    PyInstaller.__main__.run([
        str(RACINE / 'outils' / 'lanceur.py'),
        '--name', NOM,
        '--windowed',               # pas de console derrière la fenêtre
        '--noconfirm',
        '--clean',
        '--paths', str(RACINE),
        *(option for dossier in DONNEES
          for option in ('--add-data', f'{RACINE / dossier}{os.pathsep}{dossier}')),
        *options,
    ])


def main() -> None:
    construire('--onefile', *sys.argv[1:])     # + options de PyInstaller


if __name__ == '__main__':
    main()
