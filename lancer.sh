#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONIOENCODING=utf-8

echo ""
echo " ============================================"
echo "   ENSAM Notes Bot"
echo " ============================================"
echo ""

# =============================================================================
# 1. Vérification Python
# =============================================================================
if ! command -v python3 &>/dev/null; then
    echo " Python non trouvé."
    echo ""
    echo " Sur Mac    : brew install python3"
    echo "              (ou télécharge depuis https://www.python.org/downloads/)"
    echo " Sur Linux  : sudo apt install python3 python3-pip"
    echo "              (ou : sudo dnf install python3)"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo " [OK] $PYTHON_VERSION détecté."
echo ""

# =============================================================================
# 2. Environnement virtuel
# =============================================================================
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo " [1/2] Création de l'environnement virtuel..."
    python3 -m venv "$SCRIPT_DIR/venv"
    echo " [OK] venv créé."

    echo " [2/2] Installation des dépendances..."
    "$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet
    echo ""
    echo " [OK] Installation terminée !"
    echo ""
else
    # venv existant : vérifie que les dépendances sont à jour
    "$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet 2>/dev/null || true
fi

# =============================================================================
# 3. Lancement
# =============================================================================
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo ""
    echo " ============================================"
    echo "   Configuration existante trouvée"
    echo " ============================================"
    echo "   [1] Continuer  (lancer le bot normalement)"
    echo "   [2] Reconfigurer  (identifiants/bot/niveau/filière)"
    echo ""
    read -rp " Ton choix (1 ou 2) : " choix
    case "$choix" in
        2)  echo ""
            "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/setup.py" && \
            "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/main.py" \
            || { echo ""; echo " Configuration annulée."; } ;;
        *)  echo " Démarrage du bot... (Ctrl+C pour arrêter)"
            echo ""
            "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/main.py" ;;
    esac
else
    echo " Première utilisation — configuration du bot..."
    echo ""
    "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/setup.py" && \
    "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/main.py" \
    || { echo ""; echo " Configuration annulée. Relance ./lancer.sh pour recommencer."; exit 1; }
fi
