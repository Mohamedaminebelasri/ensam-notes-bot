# ☁️ Faire tourner ton bot 24/7 (gratuit, sans laisser ton PC allumé)

## Pourquoi ?

Si tu fermes ton PC, le bot s'arrête. Cette option le fait tourner en permanence, gratuitement, sur un serveur Oracle Cloud.

⏱️ **~30-45 minutes, une seule fois.**

---

## ⚠️ Prérequis

- Une **carte bancaire** (pour la vérification d'identité Oracle uniquement — **AUCUN prélèvement** sur l'offre gratuite "Always Free")
- Avoir déjà **testé le bot en local** avec succès (voir [INSTALLATION.md](INSTALLATION.md))

---

## Étape 1 — Créer un compte Oracle Cloud

1. Va sur **[cloud.oracle.com](https://cloud.oracle.com)** → clique sur **"Start for free"**
2. Remplis le formulaire (email, informations personnelles, carte bancaire pour vérification d'identité)
3. Choisis une **région proche** lors de l'inscription (ex : **France Central** pour Paris, ou une région Europe)
4. Confirme ton email et finalise la création du compte

> 💡 La carte bancaire sert uniquement à vérifier ton identité. L'offre "Always Free" ne génère aucun frais tant que tu n'actives pas de ressources payantes.

---

## Étape 2 — Créer une instance gratuite (VM)

1. Dans la console Oracle Cloud, va dans **Compute → Instances → "Create Instance"**

2. **Nom de l'instance** : donne-lui un nom (ex : `ensam-bot`)

3. **Image** : clique sur "Change image" → choisis **Ubuntu** (dernière version LTS disponible, ex : 24.04)

4. **Shape (configuration matérielle)** : clique sur "Change shape"
   - Sélectionne **Ampere** (processeur ARM)
   - Choisis la configuration **"Always Free"** — elle offre jusqu'à 4 OCPU / 24 Go RAM partageables entre plusieurs VMs
   - Pour un seul bot : **1 OCPU / 6 Go RAM** suffisent largement

5. **Clé SSH** : dans la section "Add SSH keys"
   - Clique sur **"Generate a key pair for me"**
   - Clique sur **"Save private key"** — télécharge le fichier `.key`
   - **⚠️ Garde ce fichier précieusement** — sans lui, tu ne pourras plus te connecter à la VM

6. Clique sur **"Create"** et attends ~2 minutes que la VM démarre

7. Sur la page de l'instance créée, **note l'adresse IP publique** (ex : `141.X.X.X`) — tu en auras besoin à chaque connexion

---

## Étape 3 — Se connecter à la VM (SSH)

Depuis ton PC, ouvre un **terminal** (PowerShell sur Windows, Terminal sur Mac/Linux) :

```bash
ssh -i chemin\vers\ta_cle.key ubuntu@TON_IP_PUBLIQUE
```

Remplace :
- `chemin\vers\ta_cle.key` → le chemin vers la clé téléchargée à l'étape 2 (ex : `C:\Users\Amine\Downloads\ma-cle.key`)
- `TON_IP_PUBLIQUE` → l'IP notée à l'étape 2

**Si tu obtiens "Permission denied (publickey)"** → sur Mac/Linux uniquement, restreins les droits du fichier clé :
```bash
chmod 400 ta_cle.key
```
Sur Windows, cette erreur indique généralement un mauvais chemin vers la clé.

---

## Étape 4 — Installer Python et les dépendances

Une fois connecté à la VM, exécute ces commandes :

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

---

## Étape 5 — Télécharger le projet

```bash
git clone https://github.com/Mohamedaminebelasri/ensam-notes-bot.git
cd ensam-notes-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Étape 6 — Configurer (comme en local)

```bash
python3 setup.py
```

L'assistant interactif te guidera exactement comme lors de la configuration locale :
- Identifiants SchoolApp (email + mot de passe)
- Token du bot Telegram
- Détection automatique de ton Chat ID
- Niveau (1A / 2A / 3A / 4A) et filière

> 💡 Si tu as déjà configuré le bot en local, tu peux directement copier le contenu de ton fichier `.env` local sur la VM au lieu de tout ressaisir.

---

## Étape 7 — Tester

```bash
python3 main.py --once
```

Tu devrais recevoir un message de bienvenue ou un résumé de tes notes sur Telegram. Si c'est le cas, passe à l'étape suivante.

---

## Étape 8 — Faire tourner 24/7 (systemd)

`systemd` est le gestionnaire de services Linux — il permet de lancer le bot automatiquement au démarrage et de le redémarrer en cas de crash.

**Créer le fichier de service :**

```bash
sudo nano /etc/systemd/system/ensam-bot.service
```

**Colle le contenu suivant** (remplace `/home/ubuntu/ensam-notes-bot` si le dossier est ailleurs) :

```ini
[Unit]
Description=ENSAM Notes Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ensam-notes-bot
ExecStart=/home/ubuntu/ensam-notes-bot/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Sauvegarde avec `Ctrl+O` → `Entrée`, puis quitte avec `Ctrl+X`.

**Activer et démarrer le service :**

```bash
sudo systemctl daemon-reload
sudo systemctl enable ensam-bot
sudo systemctl start ensam-bot
```

---

## Étape 9 — Vérifier que tout tourne

```bash
sudo systemctl status ensam-bot
```

Tu dois voir **`active (running)`** en vert.

Sur Telegram, envoie **`/status`** à ton bot — il doit répondre avec l'heure de la dernière vérification.

---

## 🔄 Pour reconfigurer plus tard

Si tu veux changer de filière, de niveau ou mettre à jour tes identifiants :

```bash
sudo systemctl stop ensam-bot
cd ~/ensam-notes-bot
source venv/bin/activate
python3 setup.py
sudo systemctl start ensam-bot
```

---

## 🆘 Dépannage

### "Permission denied (publickey)" à la connexion SSH
- Vérifie que le chemin vers la clé `.key` est correct
- Sur Mac/Linux : exécute `chmod 400 ta_cle.key` pour restreindre les permissions du fichier

### Le service ne démarre pas
Consulte les logs pour voir l'erreur précise :
```bash
sudo journalctl -u ensam-bot -n 50 --no-pager
```

### Le bot ne répond plus après redémarrage de la VM
Le service est normalement relancé automatiquement (`enable` à l'étape 8).
Vérifie son état :
```bash
sudo systemctl status ensam-bot
```
S'il est arrêté, relance-le :
```bash
sudo systemctl start ensam-bot
```

### La VM Oracle semble inaccessible
- Vérifie que ta VM est bien en état **"Running"** dans la console Oracle Cloud
- Les VMs "Always Free" ne s'éteignent pas toutes seules, mais vérifie la console en cas de doute

---

## 💡 Note

Cette étape est **optionnelle et avancée**. La version locale (`lancer.bat` / `lancer.sh`) fonctionne très bien pour commencer — tu reçois des notifications tant que ton PC est allumé et le bot en cours d'exécution.

Le déploiement sur Oracle Cloud est utile si tu veux des notifications 24/7, y compris la nuit ou quand ton PC est éteint.
