# 🎓 ENSAM Notes Bot

Surveille tes notes sur SchoolApp ENSAM-UMI et te notifie instantanément sur Telegram dès qu'une note est publiée — avec calcul automatique du minimum requis pour valider chaque module.

---


---

## 🔒 Confidentialité

- Tes identifiants restent **sur ton ordinateur** (ou ton propre serveur), dans un fichier `.env` local jamais partagé
- **Aucune donnée** n'est envoyée à un serveur tiers
- Les notifications passent par **ton propre bot Telegram**, créé et contrôlé par toi
- Le code est public : tu peux vérifier toi-même qu'aucune donnée n'est collectée

---

## ✨ Fonctionnalités

- 🔔 **Notification automatique** dès qu'une note est publiée sur SchoolApp
- 🧮 **Calcul du minimum requis** pour valider chaque module (examen final)
- 📊 **`/bilan`** — résumé complet de toutes tes notes en temps réel
- 🔵 **`/sim`** — simulateur interactif : teste différentes hypothèses d'examen
- 📡 **`/status`** — état du bot et heure de la dernière vérification
- 🔄 **Reconnexion automatique** si la session SchoolApp expire
- 💾 **Backup automatique** des données à chaque vérification
- 🎓 **1A, 2A, 3A, 4A** — toutes les années du cycle ingénieur supportées (S2)

---

## 🎓 Niveaux et filières supportés (Semestre 2)

| Niveau | Filières |
|---|---|
| **1A** | API-MPT |
| **2A** | API-MPT |
| **3A** | GC24 · GE-DI · GE-MCI · GI-ILSI · GIEO · GIP24 · GM-CISM · GM-IMS · GM-MPF · GME24 · IATD-SI |
| **4A** | GC24 · GE-DI · GE-MCI · GI-ILSI · GIEO · GIP24 · GM-CISM · GM-IMS · GM-MPF · GME24 · IATD-SI |

---

## 🚀 Installation

Voir **[INSTALLATION.md](INSTALLATION.md)** — guide pas à pas sans connaissances techniques requises (~15 minutes).

**En résumé :**
1. Télécharger le ZIP du projet
2. Créer un bot Telegram (via @BotFather, 2 min)
3. Double-clic sur `lancer.bat` — il gère tout automatiquement
4. Envoyer `/bilan` à ton bot pour vérifier

Pour faire tourner le bot 24/7 sans garder ton PC allumé, voir **[DEPLOIEMENT_24H.md](DEPLOIEMENT_24H.md)** (optionnel, ~30 min).

---

## 🛠️ Architecture technique

| Fichier | Rôle |
|---|---|
| `lancer.bat` | Point d'entrée unique : installe Python portable, lance setup ou le bot |
| `setup.py` | Assistant de configuration interactif (identifiants, token, filière) |
| `main.py` | Orchestration : boucle de surveillance + bot Telegram |
| `scraper.py` | Connexion à SchoolApp, extraction des notes |
| `comparator.py` | Détection des changements entre deux relevés |
| `calculator.py` | Calcul des moyennes et du minimum requis |
| `notifier.py` | Formatage et envoi des messages Telegram |
| `modules.py` | Chargement dynamique des coefficients selon le niveau et la filière |
| `filieres_database.py` | Base de données des coefficients — 1A/2A/3A/4A, générée par scraping |
| `sim_handler.py` | Logique de la commande `/sim` |
| `telegram_bot.py` | Gestion des commandes Telegram (`/bilan`, `/sim`, `/status`) |

---

## 🆘 Besoin d'aide ?

1. Consulte la **[FAQ dans INSTALLATION.md](INSTALLATION.md#️⃣-faq----problèmes-fréquents)** — la plupart des problèmes y sont couverts
2. Ouvre une **[Issue sur GitHub](https://github.com/Mohamedaminebelasri/ensam-notes-bot/issues)**
3. Précise : ta filière, l'étape concernée, et le message d'erreur exact (capture d'écran bienvenue)

---

## 📜 Licence

MIT — voir [LICENSE](LICENSE)

---

## 🙏 Contact

Créé par **Mohamed Amine Belasri** — ENSAM Meknès, promotion 2023–2028

Pour toute question ou demande d'aide à l'installation, contacte-moi directement.
