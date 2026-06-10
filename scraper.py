import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

LOGIN_URL = "https://schoolapp.ensam-umi.ac.ma/schoolapp/login"
NOTES_URL = "https://schoolapp.ensam-umi.ac.ma/schoolapp/student/noteselem-encours"


def _parse_val(s):
    s = s.strip() if s else ""
    if s in ("--", "", "N/A"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def fetch_with_retry(session, url, method="get", data=None, max_retries=3):
    for attempt in range(max_retries):
        try:
            if method == "post":
                response = session.post(url, data=data, timeout=15)
            else:
                response = session.get(url, timeout=15)
            return response
        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"[SCRAPER] Tentative {attempt+1}/{max_retries} échouée, retry dans {wait}s...", flush=True)
                time.sleep(wait)
                continue
            raise


def _do_login(session, email, password):
    resp = fetch_with_retry(session, LOGIN_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    csrf_input = soup.find("input", {"name": "_csrf"})
    if not csrf_input:
        print("[SCRAPER] Token CSRF introuvable", flush=True)
        return False
    resp = fetch_with_retry(session, LOGIN_URL, method="post", data={
        "email": email,
        "password": password,
        "_csrf": csrf_input.get("value", ""),
    })
    resp.raise_for_status()
    soup_check = BeautifulSoup(resp.text, "html.parser")
    if "login" in resp.url or soup_check.find("input", {"name": "_csrf"}):
        print("[SCRAPER] Identifiants incorrects ou session non établie", flush=True)
        return False
    return True


def _is_session_expired(resp):
    if resp.status_code in (401, 403):
        return True
    if "login" in resp.url:
        return True
    soup = BeautifulSoup(resp.text, "html.parser")
    return soup.find("input", {"name": "_csrf"}) is not None


def _new_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    return session


def get_notes():
    email    = os.getenv("SCHOOL_EMAIL")
    password = os.getenv("SCHOOL_PASSWORD")

    if not email or not password:
        print("[ERREUR] SCHOOL_EMAIL ou SCHOOL_PASSWORD manquant dans .env", flush=True)
        return []

    for attempt in range(3):
        session = _new_session()
        try:
            if not _do_login(session, email, password):
                return []

            print("[OK] Connexion réussie", flush=True)
            resp = fetch_with_retry(session, NOTES_URL)
            resp.raise_for_status()

            if _is_session_expired(resp):
                print(f"[SCRAPER] Session expirée → reconnexion... ({attempt+1}/3)", flush=True)
                continue

            soup  = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table")
            if not table:
                print("[ERREUR] Aucun tableau de notes trouvé", flush=True)
                return []

            notes = []
            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 10:
                    notes.append({
                        "code":     cols[0].get_text(strip=True),
                        "cc":       _parse_val(cols[2].get_text()),
                        "ex":       _parse_val(cols[3].get_text()),
                        "tp":       _parse_val(cols[4].get_text()),
                        "moy_so":   _parse_val(cols[5].get_text()),
                        "rat":      _parse_val(cols[6].get_text()),
                        "moy_sr":   _parse_val(cols[7].get_text()),
                        "moy":      cols[8].get_text(strip=True),
                        "decision": cols[9].get_text(strip=True),
                    })
            return notes

        except requests.RequestException as e:
            print(f"[SCRAPER] Erreur réseau (tentative {attempt+1}/3) : {e}", flush=True)
            if attempt < 2:
                time.sleep(10 * (attempt + 1))
                continue
            raise

    raise Exception("3 tentatives de connexion échouées (session expirée à chaque fois)")


if __name__ == "__main__":
    notes = get_notes()
    if notes:
        print(f"\n{len(notes)} note(s) :\n")
        print(f"{'CODE':<10} {'CC':>6} {'EX':>6} {'TP':>6} {'MoySO':>7} {'RAT':>6} {'MoySR':>7} {'Moy':>7} {'Dec'}")
        print("-" * 72)
        for n in notes:
            def _f(v): return f"{v:.2f}" if v is not None else "--"
            print(f"{n['code']:<10} {_f(n['cc']):>6} {_f(n['ex']):>6} {_f(n['tp']):>6} "
                  f"{_f(n['moy_so']):>7} {_f(n['rat']):>6} {_f(n['moy_sr']):>7} "
                  f"{n['moy']:>7} {n['decision']}")
    else:
        print("Aucune note récupérée.")
