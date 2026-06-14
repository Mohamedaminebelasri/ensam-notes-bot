# ============================================================
# ENSAM Notes Bot — Surveillance automatique des notes S2
# Auteur  : Mohamed Amine Belasri
# École   : ENSAM Meknès — École Nationale Supérieure
#            d'Arts et Métiers (Université Moulay Ismail)
# Promo   : 2024–2027
# GitHub  : https://github.com/Mohamedaminebelasri/ensam-notes-bot
# Licence : MIT — toute redistribution doit conserver
#            cette notice et le fichier LICENSE
# ============================================================

import json
import logging
import os
import sys
import pytz
from datetime import datetime
from dotenv import load_dotenv
import requests as _http

from scraper import get_notes
from comparator import load_saved_notes, save_notes, find_changes
from notifier import notify_changes, send_telegram
from modules import MODULES

load_dotenv()

_MAROC          = pytz.timezone('Africa/Casablanca')
_HEARTBEAT_FILE = os.path.join(os.path.dirname(__file__), "heartbeat.json")
_LOG_FILE       = os.path.join(os.path.dirname(__file__), "crash.log")

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(_LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
_logger = logging.getLogger(__name__)

# Capture les erreurs internes de python-telegram-bot, httpx et APScheduler
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

_consecutive_errors = 0
_MAX_ERRORS         = 3


def log(msg: str):
    now = datetime.now(_MAROC).strftime('%H:%M:%S')
    print(f"[{now}] {msg}", flush=True)


def check_update_job():
    """Tâche quotidienne : vérifie et applique une mise à jour si disponible."""
    try:
        from updater import check_and_apply_update
        updated, old, new = check_and_apply_update(log_fn=log)
        if updated:
            log(f"🔄 Mise à jour v{old}→v{new} appliquée — redémarrage...")
            sys.exit(0)  # systemd (Restart=always) relance avec le nouveau code
    except Exception as e:
        log(f"[update] Vérification ignorée : {e}")


def _now_str():
    return datetime.now(_MAROC).strftime('%d/%m/%Y à %H:%M')


def _send_alert(text: str):
    token   = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    try:
        _http.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception:
        pass


def _setup_crash_handler():
    original = sys.excepthook
    def _hook(exc_type, exc_value, exc_tb):
        if not issubclass(exc_type, KeyboardInterrupt):
            _logger.critical("UNCAUGHT EXCEPTION", exc_info=(exc_type, exc_value, exc_tb))
            _send_alert(
                f"💀 <b>Bot ENSAM crashé !</b>\n"
                f"<code>{exc_type.__name__}: {exc_value}</code>\n\n"
                f"⏰ {_now_str()}"
            )
        original(exc_type, exc_value, exc_tb)
    sys.excepthook = _hook


def _save_heartbeat():
    now = datetime.now(_MAROC)
    data = {"last_heartbeat": now.strftime('%d/%m/%Y à %H:%M'),
            "last_heartbeat_iso": now.isoformat()}
    if os.path.exists(_HEARTBEAT_FILE):
        try:
            with open(_HEARTBEAT_FILE) as f:
                existing = json.load(f)
            existing.update(data)
            data = existing
        except Exception:
            pass
    with open(_HEARTBEAT_FILE, "w") as f:
        json.dump(data, f)


def _update_last_check():
    now = datetime.now(_MAROC)
    data = {"last_check": now.strftime('%d/%m/%Y à %H:%M'),
            "last_check_iso": now.isoformat()}
    if os.path.exists(_HEARTBEAT_FILE):
        try:
            with open(_HEARTBEAT_FILE) as f:
                existing = json.load(f)
            existing.update(data)
            data = existing
        except Exception:
            pass
    with open(_HEARTBEAT_FILE, "w") as f:
        json.dump(data, f)


def _build_notes_dict(notes_list):
    return {
        n["code"]: {
            "cc":       n.get("cc"),
            "ex":       n.get("ex"),
            "tp":       n.get("tp"),
            "rat":      n.get("rat"),
            "moy_so":   n.get("moy_so"),
            "moy_sr":   n.get("moy_sr"),
            "decision": n.get("decision"),
        }
        for n in notes_list
    }


def check_notes():
    global _consecutive_errors
    log("Vérification des notes en cours...")
    try:
        notes_list = get_notes()
        if not notes_list:
            _consecutive_errors += 1
            log(f"Aucune note récupérée depuis le serveur ({_consecutive_errors}/{_MAX_ERRORS})")
            if _consecutive_errors >= _MAX_ERRORS:
                _send_alert(
                    f"⚠️ <b>Erreur bot ENSAM !</b>\n\n"
                    f"❌ Impossible de scraper les notes\n"
                    f"🔁 Tentatives : {_consecutive_errors}/3 échouées\n"
                    f"📝 Erreur : Aucune note retournée\n\n"
                    f"⏰ {_now_str()}"
                )
            return

        _consecutive_errors = 0
        _update_last_check()
        notes_dict = _build_notes_dict(notes_list)
        old        = load_saved_notes()

        if not old:
            niveau  = os.getenv("NIVEAU",  "3A")
            filiere = os.getenv("FILIERE", "IATD-SI")
            total   = sum(len(m["elements"]) for m in MODULES.values())
            send_telegram(
                f"👋 <b>Bienvenue ! Ton bot ENSAM Notes est actif.</b>\n\n"
                f"🔔 Je surveille tes notes sur SchoolApp et je te\n"
                f"   notifie automatiquement dès qu'une note est\n"
                f"   publiée (vérification toutes les 5 min)\n"
                f"🧮 Pour chaque note, je calcule le minimum requis\n"
                f"   pour valider le module\n\n"
                f"📋 <b>Mes commandes :</b>\n"
                f"📊 /bilan — résumé complet de tes notes actuelles\n"
                f"🔵 /sim — simule des notes virtuelles\n"
                f"👀 /simaffichage — voir un exemple de notification\n"
                f"📡 /status — état du bot\n"
                f"hey / /help — cette liste de commandes\n\n"
                f"🎓 Configuration : {niveau} — {filiere}\n"
                f"📚 {total} éléments surveillés\n\n"
                f"À bientôt ! 🚀"
            )
            save_notes(notes_list)
            log(f"Premier lancement — message d'accueil envoyé, {len(notes_list)} éléments sauvegardés")
            return

        changes = find_changes(old, notes_list)
        if changes:
            log(f"{len(changes)} changement(s) détecté(s) :")
            for c in changes:
                log(f"  {c['code']}.{c['type'].upper()} : {c['ancienne']} → {c['nouvelle']}")
            notify_changes(changes, notes_dict)
        else:
            log("Aucun changement détecté")

        save_notes(notes_list)
        log("État mis à jour")

    except Exception as e:
        _consecutive_errors += 1
        log(f"Erreur dans check_notes: {e} ({_consecutive_errors}/{_MAX_ERRORS})")
        if _consecutive_errors >= _MAX_ERRORS:
            _send_alert(
                f"⚠️ <b>Erreur bot ENSAM !</b>\n\n"
                f"❌ Impossible de scraper les notes\n"
                f"🔁 Tentatives : {_consecutive_errors}/3 échouées\n"
                f"📝 Erreur : {type(e).__name__}: {e}\n\n"
                f"⏰ {_now_str()}"
            )


# ── tests ─────────────────────────────────────────────────────────────────────

def run_test_dec():
    log("=== TEST 1 : Décision officielle VORD ===")
    test_notes = {
        "IA211": {"cc": 16.5, "ex": 14.0, "tp": None, "rat": None,
                  "moy_so": None, "moy_sr": None, "decision": "VORD"},
        "IA212": {"cc": 15.0, "ex": 13.5, "tp": None, "rat": None,
                  "moy_so": None, "moy_sr": None, "decision": "VORD"},
    }
    test_changes = [{"code": "IA211", "type": "cc", "ancienne": None, "nouvelle": 16.5}]
    notify_changes(test_changes, test_notes)
    log("Test 1 terminé")


def run_test_rat():
    log("=== TEST 2 : Rattrapage IA221 ===")
    test_notes = {
        "IA221": {"cc": 16.0, "ex": None, "tp": None, "rat": 13.5,
                  "moy_so": None, "moy_sr": None, "decision": None},
        "IA222": {"cc": None, "ex": None, "tp": None, "rat": None,
                  "moy_so": None, "moy_sr": None, "decision": None},
        "IA223": {"cc": None, "ex": None, "tp": None, "rat": None,
                  "moy_so": None, "moy_sr": None, "decision": None},
    }
    test_changes = [{"code": "IA221", "type": "rat", "ancienne": None, "nouvelle": 13.5}]
    notify_changes(test_changes, test_notes)
    log("Test 2 terminé")


def run_test_min():
    log("=== TEST 3 : Minimum TC23 (CC_TC231=15, EX/TP inconnus) ===")
    from calculator import calc_minimum_restant
    test_notes = {
        "TC231": {"cc": 15.0, "ex": None, "tp": None, "rat": None,
                  "moy_so": None, "moy_sr": None, "decision": None},
        "TC232": {"cc": None, "ex": None, "tp": None, "rat": None,
                  "moy_so": None, "moy_sr": None, "decision": None},
    }
    result = calc_minimum_restant(test_notes, "TC23")
    log(f"Minimum calculé pour TC23 : {result['minimum']}/20")
    log("Attendu ≈ 11.47  →  " + ("✅ OK" if abs((result["minimum"] or 0) - 11.47) < 0.01 else "❌ ERREUR"))
    test_changes = [{"code": "TC231", "type": "cc", "ancienne": None, "nouvelle": 15.0}]
    notify_changes(test_changes, test_notes)
    log("Test 3 terminé")


def run_test_complet():
    log("=== TEST : Module complété (IA21) ===")
    test_notes = {
        "IA211": {"cc": 16.0,  "ex": 14.5, "tp": None, "rat": None,
                  "moy_so": None, "moy_sr": None, "decision": None},
        "IA212": {"cc": 13.5,  "ex": 11.0, "tp": None, "rat": None,
                  "moy_so": None, "moy_sr": None, "decision": None},
    }
    test_changes = [{"code": "IA212", "type": "ex", "ancienne": None, "nouvelle": 11.0}]
    notify_changes(test_changes, test_notes)
    log("Attendu : Moy IA21 = 13.75/20 → ✅ VALIDÉ")
    log("Test terminé — vérifiez Telegram")


def run_all_tests():
    run_test_dec()
    run_test_rat()
    run_test_min()


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    if "--test-complet" in sys.argv:
        run_test_complet(); return
    if "--test-dec" in sys.argv:
        run_test_dec(); return
    if "--test-rat" in sys.argv:
        run_test_rat(); return
    if "--test-min" in sys.argv:
        run_test_min(); return
    if "--test" in sys.argv:
        run_all_tests(); return
    if os.getenv("DEMO_MODE") == "true":
        log("🎬 MODE DÉMO — données fictives, aucune vraie connexion SchoolApp")
        started_at = datetime.now(_MAROC)
        with open(_HEARTBEAT_FILE, "w") as f:
            json.dump({
                "started_at":     started_at.strftime('%d/%m/%Y à %H:%M'),
                "started_at_iso": started_at.isoformat(),
                "last_check":     "Mode démo",
                "last_check_iso": None,
            }, f)
        from telegram_bot import build_application, setup_handlers
        niveau  = os.getenv("NIVEAU",  "3A")
        filiere = os.getenv("FILIERE", "IATD-SI")
        total   = sum(len(m["elements"]) for m in MODULES.values())
        send_telegram(
            f"🎬 <b>Mode démo actif</b> — toutes les notes affichées\n"
            f"sont fictives, à des fins de démonstration.\n\n"
            f"📋 <b>Mes commandes :</b>\n"
            f"📊 /bilan — résumé de tes notes (fictives)\n"
            f"🔵 /sim — simulateur de notes\n"
            f"👀 /simaffichage — exemple de notification\n"
            f"📡 /status — état du bot\n\n"
            f"🎓 Configuration : {niveau} — {filiere}\n"
            f"📚 {total} éléments surveillés (données fictives)"
        )
        app = build_application()
        setup_handlers(app)
        log("Telegram bot actif en mode démo — Ctrl+C pour arrêter")
        try:
            app.run_polling()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            _logger.exception("CRASH FATAL — run_polling() s'est arrêté")
            _send_alert(
                f"💀 <b>Bot ENSAM — Telegram polling crashé !</b>\n"
                f"<code>{type(e).__name__}: {e}</code>\n\n"
                f"⏰ {_now_str()}"
            )
            raise
        log("Bot arrêté (mode démo)")
        return

    if "--once" in sys.argv:
        check_notes()
        log("--- 2ème appel (test réutilisation session) ---")
        check_notes()
        return

    _setup_crash_handler()

    started_at = datetime.now(_MAROC)
    with open(_HEARTBEAT_FILE, "w") as f:
        json.dump({
            "started_at":     started_at.strftime('%d/%m/%Y à %H:%M'),
            "started_at_iso": started_at.isoformat(),
            "last_check":     None,
            "last_check_iso": None,
        }, f)

    from apscheduler.schedulers.background import BackgroundScheduler
    from telegram_bot import build_application, setup_handlers

    scheduler = BackgroundScheduler()
    scheduler.add_job(check_notes,        "interval", minutes=5, jitter=60)
    scheduler.add_job(_save_heartbeat,    "interval", hours=1)
    scheduler.add_job(check_update_job,   "interval", hours=24)
    scheduler.start()
    log("Scheduler démarré (toutes les 5 min)")

    send_telegram(
        f"✅ <b>Bot ENSAM redémarré !</b>\n"
        f"🕐 Uptime depuis : {started_at.strftime('%H:%M')}\n"
        f"📊 Prochaine vérification dans 5 min\n"
        f"💡 /bilan pour les notes · /status pour l'état"
    )
    check_notes()

    app = build_application()
    setup_handlers(app)
    log("Telegram bot actif — Ctrl+C pour arrêter")
    try:
        app.run_polling()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        _logger.exception("CRASH FATAL — run_polling() s'est arrêté")
        _send_alert(
            f"💀 <b>Bot ENSAM — Telegram polling crashé !</b>\n"
            f"<code>{type(e).__name__}: {e}</code>\n\n"
            f"⏰ {_now_str()}"
        )
        raise

    scheduler.shutdown()
    log("Bot arrêté")


if __name__ == "__main__":
    main()
