# 🏗️ Architecture Modulaire du Dashboard NEURO-HAND

## 📁 Structure des fichiers

```
apps/
├── dashboard_config.py          # Configuration centrale
├── dashboard_network.py         # Threads réseau et matériel
├── dashboard_ui.py             # Composants d'interface
├── neuro_dashboardV2_new.py    # Orchestrateur principal (NOUVEAU)
└── neuro_dashboardV2.py        # Ancienne version monolithique (LEGACY)
```

---

## 📄 Description des modules

### 1️⃣ `dashboard_config.py` (~50 lignes)
**Rôle** : Centraliser toutes les constantes de configuration.

**Contenu** :
- 🌐 Configuration réseau (IP PC, ports UDP/MJPEG)
- ⚙️ Seuils de contrôle des doigts
- 🎯 Liste des doigts pilotés
- 🖥️ Paramètres de l'interface web

**Avantage** : Modifier la config sans toucher au code métier.

---

### 2️⃣ `dashboard_network.py` (~270 lignes)
**Rôle** : Gérer les communications réseau et le contrôle matériel.

**Contenu** :
- 📡 Thread UDP de réception (valeurs des doigts 0..1)
- 🤖 Thread de contrôle matériel (pilotage servos)
- 🔧 Fonctions utilitaires (parsing, anti-flutter, seuils)
- 🔒 État partagé thread-safe

**Fonctions principales** :
- `receiver_thread()` : Écoute UDP + détection timeout
- `hardware_thread(ctrl)` : Boucle de contrôle des servos
- `get_local_ip()` : Récupération IP locale

---

### 3️⃣ `dashboard_ui.py` (~240 lignes)
**Rôle** : Composants d'interface utilisateur (NiceGUI).

**Contenu** :
- 🎨 Header avec badge de statut
- 📹 Panneau vidéo (flux MJPEG + overlay HUD)
- 🎮 Panneau de contrôle (boutons, rotation pouce)
- 🖐️ Panneau 3D de visualisation
- 🔄 Boucle de mise à jour UI (50ms)

**Fonctions principales** :
- `build_header()` : Header + badge statut
- `build_camera_panel()` : Flux caméra
- `build_control_panel(...)` : Boutons de contrôle
- `build_3d_panel(...)` : Visualisation 3D
- `create_update_loop(status_label)` : Boucle d'animation

---

### 4️⃣ `neuro_dashboardV2_new.py` (~150 lignes)
**Rôle** : Orchestrateur principal qui coordonne tous les modules.

**Contenu** :
- 🚀 Point d'entrée principal (`if __name__ == "__main__"`)
- 🔗 Import et coordination des modules
- 🛑 Gestion de l'arrêt propre (SIGINT)
- 🌐 Configuration du serveur web

**Flux d'exécution** :
1. Initialisation du `HandController`
2. Démarrage des threads (UDP + matériel)
3. Configuration du serveur NiceGUI
4. Lancement de l'interface web

---

## 🎯 Avantages de cette architecture

### ✅ **Maintenabilité**
- Chaque module a une responsabilité unique
- Modifications isolées (changer la config ne touche pas l'UI)
- Plus facile à tester individuellement

### ✅ **Lisibilité**
- Code organisé logiquement
- Fonctions courtes et documentées
- Navigation facilitée

### ✅ **Réutilisabilité**
- Les modules peuvent être réutilisés dans d'autres projets
- Les composants UI sont indépendants
- La logique réseau est découplée de l'interface

### ✅ **Évolutivité**
- Ajouter une nouvelle fonctionnalité = modifier un seul module
- Facile d'ajouter de nouveaux composants UI
- Possibilité de créer des variantes (ex: dashboard simplifié)

---

## 🔄 Migration de l'ancienne version

### Pour utiliser la nouvelle architecture :

```bash
# Remplacer l'ancienne version
mv neuro_dashboardV2.py neuro_dashboardV2_old.py
mv neuro_dashboardV2_new.py neuro_dashboardV2.py
```

### Ou lancer directement :

```bash
python apps/neuro_dashboardV2_new.py
```

---

## 📊 Comparaison

| Critère | Ancienne version | Nouvelle architecture |
|---------|-----------------|----------------------|
| **Nombre de fichiers** | 1 fichier | 4 fichiers modulaires |
| **Lignes par fichier** | 764 lignes | ~50 à 270 lignes |
| **Maintenabilité** | ⚠️ Difficile | ✅ Excellente |
| **Lisibilité** | ⚠️ Moyenne | ✅ Très bonne |
| **Testabilité** | ⚠️ Difficile | ✅ Facile |
| **Réutilisabilité** | ❌ Faible | ✅ Forte |

---

## 🛠️ Personnalisation

### Modifier la configuration
👉 Éditer `dashboard_config.py`

### Ajouter un composant UI
👉 Ajouter une fonction dans `dashboard_ui.py`

### Modifier la logique réseau
👉 Éditer `dashboard_network.py`

### Changer le flux principal
👉 Modifier `neuro_dashboardV2_new.py`

---

## 🔍 Points d'attention

### Imports
Les modules s'importent entre eux. Vérifier que :
- Le `sys.path` inclut le répertoire parent
- Les imports relatifs fonctionnent correctement

### État partagé
L'état est géré dans `dashboard_network.py` avec un `threading.Lock()`.
Toujours utiliser le lock lors des accès concurrents.

### Dépendances
Les 3 modules dépendent de :
- `nicegui` (UI)
- `core.hand_controller` (contrôle matériel)
- `apps.styles.dashboard_stylesV2` (CSS/3D)

---

## 📝 TODO / Améliorations futures

- [ ] Ajouter des tests unitaires pour chaque module
- [ ] Créer un mode "debug" avec logging détaillé
- [ ] Séparer encore plus les styles CSS
- [ ] Ajouter un système de plugins pour les composants UI
- [ ] Créer une API REST pour contrôle externe
