#!/usr/bin/env python3
"""Recopie les icônes de monstres depuis le projet des synthèses.

    python outils/importer_icones.py <chemin vers dqmj2pro-synthese>

Les icônes y sont extraites de la ROM (MonsterIconDat.NICA) par
tools/extract_icons.py, une par ID interne : site/icons/<id>.png, en 40x40,
40x80 ou 40x120 selon la taille du monstre.
"""
import shutil
import subprocess
import sys
from pathlib import Path

CIBLE = Path(__file__).resolve().parents[1] / 'editeur' / 'icones'


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    depot = Path(sys.argv[1])
    source = depot / 'site' / 'icons'
    icones = sorted(source.glob('*.png'), key=lambda p: int(p.stem))
    if not icones:
        raise SystemExit(f'aucune icône dans {source}')
    CIBLE.mkdir(parents=True, exist_ok=True)
    for icone in icones:
        shutil.copy2(icone, CIBLE / icone.name)
    commit = subprocess.run(['git', '-C', str(depot), 'rev-parse', '--short', 'HEAD'],
                            capture_output=True, text=True).stdout.strip()
    (CIBLE / 'SOURCE.txt').write_text(
        'Icônes extraites de la ROM (MonsterIconDat.NICA) par tools/extract_icons.py\n'
        'de https://github.com/ovcr-Darktooth/dqmj2pro-synthesis, '
        f'commit {commit or "inconnu"}.\n', encoding='utf-8')
    print(f'{len(icones)} icônes copiées dans {CIBLE}')


if __name__ == '__main__':
    main()
