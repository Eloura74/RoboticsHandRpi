# 🚀 Guide de mise en ligne sur GitHub

Ce guide te guide pour pousser ton projet sur GitHub.

## 📋 Checklist avant le push

- [x] `.gitignore` créé
- [x] `requirements.txt` créé
- [x] `README.md` complet
- [x] Scripts d'installation créés
- [x] LICENSE ajoutée
- [ ] Vérifier les IPs dans les fichiers (à anonymiser si public)
- [ ] Tester que tout fonctionne

---

## 🔧 Préparation

### 1. Anonymiser les IPs (si repo public)

**Fichiers à vérifier :**

```bash
# hand_tracker.py
UDP_IP = "192.168.1.60"  # ← Mettre une IP exemple

# apps/neuro_dashboard.py
PC_IP = '192.168.1.10'  # ← Mettre une IP exemple
```

**Ajouter un commentaire :**
```python
# ⚠️ CONFIGURATION REQUISE : Changer cette IP avec celle de votre Raspberry Pi
UDP_IP = "192.168.1.60"  # Exemple, adapter à votre réseau
```

---

## 📤 Push sur GitHub

### Option 1 : Depuis le terminal (recommandé)

```bash
# 1. Se placer dans le dossier V2.0
cd /home/pi/robot/V2.0

# 2. Initialiser le repo git (si pas déjà fait)
git init

# 3. Ajouter tous les fichiers
git add .

# 4. Vérifier ce qui sera ajouté
git status

# 5. Premier commit
git commit -m "Initial commit - Robotic Hand V2.0 with Parallel Movements"

# 6. Ajouter le remote GitHub
git remote add origin https://github.com/Elora74/RoboticsHandRpi.git

# 7. Pousser sur GitHub
git branch -M main
git push -u origin main
```

### Option 2 : Si le repo existe déjà

```bash
cd /home/pi/robot/V2.0

# Ajouter le remote
git remote add origin https://github.com/Elora74/RoboticsHandRpi.git

# Pull d'abord (si fichiers existants sur GitHub)
git pull origin main --allow-unrelated-histories

# Push
git add .
git commit -m "Add V2.0 with parallel movements system"
git push -u origin main
```

---

## 🔑 Authentification GitHub

### Avec token personnel (recommandé)

1. Va sur GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Coche : `repo` (full control)
4. Copie le token généré

Lors du push :
```bash
Username: Elora74
Password: <colle ton token ici>
```

### Avec SSH (alternatif)

```bash
# Générer une clé SSH
ssh-keygen -t ed25519 -C "ton-email@example.com"

# Copier la clé publique
cat ~/.ssh/id_ed25519.pub

# Ajouter sur GitHub : Settings → SSH and GPG keys → New SSH key

# Utiliser l'URL SSH
git remote set-url origin git@github.com:Elora74/RoboticsHandRpi.git
```

---

## 📝 Structure finale du repo

```
RoboticsHandRpi/
├── .gitignore
├── LICENSE
├── README.md
├── MOUVEMENTS_FLUIDES.md
├── GITHUB_SETUP.md (ce fichier)
├── requirements.txt
├── requirements-rpi.txt
├── requirements-pc.txt
├── install_rpi.sh
├── install_pc.sh
├── install_pc.bat
├── hand_tracker.py
├── apps/
│   ├── __init__.py
│   ├── neuro_dashboard.py
│   ├── udp_server_v2.py
│   └── demo_parallel_movements.py
├── core/
│   ├── __init__.py
│   └── hand_controller.py
├── config/
│   └── servos_v2.json
└── tools/
    └── calibrate_servos.py
```

---

## ✅ Après le push

### 1. Vérifier sur GitHub

- Va sur https://github.com/Elora74/RoboticsHandRpi
- Vérifie que tous les fichiers sont présents
- Vérifie que le README.md s'affiche correctement

### 2. Améliorer le repo (optionnel)

**Ajouter une image de bannière :**
- Crée un dossier `docs/images/`
- Ajoute une photo de ta main robotique
- Ajoute dans le README : `![Banner](docs/images/banner.jpg)`

**Ajouter des badges :**
```markdown
[![Stars](https://img.shields.io/github/stars/Elora74/RoboticsHandRpi?style=social)](https://github.com/Elora74/RoboticsHandRpi)
[![Forks](https://img.shields.io/github/forks/Elora74/RoboticsHandRpi?style=social)](https://github.com/Elora74/RoboticsHandRpi)
```

**Activer GitHub Pages :**
- Settings → Pages
- Source : Deploy from a branch
- Branch : main → /docs

---

## 🎯 Commandes Git utiles

```bash
# Voir l'état
git status

# Voir l'historique
git log --oneline

# Ajouter des changements
git add .
git commit -m "Description du changement"
git push

# Créer une nouvelle branche
git checkout -b feature/nouvelle-fonctionnalite

# Voir les remotes
git remote -v

# Annuler le dernier commit (sans perdre les changements)
git reset --soft HEAD~1
```

---

## 🐛 Problèmes courants

### "fatal: not a git repository"
```bash
git init
```

### "fatal: remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/Elora74/RoboticsHandRpi.git
```

### "Permission denied (publickey)"
→ Utiliser HTTPS au lieu de SSH, ou configurer les clés SSH

### Fichier trop volumineux (>100MB)
```bash
# Ajouter au .gitignore
echo "fichier_volumineux.bin" >> .gitignore
git rm --cached fichier_volumineux.bin
git commit --amend
```

---

## 📱 Partage du projet

Une fois en ligne, partage le lien :

```
🤖 Robotic Hand V2.0
https://github.com/Elora74/RoboticsHandRpi

✨ Système de contrôle de main robotique avec tracking et mouvements parallèles fluides
```

---

**Bon courage ! 🚀**
