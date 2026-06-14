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

import asyncio
import json
import os
import pytz
from datetime import datetime
from dotenv import load_dotenv
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from scraper import get_notes
from modules import MODULES
from calculator import calc_minimum_restant
from notifier import _build_table, _calc_moy_if_12
from sim_handler import build_sim_handler

load_dotenv()

TOKEN           = os.getenv("TELEGRAM_TOKEN")
_MAROC          = pytz.timezone('Africa/Casablanca')
_HEARTBEAT_FILE = os.path.join(os.path.dirname(__file__), "heartbeat.json")

_total_elements = sum(len(m["elements"]) for m in MODULES.values())


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


_HELP_MSG = (
    "👋 Bonjour ! Voici ce que je peux faire :\n\n"
    "📊 /bilan\n"
    "   Résumé complet de tes notes S2 en direct\n"
    "   (notes publiées + minimums requis)\n\n"
    "🔵 /sim\n"
    "   Simulateur de notes — teste des notes\n"
    "   virtuelles et vois ce qu'il te faut\n"
    "   pour valider chaque module\n\n"
    "👀 /simaffichage\n"
    "   Voir un exemple de notification (données fictives)\n\n"
    "📡 /status\n"
    "   État du bot — dernière vérification,\n"
    "   connexion ENSAM, uptime\n\n"
    "❌ /annuler\n"
    "   Annule une simulation en cours\n\n"
    "━━━━━━━━━━━━━━━━━━━\n"
    f"🔔 Je surveille tes {_total_elements} éléments S2\n"
    "   toutes les 5 minutes automatiquement.\n"
    "   Tu seras notifié dès qu'une note change !"
)

_GREET_RE = re.compile(
    r"\b(hey|hy|hi|h[eé]|bonjour|salam)\b",
    re.IGNORECASE,
)


async def cmd_hy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Je suis vivant ! Le bot tourne normalement 🤖")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(_HELP_MSG)


async def msg_greet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text and _GREET_RE.search(update.message.text):
        await update.message.reply_text(_HELP_MSG)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(_MAROC)
    last_check_str = "inconnue"
    minutes_ago    = "?"
    started_at_str = "inconnue"

    if os.path.exists(_HEARTBEAT_FILE):
        try:
            with open(_HEARTBEAT_FILE) as f:
                hb = json.load(f)
            started_at_str = hb.get("started_at") or "inconnue"
            last_check_str = hb.get("last_check")  or "inconnue"
            last_check_iso = hb.get("last_check_iso")
            if last_check_iso:
                last_dt     = datetime.fromisoformat(last_check_iso)
                diff        = now - last_dt
                minutes_ago = int(diff.total_seconds() / 60)
        except Exception:
            pass

    niveau  = os.getenv("NIVEAU",  "3A")
    filiere = os.getenv("FILIERE", "IATD-SI")
    total_elements = sum(len(m["elements"]) for m in MODULES.values())

    connexion_line = (
        "🎬 Mode démo — données fictives"
        if os.getenv("DEMO_MODE") == "true"
        else "✅ Connexion ENSAM : OK"
    )
    msg = (
        "🟢 <b>Bot actif</b>\n\n"
        f"⏰ Dernière vérification : {last_check_str} (il y a {minutes_ago} min)\n"
        f"🚀 Démarré à : {started_at_str}\n"
        f"📊 {total_elements} éléments surveillés\n"
        f"🎓 Configuration : {niveau} — {filiere}\n"
        "🖥️ Bot en cours d'exécution\n"
        f"{connexion_line}"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_bilan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[BILAN] Commande reçue de {update.effective_user.username or update.effective_user.id}", flush=True)

    if os.getenv("DEMO_MODE") == "true":
        await update.message.reply_text("📂 Chargement des notes (mode démo)...")
        from comparator import load_saved_notes
        notes_dict = load_saved_notes()
        if not notes_dict:
            await update.message.reply_text("❌ Aucune donnée de démo trouvée.")
            return
        print(f"[BILAN] Mode démo — {len(notes_dict)} éléments chargés depuis notes.json", flush=True)
    else:
        await update.message.reply_text("⏳ Récupération des notes en cours...")
        loop       = asyncio.get_running_loop()
        notes_list = await loop.run_in_executor(None, get_notes)
        if not notes_list:
            await update.message.reply_text("❌ Erreur connexion")
            return
        notes_dict = _build_notes_dict(notes_list)
        print(f"[BILAN] {len(notes_list)} éléments récupérés — envoi des tableaux", flush=True)
    for mod_code, mod_info in MODULES.items():
        result = calc_minimum_restant(notes_dict, mod_code)

        if result is None or result["minimum"] is None:
            minimum_x = mod_info["seuil"]
        elif result["impossible"]:
            minimum_x = 20.0
        elif result["deja_valide"]:
            minimum_x = max(0.0, result["minimum"] or 0.0)
        else:
            minimum_x = result["minimum"]

        table  = _build_table(mod_info, notes_dict, minimum_x)
        moy_12 = _calc_moy_if_12(notes_dict, mod_info)

        if moy_12 is not None:
            status = "✅" if moy_12 >= mod_info["seuil"] else "❌"
            footer = f"📊 Si 12 partout : {moy_12}/20 {status}"
        else:
            footer = "📊 Si 12 partout : —"

        msg = (
            f"📦 <b>{mod_info['nom']}</b>\n"
            f"<pre>{table}</pre>\n"
            f"{footer}"
        )
        await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_simaffichage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from notifier import _build_message

    mod_code  = next(iter(MODULES))
    mod_info  = MODULES[mod_code]
    elem_code = next(iter(mod_info["elements"]))
    elem_info = mod_info["elements"][elem_code]

    if elem_info["coef_cc"] > 0:
        note_type = "cc"
    elif elem_info["coef_ex"] > 0:
        note_type = "ex"
    else:
        note_type = "tp"

    notes_dict = {
        code: {"cc": None, "ex": None, "tp": None, "rat": None,
               "moy_so": None, "moy_sr": None, "decision": None}
        for code in mod_info["elements"]
    }
    notes_dict[elem_code][note_type] = 15.0

    changes = [{"code": elem_code, "type": note_type, "ancienne": None, "nouvelle": 15.0}]
    body    = _build_message(elem_code, changes, notes_dict)

    prefix = (
        "📌 <b>EXEMPLE (donnée fictive)</b> — voici à quoi\n"
        "ressemblera une vraie notification :\n\n"
        "⬇️⬇️⬇️\n\n"
    )
    await update.message.reply_text(prefix + body, parse_mode="HTML")


def build_application() -> Application:
    return Application.builder().token(TOKEN).build()


def setup_handlers(app: Application):
    app.add_handler(CommandHandler("hy",           cmd_hy))
    app.add_handler(CommandHandler("help",         cmd_help))
    app.add_handler(CommandHandler("status",       cmd_status))
    app.add_handler(CommandHandler("bilan",        cmd_bilan))
    app.add_handler(CommandHandler("simaffichage", cmd_simaffichage))
    app.add_handler(build_sim_handler())
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_greet))
