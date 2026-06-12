@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "BASE=%~dp0"
set "RUNTIME=%BASE%runtime"
set "TMPDIR=%BASE%temp"
set "PY=%RUNTIME%\python.exe"
set "PYTHONIOENCODING=utf-8"

echo.
echo  ============================================
echo    ENSAM Notes Bot
echo  ============================================
echo.

:: =============================================================================
:: 1. Python portable (telechargement automatique a la 1ere utilisation)
:: =============================================================================
if not exist "%PY%" (
    echo  Premiere installation, merci de patienter ^(1-2 min^)...
    echo.

    if not exist "%TMPDIR%" mkdir "%TMPDIR%"

    echo  [1/4] Telechargement de Python 3.12.10...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip' -OutFile '%TMPDIR%\py.zip' -UseBasicParsing } catch { exit 1 }"
    if errorlevel 1 goto :dl_error

    echo  [2/4] Extraction...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Expand-Archive -Path '%TMPDIR%\py.zip' -DestinationPath '%RUNTIME%' -Force } catch { exit 1 }"
    if errorlevel 1 goto :extract_error

    echo  [3/4] Configuration...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$pth='%RUNTIME%\python312._pth'; $lines=Get-Content $pth; $out=@(); foreach($l in $lines){ if($l -eq '.'){$out+='.'; $out+='..'}elseif($l -eq '#import site'){$out+='import site'}else{$out+=$l} }; $out | Set-Content $pth -Encoding ASCII"
    if errorlevel 1 goto :config_error

    echo  [4/4] Installation de pip et des dependances...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%TMPDIR%\get-pip.py' -UseBasicParsing } catch { exit 1 }"
    if errorlevel 1 goto :dl_error

    "%PY%" "%TMPDIR%\get-pip.py" --quiet
    if errorlevel 1 goto :pip_error

    "%PY%" -m pip install -r "%BASE%requirements.txt" --quiet
    if errorlevel 1 goto :pip_error

    if exist "%TMPDIR%" rmdir /s /q "%TMPDIR%"

    echo.
    echo  [OK] Installation terminee !
    echo.
)

:: =============================================================================
:: 2. Configuration (1ere fois : creation du .env)
:: =============================================================================
if not exist "%BASE%.env" (
    echo  Premiere utilisation -- configuration du bot...
    echo.
    "%PY%" "%BASE%setup.py"
    if errorlevel 1 (
        echo.
        echo  Configuration annulee. Relance lancer.bat pour recommencer.
        pause
        exit /b 1
    )
    echo.
)

:: =============================================================================
:: 3. Demarrage du bot
:: =============================================================================
echo  Demarrage du bot... ^(Ctrl+C pour arreter^)
echo.
"%PY%" "%BASE%main.py"
pause
exit /b 0

:: =============================================================================
:dl_error
echo.
echo  Telechargement impossible. Verifie ta connexion
echo  internet, ou demande a Mohamed Amine la version
echo  avec Python a installer manuellement.
echo.
if exist "%RUNTIME%" rmdir /s /q "%RUNTIME%"
if exist "%TMPDIR%" rmdir /s /q "%TMPDIR%"
pause
exit /b 1

:extract_error
echo.
echo  Erreur lors de l'extraction de Python.
if exist "%TMPDIR%" rmdir /s /q "%TMPDIR%"
pause
exit /b 1

:config_error
echo.
echo  Erreur lors de la configuration de Python.
pause
exit /b 1

:pip_error
echo.
echo  Erreur lors de l'installation des dependances.
echo  Verifie ta connexion internet et reessaie.
if exist "%TMPDIR%" rmdir /s /q "%TMPDIR%"
pause
exit /b 1
