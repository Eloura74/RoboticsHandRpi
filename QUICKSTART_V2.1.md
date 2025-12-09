# ⚡ QUICKSTART V2.1

Guide ultra-rapide pour démarrer avec NEURO-HAND V2.1 Production Ready.

---

## 🚀 Démarrage rapide (3 minutes)

### Sur Raspberry Pi

```bash
# 1. Aller dans le dossier V2.1
cd ~/RoboticsHandRpi/V2.1

# 2. Activer l'environnement virtuel
source ../venv/bin/activate

# 3. Lancer le dashboard
python3 apps/neuro_dashboardV2_new.py
```

### Sur PC (tracking)

```bash
# 1. Activer le venv
cd A:\Dev\MainRobot\V2.0\V2.1
venv\Scripts\activate

# 2. Lancer le tracker
python hand_tracker.py
```

---

## 🆕 Nouvelles fonctionnalités V2.1

### 1. Tests automatisés

```bash
# Lancer tous les tests (23 tests)
pytest tests/ -v

# Avec couverture de code
pytest tests/ --cov=core --cov-report=html

# Ouvrir le rapport de couverture
# Windows: start htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
```

**Résultat attendu :**
```
====================== 23 passed in 2.45s ======================
```

---

### 2. Monitoring système

```bash
# Monitoring en temps réel
python3 tools/monitor_rpi.py

# Export JSON des métriques
python3 tools/monitor_rpi.py --json metrics.json
```

**Exemple de sortie :**
```
[12:34:56] CPU: 45.2% | RAM: 1.2GB/3.8GB (32%) | Temp: 52.3°C | Uptime: 2h15m
```

---

### 3. Vérification de l'intégrité

```bash
# Vérifier que V2.1 est correctement installé
python VERIFICATION_V2.1.py
```

**Résultat attendu :**
```
============================================================
✅ EXCELLENT
Vérifications réussies : 23/23 (100.0%)
============================================================
🎉 V2.1 est prêt pour production !
```

---

## 📋 Checklist de migration V2.0 → V2.1

### Avant de transférer sur RPi

✅ **Sur PC Windows :**
```cmd
cd A:\Dev\MainRobot\V2.0\V2.1

# 1. Vérifier l'intégrité
python VERIFICATION_V2.1.py

# 2. Vérifier les tests (optionnel, nécessite pytest)
# pytest tests/ -v

# 3. Vérifier qu'il n'y a pas d'import obsolète
findstr /s /i "dashboard_config" apps\*.py
# Doit retourner 0 résultat
```

### Transfert sur RPi

**Option 1 : SCP (recommandé)**
```bash
# Depuis PC
scp -r A:\Dev\MainRobot\V2.0\V2.1 pi@192.168.1.60:~/RoboticsHandRpi/
```

**Option 2 : Git**
```bash
# Sur PC
cd A:\Dev\MainRobot\V2.0\V2.1
git add .
git commit -m "V2.1 Production Ready"
git push origin v2.1

# Sur RPi
cd ~/RoboticsHandRpi
git pull origin v2.1
```

**Option 3 : Clé USB**
```bash
# Copier V2.1 sur clé USB
# Insérer la clé sur RPi
sudo mount /dev/sda1 /mnt
cp -r /mnt/V2.1 ~/RoboticsHandRpi/
```

### Après transfert sur RPi

```bash
cd ~/RoboticsHandRpi/V2.1

# 1. Vérifier l'intégrité
python3 VERIFICATION_V2.1.py

# 2. Activer venv
source ../venv/bin/activate

# 3. Vérifier la config
cat config.yaml

# 4. Lancer les tests (optionnel)
pytest tests/ -v

# 5. Lancer le dashboard
python3 apps/neuro_dashboardV2_new.py
```

---

## 🔧 Configuration rapide

### Éditer les IPs

**Sur RPi - `config.yaml` :**
```yaml
network:
  udp_ip: "0.0.0.0"          # Écoute sur toutes les interfaces
  udp_port: 5005
  mjpeg_url: "http://192.168.1.10:8090/cam.mjpg"  # ← IP de ton PC
```

**Sur PC - `hand_tracker.py` :**
```python
UDP_IP = "192.168.1.60"      # ← IP de ton RPi
UDP_PORT = 5005
STREAM_PORT = 8090
```

### Trouver les IPs rapidement

```bash
# Sur RPi
hostname -I | awk '{print $1}'

# Sur PC Windows
ipconfig | findstr "IPv4"

# Sur PC Linux/Mac
ip addr show | grep "inet " | grep -v 127.0.0.1
```

---

## 🛑 Arrêt propre

### Sur dashboard (via interface web)

1. Ouvrir `http://192.168.1.60:8080`
2. Cliquer sur **"STOP ALL"**
3. Fermer la page

### Via terminal

```bash
# Sur RPi, CTRL+C dans le terminal du dashboard
# Le système fait un shutdown propre des servos
```

---

## 🐛 Dépannage rapide

### Problème : Port déjà utilisé

```bash
# Trouver le processus
sudo lsof -i :5005

# Tuer le processus
sudo kill -9 <PID>
```

### Problème : PCA9685 non détecté

```bash
# Vérifier I2C
i2cdetect -y 1
# Doit afficher 0x40

# Réactiver I2C si besoin
sudo raspi-config
# Interface Options → I2C → Enable
sudo reboot
```

### Problème : Tests échouent

```bash
# Vérifier les dépendances
pip list | grep pytest

# Réinstaller pytest si besoin
pip install pytest pytest-cov pytest-mock
```

### Problème : Import error sur core

```bash
# Vérifier que __init__.py existe
ls -la core/__init__.py

# Si manquant, le recréer
cat > core/__init__.py << 'EOF'
from core.hand_controller import HandController
from core.config_loader import config, load_config
from core.logger import get_logger, logger

__all__ = ['HandController', 'config', 'load_config', 'get_logger', 'logger']
EOF
```

---

## 📚 Documentation complète

| Document | Description |
|----------|-------------|
| **README.md** | Guide principal du projet |
| **README_V2.1.md** | Nouveautés V2.1 + comparaison V2.0 |
| **CHANGELOG.md** | Historique complet des versions |
| **RESUME_MODIFICATIONS_V2.1.md** | Détail technique des modifications |
| **QUICKSTART_V2.1.md** | Ce guide (démarrage rapide) |

---

## 🎯 Commandes utiles

```bash
# Monitoring système
python3 tools/monitor_rpi.py

# Tests automatisés
pytest tests/ -v

# Vérification intégrité
python VERIFICATION_V2.1.py

# Calibration servos
python3 tools/calibrate_servos.py

# Dashboard principal
python3 apps/neuro_dashboardV2_new.py

# Serveur UDP simple (sans GUI)
python3 apps/udp_server_v2.py
```

---

## 🔗 Liens rapides

- **GitHub** : https://github.com/Elora74/RoboticsHandRpi
- **Issues** : https://github.com/Elora74/RoboticsHandRpi/issues

---

## ✅ Checklist de vérification finale

Avant de passer en production, vérifie :

- [ ] ✅ `python VERIFICATION_V2.1.py` retourne **100%**
- [ ] ✅ `pytest tests/ -v` passe **23 tests**
- [ ] ✅ `dashboard_config.py` **n'existe plus**
- [ ] ✅ Les IPs sont **correctement configurées**
- [ ] ✅ I2C fonctionne : `i2cdetect -y 1` affiche **0x40**
- [ ] ✅ Le dashboard s'ouvre sur `http://192.168.1.60:8080`
- [ ] ✅ Le streaming vidéo fonctionne
- [ ] ✅ Les servos bougent correctement

---

**V2.1 - Production Ready** 🚀

*3 minutes pour démarrer, une vie pour profiter !*
