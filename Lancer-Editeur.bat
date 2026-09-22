@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Premiere utilisation : installation de PySide6...
    python -m venv .venv || goto erreur
    .venv\Scripts\python -m pip install -q PySide6 || goto erreur
)
start "" .venv\Scripts\pythonw -m editeur %*
exit /b
:erreur
echo Echec. Python 3.10 ou plus recent est-il installe ?
pause
