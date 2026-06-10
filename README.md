# 🎓 ENSAM Notes Bot

Bot Telegram qui surveille automatiquement tes notes sur SchoolApp ENSAM et t'envoie une notification dès qu'une note change.

## ✨ Fonctionnalités

- 🔔 Notification automatique dès qu'une note est publiée
- 🧮 Calcul du minimum requis pour valider chaque module
- 📊 `/bilan` — résumé complet en direct
- 🔵 `/sim` — simulateur de notes interactif
- 📡 `/status` — état du bot
- 🔄 Reconnexion automatique si session expirée
- 💾 Backup automatique des données

## 🚀 Installation

1. Clone le repo :

```bash
git clone https://github.com/TON_USERNAME/ensam-notes-bot.git
cd ensam-notes-bot
```

2. Installe les dépendances :

```bash
pip install -r requirements.txt
```

3. Configure le `.env` :

```bash
cp .env.example .env
# Remplis avec tes vraies valeurs
```

4. Lance le bot :

```bash
python main.py
```

## ⚙️ Configuration `.env`

Copie `.env.example` en `.env` et remplis :

| Variable | Description |
|---|---|
| `SCHOOL_EMAIL` | Ton email SchoolApp ENSAM |
| `SCHOOL_PASSWORD` | Ton mot de passe SchoolApp |
| `TELEGRAM_TOKEN` | Token de ton bot (via [@BotFather](https://t.me/BotFather)) |
| `TELEGRAM_CHAT_ID` | Ton ID Telegram (via [@userinfobot](https://t.me/userinfobot)) |

## 🏗️ Structure

| Fichier | Rôle |
|---|---|
| `scraper.py` | Login + extraction des notes |
| `comparator.py` | Détection des changements |
| `calculator.py` | Calculs des moyennes |
| `notifier.py` | Messages Telegram |
| `modules.py` | Coefficients S2 ENSAM IATD-SI |
| `sim_handler.py` | Commande `/sim` interactive |
| `telegram_bot.py` | Commandes Telegram |
| `main.py` | Orchestration principale |

## ☁️ Déploiement 24/7

Compatible Oracle Cloud Free Tier (toujours gratuit) ou [Fly.io](https://fly.io) via le `Dockerfile` et `fly.toml` inclus.
