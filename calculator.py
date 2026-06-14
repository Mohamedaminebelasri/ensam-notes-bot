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

from modules import MODULES


def _parse(val):
    if val is None or val == "--":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _fill_sub(val, coef, substitute):
    """Returns None if coef=0, known val if present, substitute if unknown."""
    if coef == 0:
        return None
    return val if val is not None else substitute


def calc_moy_element(cc, ex, tp, coef_cc, coef_ex, coef_ecrit, coef_tp):
    """
    Formule 2 étapes :
      1) Note_écrit = (CC×coef_cc + EX×coef_ex) / den_disponible
      2) Moy_élém   = (Note_écrit×coef_ecrit + TP×coef_tp) / den2
    Seules les composantes non-None et de coef>0 entrent dans chaque étape.
    """
    D_e = coef_cc + coef_ex
    note_ecrit = None
    if D_e > 0:
        num_e, den_e = 0.0, 0.0
        for v_raw, c in [(cc, coef_cc), (ex, coef_ex)]:
            v = _parse(v_raw)
            if v is not None and c > 0:
                num_e += v * c
                den_e += c
        note_ecrit = num_e / den_e if den_e > 0 else None

    num, den = 0.0, 0.0
    if note_ecrit is not None:
        num += note_ecrit * coef_ecrit
        den += coef_ecrit
    tp_v = _parse(tp)
    if tp_v is not None and coef_tp > 0:
        num += tp_v * coef_tp
        den += coef_tp

    return round(num / den, 4) if den > 0 else None


def _eval_module_with_sub(notes_dict, module, substitute):
    """
    Moyenne du module en remplaçant tous les inconnus par substitute.
    Utilise moy_sr directement si disponible.
    """
    elements = module["elements"]
    num, den = 0.0, 0.0
    for code, ei in elements.items():
        note   = notes_dict.get(code, {})
        moy_sr = _parse(note.get("moy_sr"))
        if moy_sr is not None:
            moy = moy_sr
        else:
            moy = calc_moy_element(
                _fill_sub(note.get("cc"), ei["coef_cc"], substitute),
                _fill_sub(note.get("ex"), ei["coef_ex"], substitute),
                _fill_sub(note.get("tp"), ei["coef_tp"], substitute),
                ei["coef_cc"], ei["coef_ex"], ei["coef_ecrit"], ei["coef_tp"],
            )
        if moy is not None:
            num += moy * ei["coef_elem"]
            den += ei["coef_elem"]
    return num / den if den > 0 else None


def calc_moy_module(notes_dict, module_code):
    """Moyenne actuelle du module (notes partielles, sans substitution)."""
    module = MODULES.get(module_code)
    if not module:
        return None
    num, den = 0.0, 0.0
    for code, ei in module["elements"].items():
        note   = notes_dict.get(code, {})
        moy_sr = _parse(note.get("moy_sr"))
        if moy_sr is not None:
            moy = moy_sr
        else:
            moy = calc_moy_element(
                note.get("cc"), note.get("ex"), note.get("tp"),
                ei["coef_cc"], ei["coef_ex"], ei["coef_ecrit"], ei["coef_tp"],
            )
        if moy is not None:
            num += moy * ei["coef_elem"]
            den += ei["coef_elem"]
    return round(num / den, 4) if den > 0 else None


def calc_minimum_restant(notes_dict, module_code):
    """
    Minimum X tel que moy_module = seuil quand tous les inconnus = X.

    Approche symétrique : G(X) = A + B·X (linéaire car la formule 2 étapes
    est une suite de moyennes pondérées).
    On calcule G(0) et G(20) pour trouver A et B, puis X = (seuil − A) / B.
    """
    module = MODULES.get(module_code)
    if not module:
        return None

    seuil    = module["seuil"]
    elements = module["elements"]

    notes_manquantes = []
    for code, ei in elements.items():
        note = notes_dict.get(code, {})
        if note.get("moy_sr") is not None:
            continue
        for field, ck in [("cc", "coef_cc"), ("ex", "coef_ex"), ("tp", "coef_tp")]:
            if ei[ck] > 0 and note.get(field) is None:
                notes_manquantes.append(f"{field.upper()}_{code}")

    g0  = _eval_module_with_sub(notes_dict, module, 0.0)
    g20 = _eval_module_with_sub(notes_dict, module, 20.0)

    if g0 is None:
        return None

    A = g0
    B = ((g20 if g20 is not None else A) - A) / 20.0
    moy_max = round(A + B * 20.0, 2)

    if abs(B) < 1e-9:
        deja_valide = A >= seuil
        return {
            "minimum": None,
            "notes_manquantes": notes_manquantes,
            "impossible": not deja_valide,
            "deja_valide": deja_valide,
            "moy_max_possible": round(A, 2),
        }

    minimum = (seuil - A) / B
    return {
        "minimum": round(minimum, 2),
        "notes_manquantes": notes_manquantes,
        "impossible": minimum > 20,
        "deja_valide": minimum <= 0,
        "moy_max_possible": moy_max,
    }


def find_elim_element(notes_dict, module_code):
    """
    Retourne le nom (ei["nom"]) du premier élément dont Moy_élément est strictement
    < eliminatoire du module, ou None si aucun ne l'est.
    Les éléments sans aucune note (Moy_élément=None) sont ignorés.
    """
    module = MODULES.get(module_code)
    if not module:
        return None
    elim = module["eliminatoire"]
    for code, ei in module["elements"].items():
        note   = notes_dict.get(code, {})
        moy_sr = _parse(note.get("moy_sr"))
        if moy_sr is not None:
            moy = moy_sr
        else:
            moy = calc_moy_element(
                note.get("cc"), note.get("ex"), note.get("tp"),
                ei["coef_cc"], ei["coef_ex"], ei["coef_ecrit"], ei["coef_tp"],
            )
        if moy is not None and moy < elim:
            return ei["nom"]
    return None


def get_decision_finale(dec_site, moy_calculee, seuil=12.0, elim_element_name=None):
    """
    Retourne (decision_text, reason_text_ou_None).

    Deux résultats estimés seulement :
      "✅ Validé (estimé)"       — moy_module >= seuil, pas d'élément éliminatoire
      "❌ Non validé (rattrapage)" — sinon (moy < seuil OU élément éliminatoire)

    Si elim_element_name fourni, reason = "⚠️ Note éliminatoire dans : {nom}".
    Les décisions officielles VORD/NV du site sont retournées inchangées.
    """
    if dec_site in ("VORD", "NV"):
        text = "✅ Validé (officiel)" if dec_site == "VORD" else "❌ Non Validé (officiel)"
        return (text, None)
    if elim_element_name is not None:
        return (
            "❌ Non validé (rattrapage)",
            f"⚠️ Note éliminatoire dans : {elim_element_name}",
        )
    if moy_calculee is None:
        return ("⏳ En attente des notes", None)
    if moy_calculee >= seuil:
        return ("✅ Validé (estimé)", None)
    return ("❌ Non validé (rattrapage)", None)


def est_module_complet(notes_dict, module_code):
    """
    Retourne True si toutes les composantes requises (coef > 0) sont publiées
    pour chaque élément du module.
    Un élément avec moy_sr est considéré complet (rattrapage finalisé).
    """
    module = MODULES.get(module_code)
    if not module:
        return False
    for code, ei in module["elements"].items():
        note = notes_dict.get(code, {})
        if note.get("moy_sr") is not None:
            continue
        for field, ck in [("cc", "coef_cc"), ("ex", "coef_ex"), ("tp", "coef_tp")]:
            if ei[ck] > 0 and note.get(field) is None:
                return False
    return True


