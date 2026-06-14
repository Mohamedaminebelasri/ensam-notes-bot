# -*- coding: utf-8 -*-
"""
Tests de validation — logique 2 categories + base de donnees 4A.
Lance avec :  python _test_fixes.py   (depuis le dossier du projet)
"""

import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("NIVEAU",  "3A")
os.environ.setdefault("FILIERE", "IATD-SI")

SEP = "-" * 62
_ok_count   = 0
_fail_count = 0

DEC_VALIDE    = "✅ Validé (estimé)"        # ✅ Validé (estimé)
DEC_NON_VALID = "❌ Non validé (rattrapage)"     # ❌ Non validé (rattrapage)
DEC_ATTENTE   = "⏳ En attente des notes"              # ⏳ En attente des notes
DEC_VORD      = "✅ Validé (officiel)"            # ✅ Validé (officiel)
DEC_NV        = "❌ Non Validé (officiel)"        # ❌ Non Validé (officiel)
REASON_PREFIX = "⚠️ Note éliminatoire dans : "  # ⚠️ Note éliminatoire dans :


def check(cond, label, detail=""):
    global _ok_count, _fail_count
    if cond:
        _ok_count += 1
        tag = "[PASS]"
    else:
        _fail_count += 1
        tag = "[FAIL]"
    print(f"  {tag}  {label}")
    if detail:
        print(f"         {detail}")
    return cond


# ═══════════════════════════════════════════════════════════════
# TESTS D/E/F — valeurs 4A dans la base de donnees
# ═══════════════════════════════════════════════════════════════
def test_database_4A():
    print(f"\n{SEP}")
    print("TEST (d/e/f) — Valeurs 4A dans filieres_database")
    print(SEP)
    from filieres_database import FILIERES
    mods_4a = FILIERES.get("4A", {})
    ok = True

    gi = mods_4a.get("GI-ILSI", {}).get("modules", {})
    for code in ["INFO41", "INFO42", "INFO43", "INFO44"]:
        m = gi.get(code, {})
        s, e = m.get("seuil"), m.get("eliminatoire")
        r = check(s == 12.0 and e == 8.0,
                  f"4A/GI-ILSI/{code}: seuil={s}, eliminatoire={e}")
        ok = ok and r

    cism = mods_4a.get("GM-CISM", {}).get("modules", {})
    m = cism.get("CISM41", {})
    s, e = m.get("seuil"), m.get("eliminatoire")
    r = check(s == 12.0 and e == 8.0,
              f"4A/GM-CISM/CISM41: seuil={s}, eliminatoire={e}",
              "eliminatoire etait 80.0 (typo)")
    ok = ok and r

    ia = mods_4a.get("IATD-SI", {}).get("modules", {})
    for code in ["IA41", "IA42", "IA43", "IA44", "IA45"]:
        m = ia.get(code, {})
        s, e = m.get("seuil"), m.get("eliminatoire")
        r = check(s == 12.0 and e == 8.0,
                  f"4A/IATD-SI/{code}: seuil={s}, eliminatoire={e}")
        ok = ok and r

    return ok


# ═══════════════════════════════════════════════════════════════
# TEST A — regression 3A/IATD-SI
# ═══════════════════════════════════════════════════════════════
def test_regression_3A():
    print(f"\n{SEP}")
    print("TEST (a) — Regression 3A/IATD-SI : 2 categories, aucun elem eliminatoire")
    print(SEP)
    import calculator as cm
    from modules import MODULES

    ok = True
    for mod_code, mod_info in MODULES.items():
        seuil = mod_info["seuil"]
        notes = {}
        for ecode, ei in mod_info["elements"].items():
            n = {"cc": None, "ex": None, "tp": None, "moy_sr": None, "decision": None}
            if ei["coef_cc"] > 0: n["cc"] = 14.0
            if ei["coef_ex"] > 0: n["ex"] = 14.0
            if ei["coef_tp"] > 0: n["tp"] = 14.0
            notes[ecode] = n

        elim_nom = cm.find_elim_element(notes, mod_code)
        moy      = cm.calc_moy_module(notes, mod_code)
        dec, rsn = cm.get_decision_finale(None, moy, seuil, elim_nom)

        r1 = check(elim_nom is None,
                   f"{mod_code}: aucun element eliminatoire (notes=14/20)",
                   f"elim_nom={elim_nom}")
        r2 = check(dec == DEC_VALIDE,
                   f"{mod_code}: decision='{dec}'",
                   f"attendu: '{DEC_VALIDE}'")
        r3 = check(rsn is None, f"{mod_code}: raison=None")
        ok = ok and r1 and r2 and r3

    # Sous-test: 9/20 (< seuil mais > elim) -> Non valide sans raison
    mod_code = next(iter(MODULES))
    mod_info = MODULES[mod_code]
    notes9 = {}
    for ecode, ei in mod_info["elements"].items():
        n = {"cc": None, "ex": None, "tp": None, "moy_sr": None, "decision": None}
        if ei["coef_cc"] > 0: n["cc"] = 9.0
        if ei["coef_ex"] > 0: n["ex"] = 9.0
        if ei["coef_tp"] > 0: n["tp"] = 9.0
        notes9[ecode] = n
    elim9    = cm.find_elim_element(notes9, mod_code)
    moy9     = cm.calc_moy_module(notes9, mod_code)
    dec9, r9 = cm.get_decision_finale(None, moy9, mod_info["seuil"], elim9)
    print(f"\n  Sous-test {mod_code} (notes=9/20): dec='{dec9}', raison={r9}")
    r4 = check(elim9 is None and dec9 == DEC_NON_VALID and r9 is None,
               "Rattrapage sans eliminatoire: dec correcte, raison=None",
               f"dec='{dec9}', elim_nom={elim9}, raison={r9}")
    ok = ok and r4

    return ok


# ═══════════════════════════════════════════════════════════════
# TEST B — element eliminatoire
# ═══════════════════════════════════════════════════════════════
def test_elim_element():
    print(f"\n{SEP}")
    print("TEST (b) — Cas eliminatoire au niveau element")
    print("  CAS 1: API22 (coef_elem 3.5/1.5)  — moy_module < seuil")
    print("  CAS 2: API24 (coef_elem egaux 2.5) — moy_module >= seuil (BUG corrige)")
    print(SEP)

    from filieres_database import FILIERES
    import calculator as cm

    mods_1a = FILIERES["1A"]["API-MPT"]["modules"]
    orig    = cm.MODULES
    ok      = True

    # ── CAS 1 : API22 ──────────────────────────────────────────
    print("\n  CAS 1 — API22 (Thermodynamique et statique des fluides)")
    mod22   = mods_1a["API22"]
    seuil22 = mod22["seuil"]      # 11.0
    elim22  = mod22["eliminatoire"]   # 7.0
    c221    = mod22["elements"]["API221"]["coef_elem"]    # 3.5
    c222    = mod22["elements"]["API222"]["coef_elem"]    # 1.5
    moy22   = (6.0 * c221 + 18.0 * c222) / (c221 + c222)    # 9.6

    notes22 = {
        "API221": {"cc": None, "ex": None, "tp": None, "moy_sr": 6.0,  "decision": None},
        "API222": {"cc": None, "ex": None, "tp": None, "moy_sr": 18.0, "decision": None},
    }
    cm.MODULES = {"API22": mod22}
    elim_nom22      = cm.find_elim_element(notes22, "API22")
    dec22, reason22 = cm.get_decision_finale(None, moy22, seuil22, elim_nom22)
    cm.MODULES = orig

    nom_attendu22 = mod22["elements"]["API221"]["nom"]   # "Thermodynamique"
    print(f"    API221 moy=6.0 (coef={c221}), API222 moy=18.0 (coef={c222})")
    print(f"    Moy_module={moy22:.4f}, seuil={seuil22}, elim={elim22}")
    print(f"    find_elim_element -> '{elim_nom22}'  (attendu: '{nom_attendu22}')")
    print(f"    decision='{dec22}'")
    print(f"    raison='{reason22}'")

    r1 = check(elim_nom22 == nom_attendu22,
               f"find_elim_element retourne nom correct",
               f"obtenu='{elim_nom22}', attendu='{nom_attendu22}'")
    r2 = check(dec22 == DEC_NON_VALID,
               f"decision='{dec22}'",
               f"attendu: '{DEC_NON_VALID}'")
    r3 = check(reason22 == REASON_PREFIX + nom_attendu22,
               f"raison='{reason22}'",
               f"attendu: '{REASON_PREFIX}{nom_attendu22}'")
    ok = r1 and r2 and r3

    # ── CAS 2 : API24 — moy_module >= seuil mais elim ─────────
    print("\n  CAS 2 — API24 (Automatisme et construction 2) — coef_elem egaux")
    mod24   = mods_1a["API24"]
    seuil24 = mod24["seuil"]
    elim24  = mod24["eliminatoire"]
    c241    = mod24["elements"]["API241"]["coef_elem"]    # 2.5
    c242    = mod24["elements"]["API242"]["coef_elem"]    # 2.5
    moy24   = (6.0 * c241 + 18.0 * c242) / (c241 + c242)    # 12.0

    notes24 = {
        "API241": {"cc": None, "ex": None, "tp": None, "moy_sr": 6.0,  "decision": None},
        "API242": {"cc": None, "ex": None, "tp": None, "moy_sr": 18.0, "decision": None},
    }
    cm.MODULES = {"API24": mod24}
    elim_nom24      = cm.find_elim_element(notes24, "API24")
    dec24, reason24 = cm.get_decision_finale(None, moy24, seuil24, elim_nom24)
    cm.MODULES = orig

    nom_attendu24 = mod24["elements"]["API241"]["nom"]   # "Automatisme"
    print(f"    API241 moy=6.0 (coef={c241}), API242 moy=18.0 (coef={c242})")
    print(f"    Moy_module={moy24:.4f} >= seuil={seuil24} (ancienne regle = Valide — BUG corrige)")
    print(f"    find_elim_element -> '{elim_nom24}'")
    print(f"    decision='{dec24}'")
    print(f"    raison='{reason24}'")

    r4 = check(moy24 >= seuil24,
               f"Moy_module={moy24:.2f} >= seuil={seuil24} (confirme le bug corrige)")
    r5 = check(elim_nom24 == nom_attendu24,
               f"find_elim_element -> '{elim_nom24}'",
               f"attendu: '{nom_attendu24}'")
    r6 = check(dec24 == DEC_NON_VALID,
               f"decision='{dec24}'",
               f"attendu: '{DEC_NON_VALID}'")
    r7 = check(reason24 == REASON_PREFIX + nom_attendu24,
               f"raison='{reason24}'",
               f"attendu: '{REASON_PREFIX}{nom_attendu24}'")
    ok = ok and r4 and r5 and r6 and r7

    # ── Affichage texte exact ───────────────────────────────────
    print("\n  MESSAGE EXACT affiche dans Telegram (CAS 1 API22) :")
    block = f"  \U0001f3c6 Décision : {dec22}"
    if reason22:
        block += f"\n     {reason22}"
    print(f"  {block}")

    print("\n  MESSAGE EXACT affiche dans Telegram (CAS 2 API24) :")
    block2 = f"  \U0001f3c6 Décision : {dec24}"
    if reason24:
        block2 += f"\n     {reason24}"
    print(f"  {block2}")

    return ok


# ═══════════════════════════════════════════════════════════════
# TEST C — sous le seuil SANS element eliminatoire
# ═══════════════════════════════════════════════════════════════
def test_sous_seuil_sans_elim():
    print(f"\n{SEP}")
    print("TEST (c) — Sous le seuil, aucun element eliminatoire")
    print("  Attendu: 'Non valide (rattrapage)' SANS raison supplementaire")
    print(SEP)

    from filieres_database import FILIERES
    import calculator as cm

    mods_1a = FILIERES["1A"]["API-MPT"]["modules"]
    orig    = cm.MODULES
    mod22   = mods_1a["API22"]

    # moy=9.0 partout : >= elim=7.0, < seuil=11.0
    notes = {
        "API221": {"cc": None, "ex": None, "tp": None, "moy_sr": 9.0, "decision": None},
        "API222": {"cc": None, "ex": None, "tp": None, "moy_sr": 9.0, "decision": None},
    }
    cm.MODULES = {"API22": mod22}
    elim_nom    = cm.find_elim_element(notes, "API22")
    moy         = cm.calc_moy_module(notes, "API22")
    dec, reason = cm.get_decision_finale(None, moy, mod22["seuil"], elim_nom)
    cm.MODULES = orig

    print(f"  API221=9.0, API222=9.0 -> moy={moy:.2f}")
    print(f"  seuil={mod22['seuil']}, eliminatoire={mod22['eliminatoire']}")
    print(f"  find_elim_element -> {elim_nom}  (attendu: None)")
    print(f"  decision='{dec}', raison={reason}")

    r1 = check(elim_nom is None,
               "Aucun element eliminatoire (9.0 >= elim=7.0)")
    r2 = check(dec == DEC_NON_VALID,
               f"decision='{dec}'",
               f"attendu: '{DEC_NON_VALID}'")
    r3 = check(reason is None,
               "raison=None (pas de ligne supplementaire)")
    return r1 and r2 and r3


# ═══════════════════════════════════════════════════════════════
# TEST — signature
# ═══════════════════════════════════════════════════════════════
def test_api_signature():
    print(f"\n{SEP}")
    print("TEST — Signature API et imports")
    print(SEP)
    ok = True

    for name in ["calculator", "notifier", "modules"]:
        try:
            __import__(name)
            r = check(True, f"import {name} OK")
        except Exception as ex:
            r = check(False, f"import {name} ECHOUE", str(ex))
        ok = ok and r

    import calculator as cm

    # get_decision_finale doit retourner un tuple (dec, raison)
    result = cm.get_decision_finale(None, 14.0, 12.0)
    r = check(isinstance(result, tuple) and len(result) == 2,
              f"get_decision_finale retourne un tuple de longueur 2",
              f"valeur={result}")
    ok = ok and r

    # find_elim_element presente
    r2 = check(hasattr(cm, "find_elim_element"), "find_elim_element presente")
    # check_elim_element absente
    r3 = check(not hasattr(cm, "check_elim_element"),
               "check_elim_element absente (remplacee)")
    ok = ok and r2 and r3

    # Cas officiel VORD
    dec_vord, rsn_vord = cm.get_decision_finale("VORD", 10.0, 12.0)
    r4 = check(dec_vord == DEC_VORD and rsn_vord is None,
               f"VORD -> '{dec_vord}', raison={rsn_vord}")
    # Cas officiel NV
    dec_nv, rsn_nv = cm.get_decision_finale("NV", 10.0, 12.0)
    r5 = check(dec_nv == DEC_NV and rsn_nv is None,
               f"NV   -> '{dec_nv}', raison={rsn_nv}")
    ok = ok and r4 and r5

    return ok


# ═══════════════════════════════════════════════════════════════
# TEST G — notification MoySR
# ═══════════════════════════════════════════════════════════════
def test_moysr_notification():
    print(f"\n{SEP}")
    print("TEST (g) — Notification MoySR (résultat officiel après rattrapage)")
    print("  IA211 moy_sr : None → 14.0")
    print(SEP)

    import comparator as comp
    import calculator as cm
    from notifier import _build_moysr_message, _find_module

    # 1. comparator.find_changes surveille bien moy_sr
    old = {"IA211": {"cc": 12.0, "ex": 10.5, "tp": None, "rat": None,
                     "moy_so": None, "moy_sr": None, "decision": None}}
    new = [{"code": "IA211", "cc": 12.0, "ex": 10.5, "tp": None, "rat": None,
             "moy_so": None, "moy_sr": 14.0, "decision": None}]
    changes = comp.find_changes(old, new)
    moysr_changes = [c for c in changes if c["type"] == "moy_sr"]
    r1 = check(len(moysr_changes) == 1 and moysr_changes[0]["nouvelle"] == 14.0,
               "find_changes detecte moy_sr None→14.0",
               f"changes={changes}")
    ok = r1

    # 2. Decision recalculée avec moy_sr court-circuité
    notes_dict = {
        "IA211": {"cc": 12.0, "ex": 10.5, "tp": None, "rat": None,
                  "moy_so": None, "moy_sr": 14.0, "decision": None},
        "IA212": {"cc": 14.5, "ex": 14.0, "tp": None, "rat": None,
                  "moy_so": None, "moy_sr": None, "decision": None},
    }

    # IA211 : moy_sr=14.0 court-circuite (>=8.0)
    # IA212 : calc = (14.5*0.5 + 14.0*0.5)/1.0 = 14.25 (>=8.0)
    # Moy_module IA21 = (14.0*1.0 + 14.25*1.0) / 2.0 = 14.125
    moy_ia21 = cm.calc_moy_module(notes_dict, "IA21")
    elim_nom  = cm.find_elim_element(notes_dict, "IA21")
    dec, rsn  = cm.get_decision_finale(None, moy_ia21, 12.0, elim_nom)

    print(f"\n  IA21 moy_module={moy_ia21:.4f}, elim_nom={elim_nom}")
    print(f"  decision='{dec}', raison={rsn}")

    r2 = check(abs(moy_ia21 - 14.125) < 1e-3,
               f"Moy_module IA21={moy_ia21:.4f} (attendu ~14.125)")
    r3 = check(elim_nom is None,
               "Aucun element eliminatoire (14.0 et 14.25 >= 8.0)")
    r4 = check(dec == DEC_VALIDE and rsn is None,
               f"Decision='{dec}'",
               f"attendu: '{DEC_VALIDE}'")
    ok = ok and r2 and r3 and r4

    # 3. Message exact généré par _build_moysr_message
    msg = _build_moysr_message("IA211", notes_dict)
    print(f"\n  MESSAGE EXACT _build_moysr_message(IA211) :")
    print("  " + msg.replace("\n", "\n  "))

    r5 = check("14.00/20" in msg, "Message contient 'Moyenne finale : 14.00/20'")
    r6 = check("IA21" in msg,     "Message contient le code module 'IA21'")
    r7 = check(DEC_VALIDE in msg, f"Message contient '{DEC_VALIDE}'")
    r8 = check("Advanced Machine Learning Techniques" in msg,
               "Message contient le nom de l'element IA211")
    ok = ok and r5 and r6 and r7 and r8

    # 4. Cas éliminatoire avec moy_sr : IA211 moy_sr=5.0 (<8.0 elim)
    print(f"\n  Sous-test : IA211 moy_sr=5.0 (< eliminatoire=8.0)")
    notes_elim = {
        "IA211": {"cc": None, "ex": None, "tp": None, "rat": None,
                  "moy_so": None, "moy_sr": 5.0, "decision": None},
        "IA212": {"cc": 14.5, "ex": 14.0, "tp": None, "rat": None,
                  "moy_so": None, "moy_sr": None, "decision": None},
    }
    msg_elim = _build_moysr_message("IA211", notes_elim)
    print("  " + msg_elim.replace("\n", "\n  "))

    r9 = check(DEC_NON_VALID in msg_elim,
               f"Cas elim : decision='{DEC_NON_VALID}' dans le message")
    r10 = check(REASON_PREFIX in msg_elim,
                "Cas elim : raison elinatoire presente dans le message")
    ok = ok and r9 and r10

    return ok


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    results = []
    results.append(("API signature + imports",          test_api_signature()))
    results.append(("Valeurs 4A base donnees (d/e/f)",  test_database_4A()))
    results.append(("Regression 3A/IATD-SI (a)",        test_regression_3A()))
    results.append(("Elim niveau element (b)",           test_elim_element()))
    results.append(("Sous seuil sans elim (c)",          test_sous_seuil_sans_elim()))
    results.append(("Notification MoySR (g)",            test_moysr_notification()))

    print(f"\n{'=' * 62}")
    print("BILAN FINAL")
    print('=' * 62)
    all_ok = True
    for label, r in results:
        print(f"  {'[OK]' if r else '[FAIL]'}  {label}")
        all_ok = all_ok and r
    print(f"\n  {_ok_count} PASS / {_fail_count} FAIL\n")
    if all_ok:
        print("TOUS LES TESTS PASSENT — pret pour git push")
    else:
        print("CERTAINS TESTS ECHOUENT — NE PAS pousser")
    sys.exit(0 if all_ok else 1)
