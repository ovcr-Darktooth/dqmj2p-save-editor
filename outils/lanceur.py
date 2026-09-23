"""Point d'entrée de l'exe (outils/construire_exe.py) : PyInstaller lance un
script, pas un module, et editeur/__main__.py utilise des imports relatifs."""
from editeur.__main__ import main

main()
