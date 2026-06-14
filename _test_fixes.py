"""
Tests de non-régression + validation des corrections.
Lance avec :  python _test_fixes.py   (depuis le dossier du projet)
"""

import os, sys
import io

# Force UTF-8 sur stdout (emojis sur Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Force 3A/IATD-SI pour les tests de régression (config habituelle)
os.environ.setdefault("NIVEAU",  "3A")
os.environ.setdefault("FILIERE", "IATD-SI")

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SEP  = "─" * 60


def check(cond, label, detail=""):
    status = PASS if cond else FAIL
    print(f"  {status}  {label}")
    if detail:
        print(f"        {detail}")
    return cond


# ═══════════════════════════════════════════════════════════════
# TEST C/D/E — valeurs seuil/eliminatoire en 4A (base de données)
# ═══════════════════════════════════════════════════════════════
def test_database_values():
    print(f"\n{SEP}")
    print("TEST (c/d/e) — Vérification des valeurs 4A dans filieres_database")
    print(SEP)

    from filieres_database import FILIERES
    mods_4a = FILIERES.get("4A", {})
    ok = True

    # (c) GI-ILSI : INFO41-44 doivent avoir seuil=12.0
    gi_mods = mods_4a.get("GI-ILSI", {}).get("modules", {})
    for code in ["INFO41", "INFO42", "INFO43", "INFO44"]:
        m = gi_mods.get(code, {})
        s, e = m.get("seuil"), m.get("eliminatoire")
        r = check(s == 12.0 and e == 8.0,
                  f"4A/GI-ILSI/{code} : seuil={s}, eliminatoire={e}",
                  f"attendu seuil=12.0, eliminatoire=8.0")
        ok = ok and r

    # (d) GM-CISM : CISM41 doit avoir eliminatoire=8.0
    cism_mods = mods_4a.get("GM-CISM", {}).get("modules", {})
    m = cism_mods.get("CISM41", {})
    s, e = m.get("seuil"), m.get("eliminatoire")
    r = check(s == 12.0 and e == 8.0,
              f"4A/GM-CISM/CISM41 : seuil={s}, eliminatoire={e}",
              "attendu seuil=12.0, eliminatoire=8.0")
    ok = ok and r

    # (e) IATD-SI : IA41-45 doivent avoir seuil=12.0
    ia_mods = mods_4a.get("IATD-SI", {}).get("modules", {})
    for code in ["IA41", "IA42", "IA43", "IA44", "IA45"]:
        m = ia_mods.get(code, {})
        s, e = m.get("seuil"), m.get("eliminatoire")
        r = check(s == 12.0 and e == 8.0,
                  f"4A/IATD-SI/{code} : seuil={s}, eliminatoire={e}",
                  "attendu seuil=12.0, eliminatoire=8.0")
        ok = ok and r

    return ok


# ═══════════════════════════════════════════════════════════════
# TEST A — régression 3A/IATD-SI (pas d'élément éliminatoire)
# ═══════════════════════════════════════════════════════════════
def test_regression_3A():
    print(f"\n{SEP}")
    print("TEST (a) — Régression 3A/IATD-SI : cas normal sans élément éliminatoire")
    print(SEP)

    from calculator import (
        calc_moy_module, get_decision_finale, check_elim_element,
        calc_moy_element,
    )
    from modules import MODULES

    ok = True

    # Prend le premier module disponible (IA21 normalement)
    mod_code = next(iter(MODULES))
    mod_info = MODULES[mod_code]
    seuil    = mod_info["seuil"]
    elim     = mod_info["eliminatoire"]

    print(f"  Module testé : {mod_code} — seuil={seuil}, eliminatoire={elim}")

    # Construit des notes correctes (toutes = 14/20)
    notes_dict = {}
    for ecode, ei in mod_info["elements"].items():
        n = {"cc": None, "ex": None, "tp": None, "moy_sr": None, "decision": None}
        if ei["coef_cc"] > 0: n["cc"] = 14.0
        if ei["coef_ex"] > 0: n["ex"] = 14.0
        if ei["coef_tp"] > 0: n["tp"] = 14.0
        notes_dict[ecode] = n

    moy      = calc_moy_module(notes_dict, mod_code)
    has_elim = check_elim_element(notes_dict, mod_code)
    decision = get_decision_finale(None, moy, seuil, has_elim_element=has_elim)

    r1 = check(not has_elim,
               "Aucun élément éliminatoire (notes=14/20 partout)",
               f"has_elim={has_elim}")
    r2 = check(moy is not None and moy >= seuil,
               f"Moy_module={moy:.4f} ≥ seuil={seuil}",
               f"moy={moy}")
    r3 = check("Validé" in decision,
               f"Décision = '{decision}'",
               "attendu : contient 'Validé'")
    ok = r1 and r2 and r3

    # Notes basses mais PAS éliminatoires (toutes = 9/20)
    for ecode in notes_dict:
        for f in ("cc", "ex", "tp"):
            if notes_dict[ecode][f] is not None:
                notes_dict[ecode][f] = 9.0

    moy2      = calc_moy_module(notes_dict, mod_code)
    has_elim2 = check_elim_element(notes_dict, mod_code)
    decision2 = get_decision_finale(None, moy2, seuil, has_elim_element=has_elim2)

    print(f"\n  Sous-test : notes = 9/20 partout (moy attendue ~9, pas éliminatoire)")
    r4 = check(not has_elim2,
               f"Aucun élément éliminatoire (notes=9/20, elim=8.0)",
               f"has_elim={has_elim2}")
    r5 = check("Rattrapage" in decision2 or "Validé" in decision2,
               f"Décision = '{decision2}'",
               "attendu : Rattrapage ou Validé (pas Éliminatoire)")
    ok = ok and r4 and r5

    return ok


# ═══════════════════════════════════════════════════════════════
# TEST B — nouvelle règle éliminatoire AU NIVEAU ÉLÉMENT
# ═══════════════════════════════════════════════════════════════
def test_elim_element_1A():
    print(f"\n{SEP}")
    print("TEST (b) — Nouvelle règle éliminatoire au niveau élément")
    print("           Cas 1 : API22  (coef_elem inégaux — moy module < seuil)")
    print("           Cas 2 : API24  (coef_elem égaux   — moy module ≥ seuil)")
    print(SEP)

    from filieres_database import FILIERES
    import calculator as calc_mod
    from calculator import get_decision_finale, check_elim_element

    mods_1a = FILIERES["1A"]["API-MPT"]["modules"]
    original_modules = calc_mod.MODULES
    ok = True

    # ── Cas 1 : API22 ────────────────────────────────────────────
    print("\n  CAS 1 — API22 (Thermodynamique et statique des fluides)")
    mod22 = mods_1a["API22"]
    seuil22, elim22 = mod22["seuil"], mod22["eliminatoire"]
    print(f"    seuil={seuil22}, eliminatoire={elim22}")

    coef221 = mod22["elements"]["API221"]["coef_elem"]  # 3.5
    coef222 = mod22["elements"]["API222"]["coef_elem"]  # 1.5
    moy22_calc = (6.0 * coef221 + 18.0 * coef222) / (coef221 + coef222)
    print(f"    API221 moy_sr=6.0 (coef_elem={coef221}), API222 moy_sr=18.0 (coef_elem={coef222})")
    print(f"    Moy_module = (6.0×{coef221} + 18.0×{coef222}) / {coef221+coef222} = {moy22_calc:.4f}")

    notes_api22 = {
        "API221": {"cc": None, "ex": None, "tp": None, "moy_sr": 6.0,  "decision": None},
        "API222": {"cc": None, "ex": None, "tp": None, "moy_sr": 18.0, "decision": None},
    }

    # Mock MODULES → 1A/API-MPT pour que check_elim_element trouve API22
    calc_mod.MODULES = {"API22": mod22}
    has_elim22 = check_elim_element(notes_api22, "API22")
    calc_mod.MODULES = original_modules

    ancienne_decision = (
        "❌ Éliminatoire" if moy22_calc < elim22
        else "⚠️ Rattrapage possible" if moy22_calc < seuil22
        else "✅ Validé (estimé)"
    )
    nouvelle_decision = get_decision_finale(None, moy22_calc, seuil22, has_elim_element=has_elim22)

    print(f"    ANCIENNE règle (moy_module vs elim) : {ancienne_decision}")
    print(f"    NOUVELLE règle (élément vs elim)    : {nouvelle_decision}")

    r1 = check(has_elim22,
               "check_elim_element détecte API221=6.0 < elim=7.0",
               f"has_elim={has_elim22}")
    r2 = check("Éliminatoire" in nouvelle_decision,
               f"Nouvelle décision = '{nouvelle_decision}'",
               "attendu : contient 'Éliminatoire'")
    r3 = check("Éliminatoire" not in ancienne_decision,
               f"Ancienne décision = '{ancienne_decision}'",
               "ancienne règle ne détectait PAS l'élément (moy_module=9.6 > elim=7.0)")
    ok = r1 and r2 and r3

    # ── Cas 2 : API24 — démontre "✅ Validé → ❌ Éliminatoire" ──
    print("\n  CAS 2 — API24 (Automatisme et construction 2) — coef_elem égaux")
    mod24 = mods_1a["API24"]
    seuil24, elim24 = mod24["seuil"], mod24["eliminatoire"]
    print(f"    seuil={seuil24}, eliminatoire={elim24}")

    coef241 = mod24["elements"]["API241"]["coef_elem"]  # 2.5
    coef242 = mod24["elements"]["API242"]["coef_elem"]  # 2.5
    moy24_calc = (6.0 * coef241 + 18.0 * coef242) / (coef241 + coef242)  # → 12.0

    notes_api24 = {
        "API241": {"cc": None, "ex": None, "tp": None, "moy_sr": 6.0,  "decision": None},
        "API242": {"cc": None, "ex": None, "tp": None, "moy_sr": 18.0, "decision": None},
    }
    print(f"    API241 moy_sr=6.0 (coef_elem={coef241}), API242 moy_sr=18.0 (coef_elem={coef242})")
    print(f"    Moy_module = (6.0×{coef241} + 18.0×{coef242}) / {coef241+coef242} = {moy24_calc:.4f}")

    calc_mod.MODULES = {"API24": mod24}
    has_elim24 = check_elim_element(notes_api24, "API24")
    calc_mod.MODULES = original_modules

    ancienne24 = (
        "❌ Éliminatoire" if moy24_calc < elim24
        else "⚠️ Rattrapage possible" if moy24_calc < seuil24
        else "✅ Validé (estimé)"
    )
    nouvelle24 = get_decision_finale(None, moy24_calc, seuil24, has_elim_element=has_elim24)

    print(f"    ANCIENNE règle (moy_module vs elim) : {ancienne24}")
    print(f"    NOUVELLE règle (élément vs elim)    : {nouvelle24}")

    r4 = check(moy24_calc >= seuil24,
               f"Moy_module={moy24_calc:.2f} ≥ seuil={seuil24} — ancienne règle = Validé",
               "confirme que l'ancienne règle laissait passer ce cas")
    r5 = check(has_elim24,
               "check_elim_element détecte API241=6.0 < elim=7.0",
               f"has_elim={has_elim24}")
    r6 = check("Éliminatoire" in nouvelle24,
               f"Nouvelle décision = '{nouvelle24}'",
               "attendu : contient 'Éliminatoire'")
    r7 = check("Validé" in ancienne24 and "Éliminatoire" not in ancienne24,
               f"Ancienne décision = '{ancienne24}'",
               "confirme l'ancienne règle retournait Validé (BUG corrigé)")
    ok = ok and r4 and r5 and r6 and r7

    return ok


# ═══════════════════════════════════════════════════════════════
# TEST — fallback minimum_x utilise bien module["seuil"]
# ═══════════════════════════════════════════════════════════════
def test_fallback_seuil():
    print(f"\n{SEP}")
    print("TEST — Fallback minimum_x = module[\"seuil\"] (pas 12.0 hardcodé)")
    print(SEP)

    from filieres_database import FILIERES
    from calculator import calc_minimum_restant

    # Vérifie pour un module 1A (seuil=11) : si on appelle calc_minimum_restant
    # avec des notes vides, le résultat doit utiliser seuil=11 (pas 12)
    mods_1a = FILIERES["1A"]["API-MPT"]["modules"]

    # Mock MODULES pour pointer sur API21 de 1A
    import calculator as calc_mod
    original_modules = calc_mod.MODULES
    calc_mod.MODULES = {"API21": mods_1a["API21"]}

    notes_vides = {}  # aucune note
    result = calc_minimum_restant(notes_vides, "API21")

    calc_mod.MODULES = original_modules  # restaure

    seuil_attendu = 11.0
    minimum_obtenu = result["minimum"] if result else None
    ok = check(
        result is not None and result.get("minimum") is not None and abs(result["minimum"] - seuil_attendu) < 0.01,
        f"calc_minimum_restant avec notes vides → minimum={minimum_obtenu}",
        f"attendu ≈ {seuil_attendu} (seuil du module API21=1A)"
    )
    return ok


# ═══════════════════════════════════════════════════════════════
# TEST — vérification imports (pas de crash)
# ═══════════════════════════════════════════════════════════════
def test_imports():
    print(f"\n{SEP}")
    print("TEST — Vérification imports / syntaxe Python")
    print(SEP)
    ok = True
    for name in ["calculator", "notifier", "modules"]:
        try:
            __import__(name)
            r = check(True, f"import {name} OK")
        except Exception as ex:
            r = check(False, f"import {name} ÉCHOUÉ", str(ex))
        ok = ok and r
    # Vérifie que get_statut_module a bien été supprimée
    import calculator
    r = check(not hasattr(calculator, "get_statut_module"),
              "get_statut_module supprimée (dead code)",
              "si False : la fonction est encore présente")
    ok = ok and r
    # Vérifie que check_elim_element est bien exportée
    r = check(hasattr(calculator, "check_elim_element"),
              "check_elim_element présente dans calculator",
              "si False : la fonction est manquante")
    ok = ok and r
    return ok


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    results = []
    results.append(("Imports / syntaxe",        test_imports()))
    results.append(("Valeurs 4A base données",   test_database_values()))
    results.append(("Régression 3A/IATD-SI",     test_regression_3A()))
    results.append(("Règle élim. niveau élément", test_elim_element_1A()))
    results.append(("Fallback seuil dynamique",  test_fallback_seuil()))

    print(f"\n{'═' * 60}")
    print("BILAN FINAL")
    print('═' * 60)
    all_ok = True
    for label, r in results:
        print(f"  {'✅' if r else '❌'}  {label}")
        all_ok = all_ok and r
    print()
    if all_ok:
        print("✅ TOUS LES TESTS PASSENT — prêt pour git push")
    else:
        print("❌ CERTAINS TESTS ÉCHOUENT — NE PAS pousser avant correction")
    sys.exit(0 if all_ok else 1)
