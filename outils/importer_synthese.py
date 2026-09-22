#!/usr/bin/env python3
"""Recopie icônes et données de synthèse depuis le projet des synthèses.

    python outils/importer_synthese.py <chemin vers dqmj2pro-synthese>

- site/icons/<id>.png -> editeur/icones/ : icônes extraites de la ROM
  (MonsterIconDat.NICA) par tools/extract_icons.py, en 40x40, 40x80 ou 40x120
  selon la taille du monstre ;
- site/data.js -> dqmj2p_save/donnees/bestiaire.json : rang, famille et taille
  de chaque monstre, et les synthèses spéciales (2 ou 4 parents ; « patch » pour
  celles ajoutées par le patch). Les ID sont les ID internes des espèces.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
ICONES = RACINE / 'editeur' / 'icones'
BESTIAIRE = RACINE / 'dqmj2p_save' / 'donnees' / 'bestiaire.json'
FAMILLES = {'Slime': 'Gluant', 'Dragon': 'Dragon', 'Nature': 'Nature', 'Beast': 'Bête',
            'Material': 'Matière', 'Demon': 'Démon', 'Zombie': 'Zombie', '???': '???'}


def importer_icones(depot: Path) -> int:
    icones = sorted((depot / 'site' / 'icons').glob('*.png'), key=lambda p: int(p.stem))
    if not icones:
        raise SystemExit(f'aucune icône dans {depot / "site" / "icons"}')
    ICONES.mkdir(parents=True, exist_ok=True)
    for icone in icones:
        shutil.copy2(icone, ICONES / icone.name)
    return len(icones)


def importer_bestiaire(depot: Path) -> tuple[int, int]:
    texte = (depot / 'site' / 'data.js').read_text(encoding='utf-8')
    donnees = json.loads(texte[texte.index('{'): texte.rindex('}') + 1])
    monstres = {
        str(m['id']): {'rang': m.get('rank'), 'famille': FAMILLES.get(m.get('family')),
                       'taille': m.get('size')}
        for m in donnees['monsters']}
    recettes = [{'resultat': r['r'], 'parents': r['p'], 'patch': r['patch']}
                for r in donnees['recipes']]
    BESTIAIRE.parent.mkdir(parents=True, exist_ok=True)
    BESTIAIRE.write_text(json.dumps({'monstres': monstres, 'recettes': recettes},
                                    ensure_ascii=False, indent=0), encoding='utf-8')
    return len(monstres), len(recettes)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    depot = Path(sys.argv[1])
    n_icones = importer_icones(depot)
    n_monstres, n_recettes = importer_bestiaire(depot)
    commit = subprocess.run(['git', '-C', str(depot), 'rev-parse', '--short', 'HEAD'],
                            capture_output=True, text=True).stdout.strip()
    source = ('Issu de https://github.com/ovcr-Darktooth/dqmj2pro-synthesis, '
              f'commit {commit or "inconnu"}.\n')
    (ICONES / 'SOURCE.txt').write_text(
        'Icônes extraites de la ROM (MonsterIconDat.NICA) par tools/extract_icons.py.\n'
        + source, encoding='utf-8')
    (BESTIAIRE.parent / 'SOURCE.txt').write_text(
        'bestiaire.json : rang, famille, taille et synthèses spéciales, repris de\n'
        'site/data.js (lui-même construit depuis les bases de DQMJ2Pro_Translation_FR).\n'
        + source, encoding='utf-8')
    print(f'{n_icones} icônes, {n_monstres} monstres, {n_recettes} recettes importés')


if __name__ == '__main__':
    main()
