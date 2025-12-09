# 📋 PLAN D'ACTION - NEURO-HAND V2.0

## 🎯 Objectif

Sécuriser la base technique du projet pour garantir maintenabilité et évolutivité sur 2-3 ans.

---

## ⚡ PHASE 1 : URGENT (Semaine 1)

### 1.1 Tests unitaires (Priorité CRITIQUE)

**Durée estimée** : 1 journée  
**Fichiers à créer** :
- ✅ `tests/test_hand_controller.py` (CRÉÉ)
- `tests/test_config_loader.py`
- `tests/test_security.py`
- `tests/conftest.py` (fixtures pytest)

**Actions détaillées** :

```bash
# Installation dépendances tests
pip install pytest pytest-cov pytest-mock

# Création structure
mkdir -p tests
touch tests/__init__.py
touch tests/conftest.py

# Lancer tests
pytest tests/ -v --cov=core --cov=apps --cov-report=html

# Cible : >60% coverage sur core/
```

**Checklist** :
- [ ] test_hand_controller.py : 15 tests minimum
- [ ] test_config_loader.py : 8 tests minimum
- [ ] test_security.py : 6 tests (HMAC, rate limiting, validation)
- [ ] Coverage >60% sur core/
- [ ] Documentation sur lancement tests dans README.md

---

### 1.2 Unifier configuration (Priorité HAUTE)

**Durée estimée** : 2-3 heures  
**Objectif** : Supprimer `dashboard_config.py`, tout migrer vers `config.yaml`

**Actions** :

1. **Vérifier tous les imports de dashboard_config.py** :
```bash
grep -r "from apps.dashboard_config import" .
grep -r "import dashboard_config" .
```

2. **Remplacer imports** :
```python
# AVANT
from apps.dashboard_config import UDP_PORT, FINGERS, MJPEG_URL

# APRÈS
from core.config_loader import config
udp_port = config.network.udp_port
fingers = config.fingers
mjpeg_url = config.network.mjpeg_url
```

3. **Supprimer fichier** :
```bash
git rm apps/dashboard_config.py
```

4. **Tester le dashboard démarre correctement** :
```bash
python apps/neuro_dashboardV2_new.py
```

**Checklist** :
- [ ] Tous les imports migrés vers config_loader
- [ ] dashboard_config.py supprimé
- [ ] Dashboard démarre sans erreur
- [ ] Commit: "refactor: unify config, remove dashboard_config.py"

---

### 1.3 Gestion d'erreurs spécifiques

**Durée estimée** : 3 heures  
**Objectif** : Remplacer `except Exception:` par exceptions ciblées

**Fichiers à modifier** :
- `core/hand_controller.py` (lignes 136, 256, 330, 498)
- `apps/dashboard_network.py` (lignes 126, 176, 331)
- `hand_tracker.py` (lignes 101, 106, 117, 606)

**Pattern à suivre** :
```python
# AVANT
try:
    self.kit.continuous_servo[channel].throttle = value
except Exception as e:
    print(f"Erreur: {e}")

# APRÈS
try:
    self.kit.continuous_servo[channel].throttle = value
except (OSError, IOError) as e:
    logger.warning(f"Erreur I2C temporaire canal {channel}: {e}")
except (AttributeError, IndexError) as e:
    logger.critical(f"Bug critique canal {channel}: {e}", exc_info=True)
    raise
```

**Checklist** :
- [ ] core/hand_controller.py : exceptions spécifiques
- [ ] apps/dashboard_network.py : exceptions spécifiques
- [ ] hand_tracker.py : exceptions spécifiques
- [ ] Tous les logger.error ont exc_info=True
- [ ] Commit: "fix: replace broad exceptions with specific ones"

---

## 🔧 PHASE 2 : IMPORTANT (Semaine 2)

### 2.1 Refactorer hand_tracker.py

**Durée estimée** : 1 journée  
**Objectif** : Découper en modules tracking/, rendering/, network/

**Structure cible** :
```
tracking/
├── __init__.py
├── detector.py          # ~80 lignes - MediaPipe
├── mapper.py            # ~60 lignes - Landmarks → 0..1
├── stabilizer.py        # ~50 lignes - Startup stabilization
└── renderer.py          # ~180 lignes - Rendu visuel

network/
└── mjpeg_server.py      # ~100 lignes - Serveur HTTP

apps/
└── start_tracker.py     # ~120 lignes - Main loop
```

**Étapes** :

1. **Créer tracking/detector.py** :
```python
class HandDetector:
    def __init__(self, config):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(...)
    
    def detect(self, frame) -> Optional[HandDetection]:
        """Détecte main dans frame, retourne landmarks."""
        ...
```

2. **Créer tracking/mapper.py** :
```python
class FingerMapper:
    def map(self, landmarks) -> Dict[str, float]:
        """Convertit landmarks en valeurs 0..1 par doigt."""
        ...
```

3. **Créer tracking/renderer.py** :
```python
class HandRenderer:
    def render(self, frame, landmarks):
        """Applique effets visuels."""
        ...
```

4. **Créer network/mjpeg_server.py** :
```python
class MJPEGStreamer:
    def __init__(self, port):
        ...
    def start(self):
        ...
    def update_frame(self, frame):
        ...
```

5. **Simplifier apps/start_tracker.py** (nouveau point d'entrée) :
```python
class HandTrackerApp:
    def __init__(self, config):
        self.detector = HandDetector(config)
        self.mapper = FingerMapper(config)
        self.renderer = HandRenderer(config)
        self.streamer = MJPEGStreamer(config)
    
    def run(self):
        """Boucle principale."""
        ...
```

**Checklist** :
- [ ] Modules tracking/ créés et fonctionnels
- [ ] network/mjpeg_server.py extrait
- [ ] apps/start_tracker.py < 150 lignes
- [ ] Tests unitaires pour detector, mapper
- [ ] Documentation dans chaque module
- [ ] Commit: "refactor: split hand_tracker.py into modules"

---

### 2.2 Monitoring système

**Durée estimée** : Demi-journée  
**Fichiers** :
- ✅ `tools/monitor_rpi.py` (CRÉÉ)
- `apps/ui/components/system_metrics.py` (à créer)

**Actions** :

1. **Intégrer métriques dans dashboard** :
```python
# apps/ui/components/system_metrics.py
class SystemMetricsPanel:
    def __init__(self):
        self.monitor = RPiMonitor()
    
    def render(self, container):
        """Affiche métriques temps réel."""
        with container:
            # Graphiques CPU, RAM, température
            ...
```

2. **Ajouter onglet SYSTEM dans dashboard** :
```python
# apps/neuro_dashboardV2_new.py
with ui.tab_panel('SYSTEM'):
    system_panel = SystemMetricsPanel()
    system_panel.render()
```

3. **Alertes si métriques critiques** :
```python
if metrics['temperature']['cpu_celsius'] > 70:
    logger.warning(f"Température élevée: {temp}°C")
    ui.notify("⚠️ Température élevée", type='warning')
```

**Checklist** :
- [ ] tools/monitor_rpi.py fonctionnel en standalone
- [ ] Intégration dashboard avec graphiques
- [ ] Alertes température >70°C
- [ ] Alertes CPU >80%
- [ ] Commit: "feat: add system monitoring to dashboard"

---

### 2.3 Profiling performance

**Durée estimée** : 2 heures  
**Objectif** : Identifier goulots d'étranglement CPU

**Actions** :

1. **Profiling PC (hand tracker)** :
```bash
pip install py-spy
py-spy record -o profile_tracker.svg -- python hand_tracker.py
# Laisser tourner 30s, puis Ctrl+C
# Ouvrir profile_tracker.svg
```

2. **Profiling RPi (dashboard)** :
```bash
# Sur RPi
py-spy record -o profile_dashboard.svg -- python apps/neuro_dashboardV2_new.py
```

3. **Analyser et documenter** :
- Créer `docs/PERFORMANCE.md` avec résultats
- Identifier top 5 fonctions coûteuses
- Proposer optimisations ciblées

**Checklist** :
- [ ] Profiling hand_tracker.py effectué
- [ ] Profiling dashboard effectué
- [ ] docs/PERFORMANCE.md créé avec résultats
- [ ] Optimisations identifiées documentées

---

## 📈 PHASE 3 : AMÉLIORATION CONTINUE (Mois 1)

### 3.1 CI/CD avec GitHub Actions

**Durée** : 1 journée

**Fichier** : `.github/workflows/ci.yml`

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install deps
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov ruff
      - name: Linting
        run: ruff check .
      - name: Tests
        run: pytest --cov=core --cov=tracking --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

**Checklist** :
- [ ] .github/workflows/ci.yml créé
- [ ] Tests passent sur GitHub Actions
- [ ] Badge coverage dans README.md

---

### 3.2 Optimisations performance

**Durée** : 1 journée

**hand_tracker.py optimisations** :

1. **Downsampling masque** :
```python
def create_hand_mask_advanced(frame, landmarks):
    h, w = frame.shape[:2]
    small_h, small_w = h // 2, w // 2
    # Travailler à 50% résolution
    mask_small = create_mask(small_h, small_w, landmarks)
    mask = cv2.resize(mask_small, (w, h))
    return mask
```

2. **Réduire kernel blur** :
```python
mask = cv2.GaussianBlur(mask, (11, 11), 0)  # Au lieu de (21, 21)
```

3. **Skip frame rendering** :
```python
if self.frame_count % 2 == 0:
    self._cached_mask = create_hand_mask_advanced(...)
```

4. **MediaPipe model_complexity=0** :
```python
hands = mp_hands.Hands(
    model_complexity=0,  # Modèle léger
    min_tracking_confidence=0.7
)
```

**Checklist** :
- [ ] Optimisations implémentées
- [ ] Benchmark avant/après (FPS, CPU)
- [ ] Documentation dans docs/PERFORMANCE.md

---

### 3.3 API REST (optionnel)

**Durée** : 2 jours

**Fichier** : `apps/api_server.py`

```python
from fastapi import FastAPI
from core.hand_controller import HandController

app = FastAPI()
ctrl = HandController()

@app.post("/fingers/{name}/open")
def open_finger(name: str):
    ctrl.open_finger(name)
    return {"status": "ok", "finger": name, "state": "open"}

@app.post("/fingers/{name}/close")
def close_finger(name: str):
    ctrl.close_finger(name)
    return {"status": "ok", "finger": name, "state": "close"}

@app.get("/status")
def get_status():
    return {"fingers": ctrl.state, "power": ctrl.power_enabled}
```

---

## 📊 MÉTRIQUES DE SUCCÈS

| Métrique | Avant | Cible Semaine 1 | Cible Semaine 2 | Cible Mois 1 |
|----------|-------|-----------------|-----------------|--------------|
| **Tests coverage** | 0% | 40% | 60% | 75% |
| **Fichiers >300 lignes** | 3 | 2 | 1 | 0 |
| **Exceptions non typées** | ~15 | 5 | 0 | 0 |
| **CPU RPi idle** | ? | mesuré | <30% | <25% |
| **FPS hand tracker** | ? | mesuré | >25 | >30 |

---

## 🚀 COMMANDES RAPIDES

```bash
# Tests
pytest tests/ -v --cov=core --cov-report=html

# Monitoring RPi
python tools/monitor_rpi.py --interval 2.0

# Profiling
py-spy record -o profile.svg -- python hand_tracker.py

# Linting
ruff check . --fix

# Lancer dashboard
python apps/neuro_dashboardV2_new.py

# Lancer tracker PC
python hand_tracker.py
```

---

## 📝 NOTES

- **Priorité absolue** : Tests unitaires (Phase 1.1)
- **Quick win** : Unification config (Phase 1.2, 2-3h)
- **Impact long terme** : Refactoring hand_tracker.py (Phase 2.1)
- **Visibilité** : Monitoring système (Phase 2.2)

**Effort total estimé** : 5-6 jours de travail concentré.
