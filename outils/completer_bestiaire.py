#!/usr/bin/env python3
"""Complète les familles et rangs absents de bestiaire.json.

    python outils/completer_bestiaire.py <chemin vers DQMJ2Pro_Translation_FR>

bestiaire.json (projet des synthèses) n'a pas de fiche pour une soixantaine
d'espèces. On les retrouve par leur nom dans Database_FR/monster_database.csv
de la traduction, et on écrit donnees/complement_bestiaire.json, lu en second
par bestiaire.py : il ne remplace jamais une valeur de bestiaire.json. La
taille n'est pas reprise, elle décide du placement dans l'équipe.
"""
import csv
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
from dqmj2p_save import bestiaire, noms  # noqa: E402
from dqmj2p_save import format as F  # noqa: E402

COMPLEMENT = RACINE / 'dqmj2p_save' / 'donnees' / 'complement_bestiaire.json'
FAMILLES = {'Matériel': 'Matière', 'Mort-vivant': 'Zombie'}   # noms de la base -> ceux d'ici
# Relevés en jeu, pour les espèces absentes de la base.
MANUEL = {
    133: {'famille': 'Nature'},     # Volapistil
    295: {'famille': 'Zombie'},     # Boumbone
    353: {'famille': 'Gluant'},     # Gluanuyeux (dressé, il donne un Gluant de métal)
    451: {'famille': 'Bête'},       # Anaqueuda : la queue de l'Ailéopard, même famille
}


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    base = Path(sys.argv[1]) / 'Database_FR' / 'monster_database.csv'
    lignes = [r for r in csv.reader(base.open(encoding='utf-8'))
              if r and r[0] not in ('Rank', 'Rang')]
    par_nom = {r[2].casefold(): r for r in lignes}
    especes = noms.table('especes')
    # bestiaire.json seul : bestiaire.fiche() inclut déjà l'ancien complément.
    origine = json.loads(bestiaire.FICHIER.read_text(encoding='utf-8'))['monstres']

    complement, introuvables = {}, []
    for id_ in range(1, F.NB_BITS_ESPECES):     # au-delà : variantes X et XY
        fiche = origine.get(str(id_), {})
        if especes[id_] == noms.INUTILISE or (fiche.get('famille') and fiche.get('rang')):
            continue
        ligne = par_nom.get(especes[id_].casefold())
        valeurs = {'rang': ligne[0], 'famille': FAMILLES.get(ligne[4], ligne[4])} if ligne else {}
        valeurs |= MANUEL.get(id_, {})
        manquantes = {cle: v for cle, v in valeurs.items() if fiche.get(cle) is None}
        if manquantes:
            complement[str(id_)] = manquantes
        if not (fiche.get('famille') or valeurs.get('famille')):
            introuvables.append(f'{id_} {especes[id_]}')

    COMPLEMENT.write_text(json.dumps(complement, ensure_ascii=False, indent=1) + '\n',
                          encoding='utf-8')
    print(f'{len(complement)} espèces complétées ; sans famille : {", ".join(introuvables)}')


if __name__ == '__main__':
    main()
