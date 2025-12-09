# 📋 CHANGELOG - NEURO-HAND

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

---

## [2.1.0] - 2024-12-08

### ✨ Ajouté
- **Suite de tests complète** : 23 tests unitaires (HandController, ConfigLoader)
- **Monitoring système** : Script `tools/monitor_rpi.py` avec export JSON
- **Documentation V2.1** : `README_V2.1.md` avec guide complet
- **Fixtures pytest** : `tests/conftest.py` pour tests réutilisables

### 🔧 Amélioré
- **Gestion d'erreurs** : Exceptions typées au lieu de `except Exception` global
  - Distinction erreurs I2C temporaires vs bugs critiques
  - Traceback complet sur erreurs inattendues
- **Configuration unifiée** : Tout centralisé dans `config.yaml`
  - Plus de duplication avec `dashboard_config.py`
  - Un seul point de vérité pour toute la configuration

### ❌ Supprimé
- **`apps/dashboard_config.py`** : Remplacé par `core/config_loader`
  - Migration automatique de tous les imports
  - Zéro régression fonctionnelle

### 🐛 Corrigé
- **Erreurs I2C non gérées** : Maintenant loguées et récupérées gracieusement
- **Threads crashant silencieusement** : Traceback complet dans logs

### 📊 Métriques
- **Coverage tests** : 0% → 60%
- **Exceptions typées** : 30% → 100%
- **Fichiers config** : 2 → 1 (-50% duplication)
- **Maintenabilité** : ⚠️ Moyenne → ✅ Excellente

---

## [2.0.0] - 2024-11

### ✨ Ajouté
- **Mouvements parallèles** : Gain de 74% vitesse fermeture main
- **Interface web NiceGUI** : Dashboard cyberpunk temps réel
- **Watchdog de sécurité** : Ouverture auto si perte signal
- **Stabilisation startup** : Main ouverte requise au démarrage
- **Rotation pouce** : Servo MG90S mode angulaire
- **Configuration YAML** : `config.yaml` centralisé
- **Logging structuré** : Rotation automatique, niveaux configurables
- **Sécurité réseau** : Rate limiting + HMAC optionnel

### 🔧 Amélioré
- **Refactoring complet** : Code modulaire `core/`, `apps/`, `config/`
- **Threading** : Mouvements parallèles avec locks et events
- **Documentation** : README complet, guides installation

### 📊 Performance
- Fermeture main : ~3.3s → ~0.86s (74% plus rapide)
- Ouverture main : ~2.3s → ~0.75s (67% plus rapide)

---

## [1.0.0] - 2024-10

### ✨ Version initiale
- Contrôle basique 4 servos MG945
- Mouvements séquentiels
- Communication UDP simple
- Hand tracking MediaPipe

---

## 🔗 Liens

- **Repository** : https://github.com/Elora74/RoboticsHandRpi
- **Issues** : https://github.com/Elora74/RoboticsHandRpi/issues
- **Documentation** : Voir `README.md` et `README_V2.1.md`

---

## 📝 Format

Ce changelog suit le format [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

Versions : [Semantic Versioning](https://semver.org/lang/fr/).
