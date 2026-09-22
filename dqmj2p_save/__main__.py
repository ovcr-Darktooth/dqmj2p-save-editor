"""Inspection rapide en ligne de commande : python -m dqmj2p_save <fichier>"""
import sys

from .format import IMAGES_PAR_SECONDE
from .noms import table
from .sauvegarde import ErreurSauvegarde, Sauvegarde


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    try:
        sauvegarde = Sauvegarde.ouvrir(sys.argv[1])
    except ErreurSauvegarde as e:
        raise SystemExit(f'ERREUR : {e}')

    j = sauvegarde.joueur
    secondes = j['temps_jeu'] // IMAGES_PAR_SECONDE
    print(f'{sauvegarde.chemin.name} : copie {sauvegarde.index_copie + 1} active')
    print(f'  {j["nom"]}, {secondes // 3600} h {secondes // 60 % 60:02} min '
          f'{secondes % 60:02} s, {j["or"]} or (+ {j["banque"]} en banque), '
          f'{j["victoires"]} victoires, {j["dressages"]} dressages, '
          f'{j["syntheses"]} synthèses')
    monstres = sauvegarde.monstres()
    print(f'  {len(monstres)} monstres')
    for m in monstres:
        print(f'  [{m.emplacement:2}] {sauvegarde.role(m):9}  '
              f'{table("especes")[m["espece"]]:22} {m["surnom"]:8}  '
              f'niv. {m["niveau"]:2}  PV {m["pv_max"]:4}  PM {m["pm_max"]:4}  '
              f'ATQ {m["attaque"]:4}  DEF {m["defense"]:4}  '
              f'AGI {m["agilite"]:4}  SAG {m["sagesse"]:4}')


if __name__ == '__main__':
    main()
