import os as _os
from dotenv import load_dotenv as _load_dotenv

_load_dotenv()

# Données IATD-SI codées en dur : fallback si filieres_database.py est absent
_MODULES_IATD_SI = {
    "IA21": {
        "nom": "Techniques Avancées d'Apprentissage Automatique et Séries Chronologiques",
        "coef_mod": 5.0, "seuil": 12.0, "eliminatoire": 8.0,
        "elements": {
            "IA211": {"nom": "Advanced Machine Learning Techniques",
                      "coef_cc": 0.5, "coef_ex": 0.5, "coef_ecrit": 1.0,
                      "coef_tp": 0.0, "coef_elem": 1.0},
            "IA212": {"nom": "Advanced Time Series Analysis and Neural Networks",
                      "coef_cc": 0.5, "coef_ex": 0.5, "coef_ecrit": 1.0,
                      "coef_tp": 0.0, "coef_elem": 1.0},
        }
    },
    "IA22": {
        "nom": "Architecture Orientée Objet et Java Avancé",
        "coef_mod": 5.0, "seuil": 12.0, "eliminatoire": 8.0,
        "elements": {
            "IA221": {"nom": "Modélisation des Systèmes",
                      "coef_cc": 0.5, "coef_ex": 0.5, "coef_ecrit": 1.0,
                      "coef_tp": 0.0, "coef_elem": 1.0},
            "IA222": {"nom": "Conception Orientée Objet",
                      "coef_cc": 0.5, "coef_ex": 0.5, "coef_ecrit": 1.0,
                      "coef_tp": 0.0, "coef_elem": 1.0},
            "IA223": {"nom": "Java Expert",
                      "coef_cc": 0.5, "coef_ex": 0.5, "coef_ecrit": 1.0,
                      "coef_tp": 0.0, "coef_elem": 1.0},
        }
    },
    "IA23": {
        "nom": "Techniques d'IA pour la Vision Avancée et le Traitement du Langage Naturel",
        "coef_mod": 5.0, "seuil": 12.0, "eliminatoire": 8.0,
        "elements": {
            "IA231": {"nom": "Core Concepts and Techniques in Computer Vision",
                      "coef_cc": 0.0, "coef_ex": 1.0, "coef_ecrit": 1.0,
                      "coef_tp": 0.0, "coef_elem": 1.0},
            "IA232": {"nom": "Advanced Deep Learning for Computer Vision",
                      "coef_cc": 0.5, "coef_ex": 0.5, "coef_ecrit": 1.0,
                      "coef_tp": 0.0, "coef_elem": 1.0},
            "IA233": {"nom": "Advanced Deep Learning for NLP",
                      "coef_cc": 0.5, "coef_ex": 0.5, "coef_ecrit": 1.0,
                      "coef_tp": 0.0, "coef_elem": 1.0},
        }
    },
    "IA24": {
        "nom": "Modélisation Statistique et Recherche Opérationnelle pour Les Sciences de Données",
        "coef_mod": 5.0, "seuil": 12.0, "eliminatoire": 8.0,
        "elements": {
            "IA241": {"nom": "Probabilité et Tests Statistiques pour Data Science",
                      "coef_cc": 0.5, "coef_ex": 0.5, "coef_ecrit": 1.5,
                      "coef_tp": 0.0, "coef_elem": 1.5},
            "IA242": {"nom": "Recherche Opérationnelle",
                      "coef_cc": 0.3, "coef_ex": 0.7, "coef_ecrit": 1.0,
                      "coef_tp": 0.0, "coef_elem": 1.0},
        }
    },
    "LE2": {
        "nom": "Langues Etrangères (Anglais, Français)",
        "coef_mod": 3.0, "seuil": 12.0, "eliminatoire": 8.0,
        "elements": {
            "LE21": {"nom": "Langue Anglaise",
                     "coef_cc": 0.0, "coef_ex": 1.0, "coef_ecrit": 1.0,
                     "coef_tp": 1.0, "coef_elem": 2.0},
            "LE22": {"nom": "Langue Française",
                     "coef_cc": 0.0, "coef_ex": 1.0, "coef_ecrit": 1.0,
                     "coef_tp": 1.0, "coef_elem": 2.0},
        }
    },
    "PS2": {
        "nom": "Culture and Art Skills",
        "coef_mod": 3.0, "seuil": 12.0, "eliminatoire": 8.0,
        "elements": {
            "PS21": {"nom": "Arts",
                     "coef_cc": 0.0, "coef_ex": 1.0, "coef_ecrit": 1.0,
                     "coef_tp": 0.5, "coef_elem": 1.5},
            "PS22": {"nom": "Culture",
                     "coef_cc": 0.0, "coef_ex": 1.0, "coef_ecrit": 1.0,
                     "coef_tp": 0.5, "coef_elem": 1.5},
        }
    },
    "TC23": {
        "nom": "Mécanique des fluides et machines thermiques",
        "coef_mod": 4.0, "seuil": 12.0, "eliminatoire": 8.0,
        "elements": {
            "TC231": {"nom": "Mécanique des fluides",
                      "coef_cc": 0.3, "coef_ex": 0.7, "coef_ecrit": 1.5,
                      "coef_tp": 0.5, "coef_elem": 2.0},
            "TC232": {"nom": "Machines thermiques",
                      "coef_cc": 0.0, "coef_ex": 1.0, "coef_ecrit": 1.0,
                      "coef_tp": 0.0, "coef_elem": 1.0},
        }
    },
}


def _load_modules():
    filiere = _os.getenv("FILIERE", "IATD-SI")
    try:
        from filieres_database import FILIERES
        known = sorted(FILIERES.keys())
        if filiere not in FILIERES:
            print(f"❌ Filière '{filiere}' inconnue.", flush=True)
            print(f"   Filières disponibles : {known}", flush=True)
            raise SystemExit(1)
        mods = FILIERES[filiere]["modules"]
        print(f"[MODULES] Filière chargée : {filiere} ({len(mods)} modules)", flush=True)
        return mods
    except ImportError:
        if filiere != "IATD-SI":
            print(
                f"❌ filieres_database.py introuvable et filière demandée '{filiere}' ≠ IATD-SI.\n"
                f"   Lance explore_coefficients.py pour générer la base de données.",
                flush=True,
            )
            raise SystemExit(1)
        print("[MODULES] filieres_database.py absent — fallback IATD-SI (données intégrées)", flush=True)
        return _MODULES_IATD_SI


MODULES = _load_modules()
