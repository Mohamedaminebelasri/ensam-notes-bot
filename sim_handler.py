"""ConversationHandler Telegram pour /sim — simulation de notes."""

import asyncio
import warnings
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.warnings import PTBUserWarning

warnings.filterwarnings("ignore", message=".*per_message.*", category=PTBUserWarning)
from telegram.ext import (
    ConversationHandler, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)

from modules import MODULES
from calculator import calc_moy_element, calc_minimum_restant, _eval_module_with_sub
from scraper import get_notes

CHOOSE_MODULE, CHOOSE_NOTE, ENTER_VALUE, CONFIRM_MORE = range(4)

_TYPE_LABELS = {"cc": "CC", "ex": "Examen", "tp": "TP"}
_LW = 10
_CW = 12


def _trunc(s, n):
    return (s[: n - 3] + "...") if len(s) > n else s


def _cell(text, w=_CW):
    return text.center(w)


def _parse(v):
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _build_merged(mod_code, real_notes, virtual_notes):
    merged = {}
    for elem_code in MODULES[mod_code]["elements"]:
        real = real_notes.get(elem_code, {})
        virt = virtual_notes.get(elem_code, {})
        merged[elem_code] = {
            "cc":      virt["cc"] if "cc" in virt else real.get("cc"),
            "ex":      virt["ex"] if "ex" in virt else real.get("ex"),
            "tp":      virt["tp"] if "tp" in virt else real.get("tp"),
            "moy_sr":  real.get("moy_sr"),
            "decision": real.get("decision"),
        }
    return merged


def _sim_cell(elem_code, field, real_notes, virtual_notes, ei, min_x):
    coef = ei[f"coef_{field}"]
    if coef == 0:
        return _cell("—")
    virt = virtual_notes.get(elem_code, {})
    if field in virt:
        return _cell(f"🔵 {virt[field]:.1f}")
    real_val = _parse(real_notes.get(elem_code, {}).get(field))
    if real_val is not None:
        return _cell(f"✅ {real_val:.2f}")
    return _cell(f"⚠️ {min_x:.2f}")


def _moy_elem_cell(elem_code, real_notes, virtual_notes, ei, min_x):
    real = real_notes.get(elem_code, {})
    moy_sr = _parse(real.get("moy_sr"))
    if moy_sr is not None:
        return _cell(f"✅ {moy_sr:.2f}")

    virt = virtual_notes.get(elem_code, {})

    def get_val(field, ck):
        if ei[ck] == 0:
            return None, True
        if field in virt:
            return virt[field], True
        rv = _parse(real.get(field))
        if rv is not None:
            return rv, True
        return min_x, False

    cc_v, cc_k = get_val("cc", "coef_cc")
    ex_v, ex_k = get_val("ex", "coef_ex")
    tp_v, tp_k = get_val("tp", "coef_tp")

    moy = calc_moy_element(
        cc_v, ex_v, tp_v,
        ei["coef_cc"], ei["coef_ex"], ei["coef_ecrit"], ei["coef_tp"],
    )
    if moy is None:
        return _cell("—")

    icon = "⚙️" if (not (cc_k and ex_k and tp_k) or bool(virt)) else "✅"
    return _cell(f"{icon} {moy:.2f}")


def _build_sim_table(mod_code, real_notes, virtual_notes, min_x):
    module = MODULES[mod_code]
    elements = module["elements"]
    codes = list(elements.keys())
    n = len(codes)

    def hline(l, m, r):
        return l + "─" * _LW + (m + "─" * _CW) * n + r

    def row(label, cells):
        return "│" + label + "│" + "│".join(cells) + "│"

    top = hline("┌", "┬", "┐")
    sep = hline("├", "┼", "┤")
    bot = hline("└", "┴", "┘")

    header = row(" " * _LW, [_cell(_trunc(elements[c]["nom"], _CW)) for c in codes])

    note_rows = []
    for field, label in [("cc", "CC"), ("ex", "Examen"), ("tp", "TP")]:
        cells = [_sim_cell(c, field, real_notes, virtual_notes, elements[c], min_x) for c in codes]
        note_rows.append(row(f" {label}".ljust(_LW), cells))

    moy_cells = [_moy_elem_cell(c, real_notes, virtual_notes, elements[c], min_x) for c in codes]
    moy_row = row(" Moy élém".ljust(_LW), moy_cells)

    return "\n".join([top, header, sep] + note_rows + [moy_row, bot])


def _build_sim_result(mod_code, real_notes, virtual_notes):
    module = MODULES[mod_code]
    merged = _build_merged(mod_code, real_notes, virtual_notes)

    result = calc_minimum_restant(merged, mod_code)

    if result is None or result["minimum"] is None:
        min_x = 12.0
        min_line = "ℹ️ Calcul indisponible"
    elif result["impossible"]:
        min_x = 20.0
        min_line = f"❌ Impossible ! Max : {result['moy_max_possible']}/20"
    elif result["deja_valide"]:
        min_x = max(0.0, result["minimum"] or 0.0)
        min_line = "✅ Déjà validé !"
    else:
        min_x = result["minimum"]
        min_line = f"{min_x:.2f}/20"

    table = _build_sim_table(mod_code, real_notes, virtual_notes, min_x)

    moy_mod = _eval_module_with_sub(merged, module, min_x)
    moy_str = f"{moy_mod:.2f}/20" if moy_mod is not None else "—"
    seuil = module["seuil"]
    if moy_mod is None:
        validé = "⏳"
    elif moy_mod >= seuil:
        validé = "✅ VALIDÉ"
    else:
        validé = "❌ NON VALIDÉ"

    sim_lines = []
    for elem_code, fields in virtual_notes.items():
        elem_nom = module["elements"][elem_code]["nom"]
        for field, val in fields.items():
            sim_lines.append(f"  {_TYPE_LABELS[field]} de {elem_nom} = {val}")
    sim_summary = "Notes simulées :\n" + "\n".join(sim_lines)

    return (
        f"🔵 <b>Simulation — {module['nom']}</b>\n\n"
        f"{sim_summary}\n\n"
        f"<pre>{table}</pre>\n\n"
        f"🎯 Min restant : {min_line}\n"
        f"📊 Moy module : {moy_str} {validé}\n\n"
        f"Légende : ✅ Réel  🔵 Simulé  ⚠️ Min requis"
    )


def _module_keyboard():
    rows = []
    for mod_code, mod_info in MODULES.items():
        name = _trunc(mod_info["nom"], 40)
        rows.append([InlineKeyboardButton(name, callback_data=f"sim_mod:{mod_code}")])
    return InlineKeyboardMarkup(rows)


def _note_keyboard(mod_code):
    module = MODULES[mod_code]
    rows = []
    for elem_code, ei in module["elements"].items():
        elem_name = _trunc(ei["nom"], 30)
        for field, label in _TYPE_LABELS.items():
            if ei[f"coef_{field}"] > 0:
                rows.append([InlineKeyboardButton(
                    f"{elem_name} — {label}",
                    callback_data=f"sim_note:{elem_code}:{field}",
                )])
    rows.append([InlineKeyboardButton("↩️ Retour modules", callback_data="sim_back")])
    return InlineKeyboardMarkup(rows)


# ── handlers ──────────────────────────────────────────────────────────────────

async def cmd_sim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["sim"] = {}
    await update.message.reply_text(
        "🔵 <b>Simulation de notes</b>\n\nChoisis un module :",
        reply_markup=_module_keyboard(),
        parse_mode="HTML",
    )
    return CHOOSE_MODULE


async def choose_module(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mod_code = query.data.split(":")[1]
    context.user_data["sim"] = {"module_code": mod_code, "virtual_notes": {}}

    await query.edit_message_text(
        f"📦 <b>{MODULES[mod_code]['nom']}</b>\n\nQuelle note veux-tu simuler ?",
        reply_markup=_note_keyboard(mod_code),
        parse_mode="HTML",
    )
    return CHOOSE_NOTE


async def choose_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "sim_back":
        context.user_data["sim"] = {}
        await query.edit_message_text(
            "🔵 <b>Simulation de notes</b>\n\nChoisis un module :",
            reply_markup=_module_keyboard(),
            parse_mode="HTML",
        )
        return CHOOSE_MODULE

    _, elem_code, field = query.data.split(":")
    sim = context.user_data["sim"]
    sim["current_elem"] = elem_code
    sim["current_type"] = field

    mod_code = sim["module_code"]
    elem_name = MODULES[mod_code]["elements"][elem_code]["nom"]
    type_label = _TYPE_LABELS[field]

    await query.edit_message_text(
        f"Entre la note virtuelle pour\n"
        f"<b>[{type_label}]</b> de <b>[{elem_name}]</b> (0-20) :",
        parse_mode="HTML",
    )
    return ENTER_VALUE


async def enter_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(",", ".")
    try:
        val = float(text)
    except ValueError:
        await update.message.reply_text("❌ Note invalide. Entre un nombre entre 0 et 20 :")
        return ENTER_VALUE

    if not (0 <= val <= 20):
        await update.message.reply_text("❌ La note doit être entre 0 et 20 :")
        return ENTER_VALUE

    sim = context.user_data["sim"]
    elem_code = sim["current_elem"]
    field = sim["current_type"]
    sim["virtual_notes"].setdefault(elem_code, {})[field] = val

    mod_code = sim["module_code"]
    elem_name = MODULES[mod_code]["elements"][elem_code]["nom"]
    type_label = _TYPE_LABELS[field]

    await update.message.reply_text(
        f"Note ajoutée ✅\n"
        f"<b>{type_label}</b> de <i>{elem_name}</i> = {val}\n\n"
        f"Veux-tu simuler une autre note dans ce module ?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Oui, autre note", callback_data="sim_more")],
            [InlineKeyboardButton("📊 Non, voir résultat", callback_data="sim_result")],
        ]),
        parse_mode="HTML",
    )
    return CONFIRM_MORE


async def confirm_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "sim_more":
        sim = context.user_data["sim"]
        mod_code = sim["module_code"]
        await query.edit_message_text(
            f"📦 <b>{MODULES[mod_code]['nom']}</b>\n\nQuelle note veux-tu simuler ?",
            reply_markup=_note_keyboard(mod_code),
            parse_mode="HTML",
        )
        return CHOOSE_NOTE

    await query.edit_message_text("⏳ Calcul en cours...")

    loop = asyncio.get_running_loop()
    notes_list = await loop.run_in_executor(None, get_notes)

    if not notes_list:
        await query.edit_message_text("❌ Impossible de récupérer les notes réelles.")
        return ConversationHandler.END

    real_notes = {
        n["code"]: {
            "cc": n.get("cc"), "ex": n.get("ex"), "tp": n.get("tp"),
            "moy_sr": n.get("moy_sr"), "decision": n.get("decision"),
        }
        for n in notes_list
    }

    sim = context.user_data["sim"]
    msg = _build_sim_result(sim["module_code"], real_notes, sim["virtual_notes"])
    await query.edit_message_text(msg, parse_mode="HTML")
    return ConversationHandler.END


async def cmd_annuler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("sim", None)
    await update.message.reply_text("❌ Simulation annulée.")
    return ConversationHandler.END


# ── ConversationHandler factory ───────────────────────────────────────────────

def build_sim_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("sim", cmd_sim)],
        states={
            CHOOSE_MODULE: [CallbackQueryHandler(choose_module, pattern=r"^sim_mod:")],
            CHOOSE_NOTE: [
                CallbackQueryHandler(choose_note, pattern=r"^sim_note:"),
                CallbackQueryHandler(choose_note, pattern=r"^sim_back$"),
            ],
            ENTER_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_value)],
            CONFIRM_MORE: [CallbackQueryHandler(confirm_more, pattern=r"^sim_(more|result)$")],
        },
        fallbacks=[CommandHandler("annuler", cmd_annuler)],
    )
