@echo off
chcp 65001 >nul
echo ============================================
echo   ENSAM Notes Bot — Installation
echo ============================================
echo.

:: Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou pas dans le PATH.
    echo Télécharge Python sur https://www.python.org/downloads/
    echo Active bien "Add Python to PATH" lors de l'installation.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v détecté.

:: Créer l'environnement virtuel
if not exist "venv\" (
    echo.
    echo [1/3] Création de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 (
        echo [ERREUR] Impossible de créer l'environnement virtuel.
        pause
        exit /b 1
    )
    echo [OK] Environnement virtuel créé.
) else (
    echo [OK] Environnement virtuel déjà présent.
)

:: Installer les dépendances
echo.
echo [2/3] Installation des dépendances...
call venv\Scripts\pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERREUR] Échec de l'installation des dépendances.
    pause
    exit /b 1
)
echo [OK] Dépendances installées.

:: Lancer la configuration
echo.
echo [3/3] Configuration du bot...
echo.
call venv\Scripts\python setup.py
if errorlevel 1 (
    echo.
    echo [INFO] Configuration annulée ou incomplète.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Installation terminée !
echo   Lance le bot avec : lancer.bat
echo ============================================
pause
