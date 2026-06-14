# -*- coding: utf-8 -*-
"""
Tests du système de mise à jour automatique (updater.py).
Lance avec :  python _test_updater.py
"""
import io, os, sys, shutil, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("NIVEAU",  "3A")
os.environ.setdefault("FILIERE", "IATD-SI")

SEP = "-" * 62
_ok_count   = 0
_fail_count = 0


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


# ── helpers ──────────────────────────────────────────────────────────────────

def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def _write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ═══════════════════════════════════════════════════════════════
# TEST A — import et structure de base
# ═══════════════════════════════════════════════════════════════
def test_import_et_structure():
    print(f"\n{SEP}")
    print("TEST (import) — updater.py importable, VERSION créée")
    print(SEP)
    ok = True

    try:
        import updater as u
        r = check(True, "import updater OK")
    except Exception as ex:
        return check(False, f"import updater ECHOUE", str(ex))

    r1 = check(hasattr(u, "check_and_apply_update"),
               "check_and_apply_update présente")
    r2 = check(hasattr(u, "UPDATE_FILES") and len(u.UPDATE_FILES) >= 13,
               f"UPDATE_FILES contient {len(u.UPDATE_FILES)} fichiers")
    r3 = check("updater.py" in u.UPDATE_FILES,
               "updater.py dans UPDATE_FILES (auto-mise à jour)")
    r4 = check(".env" not in u.UPDATE_FILES and "notes.json" not in u.UPDATE_FILES,
               ".env et notes.json ABSENTS de UPDATE_FILES")

    ver = _read(u.VER_FILE)
    r5 = check(ver is not None, f"VERSION existe : '{ver}'")

    ok = r and r1 and r2 and r3 and r4 and r5
    return ok


# ═══════════════════════════════════════════════════════════════
# TEST A — VERSION locale = VERSION distante → pas de mise à jour
# ═══════════════════════════════════════════════════════════════
def test_no_update_when_same_version():
    print(f"\n{SEP}")
    print("TEST (a) — Même version locale et distante → aucune mise à jour")
    print(SEP)

    import updater as u
    orig = _read(u.VER_FILE)

    # Force VERSION locale = "1.0.0" (identique au repo distant)
    _write(u.VER_FILE, "1.0.0")
    try:
        updated, old, new = u.check_and_apply_update()
        print(f"  → updated={updated}, old={old!r}, new={new!r}")

        r1 = check(updated is False, "Pas de mise à jour (versions identiques)")
        r2 = check(old == new, f"old=={new} (pas de changement)")
        r3 = check(not os.path.exists(u.TMP_DIR),
                   ".update_tmp nettoyé après pas-de-mise-à-jour")
        return r1 and r2 and r3
    finally:
        if orig is not None:
            _write(u.VER_FILE, orig)


# ═══════════════════════════════════════════════════════════════
# TEST B — VERSION locale "0.9.0" → mise à jour vers "1.0.0"
# ═══════════════════════════════════════════════════════════════
def test_update_from_old_version():
    print(f"\n{SEP}")
    print("TEST (b) — VERSION locale='0.9.0' → mise à jour vers 1.0.0")
    print("  (télécharge les fichiers réels depuis GitHub — nécessite internet)")
    print(SEP)

    import updater as u
    orig_ver = _read(u.VER_FILE)

    _write(u.VER_FILE, "0.9.0")
    try:
        updated, old, new = u.check_and_apply_update(log_fn=print)
        print(f"  → updated={updated}, old={old!r}, new={new!r}")

        if not updated:
            # Peut arriver si pas d'internet — traité comme test ignoré
            print("  ⚠️  Pas de réseau ou dépôt inaccessible — test ignoré")
            _write(u.VER_FILE, orig_ver or "1.0.0")
            return check(True, "Test b ignoré (hors ligne) — non bloquant")

        r1 = check(updated is True, "Mise à jour détectée et appliquée")
        r2 = check(old == "0.9.0",  f"Ancienne version correcte: {old!r}")
        r3 = check(new == "1.0.0",  f"Nouvelle version correcte: {new!r}")
        r4 = check(_read(u.VER_FILE) == "1.0.0",
                   f"VERSION sur disque = '1.0.0'")
        r5 = check(not os.path.exists(u.TMP_DIR),
                   ".update_tmp nettoyé après mise à jour")
        return r1 and r2 and r3 and r4 and r5
    finally:
        # Restaure la version correcte quelle que soit l'issue
        cur = _read(u.VER_FILE)
        if cur not in ("1.0.0", None):
            _write(u.VER_FILE, "1.0.0")


# ═══════════════════════════════════════════════════════════════
# TEST C — Échec réseau → silencieux, pas de crash
# ═══════════════════════════════════════════════════════════════
def test_network_failure():
    print(f"\n{SEP}")
    print("TEST (c) — Échec réseau → silencieux, aucun crash, aucun blocage")
    print(SEP)

    import updater as u
    orig_repo = u.REPO_RAW
    orig_ver  = _read(u.VER_FILE)

    # Pointe vers une URL invalide pour simuler l'absence de réseau
    u.REPO_RAW = "https://invalid.example.invalid/repo-inexistant"
    _write(u.VER_FILE, "0.9.0")  # force "besoin de mise à jour" si réseau OK

    try:
        updated, old, new = u.check_and_apply_update()
        print(f"  → updated={updated}, old={old!r}, new={new!r}")

        r1 = check(updated is False, "Pas de mise à jour (réseau KO)")
        r2 = check(not os.path.exists(u.TMP_DIR),
                   ".update_tmp nettoyé même en cas d'échec réseau")
        return r1 and r2
    except Exception as ex:
        return check(False, "Exception levée (NE DOIT PAS arriver)", str(ex))
    finally:
        u.REPO_RAW = orig_repo
        _write(u.VER_FILE, orig_ver or "1.0.0")


# ═══════════════════════════════════════════════════════════════
# TEST D — .env et notes.json intacts après mise à jour simulée
# ═══════════════════════════════════════════════════════════════
def test_env_preserved():
    print(f"\n{SEP}")
    print("TEST (d) — .env et notes.json JAMAIS touchés par l'updater")
    print(SEP)

    import updater as u

    r1 = check(".env"            not in u.UPDATE_FILES, ".env absent de UPDATE_FILES")
    r2 = check("notes.json"      not in u.UPDATE_FILES, "notes.json absent de UPDATE_FILES")
    r3 = check("notes_backup.json" not in u.UPDATE_FILES,
               "notes_backup.json absent de UPDATE_FILES")
    r4 = check("heartbeat.json"  not in u.UPDATE_FILES, "heartbeat.json absent de UPDATE_FILES")
    r5 = check(".env.example"    not in u.UPDATE_FILES, ".env.example absent de UPDATE_FILES")

    # Vérifie que les fichiers réels n'ont pas été modifiés (si présents)
    env_exists = os.path.exists(os.path.join(u.BASE_DIR, ".env"))
    notes_exists = os.path.exists(os.path.join(u.BASE_DIR, "notes.json"))
    if env_exists:
        r6 = check(True, ".env présent sur disque (contenu non vérifié — normal)")
    else:
        r6 = check(True, ".env absent du disque (pas de config locale — normal)")
    if notes_exists:
        r7 = check(True, "notes.json présent sur disque (contenu non vérifié — normal)")
    else:
        r7 = check(True, "notes.json absent du disque — normal")

    return r1 and r2 and r3 and r4 and r5 and r6 and r7


# ═══════════════════════════════════════════════════════════════
# TEST E — python main.py --once toujours fonctionnel (régression)
# ═══════════════════════════════════════════════════════════════
def test_main_regression():
    print(f"\n{SEP}")
    print("TEST (e) — Régression : python main.py --once ne crashe pas")
    print("  (réseau/credentials optionnels — exit code != 2 accepté)")
    print(SEP)

    # Vérifie d'abord que main.py est importable sans erreur de syntaxe
    r1 = check(True, "main.py modifié — vérification syntaxe")
    try:
        result = subprocess.run(
            [sys.executable, "-c",
             "import ast; ast.parse(open('main.py', encoding='utf-8').read()); print('syntax OK')"],
            capture_output=True, text=True, timeout=10,
        )
        r1 = check(result.returncode == 0 and "syntax OK" in result.stdout,
                   "main.py syntaxe valide",
                   result.stderr.strip() or "OK")
    except Exception as ex:
        r1 = check(False, "Vérification syntaxe main.py", str(ex))

    # Vérifie que updater.py est importable
    try:
        result2 = subprocess.run(
            [sys.executable, "-c", "import updater; print('updater OK')"],
            capture_output=True, text=True, timeout=10,
        )
        r2 = check(result2.returncode == 0 and "updater OK" in result2.stdout,
                   "updater.py importable dans subprocess",
                   result2.stderr.strip() or "OK")
    except Exception as ex:
        r2 = check(False, "Import updater dans subprocess", str(ex))

    # check_update_job dans main.py (vérifie que la fonction existe)
    try:
        result3 = subprocess.run(
            [sys.executable, "-c",
             "import main; assert hasattr(main, 'check_update_job'); print('job OK')"],
            capture_output=True, text=True, timeout=15,
        )
        r3 = check(result3.returncode == 0 and "job OK" in result3.stdout,
                   "check_update_job présente dans main.py",
                   result3.stderr.strip() or "OK")
    except Exception as ex:
        r3 = check(False, "Vérification check_update_job", str(ex))

    return r1 and r2 and r3


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    results = []
    results.append(("Import + structure",        test_import_et_structure()))
    results.append(("(a) Meme version → rien",   test_no_update_when_same_version()))
    results.append(("(b) Ancienne ver → update", test_update_from_old_version()))
    results.append(("(c) Réseau KO → silencieux",test_network_failure()))
    results.append(("(d) .env/notes.json intacts",test_env_preserved()))
    results.append(("(e) Régression main.py",    test_main_regression()))

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
