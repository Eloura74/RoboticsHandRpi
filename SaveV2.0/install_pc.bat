@echo off
REM Script d'installation automatique pour PC Windows
REM Usage: install_pc.bat

echo ===========================================
echo   Installation Hand Tracker - Windows
echo ===========================================
echo.

REM 1. Vérifier Python
echo [1/3] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python n'est pas installe ou pas dans le PATH !
    echo Installer Python 3.9+ depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo Python OK

REM 2. Création de l'environnement virtuel
echo.
echo [2/3] Creation de l'environnement virtuel...
if exist venv (
    echo venv existe deja, suppression...
    rmdir /s /q venv
)

python -m venv venv
call venv\Scripts\activate.bat

REM 3. Installation des packages
echo.
echo [3/3] Installation des packages Python...
python -m pip install --upgrade pip
pip install -r requirements-pc.txt

echo.
pip list | findstr "opencv-python mediapipe"

REM Résumé
echo.
echo ===========================================
echo Installation terminee !
echo ===========================================
echo.
echo Prochaines etapes :
echo.
echo 1. Editer hand_tracker.py pour mettre l'IP du Raspberry Pi
echo    UDP_IP = "192.168.1.XX"  # IP de ton RPi
echo.
echo 2. Activer le venv :
echo    venv\Scripts\activate.bat
echo.
echo 3. Lancer le tracker :
echo    python hand_tracker.py
echo.
echo Voir README.md pour plus de details.
echo.
pause
