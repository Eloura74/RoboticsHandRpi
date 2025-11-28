# ⚡ Quick Start Guide

Guide de démarrage rapide en 5 minutes.

---

## 🎯 Installation Express

### Sur Raspberry Pi

```bash
cd ~
git clone https://github.com/Elora74/RoboticsHandRpi.git
cd RoboticsHandRpi/V2.0
bash install_rpi.sh
```

Suivre les instructions du script.

### Sur PC

**Windows :**
```bash
git clone https://github.com/Elora74/RoboticsHandRpi.git
cd RoboticsHandRpi\V2.0
install_pc.bat
```

**Linux/Mac :**
```bash
git clone https://github.com/Elora74/RoboticsHandRpi.git
cd RoboticsHandRpi/V2.0
bash install_pc.sh
```

---

## ⚙️ Configuration minimale

### 1. Sur PC - Éditer `hand_tracker.py`

```python
UDP_IP = "192.168.1.XX"  # ← Ton IP Raspberry Pi
```

Pour trouver l'IP du RPi :
```bash
# Sur le Raspberry Pi
hostname -I
```

### 2. Sur RPi - Éditer `apps/neuro_dashboard.py`

```python
PC_IP = '192.168.1.XX'  # ← Ton IP PC
```

Pour trouver l'IP du PC :
- Windows : `ipconfig`
- Linux/Mac : `ip addr show`

---

## 🚀 Lancement

### 1. Raspberry Pi

```bash
cd ~/RoboticsHandRpi/V2.0
source venv/bin/activate
python3 apps/neuro_dashboard.py
```

**⚠️ Ordre important :**
1. Main en position ouverte physiquement
2. Alimentation servos COUPÉE
3. Lancer le script
4. Attendre "servos au neutre"
5. Allumer l'alimentation servos

Puis ouvrir : `http://IP_DU_RPI:8080`

### 2. PC (Hand Tracking)

```bash
cd RoboticsHandRpi/V2.0
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
python3 hand_tracker.py
```

Garde ta main ouverte pendant 2-3 secondes pour la stabilisation.

---

## 🎮 Utilisation

1. **Dashboard Web** : `http://192.168.1.60:8080`
   - Métriques en temps réel
   - Contrôle manuel
   - Arrêt d'urgence

2. **Hand Tracking**
   - Main ouverte = servos ouverts
   - Main fermée = servos fermés
   - Fonctionne doigt par doigt

3. **STOP d'urgence**
   - Bouton rouge sur le dashboard
   - Ou `Ctrl+C` dans les terminaux

---

## 🔧 Test rapide sans tracking

```bash
# Sur Raspberry Pi
python3 apps/demo_parallel_movements.py
```

Menu interactif pour tester tous les mouvements.

---

## 📚 Documentation complète

- **Installation détaillée :** [README.md](README.md)
- **Mouvements parallèles :** [MOUVEMENTS_FLUIDES.md](MOUVEMENTS_FLUIDES.md)
- **Push sur GitHub :** [GITHUB_SETUP.md](GITHUB_SETUP.md)

---

**C'est parti ! 🚀**
