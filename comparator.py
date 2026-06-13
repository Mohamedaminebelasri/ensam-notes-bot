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
import os
import shutil

NOTES_FILE  = os.path.join(os.path.dirname(__file__), "notes.json")
BACKUP_FILE = os.path.join(os.path.dirname(__file__), "notes_backup.json")


def load_saved_notes() -> dict:
    if not os.path.exists(NOTES_FILE):
        return {}
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        print("[COMPARATOR] notes.json corrompu — restauration depuis backup...", flush=True)
        if os.path.exists(BACKUP_FILE):
            try:
                shutil.copy(BACKUP_FILE, NOTES_FILE)
                with open(NOTES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print("[COMPARATOR] Restauration réussie.", flush=True)
                return data if isinstance(data, dict) else {}
            except Exception as e:
                print(f"[COMPARATOR] Échec restauration backup : {e}", flush=True)
        return {}


def save_notes(notes: list):
    data = {
        n["code"]: {
            "cc":       n.get("cc"),
            "ex":       n.get("ex"),
            "tp":       n.get("tp"),
            "rat":      n.get("rat"),
            "moy_so":   n.get("moy_so"),
            "moy_sr":   n.get("moy_sr"),
            "decision": n.get("decision"),
        }
        for n in notes
    }
    if os.path.exists(NOTES_FILE):
        shutil.copy(NOTES_FILE, BACKUP_FILE)
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_changes(old: dict, new: list) -> list:
    changes = []
    for note in new:
        code     = note["code"]
        old_note = old.get(code, {})
        for field in ("cc", "ex", "tp", "rat"):
            old_val = old_note.get(field)
            new_val = note.get(field)
            if new_val is not None and old_val != new_val:
                changes.append({
                    "code":     code,
                    "type":     field,
                    "ancienne": old_val,
                    "nouvelle": new_val,
                })
    return changes
