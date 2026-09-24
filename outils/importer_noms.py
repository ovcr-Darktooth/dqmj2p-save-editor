#!/usr/bin/env python3
"""Recopie les tables de noms depuis un dépôt de traduction.

    python outils/importer_noms.py <chemin vers DQMJ2Pro_Translation_FR>
    python outils/importer_noms.py <chemin vers DQMJ2Pro_Translation> en

La langue (fr par défaut) choisit le dossier noms/<langue>/ écrit. Les deux
patchs ont les mêmes fichiers (Translation/STRINGS), alignés ligne à ligne.
À relancer après chaque correction de nom dans la traduction. La ligne N de
chaque fichier est le nom de l'ID N (ligne 0 : aucun).
"""
import subprocess
import sys
from pathlib import Path

TABLES = {                          # fichier de la traduction -> table ici
    'msg_monstername.txt': 'especes.txt',
    'msg_skillname.txt': 'competences.txt',
    'msg_itemname.txt': 'objets.txt',
    'msg_itemhelp.txt': 'objets_aide.txt',
    'msg_tokusei.txt': 'attributs.txt',
}
# Descriptions des attributs : msg_library les range à partir de sa ligne 16
# (attribut 1 à la ligne 17), après les textes propres à la bibliothèque.
DESCRIPTIONS_ATTRIBUTS = ('msg_library.txt', 16, 'attributs_aide.txt')
# Manuel du dresseur : msg_traveler donne les titres des entrées (lignes 0 à
# 47, ligne 0 : aucune), puis leurs textes, dans le même ordre, à partir de la
# ligne 51.
MANUEL = ('msg_traveler.txt', 48, 51, 'manuel.txt', 'manuel_aide.txt')
DEPOTS = {                          # langue -> dépôt de la traduction
    'fr': 'https://github.com/ovcr-Darktooth/DQMJ2Pro_Translation_FR',
    'en': 'https://github.com/saneezore07/DQMJ2Pro_Translation',
}
NOMS = Path(__file__).resolve().parents[1] / 'dqmj2p_save' / 'noms'


def main() -> None:
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] not in DEPOTS):
        raise SystemExit(__doc__)
    depot = Path(sys.argv[1])
    langue = sys.argv[2] if len(sys.argv) == 3 else 'fr'
    source = depot / 'Translation' / 'STRINGS'
    cible = NOMS / langue
    cible.mkdir(parents=True, exist_ok=True)
    for nom_source, nom_cible in TABLES.items():
        lignes = (source / nom_source).read_text(encoding='utf-8').splitlines()
        (cible / nom_cible).write_text('\n'.join(lignes) + '\n', encoding='utf-8')
        print(f'{nom_cible} : {len(lignes)} noms')
    nom_source, decalage, nom_cible = DESCRIPTIONS_ATTRIBUTS
    lignes = (source / nom_source).read_text(encoding='utf-8').splitlines()[decalage:]
    (cible / nom_cible).write_text('\n'.join(lignes) + '\n', encoding='utf-8')
    print(f'{nom_cible} : {len(lignes)} descriptions')
    importer_manuel(source, cible)
    commit = subprocess.run(['git', '-C', str(depot), 'rev-parse', '--short', 'HEAD'],
                            capture_output=True, text=True).stdout.strip()
    (cible / 'SOURCE.txt').write_text(
        f'Noms issus de {DEPOTS[langue]}\n'
        f'(Translation/STRINGS), commit {commit or "inconnu"}.\n', encoding='utf-8')


def importer_manuel(source: Path, cible: Path) -> None:
    nom_source, nb_titres, debut_textes, titres, textes = MANUEL
    lignes = (source / nom_source).read_text(encoding='utf-8').splitlines()
    for nom_cible, extrait in ((titres, lignes[:nb_titres]),
                               (textes, lignes[debut_textes: debut_textes + nb_titres])):
        (cible / nom_cible).write_text('\n'.join(extrait) + '\n', encoding='utf-8')
        print(f'{nom_cible} : {len(extrait)} lignes')


if __name__ == '__main__':
    main()
