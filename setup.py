"""
Assistant de configuration interactif — Bot ENSAM Notes.
Lance avec : python setup.py
"""

import os
import sys
import requests
from pathlib import Path

_DIR     = Path(__file__).parent
ENV_FILE = _DIR / ".env"


# ─── affichage ───────────────────────────────────────────────────────────────

def _print(msg=""):
    print(msg, flush=True)

def _ok(msg):
    _print(f"✅ {msg}")

def _err(msg):
    _print(f"❌ {msg}")

def _warn(msg):
    _print(f"⚠️  {msg}")

def _sep():
    _print("─" * 55)


# ─── lecture .env existant ───────────────────────────────────────────────────

def _read_env() -> dict:
    vals = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                vals[k.strip()] = v.strip()
    return vals


def _write_env(vals: dict):
    lines = [
        "# Bot ENSAM Notes — configuration générée par setup.py",
        f"SCHOOL_EMAIL={vals['SCHOOL_EMAIL']}",
        f"SCHOOL_PASSWORD={vals['SCHOOL_PASSWORD']}",
        f"TELEGRAM_TOKEN={vals['TELEGRAM_TOKEN']}",
        f"TELEGRAM_CHAT_ID={vals['TELEGRAM_CHAT_ID']}",
        f"FILIERE={vals['FILIERE']}",
        "",
    ]
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")


# ─── test connexion SchoolApp ─────────────────────────────────────────────────

def _test_login(email: str, password: str) -> tuple[bool, str]:
    try:
        import importlib.util, types

        # Charge scraper sans exécuter le bloc __main__
        spec   = importlib.util.spec_from_file_location("scraper", _DIR / "scraper.py")
        mod    = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        session = mod._new_session()
        ok      = mod._do_login(session, email, password)
        return ok, "" if ok else "Identifiants refusés par le serveur"
    except Exception as e:
        return False, str(e)


# ─── test Telegram ────────────────────────────────────────────────────────────

def _send_test_telegram(token: str, chat_id: str) -> tuple[bool, str]:
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id":    chat_id,
            "text":       "✅ Test ENSAM Notes Bot — configuration en cours !",
            "parse_mode": "HTML",
        }, timeout=10)
        if r.status_code == 200 and r.json().get("ok"):
            return True, ""
        detail = r.json().get("description", r.text[:120])
        return False, detail
    except requests.RequestException as e:
        return False, str(e)


# ─── liste filières ───────────────────────────────────────────────────────────

def _get_filieres() -> list[str]:
    try:
        sys.path.insert(0, str(_DIR))
        from filieres_database import FILIERES
        return sorted(FILIERES.keys())
    except ImportError:
        return [
            "GC24", "GE-DI", "GE-MCI", "GI-ILSI", "GIEO",
            "GIP24", "GM-CISM", "GM-IMS", "GM-MPF", "GME24", "IATD-SI",
        ]


# ─── étapes ──────────────────────────────────────────────────────────────────

def step_welcome(existing: dict) -> bool:
    _print()
    _print("👋 Bienvenue ! Configurons ton bot ENSAM Notes (2 min).")
    _print()
    if existing:
        _warn("Une configuration existe déjà.")
        while True:
            rep = input("   La remplacer ? (o/n) : ").strip().lower()
            if rep in ("o", "oui", "y", "yes"):
                return True
            if rep in ("n", "non", "no"):
                _print("Configuration conservée. À bientôt !")
                return False
    return True


def step_school(existing: dict) -> tuple[str, str]:
    _sep()
    _print("🏫  Étape 1/4 — Identifiants SchoolApp ENSAM")
    _print()

    while True:
        default_email = existing.get("SCHOOL_EMAIL", "")
        prompt_email  = f"   Email [{default_email}] : " if default_email else "   Email : "
        email = input(prompt_email).strip() or default_email

        print("   ⚠️  Ton mot de passe sera visible à l'écran —")
        print("       assure-toi d'être seul devant ton PC.")
        password = input("   Mot de passe : ")

        _print("   Vérification de la connexion...")
        ok, reason = _test_login(email, password)
        if ok:
            _ok("Connexion réussie !")
            return email, password
        _err(f"Échec : {reason or 'identifiants incorrects'}. Réessaie.")
        _print()


def step_telegram_token(existing: dict) -> str:
    _sep()
    _print("🤖  Étape 2/4 — Token du bot Telegram")
    _print()
    _print("   Pas encore de bot Telegram ?")
    _print("   1. Ouvre Telegram, cherche @BotFather")
    _print("   2. Envoie /newbot et suis les instructions")
    _print("   3. Colle le token ici (ressemble à 123456:ABC-...)")
    _print()

    default = existing.get("TELEGRAM_TOKEN", "")
    while True:
        prompt = f"   Token [{default[:20]}...] : " if default else "   Token : "
        token  = input(prompt).strip() or default
        if token:
            return token
        _err("Le token ne peut pas être vide.")


def step_telegram_chat(existing: dict, token: str) -> str:
    _sep()
    _print("💬  Étape 3/4 — Chat ID Telegram")
    _print()
    _print("   Pour trouver ton Chat ID :")
    _print("   1. Ouvre Telegram, cherche @userinfobot")
    _print("   2. Envoie /start — il te donnera ton ID")
    _print()

    default = existing.get("TELEGRAM_CHAT_ID", "")
    while True:
        prompt  = f"   Chat ID [{default}] : " if default else "   Chat ID : "
        chat_id = input(prompt).strip() or default
        if not chat_id:
            _err("Le Chat ID ne peut pas être vide.")
            continue

        _print("   Envoi d'un message de test...")
        ok, reason = _send_test_telegram(token, chat_id)
        if ok:
            _ok("Message envoyé !")
            while True:
                rep = input("   Tu as bien reçu le message sur Telegram ? (o/n) : ").strip().lower()
                if rep in ("o", "oui", "y", "yes"):
                    return chat_id
                if rep in ("n", "non", "no"):
                    _err("Réessaie avec un autre token ou Chat ID.")
                    return step_telegram_chat(existing, token)
        else:
            _err(f"Échec : {reason}. Vérifie le token et le Chat ID.")


def step_filiere(existing: dict) -> str:
    _sep()
    _print("🎓  Étape 4/4 — Choix de ta filière (3ème Année, S2)")
    _print()
    filieres = _get_filieres()
    for i, code in enumerate(filieres, 1):
        marker = " ◀ actuelle" if code == existing.get("FILIERE") else ""
        _print(f"   {i:2d}. {code}{marker}")
    _print()
    _print("   Pas sûr ? Va sur SchoolApp > Plan Etudes > 3ème Année")
    _print("   > 2ème Semestre et compare les codes modules avec 'Mes Notes'.")
    _print()

    while True:
        rep = input(f"   Ton choix (1-{len(filieres)}) : ").strip()
        try:
            idx = int(rep) - 1
            if 0 <= idx < len(filieres):
                chosen = filieres[idx]
                _ok(f"Filière sélectionnée : {chosen}")
                return chosen
        except ValueError:
            pass
        _err(f"Entre un nombre entre 1 et {len(filieres)}.")


def step_write_env(vals: dict):
    _sep()
    _write_env(vals)
    _ok(f"Fichier .env écrit : {ENV_FILE}")


def step_final(filiere: str):
    _print()
    _print("=" * 55)
    _ok("Configuration terminée et testée !")
    _print()
    _print("   Pour démarrer ton bot :")
    _print("     python main.py --once   (premier test)")
    _print("     python main.py          (surveillance continue)")
    _print()
    _print(f"   Filière configurée : {filiere}")
    _print("=" * 55)
    _print()


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    existing = _read_env()

    if not step_welcome(existing):
        return

    email, password = step_school(existing)
    token           = step_telegram_token(existing)
    chat_id         = step_telegram_chat(existing, token)
    filiere         = step_filiere(existing)

    step_write_env({
        "SCHOOL_EMAIL":    email,
        "SCHOOL_PASSWORD": password,
        "TELEGRAM_TOKEN":  token,
        "TELEGRAM_CHAT_ID": chat_id,
        "FILIERE":         filiere,
    })

    step_final(filiere)


if __name__ == "__main__":
    main()
