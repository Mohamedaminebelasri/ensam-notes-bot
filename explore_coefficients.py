"""
Script d'exploration pour construire la base de données des coefficients
de toutes les filières S2 (3ème Année) de l'ENSAM-UMI SchoolApp.

Structure réelle de la page plan-etudes-view/modules :
  POST  /schoolapp/plan-etudes-view/modules
  Body  niveau=3A & filiere=<CODE> & semestre=S2 & _csrf=<token>

  Table principale (class "table-striped display") :
    Ligne [clickable]       → module  : col[1]=CodeMod, col[2]=Intitule,
                                        col[7]=CoefMod, col[8]=Seuil, col[9]=Eliminatoire
    Ligne [table-warning]   → sous-en-tête éléments (ignorer)
    Ligne [collapse …]      → table embarquée redondante (ignorer)
    Ligne []                → élément : col[0]=CodeElem, col[1]=Intitule,
                                        col[5]=CoefCC, col[6]=CoefEX, col[7]=CoefEcrit,
                                        col[8]=CoefTP, col[9]=CoefEelem

Exécution : python explore_coefficients.py
"""

import os
import sys
import json
import time
import re
import io
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
load_dotenv()

LOGIN_URL   = "https://schoolapp.ensam-umi.ac.ma/schoolapp/login"
PLAN_URL    = "https://schoolapp.ensam-umi.ac.ma/schoolapp/plan-etudes-view/modules"

FILIERES_CIBLES = [
    "GC24", "GE-DI", "GE-MCI", "GI-ILSI", "GIEO",
    "GIP24", "GM-CISM", "GM-IMS", "GM-MPF", "GME24", "IATD-SI",
]

# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

def _new_session():
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    return s


def _get_csrf(html_or_soup):
    if isinstance(html_or_soup, str):
        html_or_soup = BeautifulSoup(html_or_soup, "html.parser")
    tag = html_or_soup.find("input", {"name": "_csrf"})
    return tag.get("value", "") if tag else ""


def login(session, email, password):
    r = session.get(LOGIN_URL, timeout=15)
    r.raise_for_status()
    csrf = _get_csrf(r.text)
    if not csrf:
        print("[ERREUR] CSRF introuvable sur la page de login")
        return False
    r2 = session.post(LOGIN_URL, data={
        "email": email, "password": password, "_csrf": csrf
    }, timeout=15)
    r2.raise_for_status()
    soup2 = BeautifulSoup(r2.text, "html.parser")
    if "login" in r2.url or soup2.find("input", {"name": "_csrf"}):
        print("[ERREUR] Identifiants incorrects")
        return False
    print("[OK] Connexion reussie")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Formulaire
# ─────────────────────────────────────────────────────────────────────────────

def get_csrf_from_plan_page(session):
    r = session.get(PLAN_URL, timeout=15)
    r.raise_for_status()
    return _get_csrf(r.text)


def fetch_filiere(session, filiere_code, niveau="3A", semestre="S2"):
    csrf = get_csrf_from_plan_page(session)
    data = {
        "niveau":   niveau,
        "filiere":  filiere_code,
        "semestre": semestre,
        "_csrf":    csrf,
    }
    r = session.post(PLAN_URL, data=data, timeout=20)
    r.raise_for_status()
    return r.text


# ─────────────────────────────────────────────────────────────────────────────
# Parsing
# ─────────────────────────────────────────────────────────────────────────────

def _f(s):
    """Convertit une string en float ou None."""
    s = (s or "").strip()
    if s in ("", "--", "N/A"):
        return None
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def parse_filiere_html(html):
    """
    Parse la page résultat de plan-etudes-view/modules.

    Structure attendue dans la table principale (class table-striped) :
      [clickable]     → ligne module
      [table-warning] → sous-en-tête éléments  (skip)
      [collapse ...]  → table redondante        (skip)
      []              → ligne élément
    """
    soup = BeautifulSoup(html, "html.parser")

    # Sélectionne la table principale (striped)
    main_table = soup.find("table", class_="table-striped")
    if main_table is None:
        # Fallback : prend la plus grande table
        tables = soup.find_all("table")
        if not tables:
            return {}
        main_table = max(tables, key=lambda t: len(t.find_all("tr")))

    modules = {}
    current_mod_code = None
    current_mod      = None

    for row in main_table.find_all("tr"):
        classes = row.get("class", [])
        cls     = " ".join(classes)

        # ── LIGNE MODULE ──────────────────────────────────────────────────
        if "clickable" in cls:
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            # Colonnes : [0]=bouton, [1]=CodeMod, [2]=Intitule, [3]=Descriptif,
            #            [4]=Niveau, [5]=Semestre, [6]=VHMOD,
            #            [7]=CoefMod, [8]=Seuil, [9]=Eliminatoire
            if len(cells) < 8:
                continue
            current_mod_code = cells[1]
            current_mod = {
                "nom":          cells[2],
                "coef_mod":     _f(cells[7]),
                "seuil":        _f(cells[8]) if len(cells) > 8 else None,
                "eliminatoire": _f(cells[9]) if len(cells) > 9 else None,
                "elements":     {},
            }
            modules[current_mod_code] = current_mod
            continue

        # ── LIGNES A IGNORER ─────────────────────────────────────────────
        if "table-warning" in cls or "table-info" in cls or cls.startswith("collapse"):
            continue
        # Lignes collapse contiennent des tables embarquées — déjà dans tables séparées
        if any(c.startswith("collapse") for c in classes):
            continue

        # ── LIGNE ELEMENT ─────────────────────────────────────────────────
        if current_mod is not None:
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) < 9:
                continue
            code_e = cells[0]
            # Vérifie que ce n'est pas un sous-header ou une ligne vide
            if not code_e or code_e in ("CodeElem", current_mod_code, ""):
                continue
            # Un code élément ressemble à : lettres + 3+ chiffres (IA211, TC231, LE21...)
            if not re.match(r'^[A-Z]{1,6}[-]?[A-Z]{0,4}\d+$', code_e):
                continue

            # Colonnes éléments : [0]=CodeElem, [1]=Intitule,
            #   [2]=VHCTD, [3]=VHTP, [4]=VHEVAL,
            #   [5]=CoefCC, [6]=CoefEX, [7]=CoefEcrit, [8]=CoefTP, [9]=CoefEelem
            current_mod["elements"][code_e] = {
                "nom":        cells[1],
                "coef_cc":    _f(cells[5]),
                "coef_ex":    _f(cells[6]),
                "coef_ecrit": _f(cells[7]),
                "coef_tp":    _f(cells[8]),
                "coef_elem":  _f(cells[9]) if len(cells) > 9 else None,
            }

    return modules


# ─────────────────────────────────────────────────────────────────────────────
# ÉTAPE 1 — Résumé formulaire
# ─────────────────────────────────────────────────────────────────────────────

def step1_summary(session):
    print("\n" + "="*70)
    print("ETAPE 1 -- Structure du formulaire plan-etudes-view")
    print("="*70)

    r = session.get(PLAN_URL, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    form = soup.find("form")
    action = form.get("action", PLAN_URL) if form else PLAN_URL
    method = (form.get("method", "post") if form else "post").upper()
    csrf = _get_csrf(soup)

    print(f"  Form   : {method} {action}")
    print(f"  CSRF   : ...{csrf[-16:] if csrf else 'introuvable'}")

    selects = soup.find_all("select")
    print(f"\n  {len(selects)} select(s) :")
    for sel in selects:
        name = sel.get("name") or sel.get("id", "?")
        opts = [(o.get("value",""), o.get_text(strip=True)) for o in sel.find_all("option")]
        print(f"    name='{name}' ({len(opts)} options) :")
        for v, lbl in opts[:5]:
            print(f"        '{v}' -> '{lbl}'")
        if len(opts) > 5:
            print(f"        ... +{len(opts)-5} autres")

    print("""
  RESUME FORMULAIRE :
    POST /schoolapp/plan-etudes-view/modules
    Body : niveau (1A..M2)  +  filiere (code exact)  +  semestre (S1/S2)  +  _csrf

  STRUCTURE TABLEAU RESULTAT :
    Table principale (table-striped) :
      [clickable]     -> module : col[1]=CodeMod, col[2]=Intitule,
                                  col[7]=CoefMod, col[8]=Seuil, col[9]=Eliminatoire
      [table-warning] -> sous-en-tete elements (skip)
      [collapse ..]   -> table imbriquee redondante (skip)
      []              -> element : col[0]=CodeElem, col[1]=Intitule,
                                   col[5]=CoefCC, col[6]=CoefEX, col[7]=CoefEcrit,
                                   col[8]=CoefTP, col[9]=CoefEelem
    + Tables separees (table-sm display) une par module avec les elements
      (meme donnees, on utilise la table principale)
    Tout est dans le HTML initial -- pas de chargement AJAX separe.
""")


# ─────────────────────────────────────────────────────────────────────────────
# ÉTAPE 2 — Test IATD-SI
# ─────────────────────────────────────────────────────────────────────────────

def step2_test_iatd_si(session):
    print("="*70)
    print("ETAPE 2 -- Test IATD-SI (3A, S2)")
    print("="*70)

    html = fetch_filiere(session, "IATD-SI")

    # Sauvegarde debug
    with open("debug_iatd_si_v2.html", "w", encoding="utf-8") as f:
        f.write(html)

    modules = parse_filiere_html(html)
    if not modules:
        print("[ERREUR] Aucun module parse -- voir debug_iatd_si_v2.html")
        return None

    print(f"  {len(modules)} modules trouves :\n")
    for code, mod in modules.items():
        print(f"  {code} : {mod['nom'][:55]}")
        print(f"         coef={mod['coef_mod']}  seuil={mod['seuil']}  elim={mod['eliminatoire']}")
        for ec, el in mod["elements"].items():
            print(f"    {ec} : cc={el['coef_cc']} ex={el['coef_ex']} "
                  f"ecrit={el['coef_ecrit']} tp={el['coef_tp']} elem={el['coef_elem']}")
        print()

    # JSON
    print("[JSON] (premier module) :")
    first = next(iter(modules.items()))
    print(json.dumps({first[0]: first[1]}, ensure_ascii=False, indent=2))

    # Comparaison avec modules.py
    _compare_with_modules_py(modules)

    return modules


def _compare_with_modules_py(scraped):
    try:
        _dir = os.path.dirname(os.path.abspath(__file__))
        if _dir not in sys.path:
            sys.path.insert(0, _dir)
        from modules import MODULES
    except ImportError:
        print("[COMP] modules.py introuvable, skip")
        return

    print("\n[COMP vs modules.py] :")
    ok = fail = 0
    for code, ref in MODULES.items():
        if code not in scraped:
            print(f"  MANQUANT : {code}")
            fail += 1
            continue
        sc   = scraped[code]
        diff = []
        for fld in ["coef_mod", "seuil", "eliminatoire"]:
            if ref.get(fld) != sc.get(fld):
                diff.append(f"{fld}: ref={ref.get(fld)} sc={sc.get(fld)}")
        for ec, er in ref["elements"].items():
            if ec not in sc["elements"]:
                diff.append(f"elem manquant: {ec}")
                continue
            se = sc["elements"][ec]
            for ef in ["coef_cc", "coef_ex", "coef_ecrit", "coef_tp", "coef_elem"]:
                if er.get(ef) != se.get(ef):
                    diff.append(f"{ec}.{ef}: ref={er.get(ef)} sc={se.get(ef)}")
        if diff:
            print(f"  DIFF {code}: {diff}")
            fail += 1
        else:
            print(f"  OK   {code}")
            ok += 1
    print(f"  Bilan : {ok} OK / {fail} diff sur {len(MODULES)} modules ref")


# ─────────────────────────────────────────────────────────────────────────────
# ÉTAPE 3 — Boucle toutes les filières
# ─────────────────────────────────────────────────────────────────────────────

def step3_scrape_all(session, iatd_modules):
    print("\n" + "="*70)
    print("ETAPE 3 -- Scraping de toutes les filieres 3A S2")
    print("="*70)

    all_data = {}

    for filiere_code in FILIERES_CIBLES:
        print(f"\n  [{filiere_code}]", end="", flush=True)

        # IATD-SI deja scrapee
        if filiere_code == "IATD-SI" and iatd_modules:
            all_data["IATD-SI"] = iatd_modules
            n_m = len(iatd_modules)
            n_e = sum(len(m["elements"]) for m in iatd_modules.values())
            print(f"  (cache) -> {n_m} modules, {n_e} elements")
            continue

        try:
            html = fetch_filiere(session, filiere_code)

            # Sauvegarde debug
            safe = filiere_code.replace("-", "_")
            with open(f"debug_{safe}.html", "w", encoding="utf-8") as f:
                f.write(html)

            modules = parse_filiere_html(html)
            all_data[filiere_code] = modules
            n_m = len(modules)
            n_e = sum(len(m["elements"]) for m in modules.values())
            print(f"  -> {n_m} modules, {n_e} elements")

        except Exception as e:
            print(f"  ERREUR: {e}")
            all_data[filiere_code] = {}

        time.sleep(2)

    return all_data


# ─────────────────────────────────────────────────────────────────────────────
# ÉTAPE 4 — Génération des fichiers
# ─────────────────────────────────────────────────────────────────────────────

def step4_generate(all_data):
    print("\n" + "="*70)
    print("ETAPE 4 -- Generation filieres_database.py / .json")
    print("="*70)

    filieres = {}
    for code in FILIERES_CIBLES:
        mods = all_data.get(code, {})
        filieres[code] = {
            "nom_complet": code,
            "modules":     mods,
        }

    # ── .py ──────────────────────────────────────────────────────────────────
    py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "filieres_database.py")
    with open(py_path, "w", encoding="utf-8") as f:
        f.write('"""\nBase de données des coefficients -- toutes filières 3A S2\nGénéré automatiquement par explore_coefficients.py\n"""\n\n')
        f.write("FILIERES = ")
        f.write(_to_py(filieres))
        f.write("\n")
    print(f"  Genere : {py_path}")

    # ── .json ────────────────────────────────────────────────────────────────
    json_path = py_path.replace(".py", ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(filieres, f, ensure_ascii=False, indent=2)
    print(f"  Genere : {json_path}")

    return filieres


def _to_py(obj, depth=0):
    """Sérialise récursivement en Python formaté."""
    pad  = "    " * depth
    pad1 = "    " * (depth + 1)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        items = []
        for k, v in obj.items():
            items.append(f"{pad1}{repr(k)}: {_to_py(v, depth+1)}")
        return "{\n" + ",\n".join(items) + ",\n" + pad + "}"
    if isinstance(obj, str):
        return repr(obj)
    if obj is None:
        return "None"
    return repr(obj)


# ─────────────────────────────────────────────────────────────────────────────
# ÉTAPE 5 — Vérification finale
# ─────────────────────────────────────────────────────────────────────────────

def step5_verify(filieres):
    print("\n" + "="*70)
    print("ETAPE 5 -- Verification finale")
    print("="*70)

    # A) IATD-SI vs modules.py
    print("\n[A] IATD-SI vs modules.py :")
    iatd_mods = filieres.get("IATD-SI", {}).get("modules", {})
    if iatd_mods:
        _compare_with_modules_py(iatd_mods)
    else:
        print("  IATD-SI absent ou vide")

    # B) Tableau récapitulatif
    print(f"\n[B] Recapitulatif par filiere :")
    print(f"  {'Filiere':<12} {'Modules':>8} {'Elements':>10}  Status")
    print("  " + "-"*50)
    for code in FILIERES_CIBLES:
        mods = filieres.get(code, {}).get("modules", {})
        n_m  = len(mods)
        n_e  = sum(len(m.get("elements", {})) for m in mods.values())
        if n_m == 0:
            status = "!!! 0 modules -- verifier"
        else:
            status = "OK"
        print(f"  {code:<12} {n_m:>8} {n_e:>10}  {status}")

    print("\n[DONE] filieres_database.py + filieres_database.json generes.")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("="*70)
    print("Exploration des coefficients -- ENSAM-UMI SchoolApp")
    print("="*70)

    email    = os.getenv("SCHOOL_EMAIL")
    password = os.getenv("SCHOOL_PASSWORD")
    if not email or not password:
        print("[ERREUR] SCHOOL_EMAIL ou SCHOOL_PASSWORD manquant dans .env")
        sys.exit(1)

    session = _new_session()
    if not login(session, email, password):
        sys.exit(1)

    step1_summary(session)

    iatd_modules = step2_test_iatd_si(session)
    if iatd_modules is None:
        print("\n[ARRET] Parsing Etape 2 echoue -- voir debug_iatd_si_v2.html")
        sys.exit(1)

    all_data  = step3_scrape_all(session, iatd_modules)
    filieres  = step4_generate(all_data)
    step5_verify(filieres)


if __name__ == "__main__":
    main()
