# 📦 Guide d'installation — ENSAM Notes Bot

> Aucune connaissance technique requise. Durée estimée : **15 minutes**.

---

## Étape 1 — Télécharger le projet

1. Va sur la page GitHub du projet :
   **https://github.com/Mohamedaminebelasri/ensam-notes-bot**

2. Clique sur le bouton vert **`<> Code`** → **`Download ZIP`**

3. Extrais le ZIP sur ton Bureau (ou n'importe quel dossier)

   > 💡 Évite les chemins avec des espaces ou des caractères spéciaux (ex : `Mes Documents` → préfère `Bureau` ou `C:\ENSAM-Bot\`)

---

## Étape 2 — Créer ton bot Telegram

> Si tu as déjà un bot Telegram configuré, passe à l'Étape 3.

1. Ouvre **Telegram** sur ton téléphone ou PC

2. Cherche **@BotFather** et clique dessus

3. Envoie la commande `/newbot`

4. BotFather va te demander :
   - **Un nom** pour ton bot (ex : `ENSAM Notes`)
   - **Un username** (doit finir par `_bot`) — format suggéré : `prenom` + 4 chiffres + `_bot`
     (ex : `amine1234_bot`)

5. BotFather te donne un **TOKEN** — une longue chaîne de caractères de la forme :
   ```
   8742499507:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   **Copie-le quelque part, tu en auras besoin à l'Étape 3.**

6. **Important** : cherche ton nouveau bot dans Telegram et **envoie-lui n'importe quel message** (ex : `salut`).
   Cela permet au bot de détecter automatiquement ton ID.

---

## Étape 3 — Lancer le bot

1. Va dans le dossier extrait à l'Étape 1

2. **Double-clique sur `lancer.bat`**

### ⚠️ Avertissement Windows "Éditeur inconnu"

Windows peut afficher un message de sécurité du type :
> *"Windows a protégé votre ordinateur — Éditeur inconnu"*

C'est **normal** pour tout fichier `.bat` téléchargé depuis Internet.
- Clique sur **"Informations complémentaires"**
- Puis clique sur **"Exécuter quand même"**

Le code est open source — tu peux vérifier son contenu en l'ouvrant avec le Bloc-notes.

---

### 🔧 Première installation (automatique)

Au premier lancement, `lancer.bat` va automatiquement :

| Étape | Ce qui se passe |
|---|---|
| `[1/4]` | Téléchargement de Python 3.12 (~11 Mo) depuis python.org |
| `[2/4]` | Extraction dans le dossier `runtime/` |
| `[3/4]` | Configuration de Python |
| `[4/4]` | Installation des dépendances (requests, telegram-bot, etc.) |

> ⏱️ Cette étape prend **1 à 2 minutes** selon ta connexion internet.
> Elle ne se produit **qu'une seule fois**.

---

### ⚙️ Configuration (assistant interactif)

Ensuite, `setup.py` se lance automatiquement et te guide en 4 étapes :

**Étape 1/4 — Identifiants SchoolApp**
- Entre ton email et mot de passe SchoolApp
- *(Le mot de passe s'affiche à l'écran — assure-toi d'être seul)*
- Le bot teste la connexion immédiatement

**Étape 2/4 — Token du bot Telegram**
- Colle le token copié à l'Étape 2

**Étape 3/4 — Chat ID (détection automatique)**
- Le bot détecte automatiquement ton ID Telegram
- Il te demande simplement d'appuyer sur Entrée *(tu dois avoir envoyé "salut" à ton bot à l'Étape 2)*
- Ton ID est récupéré depuis l'API Telegram — aucune saisie manuelle

**Étape 4/4 — Choix de ta filière**
- Une liste numérotée de 1 à 11 s'affiche
- Entre le numéro correspondant à ta filière (3ème Année, S2)

---

## Étape 4 — Vérification

Une fois la configuration terminée, `main.py` démarre automatiquement.

Envoie la commande **`/bilan`** à ton bot Telegram pour vérifier que tout fonctionne.

Tu devrais recevoir un résumé de tes notes actuelles.

> ✅ **C'est terminé !** À partir de maintenant, le bot tourne et te notifiera dès qu'une nouvelle note est publiée sur SchoolApp.

---

## ☁️ Faire tourner le bot 24/7

Pour recevoir des notifications même quand ton PC est éteint, tu peux déployer le bot sur un serveur cloud gratuit.

**Option recommandée : Oracle Cloud Free Tier**
- Serveur Linux gratuit à vie (pas de carte bancaire requise au-delà de la vérification d'identité)
- Le projet inclut un `Dockerfile` pour faciliter le déploiement

**Besoin d'aide ?** Contacte Mohamed Amine Belasri directement — il peut t'aider à configurer ton propre serveur.

---

## 💻 Tu es sur Mac ou Linux ?

Utilise **`lancer.sh`** au lieu de `lancer.bat`. La logique est identique : détection Python, installation des dépendances, configuration, démarrage du bot.

### Sur Mac

1. Ouvre le **Terminal** (Cmd+Espace → "Terminal")
2. Navigue jusqu'au dossier extrait :
   ```bash
   cd ~/Desktop/ensam-notes-bot
   ```
3. Lance le script :
   ```bash
   ./lancer.sh
   ```

> **Si tu obtiens "Permission refusée"**, rends le script exécutable d'abord :
> ```bash
> chmod +x lancer.sh
> ```

> **Si `python3` n'est pas trouvé** : installe-le via `brew install python3`
> (nécessite [Homebrew](https://brew.sh)) ou depuis [python.org](https://www.python.org/downloads/).

### Sur Linux

Même procédure dans un terminal :
```bash
cd ~/Bureau/ensam-notes-bot   # ou le dossier où tu as extrait le ZIP
chmod +x lancer.sh
./lancer.sh
```

> **Si `python3` n'est pas trouvé** :
> ```bash
> sudo apt install python3 python3-pip python3-venv   # Debian/Ubuntu
> sudo dnf install python3                             # Fedora/RHEL
> ```

### Différence avec Windows

Contrairement à `lancer.bat`, `lancer.sh` utilise un **environnement virtuel** (`venv/`) plutôt qu'un Python portable téléchargé — car Python est généralement déjà présent sur Mac/Linux.

---

## 🛠️ Dépannage

### Le bot ne démarre pas / erreur au lancement
- Vérifie ta connexion internet (nécessaire à la première installation)
- Supprime le dossier `runtime/` et relance `lancer.bat` pour réinstaller Python

### "Identifiants incorrects" alors que le mot de passe est bon
- Vérifie que tu utilises bien l'email de ton compte SchoolApp ENSAM (format `prenom.nom@edu.umi.ac.ma` ou email personnel selon ton inscription)
- Essaie de te connecter manuellement sur [schoolapp.ensam-umi.ac.ma](https://schoolapp.ensam-umi.ac.ma) pour confirmer

### "Aucun message reçu" à l'étape Chat ID
- Assure-toi d'avoir envoyé un message **à ton bot** (pas à un autre contact)
- Le bot doit être celui créé à l'Étape 2 (vérifie le username `@ton_bot_username`)
- Renvoie un message et réessaie

### Je veux changer de filière ou mettre à jour mes identifiants
- Supprime le fichier `.env` dans le dossier du projet
- Relance `lancer.bat` — la configuration repart depuis le début

### Les notifications ne viennent plus
- Envoie `/status` à ton bot pour vérifier qu'il tourne
- Si le bot est arrêté, relance `lancer.bat`

---

*Pour tout autre problème, contacte Mohamed Amine Belasri.*
