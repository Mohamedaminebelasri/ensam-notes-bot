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

Ensuite, `setup.py` se lance automatiquement et te guide en 5 étapes :

**Étape 1/5 — Identifiants SchoolApp**
- Entre ton email et mot de passe SchoolApp
- *(Le mot de passe s'affiche à l'écran — assure-toi d'être seul)*
- Le bot teste la connexion immédiatement

**Étape 2/5 — Token du bot Telegram**
- Colle le token copié à l'Étape 2

**Étape 3/5 — Chat ID (détection automatique)**
- Le bot détecte automatiquement ton ID Telegram
- Il te demande simplement d'appuyer sur Entrée *(tu dois avoir envoyé "salut" à ton bot à l'Étape 2)*
- Ton ID est récupéré depuis l'API Telegram — aucune saisie manuelle

**Étape 4/5 — Choix de ton niveau**
- Entre 1 (1A), 2 (2A), 3 (3A) ou 4 (4A)

**Étape 5/5 — Choix de ta filière**
- Pour **1A et 2A** : filière `API-MPT` sélectionnée automatiquement (seule disponible)
- Pour **3A et 4A** : une liste numérotée de 1 à 11 s'affiche

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

## 🛠️ FAQ — Problèmes fréquents

### ❓ Windows affiche "L'éditeur n'a pas pu être vérifié"
C'est normal pour tout fichier `.bat` téléchargé depuis Internet — ce n'est pas un virus.
- Clique sur **"Informations complémentaires"** puis **"Exécuter quand même"**
- Si tu veux vérifier par toi-même : clique droit sur `lancer.bat` → **Modifier** pour lire le code

### ❓ BotFather dit "Sorry, this username is already taken" ou "invalid"
Le username est trop court ou déjà pris. Règles :
- Doit se terminer par `_bot`
- Au moins 5 caractères avant `_bot`
- Format recommandé : **`[prénom][4 chiffres]_bot`** (ex : `sara4821_bot`, `karim7392_bot`)

### ❓ "Identifiants refusés par le serveur"
- Vérifie ton **email SchoolApp** : c'est l'adresse avec laquelle tu te connectes sur [schoolapp.ensam-umi.ac.ma](https://schoolapp.ensam-umi.ac.ma), pas ton Gmail personnel
- Le mot de passe est affiché à l'écran — vérifie qu'il n'y a pas de faute de frappe
- Essaie de te connecter manuellement sur SchoolApp pour confirmer que tes identifiants fonctionnent

### ❓ "Aucun message reçu" après avoir envoyé "salut" à mon bot
- As-tu cherché **ton bot** par son username exact (celui donné par BotFather à l'Étape 2) ?
- Le message doit être envoyé **à ton bot**, pas à un contact ou groupe quelconque
- Renvoie un message, puis appuie sur Entrée dans le terminal pour réessayer

### ❓ "Conflict: terminated by other getUpdates request" / le bot ne répond plus
Une autre instance du bot tourne déjà avec ce token (ex : une fenêtre `lancer.bat` encore ouverte en arrière-plan).
- Ferme **toutes** les fenêtres du bot
- Attends 10 secondes
- Relance `lancer.bat`

### ❓ Des avertissements "WARNING: script ... not on PATH" s'affichent pendant l'installation
Ces avertissements sont **normaux** et sans impact — les dépendances sont bien installées. Ignore-les.

### ❓ Comment trouver ma filière exacte ?
Sur SchoolApp : **"Plan Etudes"** → ton année → **2ème Semestre**
Compare les codes de modules affichés (ex : `IA21`, `IA22`…) avec ceux dans **"Mes Notes"** — ils correspondent à une filière dans la liste.

### ❓ Le bot affiche "Filière inconnue" ou "Niveau inconnu"
Le fichier `.env` contient une valeur incorrecte pour `NIVEAU=` ou `FILIERE=`.
- Supprime `.env` et relance `lancer.bat` pour reconfigurer
- **1A / 2A** → filière `API-MPT` (sélectionnée automatiquement)
- **3A / 4A** → filière parmi : `GC24`, `GE-DI`, `GE-MCI`, `GI-ILSI`, `GIEO`, `GIP24`, `GM-CISM`, `GM-IMS`, `GM-MPF`, `GME24`, `IATD-SI`

### ❓ Je veux changer de filière, de niveau ou mettre à jour mes identifiants
- Supprime le fichier `.env` dans le dossier du projet
- Relance `lancer.bat` (Windows) ou `./lancer.sh` (Mac/Linux) — la configuration repart depuis le début

### ❓ Mon antivirus bloque lancer.bat
`lancer.bat` est un **script texte** (pas un `.exe` compilé) — tu peux lire son contenu intégralement.
- Clique droit → **Modifier** pour vérifier le code
- Le projet est open source : tout le code est visible sur [GitHub](https://github.com/Mohamedaminebelasri/ensam-notes-bot)
- Si ton antivirus bloque malgré tout, utilise `lancer.sh` dans Git Bash ou contacte-moi

### ❓ Le bot ne démarre plus / erreur au lancement
- Vérifie ta connexion internet (nécessaire à la première installation)
- **Windows :** supprime le dossier `runtime/` et relance `lancer.bat` pour réinstaller Python
- **Mac/Linux :** supprime le dossier `venv/` et relance `./lancer.sh`

### ❓ Le bot s'est arrêté sans message / crash silencieux
Le bot génère un fichier `crash.log` dans son dossier dès qu'une erreur inattendue se produit.
1. Ouvre le dossier du bot
2. Cherche le fichier `crash.log`
3. S'il contient du texte, **copie l'intégralité de son contenu**
4. Ouvre une [Issue sur GitHub](https://github.com/Mohamedaminebelasri/ensam-notes-bot/issues) et **colle le contenu du `crash.log`** dans ta description

> Sans ce fichier, il est très difficile de diagnostiquer un arrêt silencieux. C'est l'information la plus utile que tu puisses fournir.

---

## 🛠️ Développeurs / mode avancé

### Mode démo (`--demo`)

> **Note pour les contributeurs et testeurs** — cette section ne concerne pas les étudiants qui utilisent le bot pour leurs vraies notes.

Pour tester le mode démo (`python setup.py --demo`), utilise **TOUJOURS** un dossier **ET** un bot Telegram séparés de ta configuration réelle, pour éviter tout conflit ou écrasement.

**Pourquoi ?**
- `setup.py --demo` écrase le fichier `.env` et `notes.json` du dossier courant
- Si tu utilises le même bot Telegram que ta vraie config, les messages de démo se mélangent avec les vraies notifications
- En cas de fausse manip, tu pourrais écraser tes identifiants réels ou tes notes sauvegardées

**Procédure recommandée :**
1. Copie le projet dans un dossier séparé (ex : `ensam-notes-bot-demo/`)
2. Crée un second bot Telegram via @BotFather (`/newbot`) dédié à la démo
3. Lance `python setup.py --demo` dans le dossier copié avec le bot dédié
4. Ne jamais lancer `setup.py --demo` dans le dossier de ta vraie config

---

*Problème non listé ? Ouvre une [Issue sur GitHub](https://github.com/Mohamedaminebelasri/ensam-notes-bot/issues) en précisant ta filière, l'étape concernée et le message d'erreur exact.*
