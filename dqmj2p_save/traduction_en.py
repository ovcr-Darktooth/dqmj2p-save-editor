"""Catalogue anglais : texte français du code -> texte anglais (voir langue.py).

Les termes du jeu reprennent ceux du patch anglais (Party, Standby, Storage,
Traits, Scouted…), pour que l'éditeur parle comme le jeu. Les {champs} doivent
être les mêmes des deux côtés (vérifié par tests/test_langue.py).
"""

TEXTES = {
    # ── Noms du jeu absents des tables de noms ───────────────────────────────
    '(aucun)': '(none)',
    '(inutilisé)': '(unused)',
    # Familles (noms de bestiaire.json)
    'Gluant': 'Slime',
    'Dragon': 'Dragon',
    'Nature': 'Nature',
    'Bête': 'Beast',
    'Matière': 'Material',
    'Démon': 'Demon',
    'Zombie': 'Zombie',
    '???': '???',
    'Famille inconnue': 'Unknown family',
    # Lieux (noms.CARTES et format.POINTS_TELEPORTATION) : noms de msg_map du
    # patch anglais, rapprochés des noms français par leur ordre dans msg_map.
    "L'Arbirynthe": 'Treepidation',
    'Prairia': 'Doubtback',
    'Arène': 'Arena',
    'Avablanche': 'Iceolation',
    'Nécropolis': 'Necropolis',
    'Ténébria': 'Dark World',
    'Ténébria (autre zone)': 'Dark World (other area)',
    'Île des Pipits': 'Pipisle',
    'Palais Blanc': 'Blanc Palace',
    'Avablanche (autre zone)': 'Iceolation (other area)',
    'Avablanche (fin de zone)': 'Iceolation (end of area)',
    'Avablanche (fin de zone, sort)': 'Iceolation (end of area, exit)',
    'Escarpic': 'Cragravation',
    'Engloutîle': 'Unshore',
    'Archéopolis': 'Bemusoleum',
    'Albatros (extérieur)': 'Albatross (outside)',
    'Albatros (intérieur, ranch)': 'Albatross (inside, storage)',
    'Albatros (tablette du ranch)': 'Albatross (storage tablet)',
    'Albatros (sortie)': 'Albatross (exit)',
    'lieu inconnu': 'unknown place',
    'pluie': 'rain',
    'brume': 'fog',
    # Jours de la semaine
    'dimanche': 'Sunday',
    'lundi': 'Monday',
    'mardi': 'Tuesday',
    'mercredi': 'Wednesday',
    'jeudi': 'Thursday',
    'vendredi': 'Friday',
    'samedi': 'Saturday',

    # ── Champs de la sauvegarde (format.py) ──────────────────────────────────
    'Surnom': 'Nickname',
    'ID de création': 'Creation ID',
    'Espèce': 'Species',
    'Variante (0 normal, 1 X, 2 XY)': 'Variant (0 normal, 1 X, 2 XY)',
    'Polarité': 'Polarity',
    'Synthèse +': 'Synthesis +',
    'Synthèse + (base)': 'Synthesis + (base)',
    'PV': 'HP',
    'PM': 'MP',
    'PV max': 'Max HP',
    'PM max': 'Max MP',
    'Attaque': 'Attack',
    'Défense': 'Defence',
    'Agilité': 'Agility',
    'Sagesse': 'Wisdom',
    'Niveau': 'Level',
    'Arme équipée': 'Equipped weapon',
    'Tactique': 'Tactics',
    'Expérience': 'Experience',
    'Expérience du niveau suivant': 'Experience for next level',
    'Points de compétence non attribués': 'Unallocated skill points',
    'Parent 1': 'Parent 1',
    'Parent 2': 'Parent 2',
    'Grand-parent 1a': 'Grandparent 1a',
    'Grand-parent 2a': 'Grandparent 2a',
    'Grand-parent 1b': 'Grandparent 1b',
    'Grand-parent 2b': 'Grandparent 2b',
    'Parent 1 : variante': 'Parent 1: variant',
    'Parent 2 : variante': 'Parent 2: variant',
    'Grand-parent 1a : variante': 'Grandparent 1a: variant',
    'Grand-parent 2a : variante': 'Grandparent 2a: variant',
    'Grand-parent 1b : variante': 'Grandparent 1b: variant',
    'Grand-parent 2b : variante': 'Grandparent 2b: variant',
    'Parent 1 : surnom': 'Parent 1: nickname',
    'Parent 2 : surnom': 'Parent 2: nickname',
    'Année (depuis 2000)': 'Year (since 2000)',
    'Mois': 'Month',
    'Jour': 'Day',
    'Jour de la semaine (0 = dimanche)': 'Day of the week (0 = Sunday)',
    'Heure': 'Hour',
    'Minute': 'Minute',
    'Seconde': 'Second',
    'Temps de jeu': 'Play time',
    'Nom': 'Name',
    'Dernier ID de création attribué': 'Last creation ID assigned',
    'Or sur soi': 'Gold on hand',
    'Or en banque': 'Gold in bank',
    'Victoires': 'Victories',
    'Monstres dressés': 'Monsters scouted',
    'Monstres synthétisés': 'Monsters synthesised',
    'Location': 'Location',
    'Location précédente (?)': 'Previous location (?)',
    'Position X (centièmes)': 'Position X (hundredths)',
    'Position Y (centièmes)': 'Position Y (hundredths)',
    'Position Z (centièmes)': 'Position Z (hundredths)',
    'Horloge jour/nuit (1/30 s)': 'Day/night clock (1/30 s)',
    'Intempérie en cours': 'Weather in progress',
    **{f'Compétence {j}': f'Skill {j}' for j in range(1, 6)},
    **{f'Compétence {j} : points investis': f'Skill {j}: points invested'
       for j in range(1, 6)},

    # ── Erreurs du cœur ──────────────────────────────────────────────────────
    '{taille} octets : ni un .sav brut ({attendu} octets) ni un .dsv (pied de page '
    '{marqueur}).': '{taille} bytes: neither a raw .sav ({attendu} bytes) nor a .dsv '
                    '({marqueur} footer).',
    "Aucune des deux copies n'est valide (en-tête SIZ ou sommes de contrôle "
    "incorrects) : ce n'est pas une sauvegarde DQMJ2P, ou elle est vide ou corrompue.":
        'Neither of the two copies is valid (bad SIZ header or checksums): this is not '
        'a DQMJ2P save, or it is empty or corrupted.',
    'ranch plein ({n} monstres)': 'storage full ({n} monsters)',
    'emplacement {n} déjà vide': 'slot {n} already empty',
    "c'est le dernier monstre de l'équipe : placez-en un autre dans l'équipe avant de "
    'le supprimer': 'this is the last monster in the party: put another one in the '
                    'party before deleting it',
    "l'équipe doit compter au moins un monstre": 'the party needs at least one monster',
    'un monstre ne peut occuper deux cases': 'a monster cannot fill two slots',
    'équipe': 'party',
    'réserve': 'standby',
    '{colonne} : {places} places occupées pour {total} disponibles':
        '{colonne}: {places} spaces used out of {total}',
    '{champ} : {erreur}': '{champ}: {erreur}',
    '{champ} : {valeur} hors de {minimum}..{maximum}':
        '{champ}: {valeur} outside {minimum}..{maximum}',
    '{n} caractères au plus': '{n} characters at most',
    'caractères absents de la police du jeu : {caracteres}':
        "characters missing from the game's font: {caracteres}",
    'trop long une fois codé ({n} octets)': 'too long once encoded ({n} bytes)',

    # ── Fenêtre principale ───────────────────────────────────────────────────
    'Éditeur de sauvegardes DQMJ2P': 'DQMJ2P Save Editor',
    'Sauvegardes DS (*.dsv *.sav);;Tous les fichiers (*)':
        'DS saves (*.dsv *.sav);;All files (*)',
    'Équipe 1': 'Party 1',
    'Équipe 2': 'Party 2',
    'Équipe 3': 'Party 3',
    'Réserve 1': 'Standby 1',
    'Réserve 2': 'Standby 2',
    'Réserve 3': 'Standby 3',
    'Ranch': 'Storage',
    'Empl.': 'Slot',
    'Rôle': 'Role',
    'Fam.': 'Fam.',
    'Joueur': 'Player',
    'Monstres': 'Monsters',
    'Sac': 'Bag',
    'Bibliothèque': 'Library',
    '&Fichier': '&File',
    '&Ouvrir…': '&Open…',
    'Fichiers &récents': '&Recent files',
    '&Vider la liste': '&Clear list',
    '&Enregistrer': '&Save',
    'Enregistrer &sous…': 'Save &as…',
    '&Quitter': '&Quit',
    '&Monstres': '&Monsters',
    '&Dupliquer le monstre sélectionné': '&Duplicate selected monster',
    "Surnoms abrégés → &nom complet de l'espèce": 'Shortened nicknames → full species &name',
    '&Supprimer le monstre sélectionné…': 'De&lete selected monster…',
    'Choisir la langue du patch installé : noms des monstres, des compétences et des '
    'objets identiques au jeu.': 'Pick the language of the installed patch: monster, '
                                 'skill and item names will match the game.',
    'Ouvrez une sauvegarde (Ctrl+O) ou glissez-la dans la fenêtre.':
        'Open a save (Ctrl+O) or drop it onto the window.',
    'Ouvrir une sauvegarde': 'Open a save',
    'Fichier introuvable': 'File not found',
    '{chemin}\n\nIl est retiré des fichiers récents.':
        '{chemin}\n\nIt has been removed from the recent files.',
    'Ouverture impossible': 'Cannot open',
    '{n} monstres chargés.': '{n} monsters loaded.',
    'Duplication impossible': 'Cannot duplicate',
    '{surnom} dupliqué dans le ranch (emplacement {n}).':
        '{surnom} duplicated into storage (slot {n}).',
    '{surnom} ({espece}, niveau {niveau}, {role})': '{surnom} ({espece}, level {niveau}, {role})',
    "\n\nIl quittera aussi l'équipe.": '\n\nIt will also leave the party.',
    '\n\nIl quittera aussi la réserve.': '\n\nIt will also leave the standby team.',
    'Supprimer un monstre': 'Delete a monster',
    'Supprimer définitivement {description} ?': 'Permanently delete {description}?',
    "La sauvegarde n'est modifiée sur le disque qu'à l'enregistrement.":
        'The save file on disk only changes when you save.',
    'Suppression impossible': 'Cannot delete',
    '{description} supprimé.': '{description} deleted.',
    '{n} surnom(s) complété(s).': '{n} nickname(s) completed.',
    'Enregistrer sous': 'Save as',
    "Extraire les &icônes d'une ROM…": 'Extract &icons from a ROM…',
    'Choisir la ROM du jeu (japonaise ou patchée)': 'Choose the game ROM (Japanese or patched)',
    'ROM DS (*.nds);;Tous les fichiers (*)': 'DS ROM (*.nds);;All files (*)',
    'Extraction impossible': 'Cannot extract',
    '{chemin} illisible : ce fichier est-il une ROM DS ?':
        '{chemin} unreadable: is this file a DS ROM?',
    '{chemin} introuvable dans la ROM': '{chemin} not found in the ROM',
    '{archive} : archive FPK attendue': '{archive}: FPK archive expected',
    'glyphe de famille vide : police inattendue': 'empty family glyph: unexpected font',
    'font_16x16.NFTR : bloc CGLP introuvable': 'font_16x16.NFTR: CGLP block not found',
    '{monstres} icônes de monstres et {familles} de familles extraites dans {dossier}.':
        '{monstres} monster icons and {familles} family icons extracted to {dossier}.',
    'Enregistrement impossible': 'Cannot save',
    'Enregistré : {nom}': 'Saved: {nom}',
    '  (original gardé dans {nom})': '  (original kept in {nom})',
    'Modifications non enregistrées': 'Unsaved changes',
    'Enregistrer les modifications avant de continuer ?': 'Save changes before continuing?',

    # ── Onglet Joueur et horloge ─────────────────────────────────────────────
    'Le nom et les surnoms sont limités à 8 caractères, pris dans la police du jeu.':
        "Names and nicknames are limited to 8 characters from the game's font.",
    'Dernière sauvegarde en jeu': 'Last in-game save',
    'Date': 'Date',
    'Position X / Y / Z': 'Position X / Y / Z',
    'Lever du jour': 'Daybreak',
    'Tombée de la nuit': 'Nightfall',
    'Moment de la journée': 'Time of day',
    'Météo': 'Weather',
    'Seulement sur les cartes où le jeu prévoit une intempérie : forcée ailleurs, la '
    'zone perd ses monstres et sa musique.': 'Only on maps where the game has weather: '
                                             'forced anywhere else, the area loses its '
                                             'monsters and music.',
    'Téléporter': 'Teleport',
    'Téléporter vers': 'Teleport to',
    "Points relevés dans des sauvegardes faites sur place : la position, l'orientation "
    'et la carte du résumé sont recopiées.': 'Points taken from saves made on the spot: '
                                             'position, facing and the summary map are '
                                             'copied.',
    '{jour} {j:02}/{m:02}/{a} à {h:02}:{min:02}:{s:02}':
        '{jour} {a}-{m:02}-{j:02} at {h:02}:{min:02}:{s:02}',
    '{n} — {lieu}   (précédente : {n_avant} — {lieu_avant})':
        '{n} — {lieu}   (previous: {n_avant} — {lieu_avant})',
    '{meteo} en cours': '{meteo} in progress',
    'Aucune intempérie connue sur cette carte': 'No known weather on this map',
    'Carte des îles': 'Island map',
    "Le jeu y ajoute les îles au fil des chapitres de l'histoire : l'avancer peut "
    "faire sauter des événements. On ne peut pas revenir en deçà du chapitre de la "
    'partie.': 'The game adds the islands as the story chapters go by: moving the '
               'chapter forward may skip events. It cannot go below the chapter of '
               'the game.',
    'Sort Téléportation': 'Zoom spell',
    "Une zone cochée entre dans la liste du sort (dans l'ordre du jeu), sans changer "
    "de chapitre ; une île s'affiche aussi comme visitée sur la carte. Les zones déjà "
    'visitées restent cochées : le jeu les remettrait.':
        "A ticked area joins the spell list (in the game's order), without changing "
        'the chapter; an island also shows as visited on the map. Areas already '
        'visited stay ticked: the game would put them back.',
    'Zones': 'Areas',
    '{iles}  (chapitre {n})': '{iles}  (chapter {n})',
    'Aucune île': 'No island',
    'Déjà visitée dans cette partie.': 'Already visited in this game.',
    "Faire glisser la poignée, ou la molette (5 s par cran). L'horloge ne tourne qu'en "
    'plein air.': 'Drag the handle, or use the mouse wheel (5 s per notch). The clock '
                  'only runs outdoors.',
    'Nuit': 'Night',
    'nuit dans {n} min': 'night in {n} min',
    'jour dans {n} min': 'day in {n} min',

    # ── Monstres : panneau d'équipe, fiche, synthèse ─────────────────────────
    'Équipe': 'Party',
    'Réserve': 'Standby',
    'Glisser pour réorganiser.\nDepuis la liste : prendre\nla place. Vers la liste :\n'
    'renvoyer au ranch.': 'Drag to rearrange.\nFrom the list: take\nthe spot. To the '
                          'list:\nsend to storage.',
    'Impossible : {erreur}.': 'Not possible: {erreur}.',
    'Monstre': 'Monster',
    '{surnom} placé en équipe.': '{surnom} moved to the party.',
    '{surnom} placé en réserve.': '{surnom} moved to standby.',
    'Monstre renvoyé au ranch.': 'Monster sent to storage.',
    'Identité': 'Identity',
    'Niveau et stats': 'Level and stats',
    'Lignée': 'Lineage',
    'rang {rang}': 'rank {rang}',
    'taille {n}': 'size {n}',
    'niveau {n}': 'level {n}',
    'emplacement {n}': 'slot {n}',
    'Compétence': 'Skill',
    'Compétences': 'Skills',
    'Points investis': 'Points invested',
    'Synthèse': 'Synthesis',
    'Octets bruts': 'Raw bytes',
    'Enregistrement brut (0x84 octets). Les octets entre [ ] ont un rôle inconnu.':
        'Raw record (0x84 bytes). Bytes in [ ] have an unknown purpose.',
    'Obtenu par': 'Obtained from',
    'Sert à créer': 'Used to create',
    'Aucune synthèse spéciale : à obtenir par recrutement ou synthèse de familles.':
        'No special synthesis: obtained by scouting or family synthesis.',
    "N'apparaît dans aucune synthèse spéciale.": 'Not part of any special synthesis.',
    'patch': 'patch',
    'Recette ajoutée par le patch de traduction': 'Recipe added by the translation patch',

    # ── Onglet Sac ───────────────────────────────────────────────────────────
    'Rechercher dans les noms et descriptions…': 'Search names and descriptions…',
    'Objets possédés seulement': 'Owned items only',
    'ID': 'ID',
    'Objet': 'Item',
    'Quantité': 'Quantity',
    'Description': 'Description',
    'Sélectionnez un objet pour lire sa description.': 'Select an item to read its description.',
    '(pas de description)': '(no description)',

    # ── Onglet Bibliothèque ──────────────────────────────────────────────────
    'Lignes affichées': 'Shown rows',
    'Rechercher une espèce…': 'Search a species…',
    'Toutes les familles': 'All families',
    'Toutes les espèces': 'All species',
    'Dressées': 'Scouted',
    'Vues': 'Seen',
    'Vues, pas dressées': 'Seen, not scouted',
    'Jamais vues': 'Never seen',
    'Rang': 'Rank',
    'Vue': 'Seen',
    'Dressée': 'Scouted',
    'Marquer comme vues': 'Mark as seen',
    'Marquer comme dressées': 'Mark as scouted',
    'Retirer « dressée »': 'Remove "scouted"',
    'Tout décocher (jamais vues)': 'Uncheck all (never seen)',
    '{vues} espèces vues, {dressees} dressées — {affichees} affichée(s) sur {total}':
        '{vues} species seen, {dressees} scouted — {affichees} shown out of {total}',
    'Attribut': 'Trait',
    'Attributs': 'Traits',
    'Rechercher…': 'Search…',
    'Vus seulement': 'Seen only',
    'Vu': 'Seen',
    'Marquer comme vus': 'Mark as seen',
    'Tout décocher': 'Uncheck all',
    'Sélectionnez un attribut pour lire sa description.':
        'Select a trait to read its description.',
    'Sélectionnez une compétence pour lire sa description.':
        'Select a skill to read its description.',
    '{vus} vus — {affiches} affiché(s) sur {total}': '{vus} seen — {affiches} shown out of {total}',
}
