#!/usr/bin/env python3
"""Prépare le zip de la release Windows, après outils/construire_exe.py.

    python outils/preparer_zip.py <version>     # ex. v1.0.1 -> Editeur-DQMJ2P-v1.0.1-windows.zip

Contenu : l'exe, les README, la licence, un dossier icones/ vide (où l'exe
cherche les icônes), et de quoi extraire les icônes sans l'éditeur :
EXTRAIRE-ICONES.txt (instructions FR/EN) et scripts/, où les scripts
d'extraction trouvent leurs modules (editeur/extraction.py et dqmj2p_save/)
comme dans le dépôt. Affiche le nom du zip. Utilisé par
.github/workflows/release.yml.
"""
import shutil
import sys
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
EXE = next((RACINE / 'dist').glob('Editeur-DQMJ2P*'), None)
FICHIERS = {                        # source -> chemin dans le dossier du zip
    'README.md': 'README.md',
    'README_en.md': 'README_en.md',
    'LICENSE': 'LICENSE',
    'outils/EXTRAIRE-ICONES.txt': 'EXTRAIRE-ICONES.txt',
    'editeur/icones/SOURCE.txt': 'icones/SOURCE.txt',
    'outils/extraire_icones.py': 'scripts/outils/extraire_icones.py',
    'outils/extraire_familles.py': 'scripts/outils/extraire_familles.py',
    'editeur/__init__.py': 'scripts/editeur/__init__.py',
    'editeur/extraction.py': 'scripts/editeur/extraction.py',
}
PAQUETS = {'dqmj2p_save': 'scripts/dqmj2p_save'}     # copiés en entier


def preparer(version: str, sortie: Path) -> Path:
    if EXE is None:
        raise SystemExit("pas d'exe dans dist/ : lancer d'abord outils/construire_exe.py")
    dossier = sortie / f'Editeur-DQMJ2P-{version}'
    if dossier.exists():
        shutil.rmtree(dossier)
    for source, cible in {**FICHIERS, EXE.relative_to(RACINE).as_posix(): EXE.name}.items():
        (dossier / cible).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(RACINE / source, dossier / cible)
    for source, cible in PAQUETS.items():
        shutil.copytree(RACINE / source, dossier / cible,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    archive = sortie / f'{dossier.name}-windows.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zip_:
        for chemin in sorted(dossier.rglob('*')):
            zip_.write(chemin, chemin.relative_to(sortie))
    return archive


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    sortie = Path(sys.argv[2]) if len(sys.argv) == 3 else RACINE
    print(preparer(sys.argv[1], sortie).name)


if __name__ == '__main__':
    main()
