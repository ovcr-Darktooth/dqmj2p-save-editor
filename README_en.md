# DQMJ2 Professional Save Editor

*[Version française](README.md)*

Graphical save editor for *Dragon Quest Monsters: Joker 2 Professional*
(Nintendo DS). It accepts raw `.sav` files and DeSmuME / DraStic `.dsv` files.

> **Status: work in progress.** Editing of the player (name, play time, gold,
> stats), the bag and monsters (nickname, species, stats, lineage, skills,
> weapon), with the names of the French or English patch. Library viewing
> (monsters seen and scouted, traits, skills) and Scout's Handbook (entries
> unlocked, marked "new"). Right to scout giant monsters (may block the story of an early save) and to use them.
> Syntheses tab: the special syntheses that the monsters in the party, on
> standby and in storage already allow, or soon will (polarity ignored by
> default, as the English patch allows).

## How it works

The editor changes the save **in place**: only the edited fields change.
Checksums are recomputed, and both copies and the `.dsv` footer are kept.
Areas whose purpose is still unknown are never touched. A save that is opened
and saved without changes comes out byte-for-byte identical.

Before each write, a timestamped copy of the original is kept
(`game.dsv.20260922-153000.bak`).

## Download (Windows)

Get the zip of the latest version from the
[Releases](https://github.com/ovcr-Darktooth/dqmj2p-save-editor/releases),
unzip it and run `Editeur-DQMJ2P.exe`: Python is not required. Windows may
show a SmartScreen warning (unsigned exe): "More info", then "Run anyway".

## Running the editor from source

Double-click `Lancer-Editeur.bat`. The first time, it creates a `.venv`
environment and installs PySide6 into it. You can also drop a save onto the
window, or run:

```
python -m editeur game.dsv
```

### Language

**Langue / Language** menu: French or English. Pick the language of the patch
installed on your ROM: the interface and the names of monsters, skills, traits
and items then match the game. The choice also matters for "Shortened
nicknames → full species name", which compares nicknames with the species
names of that language. Switching language keeps the open save and its unsaved
changes.

On first launch, the editor uses French if your system is in French, English
otherwise.

### Icons (optional)

Monster, family and menu button icons are game graphics: they are not in this
repository.
Without them, the editor works and shows empty boxes. To extract them from
your ROM (original Japanese or patched): **File → Extract icons from a ROM…**
menu. They are stored where the editor looks for them (`editeur/icones/`, or
`icones/` next to the exe) and show up right away.

Same thing from the command line (the release zip includes these scripts in
`scripts/`, with French and English instructions in `EXTRAIRE-ICONES.txt`):

```
python outils/extraire_icones.py <your .nds ROM> [folder]
python outils/extraire_familles.py <your .nds ROM> [folder\familles]
python outils/extraire_boutons.py <your .nds ROM> [folder\boutons]
```

Monster icons can also come from a clone of the
[dqmj2pro-synthesis](https://github.com/ovcr-Darktooth/dqmj2pro-synthesis)
project, which already publishes them: `python outils/importer_synthese.py <clone>`.

## Using it from Python

The code is written in French (module, class and field names).

Quick inspection: `python -m dqmj2p_save game.dsv`

```python
from dqmj2p_save import Sauvegarde, langue

langue.choisir('en')                    # English patch names

s = Sauvegarde.ouvrir('game.dsv')       # open a save
for m in s.monstres():                  # monsters: slot, role, species, level
    print(m.emplacement, s.role(m), m['espece'], m['niveau'])

s.monstre(11)['attaque'] = 500          # attack of the monster in slot 11
s.enregistrer()                         # save
```

## Layout

| Folder | Purpose |
|---|---|
| `dqmj2p_save/` | Core, no interface, standard library only |
| `editeur/` | Graphical interface (PySide6) |
| `dqmj2p_save/noms/fr/`, `noms/en/` | Species, skill, trait and item names of each patch (line N = ID N) |
| `outils/importer_noms.py` | Resyncs these names from a translation repository (`… <repo> en` for English) |
| `dqmj2p_save/langue.py` | Current language; interface text translated by `traduction_en.py` |
| `editeur/icones/` | Monster icons (`<id>.png`), to extract (not versioned) |
| `editeur/extraction.py` | Extracts icons from a ROM (File menu), reads NitroFS |
| `outils/extraire_icones.py` | The same, from the command line (`MonsterIconDat.NICA`) |
| `dqmj2p_save/donnees/bestiaire.json` | Rank, family, size and special syntheses |
| `dqmj2p_save/syntheses.py` | Special syntheses within reach of owned monsters (Syntheses tab) |
| `outils/importer_synthese.py` | Copies icons and bestiary from the synthesis project |
| `editeur/icones/familles/` | Family icons, glyphs from the game font (not versioned) |
| `outils/extraire_familles.py` | Family icons from the command line (`font_16x16.NFTR` + menu palette) |
| `editeur/icones/boutons/` | Menu button icons (`<id>.png`), to extract (not versioned) |
| `outils/extraire_boutons.py` | Menu button icons from the command line (`menu_icon_data.cch` + `.cpl`) |
| `docs/format-sauvegarde.md` | Map of the format, with what is still unknown (in French) |
| `outils/construire_exe.py` | Builds the exe (PyInstaller) |
| `outils/preparer_zip.py` | Prepares the release zip (exe, extraction scripts, `EXTRAIRE-ICONES.txt`) |
| `.github/workflows/release.yml` | Windows exe on every PR; release when a `vX.Y.Z` tag is pushed (notes: `docs/notes-de-version/vX.Y.Z.md`) |
| `tests/` | `python -m unittest discover tests` |

Tests on real saves read `tests/donnees/*.dsv`. These files are not
versioned: put your own saves there.

## Credits

The save format was reverse-engineered by **Ceris White** and the team of the
[DQMJ2 Professional Translation](https://github.com/saneezore07/DQMJ2Pro_Translation)
project. This repository does not reuse their code: it reimplements the format
from their documentation.

French names come from the
[DQMJ2Pro_Translation_FR](https://github.com/ovcr-Darktooth/DQMJ2Pro_Translation_FR)
translation, English names from
[DQMJ2Pro_Translation](https://github.com/saneezore07/DQMJ2Pro_Translation),
syntheses from the [dqmj2pro-synthesis](https://github.com/ovcr-Darktooth/dqmj2pro-synthesis)
project, whose `tools/extract_icons.py` decoded the icon format
(`MonsterIconDat.NICA`) used by `outils/extraire_icones.py`.

## Warning

Always keep a copy of your save. With DraStic, close the game before replacing
the file, otherwise the emulator overwrites it when quitting.
