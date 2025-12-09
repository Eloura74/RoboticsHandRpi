# 🤖 Robotic Hand V2.1 - Production Ready System

Système de contrôle de main robotique avec tracking par vision, mouvements parallèles fluides, tests automatisés et monitoring.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Raspberry Pi](https://img.shields.io/badge/Platform-Raspberry%20Pi-red.svg)](https://www.raspberrypi.org/)
[![Tests](https://img.shields.io/badge/Tests-23%20passed-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-60%25-yellow.svg)](tests/)

## 📋 Table des matières

- [Caractéristiques](#-caractéristiques)
- [Architecture](#-architecture)
- [Matériel requis](#-matériel-requis)
- [Installation](#-installation)
  - [Sur Raspberry Pi](#1-installation-sur-raspberry-pi)
  - [Sur PC (tracking)](#2-installation-sur-pc-pour-hand-tracking)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Mouvements Parallèles](#-mouvements-parallèles)
- [Dépannage](#-dépannage)

---

## ✨ Caractéristiques

### 🆕 Nouveautés V2.1 : Production Ready
- **✅ Suite de tests complète** : 23 tests unitaires avec pytest
- **📊 Monitoring système** : Script de monitoring CPU/RAM/température
- **🛡️ Gestion d'erreurs robuste** : Exceptions typées + tracebacks
- **📝 Configuration unifiée** : Un seul `config.yaml` (zéro duplication)
- **📚 Documentation complète** : README_V2.1.md + CHANGELOG.md

### 🎯 Héritées de V2.0 : Mouvements Parallèles
- **Plusieurs servos bougent simultanément** → mouvement 74% plus rapide
- **Tracking fluide et naturel** grâce aux threads
- Tous les doigts peuvent s'ouvrir/fermer en même temps

### 🔒 Sécurité
- ✅ Aucun mouvement au démarrage (servos au neutre)
- ✅ Arrêt propre avec shutdown sécurisé
- ✅ STOP ALL d'urgence (arrête tous les mouvements)
- ✅ Watchdog de sécurité (perte de signal → ouverture automatique)
- ✅ Stabilisation au démarrage (main ouverte requise)

### 🌐 Interface Web
- Dashboard cyberpunk avec NiceGUI
- Streaming vidéo MJPEG en temps réel
- Métriques des servos en direct
- Contrôle manuel et arrêt d'urgence

### 🎮 Hand Tracking
- Détection de main avec MediaPipe
- Tracking précis de 5 doigts
- Seuils ajustables par doigt
- Stream vidéo annotée

---

## 🏗️ Architecture

```
V2.1/
├── core/                        # 🆕 Package modulaire
│   ├── __init__.py             # Exports propres
│   ├── hand_controller.py      # Contrôleur avec gestion d'erreurs robuste
│   ├── config_loader.py        # Loader de config unifié
│   └── logger.py               # Système de logging
├── apps/                        # Applications
│   ├── neuro_dashboardV2_new.py   # Interface web principale
│   ├── dashboard_ui.py         # Composants UI
│   ├── dashboard_network.py    # Threads réseau
│   └── udp_server_v2.py        # Serveur UDP simple (sans GUI)
├── tests/                       # 🆕 Tests automatisés
│   ├── conftest.py             # Fixtures pytest
│   ├── test_hand_controller.py # Tests HandController (12 tests)
│   └── test_config_loader.py   # Tests ConfigLoader (11 tests)
├── tools/                       # Outils
│   ├── monitor_rpi.py          # 🆕 Monitoring système
│   └── calibrate_servos.py     # Calibration servos
├── config/
│   └── servos_v2.json          # Configuration des servos
├── config.yaml                  # 🆕 Configuration unifiée
├── hand_tracker.py             # Script PC pour tracking (NON MODIFIÉ)
├── README_V2.1.md              # 🆕 Guide des nouveautés
└── CHANGELOG.md                # 🆕 Journal des modifications
```

### Communication
```
[PC avec webcam]                    [Raspberry Pi]
     |                                    |
hand_tracker.py ----UDP:5005----> neuro_dashboard.py
     |                                    |
  MJPEG:8090 <---------- Streaming vidéo |
                                          |
                                    HandController
                                          |
                                    PCA9685 (I2C)
                                          |
                                    4x Servos MG945
```

---

## 🛠️ Matériel requis

### Raspberry Pi (Main robotique)
- **Raspberry Pi 4** (2GB+ recommandé)
- **PCA9685** - Contrôleur PWM 16 canaux (I2C)
- **4x Servos MG945 360°** (ou équivalent)
- Alimentation **5V 3A minimum** pour les servos
- Connexion réseau (WiFi ou Ethernet)

### PC (Hand Tracking)
- **Webcam** USB ou intégrée
- **Python 3.9+**
- Même réseau local que le Raspberry Pi

### Câblage Raspberry Pi ↔ PCA9685
```
RPi Pin     →  PCA9685
GPIO 2 (SDA) → SDA
GPIO 3 (SCL) → SCL
GND          → GND
5V           → VCC (logique)

PCA9685      →  Servos
V+           → Alimentation externe 5V (3A+)
GND          → GND alimentation
Channel 0-3  → Signaux des 4 servos
```

---

## 📦 Installation

### 1. Installation sur Raspberry Pi

#### Prérequis système
```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer Python 3 et pip
sudo apt install python3 python3-pip python3-venv -y

# Activer I2C
sudo raspi-config
# Interface Options → I2C → Enable

# Redémarrer
sudo reboot
```

#### Cloner le projet
```bash
cd ~
git clone https://github.com/Elora74/RoboticsHandRpi.git
cd RoboticsHandRpi/V2.0
```

#### Créer l'environnement virtuel
```bash
# Créer le venv
python3 -m venv venv

# Activer
source venv/bin/activate

# Installer les dépendances Raspberry Pi
pip install --upgrade pip
pip install -r requirements-rpi.txt
```

#### Vérifier I2C
```bash
# Installer i2c-tools
sudo apt install i2c-tools -y

# Détecter le PCA9685 (doit afficher 0x40)
i2cdetect -y 1
```

---

### 2. Installation sur PC (pour hand tracking)

#### Windows
```bash
# Créer un dossier
cd Documents
git clone https://github.com/Elora74/RoboticsHandRpi.git
cd RoboticsHandRpi/V2.0

# Créer environnement virtuel
python -m venv venv
venv\Scripts\activate

# Installer dépendances PC
pip install --upgrade pip
pip install -r requirements-pc.txt
```

#### Linux/Mac
```bash
git clone https://github.com/Elora74/RoboticsHandRpi.git
cd RoboticsHandRpi/V2.0

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements-pc.txt
```

---

## ⚙️ Configuration

### 1. Configuration des IPs

**Sur le PC** - Éditer `hand_tracker.py` :
```python
UDP_IP = "192.168.1.60"  # ← IP de ton Raspberry Pi
UDP_PORT = 5005
STREAM_PORT = 8090
```

**Sur le Raspberry Pi** - Éditer `apps/neuro_dashboard.py` :
```python
PC_IP = '192.168.1.10'  # ← IP de ton PC
MJPEG_PORT = 8090
```

### 2. Trouver les IPs

**Raspberry Pi :**
```bash
hostname -I
```

**PC Windows :**
```bash
ipconfig
# Chercher "Adresse IPv4"
```

**PC Linux/Mac :**
```bash
ip addr show
# ou
ifconfig
```

### 3. Configuration des servos

Le fichier `config/servos_v2.json` contient les paramètres de chaque doigt :

```json
{
  "servos": {
    "index": {
      "channel": 2,          // Canal PCA9685 (0-15)
      "neutral": 0.350,      // Throttle neutre (arrêt)
      "dir_close": -1,       // Direction fermeture (1 ou -1)
      "speed_close": 0.5,    // Vitesse fermeture (0.0-1.0)
      "speed_open": 0.5,     // Vitesse ouverture
      "t_close": 0.850,      // Durée fermeture (secondes)
      "t_open": 0.72         // Durée ouverture
    }
  }
}
```

**Pour calibrer tes servos :**
```bash
cd ~/RoboticsHandRpi/V2.0
source venv/bin/activate
python3 tools/calibrate_servos.py
```

---

## 🚀 Utilisation

### Démarrage complet du système

#### 1. Sur le Raspberry Pi

**⚠️ IMPORTANT : Suivre cet ordre !**

```bash
cd ~/RoboticsHandRpi/V2.0
source venv/bin/activate

# ÉTAPE 1 : Main en position OUVERTE physiquement
# ÉTAPE 2 : Alimentation 5V des servos COUPÉE
# ÉTAPE 3 : Lancer le dashboard

python3 apps/neuro_dashboard.py
```

Puis :
1. Attends le message `[INFO] Les servos sont au NEUTRE`
2. **Allume l'alimentation 5V des servos**
3. Vérifie qu'aucun servo ne bouge
4. Ouvre le dashboard : `http://192.168.1.60:8080`

#### 2. Sur le PC (tracking)

```bash
cd RoboticsHandRpi/V2.0
source venv/bin/activate  # ou venv\Scripts\activate sur Windows

python3 hand_tracker.py
```

Le tracking démarre après stabilisation (main ouverte requise pendant 2-3 secondes).

---

### Mode démo (sans tracking)

Pour tester le système sans webcam :

```bash
# Sur Raspberry Pi
python3 apps/demo_parallel_movements.py
```

Menu interactif pour tester :
- Mouvements séquentiels vs parallèles
- Doigts individuels
- Comparaison de performance
- Arrêt d'urgence

---

### Mode serveur UDP simple (sans GUI)

```bash
python3 apps/udp_server_v2.py
```

Version minimaliste sans interface web, juste le contrôle UDP.

---

## ⚡ Mouvements Parallèles

### Utilisation dans le code

```python
from core.hand_controller import HandController

controller = HandController()

# NOUVEAU : Mouvements parallèles (par défaut)
controller.open_hand()          # Tous les doigts en même temps
controller.close_hand()         # Gain de 74% de vitesse !

# Doigts individuels en parallèle
controller.open_finger("index", parallel=True)
controller.close_finger("majeur", parallel=True)
# Les deux bougent simultanément !

# Ancien comportement (séquentiel)
controller.open_hand(parallel=False)
```

### Performances

| Action | Séquentiel | Parallèle | Gain |
|--------|-----------|-----------|------|
| `close_hand()` | ~3.3s | ~0.86s | **74%** |
| `open_hand()` | ~2.3s | ~0.75s | **67%** |

📖 **Documentation complète :** Voir [MOUVEMENTS_FLUIDES.md](MOUVEMENTS_FLUIDES.md)

---

## 🐛 Dépannage

### Problème : Port UDP déjà utilisé

**Symptôme :**
```
[FATAL] Impossible de lier le port 5005: [Errno 98] Address already in use
```

**Solution :**
```bash
# Trouver le processus
sudo lsof -i :5005

# Tuer le processus
sudo kill -9 <PID>

# Ou utiliser le kill automatique intégré (déjà dans le code)
```

---

### Problème : PCA9685 non détecté

**Symptôme :**
```
[ERROR] No I2C device at address 0x40
```

**Solutions :**
```bash
# 1. Vérifier que I2C est activé
sudo raspi-config
# Interface Options → I2C → Enable

# 2. Vérifier les connexions
i2cdetect -y 1

# 3. Vérifier les permissions
sudo usermod -aG i2c $USER
```

---

### Problème : Servos ne bougent pas

**Checklist :**
- [ ] Alimentation 5V branchée et allumée ?
- [ ] GND commun entre RPi et alimentation ?
- [ ] Câblage I2C correct (SDA/SCL) ?
- [ ] Le neutre est-il calibré dans `servos_v2.json` ?

**Test manuel :**
```bash
python3 tools/calibrate_servos.py
```

---

### Problème : Hand tracking ne démarre pas

**Symptôme :**
```
[ERROR] Caméra introuvable
```

**Solutions :**
```bash
# Windows : vérifier les autorisations caméra
# Paramètres → Confidentialité → Caméra

# Linux : vérifier les permissions
ls -l /dev/video*
sudo usermod -aG video $USER

# Tester avec OpenCV
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

---

### Problème : Streaming vidéo ne s'affiche pas

**Checklist :**
- [ ] Les deux machines sont sur le même réseau ?
- [ ] Les IPs sont correctement configurées ?
- [ ] Le firewall bloque-t-il le port 8090 ?

**Test :**
```bash
# Sur PC, vérifier que le serveur écoute
netstat -an | grep 8090

# Sur RPi, tester l'URL
curl http://PC_IP:8090/cam.mjpg
```

---

## 📚 Documentation supplémentaire

- **[MOUVEMENTS_FLUIDES.md](MOUVEMENTS_FLUIDES.md)** - Guide technique des mouvements parallèles
- **Calibration** - Utiliser `tools/calibrate_servos.py`
- **API** - Voir docstrings dans `core/hand_controller.py`

---

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésite pas à :
- Ouvrir une issue pour signaler un bug
- Proposer des améliorations
- Soumettre des pull requests

---

## 📝 Changelog

### V2.1 (2024-12) - Production Ready 🚀
- ✅ **23 tests unitaires** avec pytest (coverage 60%)
- 🛡️ **Gestion d'erreurs robuste** : Exceptions typées I2C vs bugs
- 📊 **Script de monitoring** : CPU, RAM, température avec export JSON
- 📝 **Configuration unifiée** : `dashboard_config.py` → `config.yaml`
- 📚 **Documentation complète** : README_V2.1.md + CHANGELOG.md
- 🐛 **Corrections** : Erreurs I2C récupérées gracieusement

### V2.0 (2024-11)
- ✨ **Mouvements parallèles** avec threads (gain 74%)
- ✨ Interface web NiceGUI cyberpunk
- ✨ Système de watchdog amélioré
- ✨ Stabilisation au démarrage
- 🔧 Refactoring complet du code
- 📖 Documentation complète

### V1.0 (2024-10)
- Version initiale avec mouvements séquentiels

---

## 📄 License

MIT License - Voir [LICENSE](LICENSE) pour plus de détails.

---

## 🙏 Remerciements

- **Adafruit** pour les librairies CircuitPython
- **Google MediaPipe** pour le hand tracking
- **NiceGUI** pour l'interface web

---

## 📞 Support

Pour toute question ou problème :
- **Issues GitHub** : [Ouvrir une issue](https://github.com/Elora74/RoboticsHandRpi/issues)
- **Documentation** : Lire les fichiers `.md` du projet

---

**Made with ❤️ by Elora74**
