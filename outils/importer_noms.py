#!/usr/bin/env python3
"""Recopie les tables de noms depuis le dépôt de traduction FR.

    python outils/importer_noms.py <chemin vers DQMJ2Pro_Translation_FR>

À relancer après chaque correction de nom dans la traduction. La ligne N de
chaque fichier est le nom de l'ID N (ligne 0 : aucun).
"""
import subprocess
import sys
from pathlib import Path

TABLES = {                          # fichier de la traduction -> table ici
    'msg_monstername.txt': 'especes.txt',
    'msg_skillname.txt': 'competences.txt',
}
CIBLE = Path(__file__).resolve().parents[1] / 'dqmj2p_save' / 'noms' / 'fr'


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    depot = Path(sys.argv[1])
    source = depot / 'Translation' / 'STRINGS'
    CIBLE.mkdir(parents=True, exist_ok=True)
    for nom_source, nom_cible in TABLES.items():
        lignes = (source / nom_source).read_text(encoding='utf-8').splitlines()
        (CIBLE / nom_cible).write_text('\n'.join(lignes) + '\n', encoding='utf-8')
        print(f'{nom_cible} : {len(lignes)} noms')
    commit = subprocess.run(['git', '-C', str(depot), 'rev-parse', '--short', 'HEAD'],
                            capture_output=True, text=True).stdout.strip()
    (CIBLE / 'SOURCE.txt').write_text(
        'Noms issus de https://github.com/ovcr-Darktooth/DQMJ2Pro_Translation_FR\n'
        f'(Translation/STRINGS), commit {commit or "inconnu"}.\n', encoding='utf-8')


if __name__ == '__main__':
    main()
