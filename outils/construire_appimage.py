#!/usr/bin/env python3
"""Construit l'AppImage Linux de l'éditeur (PyInstaller, puis appimagetool).

    pip install pyinstaller PySide6
    python outils/construire_appimage.py <version> [appimagetool]
        # ex. v1.0.4 -> dist/Editeur-DQMJ2P-v1.0.4-x86_64.AppImage

appimagetool (https://github.com/AppImage/appimagetool) est cherché dans le
PATH si son chemin n'est pas donné. L'éditeur est construit en dossier
(--onedir) plutôt qu'en un fichier : l'AppImage le compresse déjà. Il cherche
les icônes dans un dossier icones/ à côté du fichier .AppImage (voir
editeur/icones.py). Affiche le nom de l'AppImage. Utilisé par
.github/workflows/release.yml.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from construire_exe import NOM, RACINE, construire

MODELES = RACINE / 'outils' / 'appimage'    # .desktop et icône de l'application
ID = 'editeur-dqmj2p'                       # nom du .desktop et de l'icône
APPRUN = f"""#!/bin/sh
ICI="$(dirname "$(readlink -f "$0")")"
exec "$ICI/usr/bin/{NOM}/{NOM}" "$@"
"""


def preparer_appdir(appdir: Path) -> None:
    """AppDir : l'éditeur dans usr/bin/, AppRun, .desktop et icône à la racine."""
    if appdir.exists():
        shutil.rmtree(appdir)
    shutil.copytree(RACINE / 'dist' / NOM, appdir / 'usr' / 'bin' / NOM, symlinks=True)
    apprun = appdir / 'AppRun'
    apprun.write_text(APPRUN, encoding='utf-8', newline='\n')
    apprun.chmod(0o755)
    for fichier in (f'{ID}.desktop', f'{ID}.svg'):
        shutil.copy2(MODELES / fichier, appdir / fichier)


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    version = sys.argv[1]
    outil = sys.argv[2] if len(sys.argv) == 3 else shutil.which('appimagetool')
    if not outil:
        raise SystemExit("appimagetool introuvable : donner son chemin en 2e argument")
    construire('--onedir')
    appdir = RACINE / 'build' / 'AppDir'
    preparer_appdir(appdir)
    sortie = RACINE / 'dist' / f'{NOM}-{version}-x86_64.AppImage'
    subprocess.run([outil, '--no-appstream', str(appdir), str(sortie)], check=True,
                   env={**os.environ, 'ARCH': 'x86_64'})
    print(sortie.name)


if __name__ == '__main__':
    main()
