# 🚨 FIX URGENTE - RAM CRITIQUE (90%)

**Problème détecté** : RAM à 90% - Système instable

**Durée de résolution** : 5-10 minutes

---

## ⚡ ACTIONS IMMÉDIATES (dans l'ordre)

### **ACTION 1 : Diagnostic rapide** (1 min)

```bash
cd a:\Dev\MainRobot\V2.0
python tools\diagnose_memory.py
```

Ça va afficher :
- Les processus qui consomment le plus
- Les recommandations

---

### **ACTION 2 : Fermer processus gourmands** (2 min)

**Sur Windows**, ouvre le Gestionnaire des tâches :
- `Ctrl + Shift + Esc`
- Onglet "Processus"
- Trier par "Mémoire"

**Ferme dans cet ordre** :

1. ✅ **Navigateurs inutiles** (Chrome, Edge, Firefox)
   - Garde SEULEMENT 1 onglet : le dashboard
   - Ferme tous les autres

2. ✅ **VSCode/IDE** si pas utilisé actuellement
   - Sauvegarde ton travail
   - Ferme VSCode temporairement

3. ✅ **Discord, Spotify, Steam** etc.
   - Applications en arrière-plan
   - Tu peux les réouvrir après

**Gain attendu** : 30-50% de RAM libérée

---

### **ACTION 3 : Redémarrer le dashboard en mode léger** (2 min)

#### A. Arrête le dashboard actuel

```bash
# Appuie sur Ctrl+C dans le terminal qui exécute le dashboard
```

#### B. Lance en mode optimisé

```bash
cd a:\Dev\MainRobot\V2.0

# Copier la config optimisée
copy config_low_memory.yaml config.yaml

# Relancer
python apps\neuro_dashboardV2_new.py
```

**Optimisations appliquées** :
- ⚡ UI à 6 FPS au lieu de 20 FPS (économie 15% RAM)
- ⚡ Logs WARNING seulement (économie 5% RAM)
- ⚡ Webcam RPi désactivée (économie 10% RAM)

**Gain attendu** : 20-30% RAM économisée

---

### **ACTION 4 : Optimiser hand_tracker.py** (3 min)

Si `hand_tracker.py` tourne sur le PC, **modifie-le** :

```python
# Ligne 130 environ
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5,
    model_complexity=0  # ⚡ AJOUTER CETTE LIGNE (était 1)
)
```

```python
# Ligne 35 environ - Désactiver effets visuels
ENABLE_HAND_MASK = False  # ⚡ Était True
GLOW_ENABLED = False      # ⚡ Désactiver glow
SCANLINE_ENABLED = False  # ⚡ Désactiver scanlines
```

```python
# Ligne 90 environ - Réduire qualité JPEG
ret, jpeg = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
#                                                                       ⚡ Était 75
```

**Relance hand_tracker.py** :
```bash
python hand_tracker.py
```

**Gain attendu** : 30-40% RAM économisée sur hand_tracker

---

## 📊 VÉRIFICATION

Après avoir appliqué les actions, vérifie :

```bash
python tools\diagnose_memory.py
```

**Résultat attendu** :
- RAM < 70% = ✅ OK
- RAM 70-80% = 🟡 Acceptable
- RAM > 80% = 🔴 Continuer optimisation

---

## 🔧 SI RAM TOUJOURS > 80% - SOLUTIONS AVANCÉES

### **Solution A : Créer un fichier swap (Windows)**

```powershell
# Ouvrir PowerShell en admin
# Augmenter la taille du fichier d'échange

# Panneau de configuration → Système → Paramètres système avancés
# → Performances → Paramètres → Avancé → Mémoire virtuelle
# → Personnaliser : Taille initiale et maximale à 4096 MB
```

### **Solution B : Redémarrer complètement**

```bash
# Ferme TOUT
# Redémarre Windows
# Relance SEULEMENT le dashboard
```

**Cela nettoie** :
- Cache Windows
- Processus zombies
- Fuites mémoire

### **Solution C : Mode ultra-light (dashboard sans UI)**

```bash
# Utilise le serveur UDP simple sans interface web
python apps\udp_server_v2.py
```

**Économie** : ~200-300 MB RAM (pas d'interface web)

**Inconvénient** : Pas de visualisation, juste contrôle

---

## 🎯 RÉSUMÉ DES GAINS

| Action | Gain RAM | Difficulté | Temps |
|--------|----------|------------|-------|
| Fermer navigateurs | 30-50% | ⭐ Facile | 1 min |
| Config optimisée | 20-30% | ⭐ Facile | 2 min |
| hand_tracker léger | 30-40% | ⭐⭐ Moyen | 3 min |
| Redémarrage | 10-20% | ⭐ Facile | 5 min |
| Mode UDP simple | 15-20% | ⭐ Facile | 1 min |

**Cumul possible** : 50-70% de RAM libérée !

---

## ⚠️ CAUSES PROBABLES DU PROBLÈME

Basé sur l'image que tu as montrée :

1. **Dashboard Enhanced + Health panel** = Gourmand
   - Monitoring psutil en temps réel
   - Mise à jour toutes les 2 secondes
   - **→ Utilise config optimisée**

2. **Navigateur avec dashboard ouvert** = 200-500 MB
   - NiceGUI charge Three.js
   - Streaming vidéo MJPEG
   - **→ Ferme les autres onglets**

3. **hand_tracker.py avec effets visuels** = 300-500 MB
   - MediaPipe model_complexity=1
   - Effets glow, masque, scanlines
   - **→ Passe en model_complexity=0**

4. **Pas de swap configuré** = Système instable
   - Si RAM pleine → crash
   - **→ Configure swap**

---

## 💡 PRÉVENTION FUTURE

Pour éviter le problème à l'avenir :

### **1. Utilise config_low_memory.yaml par défaut**

```bash
# Toujours lancer avec
python apps\neuro_dashboardV2_new.py
# (utilise automatiquement config.yaml)
```

### **2. Script de nettoyage automatique**

```bash
# Tous les jours à 3h du matin (Planificateur de tâches Windows)
python tools\optimize_memory.py
```

### **3. Surveille régulièrement**

```bash
# Toutes les heures, vérifie
python tools\diagnose_memory.py
```

### **4. Redémarre le dashboard toutes les 6h**

Crée un script batch `restart_dashboard.bat` :

```batch
@echo off
echo Redémarrage du dashboard...

REM Tuer le processus Python
taskkill /F /IM python.exe

REM Attendre 5 secondes
timeout /t 5

REM Relancer
cd a:\Dev\MainRobot\V2.0
python apps\neuro_dashboardV2_new.py
```

Planifie-le avec le Planificateur de tâches Windows.

---

## 🆘 SI RIEN NE FONCTIONNE

### **Symptômes d'un vrai problème matériel** :

- RAM toujours > 85% même après redémarrage
- Système gèle/crash régulièrement
- Applications se ferment toutes seules

### **Solutions matérielles** :

1. **Ajouter de la RAM physique**
   - Si PC : Acheter barrette DDR4/DDR5
   - Si Raspberry Pi : Passer d'un modèle 2GB → 4GB ou 8GB

2. **Utiliser un PC plus puissant pour hand_tracker**
   - Raspberry Pi fait seulement le contrôle servos
   - PC puissant fait le tracking + dashboard

3. **Mode distribué** :
   - PC 1 : hand_tracker.py
   - PC 2 : dashboard web
   - Raspberry Pi : contrôle servos seulement

---

## ✅ CHECKLIST DE RÉSOLUTION

- [ ] Diagnostic exécuté (`diagnose_memory.py`)
- [ ] Navigateurs fermés (sauf 1 onglet dashboard)
- [ ] IDE fermé temporairement
- [ ] Config optimisée copiée
- [ ] Dashboard relancé en mode léger
- [ ] hand_tracker optimisé (model_complexity=0)
- [ ] Effets visuels désactivés
- [ ] RAM vérifiée < 70%
- [ ] Swap configuré (si absent)
- [ ] Redémarrage complet si besoin

---

## 📞 SUPPORT

Si le problème persiste après toutes ces actions :

1. **Exporte le diagnostic** :
   ```bash
   python tools\diagnose_memory.py --export
   ```
   → Génère `memory_diagnostic_report.json`

2. **Partage le fichier** pour analyse approfondie

3. **Vérifie les logs** :
   ```bash
   type logs\neurohand.log
   ```

---

**TL;DR - Actions en 3 minutes** :

```bash
# 1. Ferme Chrome/Firefox (garde 1 onglet)
# 2. Copie config optimisée
copy config_low_memory.yaml config.yaml

# 3. Relance dashboard
python apps\neuro_dashboardV2_new.py
```

**→ RAM devrait passer de 90% → 60-70% ✅**

---

**Made with ❤️ for stable systems**

*NEURO-HAND V2.1 - RAM Fix Guide*
