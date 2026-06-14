# ============================================================
# ENSAM Notes Bot — Système de mise à jour automatique
# Auteur  : Mohamed Amine Belasri
# Licence : MIT
# ============================================================

import os
import shutil
import sys
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_RAW = "https://raw.githubusercontent.com/Mohamedaminebelasri/ensam-notes-bot/master"
TMP_DIR  = os.path.join(BASE_DIR, ".update_tmp")
VER_FILE = os.path.join(BASE_DIR, "VERSION")

UPDATE_FILES = [
    "main.py",
    "scraper.py",
    "calculator.py",
    "comparator.py",
    "notifier.py",
    "modules.py",
    "telegram_bot.py",
    "sim_handler.py",
    "setup.py",
    "filieres_database.py",
    "filieres_database.json",
    "requirements.txt",
    "VERSION",
    "updater.py",
]

_TIMEOUT = 8  # secondes par fichier


def _read_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def _download(url, dest):
    with urllib.request.urlopen(url, timeout=_TIMEOUT) as r:
        data = r.read()
    with open(dest, "wb") as f:
        f.write(data)


def _cleanup():
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR, ignore_errors=True)


def check_and_apply_update(log_fn=None):
    """
    Vérifie si une mise à jour est disponible sur GitHub et l'applique.

    Retourne (updated: bool, old_ver: str, new_ver: str).
    Ne lève jamais d'exception — toutes les erreurs réseau sont ignorées
    silencieusement.
    """
    if log_fn is None:
        log_fn = lambda _: None  # silencieux par défaut

    # Crée VERSION local si absent (1ère utilisation)
    local_ver = _read_file(VER_FILE)
    if local_ver is None:
        with open(VER_FILE, "w", encoding="utf-8") as f:
            f.write("1.0.0\n")
        local_ver = "1.0.0"

    # Télécharge VERSION distante
    try:
        os.makedirs(TMP_DIR, exist_ok=True)
        _download(f"{REPO_RAW}/VERSION", os.path.join(TMP_DIR, "VERSION"))
        remote_ver = _read_file(os.path.join(TMP_DIR, "VERSION"))
        if not remote_ver:
            raise ValueError("VERSION distante vide")
    except Exception:
        _cleanup()
        return (False, local_ver, local_ver)

    # Pas de mise à jour nécessaire
    if remote_ver == local_ver:
        _cleanup()
        return (False, local_ver, local_ver)

    # Télécharge tous les fichiers dans TMP_DIR
    try:
        old_req = _read_file(os.path.join(BASE_DIR, "requirements.txt"))
        for fname in UPDATE_FILES:
            _download(f"{REPO_RAW}/{fname}", os.path.join(TMP_DIR, fname))
        new_req = _read_file(os.path.join(TMP_DIR, "requirements.txt"))
    except Exception:
        _cleanup()
        return (False, local_ver, local_ver)

    # Tous les téléchargements réussis → copie atomique
    for fname in UPDATE_FILES:
        src = os.path.join(TMP_DIR, fname)
        dst = os.path.join(BASE_DIR, fname)
        shutil.copy2(src, dst)

    _cleanup()

    # Relance pip si requirements.txt a changé
    if old_req != new_req:
        try:
            import subprocess
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r",
                 os.path.join(BASE_DIR, "requirements.txt"), "--quiet"],
                check=False, timeout=120,
            )
        except Exception:
            pass

    log_fn(f"🔄 Mise à jour appliquée : v{local_ver} → v{remote_ver}")
    return (True, local_ver, remote_ver)


if __name__ == "__main__":
    # Point d'entrée depuis lancer.bat / lancer.sh
    check_and_apply_update(log_fn=print)
