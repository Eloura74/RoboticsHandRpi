@echo off
REM ============================================================
REM SCRIPT DE REDÉMARRAGE DU DASHBOARD - Version Enhanced
REM ============================================================
echo.
echo ========================================
echo   NEURO-HAND DASHBOARD - RESTART
echo ========================================
echo.

REM Arrête tous les processus Python (dashboard actuel)
echo [1/4] Stopping Python processes...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

REM Supprime le cache Python
echo [2/4] Clearing Python cache...
if exist __pycache__ rd /S /Q __pycache__ >nul 2>&1
if exist apps\__pycache__ rd /S /Q apps\__pycache__ >nul 2>&1
if exist apps\ui\__pycache__ rd /S /Q apps\ui\__pycache__ >nul 2>&1
if exist apps\network\__pycache__ rd /S /Q apps\network\__pycache__ >nul 2>&1
if exist core\__pycache__ rd /S /Q core\__pycache__ >nul 2>&1
del /S /Q *.pyc >nul 2>&1
echo    Cache cleared!

REM Active l'environnement virtuel
echo [3/4] Activating virtual environment...
call venv\Scripts\activate
echo    Venv activated!

REM Lance le dashboard Enhanced
echo [4/4] Starting NEURO-HAND Dashboard Enhanced...
echo.
echo ========================================
echo   DASHBOARD RUNNING ON:
echo   http://192.168.1.60:8080
echo ========================================
echo.
echo Press Ctrl+C to stop
echo.

python apps\neuro_dashboard_enhanced.py

pause
