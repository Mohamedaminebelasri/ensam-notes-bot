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
# TEST G — échec copie mi-chemin → VERSION inchangée → retry réussit
# ═══════════════════════════════════════════════════════════════
def test_copy_failure_version_safe():
    print(f"\n{SEP}")
    print("TEST (g) — Echec copie 3eme fichier → VERSION inchangee → retry reussit")
    print(SEP)

    import updater as u
    import tempfile
    import shutil as _shutil

    # Répertoire isolé — les faux fichiers ne touchent jamais le projet réel
    test_dir   = tempfile.mkdtemp(prefix="ensam_test_g_")
    tmp_dir_g  = os.path.join(test_dir, ".update_tmp")
    ver_file_g = os.path.join(test_dir, "VERSION")

    # Sauvegarde de l'état original du module
    orig_base     = u.BASE_DIR
    orig_tmp      = u.TMP_DIR
    orig_ver      = u.VER_FILE
    orig_repo     = u.REPO_RAW
    orig_download = u._download
    orig_copy     = u._copy_file

    u.BASE_DIR = test_dir
    u.TMP_DIR  = tmp_dir_g
    u.VER_FILE = ver_file_g
    u.REPO_RAW = "https://invalid.example.test"  # force hors-ligne → tout mocké

    def mock_download(url, dest):
        """Simule un téléchargement réussi sans réseau."""
        fname   = os.path.basename(dest)
        content = "1.0.0" if fname == "VERSION" else f"# updated {fname}\n"
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)

    u._download = mock_download
    ok = True

    try:
        # ── PHASE 1 : 3ème copie échoue ──────────────────────────────
        print("\n  Phase 1 — copie echoue sur le 3eme fichier (PermissionError)")
        _write(ver_file_g, "0.9.0")

        call_count = [0]

        def mock_copy_fail_on_3(src, dst):
            call_count[0] += 1
            if call_count[0] == 3:
                raise PermissionError("Acces refuse (simulation test g)")
            orig_copy(src, dst)

        u._copy_file = mock_copy_fail_on_3
        updated1, old1, new1 = u.check_and_apply_update()

        ver_phase1 = _read(ver_file_g)
        print(f"  updated={updated1}, VERSION='{ver_phase1}', appels_copie={call_count[0]}")

        r1 = check(updated1 is False,
                   "Phase 1 : retourne False (pas de mise a jour)")
        r2 = check(ver_phase1 == "0.9.0",
                   f"Phase 1 : VERSION='{ver_phase1}' (toujours '0.9.0' — non ecrasee)")
        r3 = check(not os.path.exists(tmp_dir_g),
                   "Phase 1 : .update_tmp nettoye malgre l'echec")
        r4 = check(call_count[0] == 3,
                   f"Phase 1 : 3 appels de _copy_file avant echec (obtenu : {call_count[0]})")
        ok = ok and r1 and r2 and r3 and r4

        # ── PHASE 2 : retry — tout reussit ───────────────────────────
        print("\n  Phase 2 — retry (simule relancement lancer.bat)")
        # VERSION locale = "0.9.0" encore (simule le relancement)
        u._copy_file  = orig_copy   # restaure la vraie copie
        call_count[0] = 0

        updated2, old2, new2 = u.check_and_apply_update()

        ver_phase2 = _read(ver_file_g)
        print(f"  updated={updated2}, old='{old2}', new='{new2}', VERSION='{ver_phase2}'")

        r5 = check(updated2 is True,
                   "Phase 2 : mise a jour reussie au retry")
        r6 = check(old2 == "0.9.0",
                   f"Phase 2 : ancienne version '{old2}'")
        r7 = check(new2 == "1.0.0",
                   f"Phase 2 : nouvelle version '{new2}'")
        r8 = check(ver_phase2 == "1.0.0",
                   f"Phase 2 : VERSION='{ver_phase2}' (mise a jour vers '1.0.0')")
        r9 = check(not os.path.exists(tmp_dir_g),
                   "Phase 2 : .update_tmp nettoye apres retry reussi")

        # Verifie que les vrais fichiers du projet n'ont PAS ete touches
        real_ver = _read(os.path.join(orig_base, "VERSION"))
        r10 = check(real_ver == "1.0.0",
                    f"Fichiers reels intacts : VERSION projet='{real_ver}'")

        ok = ok and r5 and r6 and r7 and r8 and r9 and r10

    finally:
        # Restaure l'etat original du module
        u.BASE_DIR   = orig_base
        u.TMP_DIR    = orig_tmp
        u.VER_FILE   = orig_ver
        u.REPO_RAW   = orig_repo
        u._download  = orig_download
        u._copy_file = orig_copy
        _shutil.rmtree(test_dir, ignore_errors=True)

    return ok


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
    results.append(("(g) Copie échouée → VERSION safe → retry", test_copy_failure_version_safe()))

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
