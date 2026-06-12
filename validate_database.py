"""
Script de validation de filieres_database.py
  Niveau 1 : vérifications automatiques (11 filières)
  Niveau 2 : tableaux lisibles  (IATD-SI, GE-DI, GM-CISM)
  Niveau 3 : re-scraping de contrôle (GE-DI, GIEO, GME24)

Exécution : python validate_database.py
"""

import os
import sys
import io
import re
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
load_dotenv()

# ─── imports projet ──────────────────────────────────────────────────────────
_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from filieres_database import FILIERES

FILIERES_CIBLES = [
    "GC24", "GE-DI", "GE-MCI", "GI-ILSI", "GIEO",
    "GIP24", "GM-CISM", "GM-IMS", "GM-MPF", "GME24", "IATD-SI",
]
NIVEAU2_FILIERES = ["IATD-SI", "GE-DI", "GM-CISM"]
NIVEAU3_FILIERES = ["GE-DI", "GIEO", "GME24"]

TOL = 0.01
COEF_MOD_TOTAL = 30.0

# ─── helpers ─────────────────────────────────────────────────────────────────

def sep(char="─", width=72):
    return char * width


def _near(a, b):
    return abs((a or 0) - (b or 0)) < TOL


def _check_html_garbage(text):
    return bool(re.search(r'[<>&]|&nbsp;|&#\d+;', text or ""))


# ═════════════════════════════════════════════════════════════════════════════
# NIVEAU 1 — Vérifications automatiques
# ═════════════════════════════════════════════════════════════════════════════

def niveau1():
    print("\n" + sep("═"))
    print("NIVEAU 1 — Vérifications automatiques (11 filières)")
    print(sep("═"))

    global_errors = []
    summary_rows  = []

    for filiere_code in FILIERES_CIBLES:
        fdata   = FILIERES.get(filiere_code, {})
        modules = fdata.get("modules", {})
        errors  = []

        # ── 1. Somme CoefMod ─────────────────────────────────────────────
        total_coef = sum(
            (m.get("coef_mod") or 0) for m in modules.values()
        )
        if abs(total_coef - COEF_MOD_TOTAL) > TOL:
            errors.append(
                f"[COEF_MOD] somme={total_coef:.2f} ≠ {COEF_MOD_TOTAL} "
                f"(delta={total_coef - COEF_MOD_TOTAL:+.2f})"
            )

        # ── 2. CoefCC + CoefEX == CoefEcrit ──────────────────────────────
        #    Relation réelle observée : CoefEcrit + CoefTP == CoefEelem
        #    On vérifie les deux et on signale chacune.
        for mod_code, mod in modules.items():
            for elem_code, el in mod.get("elements", {}).items():
                cc     = el.get("coef_cc")    or 0.0
                ex     = el.get("coef_ex")    or 0.0
                ecrit  = el.get("coef_ecrit") or 0.0
                tp     = el.get("coef_tp")    or 0.0
                elem   = el.get("coef_elem")  or 0.0

                # Check demandé : cc + ex == ecrit
                if not _near(cc + ex, ecrit):
                    errors.append(
                        f"[CC+EX≠ECRIT] {mod_code}/{elem_code} : "
                        f"cc={cc}+ex={ex}={cc+ex:.2f} ≠ ecrit={ecrit}"
                    )

                # Check structurel fiable : ecrit + tp == elem
                if not _near(ecrit + tp, elem):
                    errors.append(
                        f"[ECRIT+TP≠ELEM] {mod_code}/{elem_code} : "
                        f"ecrit={ecrit}+tp={tp}={ecrit+tp:.2f} ≠ elem={elem}"
                    )

        # ── 3. CoefEelem > 0 ─────────────────────────────────────────────
        for mod_code, mod in modules.items():
            for elem_code, el in mod.get("elements", {}).items():
                if (el.get("coef_elem") or 0) <= 0:
                    errors.append(
                        f"[COEF_ELEM<=0] {mod_code}/{elem_code} : "
                        f"coef_elem={el.get('coef_elem')}"
                    )

        # ── 4. Pas de code dupliqué ───────────────────────────────────────
        seen_codes = {}
        for mod_code, mod in modules.items():
            if mod_code in seen_codes:
                errors.append(f"[DOUBLON] CodeMod '{mod_code}' dupliqué")
            seen_codes[mod_code] = True
            for elem_code in mod.get("elements", {}):
                key = f"elem:{elem_code}"
                if key in seen_codes:
                    errors.append(
                        f"[DOUBLON] CodeElem '{elem_code}' dupliqué "
                        f"dans {filiere_code}"
                    )
                seen_codes[key] = True

        # ── 5. Noms non-vides / sans HTML résiduel ────────────────────────
        filiere_nom = fdata.get("nom_complet", "")
        if not filiere_nom or _check_html_garbage(filiere_nom):
            errors.append(f"[NOM_FILIERE] nom_complet suspect : '{filiere_nom}'")

        for mod_code, mod in modules.items():
            nom_mod = mod.get("nom", "")
            if not nom_mod:
                errors.append(f"[NOM_VIDE] module {mod_code} : nom vide")
            elif _check_html_garbage(nom_mod):
                errors.append(
                    f"[HTML_RESIDUEL] module {mod_code} : '{nom_mod[:50]}'"
                )
            for elem_code, el in mod.get("elements", {}).items():
                nom_el = el.get("nom", "")
                if not nom_el:
                    errors.append(
                        f"[NOM_VIDE] élément {mod_code}/{elem_code} : nom vide"
                    )
                elif _check_html_garbage(nom_el):
                    errors.append(
                        f"[HTML_RESIDUEL] {mod_code}/{elem_code} : '{nom_el[:50]}'"
                    )

        # ── Accumulation ─────────────────────────────────────────────────
        n_errors = len(errors)
        status   = "OK" if n_errors == 0 else f"{n_errors} erreur(s)"
        summary_rows.append((filiere_code, total_coef, n_modules(modules), status))
        global_errors.extend(
            [f"  [{filiere_code}] {e}" for e in errors]
        )

    # ── Tableau récapitulatif ─────────────────────────────────────────────
    print(f"\n{'Filière':<12} {'Somme CoefMod':>14} {'Modules':>8}  Résultat")
    print("  " + sep("-", 55))
    ok_count = 0
    for (code, total, n_mod, status) in summary_rows:
        marker = "OK " if status == "OK" else "!! "
        if status == "OK":
            ok_count += 1
        flag = "✓" if status == "OK" else "✗"
        print(f"  {code:<12} {total:>13.2f} {n_mod:>8}  {flag} {status}")

    print(f"\n  {ok_count}/11 filières sans erreur")

    if global_errors:
        print(f"\n  Détail des {len(global_errors)} anomalie(s) :")
        for e in global_errors:
            print(f"    {e}")
    else:
        print("\n  Aucune anomalie détectée.")

    return ok_count, global_errors


def n_modules(modules):
    return len(modules)


# ═════════════════════════════════════════════════════════════════════════════
# NIVEAU 2 — Tableaux lisibles
# ═════════════════════════════════════════════════════════════════════════════

def niveau2():
    print("\n" + sep("═"))
    print("NIVEAU 2 — Tableaux lisibles (IATD-SI, GE-DI, GM-CISM)")
    print(sep("═"))

    for filiere_code in NIVEAU2_FILIERES:
        fdata   = FILIERES.get(filiere_code, {})
        modules = fdata.get("modules", {})

        print(f"\n{'─'*72}")
        print(f"  Filière : {filiere_code}  ({len(modules)} modules)")
        print(f"{'─'*72}")

        # En-tête modules
        print(f"  {'CodeMod':<10} {'Intitulé':<40} {'CoefMod':>8} {'Seuil':>7} {'Elim':>6}")
        print(f"  {'-'*10} {'-'*40} {'-'*8} {'-'*7} {'-'*6}")

        for mod_code, mod in modules.items():
            nom_mod = (mod.get("nom") or "")[:40]
            coef    = mod.get("coef_mod") or ""
            seuil   = mod.get("seuil")   or ""
            elim    = mod.get("eliminatoire") or ""
            print(f"  {mod_code:<10} {nom_mod:<40} {str(coef):>8} {str(seuil):>7} {str(elim):>6}")

            # Éléments du module
            elements = mod.get("elements", {})
            if not elements:
                print(f"    (aucun élément)")
                continue

            print(f"    {'CodeElem':<10} {'Intitulé':<35} {'CC':>5} {'EX':>5} {'Ecrit':>7} {'TP':>5} {'Elem':>6}")
            print(f"    {'-'*10} {'-'*35} {'-'*5} {'-'*5} {'-'*7} {'-'*5} {'-'*6}")
            for elem_code, el in elements.items():
                nom_el = (el.get("nom") or "")[:35]
                cc     = el.get("coef_cc")    if el.get("coef_cc")    is not None else "?"
                ex     = el.get("coef_ex")    if el.get("coef_ex")    is not None else "?"
                ecrit  = el.get("coef_ecrit") if el.get("coef_ecrit") is not None else "?"
                tp     = el.get("coef_tp")    if el.get("coef_tp")    is not None else "?"
                elem   = el.get("coef_elem")  if el.get("coef_elem")  is not None else "?"
                print(
                    f"    {elem_code:<10} {nom_el:<35} "
                    f"{str(cc):>5} {str(ex):>5} {str(ecrit):>7} "
                    f"{str(tp):>5} {str(elem):>6}"
                )
            print()


# ═════════════════════════════════════════════════════════════════════════════
# NIVEAU 3 — Re-scraping de contrôle
# ═════════════════════════════════════════════════════════════════════════════

LOGIN_URL = "https://schoolapp.ensam-umi.ac.ma/schoolapp/login"
PLAN_URL  = "https://schoolapp.ensam-umi.ac.ma/schoolapp/plan-etudes-view/modules"


def _new_session():
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    return s


def _get_csrf(html):
    tag = BeautifulSoup(html, "html.parser").find("input", {"name": "_csrf"})
    return tag.get("value", "") if tag else ""


def _login(session, email, password):
    r = session.get(LOGIN_URL, timeout=15)
    csrf = _get_csrf(r.text)
    r2 = session.post(LOGIN_URL, data={
        "email": email, "password": password, "_csrf": csrf
    }, timeout=15)
    ok = "login" not in r2.url and not BeautifulSoup(r2.text, "html.parser").find("input", {"name": "_csrf"})
    return ok


def _float(s):
    s = (s or "").strip()
    try:
        return float(s.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def _fetch_and_parse(session, filiere_code):
    r = session.get(PLAN_URL, timeout=15)
    csrf = _get_csrf(r.text)
    r2 = session.post(PLAN_URL, data={
        "niveau": "3A", "filiere": filiere_code,
        "semestre": "S2", "_csrf": csrf
    }, timeout=20)
    r2.raise_for_status()
    return _parse(r2.text)


def _parse(html):
    soup = BeautifulSoup(html, "html.parser")
    main_table = soup.find("table", class_="table-striped")
    if not main_table:
        tables = soup.find_all("table")
        if not tables:
            return {}
        main_table = max(tables, key=lambda t: len(t.find_all("tr")))

    modules = {}
    current_mod = None
    current_key = None

    for row in main_table.find_all("tr"):
        cls   = " ".join(row.get("class", []))
        cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]

        if "clickable" in cls and len(cells) >= 8:
            current_key = cells[1]
            current_mod = {
                "nom":          cells[2],
                "coef_mod":     _float(cells[7]),
                "seuil":        _float(cells[8]) if len(cells) > 8 else None,
                "eliminatoire": _float(cells[9]) if len(cells) > 9 else None,
                "elements":     {},
            }
            modules[current_key] = current_mod

        elif ("table-warning" in cls or "table-info" in cls
              or any(c.startswith("collapse") for c in row.get("class", []))):
            continue

        elif current_mod is not None and len(cells) >= 9:
            code_e = cells[0]
            if not code_e or code_e in ("CodeElem", current_key, ""):
                continue
            if not re.match(r'^[A-Z]{1,6}[-]?[A-Z]{0,4}\d+$', code_e):
                continue
            current_mod["elements"][code_e] = {
                "nom":        cells[1],
                "coef_cc":    _float(cells[5]),
                "coef_ex":    _float(cells[6]),
                "coef_ecrit": _float(cells[7]),
                "coef_tp":    _float(cells[8]),
                "coef_elem":  _float(cells[9]) if len(cells) > 9 else None,
            }

    return modules


def _diff_modules(scraped, stored, filiere_code):
    diffs = []
    for mod_code, s_mod in scraped.items():
        if mod_code not in stored:
            diffs.append(f"  + module {mod_code} (dans scraped, absent de stored)")
            continue
        d_mod = stored[mod_code]
        for fld in ["coef_mod", "seuil", "eliminatoire"]:
            if not _near(s_mod.get(fld), d_mod.get(fld)):
                diffs.append(
                    f"  {mod_code}.{fld} : scraped={s_mod.get(fld)} "
                    f"stored={d_mod.get(fld)}"
                )
        for elem_code, s_el in s_mod.get("elements", {}).items():
            if elem_code not in d_mod.get("elements", {}):
                diffs.append(
                    f"  {mod_code}/{elem_code} absent de stored"
                )
                continue
            d_el = d_mod["elements"][elem_code]
            for ef in ["coef_cc", "coef_ex", "coef_ecrit", "coef_tp", "coef_elem"]:
                if not _near(s_el.get(ef), d_el.get(ef)):
                    diffs.append(
                        f"  {mod_code}/{elem_code}.{ef} : "
                        f"scraped={s_el.get(ef)} stored={d_el.get(ef)}"
                    )

    for mod_code in stored:
        if mod_code not in scraped:
            diffs.append(f"  - module {mod_code} (dans stored, absent de scraped)")

    return diffs


def _near(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) < TOL


def niveau3():
    print("\n" + sep("═"))
    print("NIVEAU 3 — Re-scraping de contrôle (GE-DI, GIEO, GME24)")
    print(sep("═"))

    email    = os.getenv("SCHOOL_EMAIL")
    password = os.getenv("SCHOOL_PASSWORD")
    if not email or not password:
        print("  [ERREUR] SCHOOL_EMAIL / SCHOOL_PASSWORD manquants dans .env")
        return 0

    session = _new_session()
    if not _login(session, email, password):
        print("  [ERREUR] Connexion échouée")
        return 0
    print("  [OK] Connecté")

    confirmed = 0
    for filiere_code in NIVEAU3_FILIERES:
        print(f"\n  Re-scraping {filiere_code}...", end="", flush=True)
        try:
            scraped = _fetch_and_parse(session, filiere_code)
            stored  = FILIERES.get(filiere_code, {}).get("modules", {})
            diffs   = _diff_modules(scraped, stored, filiere_code)
            if not diffs:
                print(f"  ✓ {filiere_code} : re-scraping identique")
                confirmed += 1
            else:
                print(f"  ✗ {filiere_code} : {len(diffs)} différence(s) :")
                for d in diffs:
                    print(f"      {d}")
        except Exception as e:
            print(f"  [ERREUR] {filiere_code} : {e}")
        time.sleep(2)

    return confirmed


# ═════════════════════════════════════════════════════════════════════════════
# RÉSULTAT FINAL
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print(sep("═"))
    print("Validation de filieres_database.py")
    print(sep("═"))

    ok1, errors1 = niveau1()
    niveau2()
    confirmed3   = niveau3()

    print("\n" + sep("═"))
    print("RÉSULTAT FINAL")
    print(sep("═"))
    print(f"  Niveau 1 : {ok1}/11 filières sans erreur")
    print(f"  Niveau 2 : tableaux affichés pour vérification manuelle")
    print(f"  Niveau 3 : {confirmed3}/3 filières confirmées identiques")

    all_ok = (ok1 == 11 and confirmed3 == 3)
    if all_ok:
        print("\n  ✓ Base de données fiable, prête pour /setup")
    else:
        print("\n  ✗ Anomalies détectées — liste ci-dessus à corriger avant /setup")
        if errors1:
            print(f"\n  Récapitulatif des erreurs Niveau 1 ({len(errors1)}) :")
            seen_filieres = {}
            for e in errors1:
                m = re.match(r'\s*\[([^\]]+)\]', e)
                f = m.group(1) if m else "?"
                seen_filieres[f] = seen_filieres.get(f, 0) + 1
            for f, cnt in sorted(seen_filieres.items()):
                print(f"    {f} : {cnt} erreur(s)")


if __name__ == "__main__":
    main()
