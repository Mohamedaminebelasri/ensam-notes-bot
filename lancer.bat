@echo off
chcp 65001 >nul

:: Vérifier l'environnement virtuel
if not exist "venv\Scripts\python.exe" (
    echo [ERREUR] Environnement virtuel introuvable.
    echo Lance d'abord installer.bat
    pause
    exit /b 1
)

:: Vérifier la configuration
if not exist ".env" (
    echo [ERREUR] Fichier .env introuvable.
    echo Lance d'abord installer.bat pour configurer le bot.
    pause
    exit /b 1
)

echo ============================================
echo   ENSAM Notes Bot — Démarrage
echo ============================================
echo.
echo Appuie sur Ctrl+C pour arrêter le bot.
echo.

call venv\Scripts\python main.py
pause
