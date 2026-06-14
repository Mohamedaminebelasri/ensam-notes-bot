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

import os
import requests
import pytz
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv

_MAROC = pytz.timezone('Africa/Casablanca')

from modules import MODULES
from calculator import (
    calc_minimum_restant, calc_moy_element, calc_moy_module,
    get_decision_finale, est_module_complet, find_elim_element,
)

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TYPE_LABELS = {"cc": "CC", "ex": "Examen", "tp": "TP", "rat": "Rattrapage"}

_LW = 10   # largeur colonne label
_CW = 11   # largeur colonne élément


# ── helpers ───────────────────────────────────────────────────────────────────

def _find_module(elem_code: str):
    for mod_code, mod_info in MODULES.items():
        if elem_code in mod_info["elements"]:
            return mod_code, mod_info
    return None, None


def _get_module_dec(mod_info, notes_dict):
    """Retourne 'VORD' ou 'NV' si le site a publié une décision officielle."""
    for code in mod_info["elements"]:
        dec = notes_dict.get(code, {}).get("decision", "")
        if dec and dec.strip() in ("VORD", "NV"):
            return dec.strip()
    return None


def _fill(val, coef, substitute):
    """val si publiée, substitute si inconnue, None si coef=0."""
    if coef == 0:
        return None
    return val if val is not None else substitute


def _moy_elem_with_sub(note, ei, substitute):
    return calc_moy_element(
        _fill(note.get("cc"), ei["coef_cc"], substitute),
        _fill(note.get("ex"), ei["coef_ex"], substitute),
        _fill(note.get("tp"), ei["coef_tp"], substitute),
        ei["coef_cc"], ei["coef_ex"], ei["coef_ecrit"], ei["coef_tp"],
    )


def _is_fully_known(note, ei):
    return all(
        note.get(f) is not None or ei[k] == 0
        for f, k in [("cc", "coef_cc"), ("ex", "coef_ex"), ("tp", "coef_tp")]
    )


def _cell(text, width=_CW):
    return text.center(width)


def _note_cell(val, is_real, coef, width=_CW):
    if coef == 0:
        return _cell("—", width)
    if is_real:
        return _cell(f"✅ {val:.2f}", width)
    return _cell(f"⚠️ {val:.2f}", width)


# ── tableau ASCII ─────────────────────────────────────────────────────────────

def _build_table(module_info, notes_dict, minimum_x):
    elements  = module_info["elements"]
    codes     = list(elements.keys())
    n, lw, cw = len(codes), _LW, _CW

    def hline(l, m, r):
        return l + "─" * lw + (m + "─" * cw) * n + r

    def make_row(label, cells):
        return "│" + label + "│" + "│".join(cells) + "│"

    top = hline("┌", "┬", "┐")
    sep = hline("├", "┼", "┤")
    bot = hline("└", "┴", "┘")

    header = make_row(" " * lw, [_cell(c, cw) for c in codes])

    note_rows = []
    for lbl, field, ck in [
        ("CC", "cc", "coef_cc"),
        ("EX", "ex", "coef_ex"),
        ("TP", "tp", "coef_tp"),
    ]:
        cells = []
        for code in codes:
            ei      = elements[code]
            val     = notes_dict.get(code, {}).get(field)
            is_real = val is not None
            display = val if is_real else minimum_x
            cells.append(_note_cell(display, is_real, ei[ck], cw))
        note_rows.append(make_row(f" {lbl}".ljust(lw), cells))

    moy_cells = []
    for code in codes:
        ei     = elements[code]
        note   = notes_dict.get(code, {})
        moy_sr = note.get("moy_sr")
        if moy_sr is not None:
            moy_cells.append(_cell(f"✅ {moy_sr:.2f}", cw))
        else:
            moy = _moy_elem_with_sub(note, ei, minimum_x)
            if moy is None:
                moy_cells.append(_cell("—", cw))
            else:
                icon = "✅" if _is_fully_known(note, ei) else "⚠️"
                moy_cells.append(_cell(f"{icon} {moy:.2f}", cw))

    moy_row = make_row(" Moy élém".ljust(lw), moy_cells)
    return "\n".join([top, header, sep] + note_rows + [moy_row, bot])


def _calc_moy_if_12(notes_dict, module_info):
    elements = module_info["elements"]
    num, den = 0.0, 0.0
    for code, ei in elements.items():
        note   = notes_dict.get(code, {})
        moy_sr = note.get("moy_sr")
        if moy_sr is not None:
            moy = moy_sr
        else:
            moy = _moy_elem_with_sub(note, ei, 12.0)
        if moy is not None:
            num += moy * ei["coef_elem"]
            den += ei["coef_elem"]
    return round(num / den, 2) if den > 0 else None


# ── messages ──────────────────────────────────────────────────────────────────

def _build_rat_message(elem_code, notes_dict):
    """Message simple pour un changement de note RAT (sans calculs)."""
    mod_code, mod_info = _find_module(elem_code)
    now     = datetime.now(_MAROC).strftime("%d/%m/%Y à %H:%M")
    rat_val = notes_dict.get(elem_code, {}).get("rat")
    rat_str = f"{rat_val:.2f}" if rat_val is not None else "—"

    if mod_info is None:
        return (
            f"🔄 <b>Note de Rattrapage publiée !</b>\n\n"
            f"📦 Module non défini\n"
            f"📚 {elem_code}\n"
            f"📝 Rattrapage : {rat_str} / 20\n\n"
            f"⏰ {now}"
        )

    mod_nom  = mod_info["nom"]
    elem_nom = mod_info["elements"][elem_code]["nom"]
    return (
        f"🔄 <b>Note de Rattrapage publiée !</b>\n\n"
        f"📦 {mod_nom}\n"
        f"📚 {elem_nom}\n"
        f"📝 Rattrapage : {rat_str} / 20\n\n"
        f"⏰ {now}"
    )


def _build_moysr_message(elem_code, notes_dict):
    """Message quand moy_sr (résultat officiel après rattrapage) est publié."""
    mod_code, mod_info = _find_module(elem_code)
    now        = datetime.now(_MAROC).strftime("%d/%m/%Y à %H:%M")
    moy_sr_val = notes_dict.get(elem_code, {}).get("moy_sr")
    moy_sr_str = f"{moy_sr_val:.2f}" if moy_sr_val is not None else "—"

    if mod_info is None:
        return (
            f"🎓 <b>Résultat officiel publié (après rattrapage) !</b>\n\n"
            f"📦 Module non défini\n"
            f"📚 {elem_code}\n"
            f"📝 Moyenne finale : {moy_sr_str}/20\n\n"
            f"⏰ {now}"
        )

    mod_nom  = mod_info["nom"]
    elem_nom = mod_info["elements"][elem_code]["nom"]

    dec_site         = _get_module_dec(mod_info, notes_dict)
    elim_nom         = find_elim_element(notes_dict, mod_code)
    moy_calc         = calc_moy_module(notes_dict, mod_code)
    decision, reason = get_decision_finale(dec_site, moy_calc, mod_info["seuil"], elim_nom)

    dec_block = f"🏆 Nouvelle décision du module {mod_code} :\n{decision}"
    if reason:
        dec_block += f"\n{reason}"

    return (
        f"🎓 <b>Résultat officiel publié (après rattrapage) !</b>\n\n"
        f"📦 {mod_nom}\n"
        f"📚 {elem_nom}\n"
        f"📝 Moyenne finale : {moy_sr_str}/20\n\n"
        f"{dec_block}\n\n"
        f"⏰ {now}"
    )


def _build_message_complet(mod_code, mod_info, notes_dict):
    """Message spécial quand toutes les notes du module sont publiées (aucun ⚠️)."""
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")

    # Toutes les notes sont réelles → minimum_x ne sert à rien, aucun ⚠️
    table = _build_table(mod_info, notes_dict, 0.0)

    moy      = calc_moy_module(notes_dict, mod_code)
    seuil    = mod_info["seuil"]
    moy_str  = f"{moy:.2f}" if moy is not None else "—"

    dec_site  = _get_module_dec(mod_info, notes_dict)
    elim_nom  = find_elim_element(notes_dict, mod_code)
    decision, reason = get_decision_finale(dec_site, moy, seuil, elim_nom)

    statut_block = decision
    if reason:
        statut_block += f"\n{reason}"

    return (
        f"🎓 <b>Module complété !</b>\n\n"
        f"📦 {mod_info['nom']}\n\n"
        f"<pre>{table}</pre>\n\n"
        f"🎯 Moyenne finale : {moy_str}/20\n"
        f"{statut_block}\n\n"
        f"⏰ {now}"
    )


def _build_message(elem_code, elem_changes, notes_dict):
    """Message complet pour un changement CC/EX/TP avec tableau et décision."""
    mod_code, mod_info = _find_module(elem_code)
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")

    notes_lines = "\n".join(
        f"📝 {TYPE_LABELS.get(c['type'], c['type'].upper())} : {c['nouvelle']} / 20"
        for c in elem_changes
    )

    if mod_info is None:
        return (
            f"🔔 <b>Nouvelle note publiée !</b>\n\n"
            f"📦 Module non défini\n"
            f"📚 {elem_code}\n"
            f"{notes_lines}\n\n"
            f"⏰ {now}"
        )

    # Toutes les notes publiées → message de complétion à la place
    if est_module_complet(notes_dict, mod_code):
        return _build_message_complet(mod_code, mod_info, notes_dict)

    mod_nom  = mod_info["nom"]
    elem_nom = mod_info["elements"][elem_code]["nom"]
    result   = calc_minimum_restant(notes_dict, mod_code)

    if result is None or result["minimum"] is None:
        minimum_x = mod_info["seuil"]
    elif result["deja_valide"]:
        minimum_x = max(0.0, result["minimum"] if result["minimum"] is not None else 0.0)
    elif result["impossible"]:
        minimum_x = 20.0
    else:
        minimum_x = result["minimum"]

    if result is None:
        min_line = "ℹ️ Calcul indisponible"
    elif result["deja_valide"]:
        min_line = "✅ Module déjà validé !"
    elif result["impossible"]:
        min_line = f"❌ Validation impossible ! Max : {result['moy_max_possible']}/20"
    else:
        min_line = f"→ {result['minimum']}/20 dans les notes restantes"

    # Décision : officielle (VORD/NV) ou estimée à partir des moyennes calculées
    dec_site           = _get_module_dec(mod_info, notes_dict)
    moy_calc           = calc_moy_module(notes_dict, mod_code)
    elim_nom           = find_elim_element(notes_dict, mod_code)
    decision, reason   = get_decision_finale(dec_site, moy_calc, mod_info["seuil"], elim_nom)
    decision_block     = f"🏆 Décision : {decision}"
    if reason:
        decision_block += f"\n   {reason}"

    table  = _build_table(mod_info, notes_dict, minimum_x)
    moy_12 = _calc_moy_if_12(notes_dict, mod_info)
    if moy_12 is not None:
        status      = "✅ Validé" if moy_12 >= mod_info["seuil"] else "❌ Non validé"
        moy_12_line = f"📊 Moy {mod_code} si 12.0 partout : {moy_12}/20 {status}"
    else:
        moy_12_line = ""

    return (
        f"🔔 <b>Nouvelle note publiée !</b>\n\n"
        f"📦 {mod_nom}\n"
        f"📚 {elem_nom}\n"
        f"{notes_lines}\n\n"
        f"🎯 <b>Minimum pour valider {mod_code} (≥{mod_info['seuil']}/20) :</b>\n"
        f"   {min_line}\n"
        f"{decision_block}\n\n"
        f"<pre>{table}</pre>\n\n"
        f"{moy_12_line}\n\n"
        f"⏰ {now}"
    )


# ── point d'entrée ────────────────────────────────────────────────────────────

def send_telegram(message: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[NOTIFIER] Variables Telegram manquantes")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }, timeout=10)
        resp.raise_for_status()
        print("[NOTIFIER] Message Telegram envoyé")
        return True
    except requests.RequestException as e:
        print(f"[NOTIFIER] Échec : {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"[NOTIFIER] Réponse API : {e.response.text}")
        return False


def notify_changes(changes: list, notes_dict: dict):
    grouped = defaultdict(list)
    for c in changes:
        grouped[c["code"]].append(c)
    for elem_code, elem_changes in grouped.items():
        rat_changes   = [c for c in elem_changes if c["type"] == "rat"]
        moysr_changes = [c for c in elem_changes if c["type"] == "moy_sr"]
        other_changes = [c for c in elem_changes if c["type"] not in ("rat", "moy_sr")]
        if rat_changes:
            send_telegram(_build_rat_message(elem_code, notes_dict))
        if moysr_changes:
            send_telegram(_build_moysr_message(elem_code, notes_dict))
        if other_changes:
            send_telegram(_build_message(elem_code, other_changes, notes_dict))
