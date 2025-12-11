# Module de Styles - Dashboard

## Structure

Ce module contient tous les éléments visuels (CSS, HTML, JavaScript) séparés du code logique principal.

### Fichiers

- **`dashboard_styles.py`** : Contient toutes les ressources graphiques
  - `CSS_STYLE` : Styles CSS (thème cyberpunk/néon)
  - `HAND_3D_STRUCTURE` : Structure HTML du conteneur 3D
  - `HAND_3D_JS` : Moteur 3D (Three.js) pour l'affichage holographique

- **`__init__.py`** : Fichier d'initialisation du module Python

## Utilisation

Dans votre application principale (`neuro_dashboard.py`), importez simplement :

```python
from apps.styles.dashboard_styles import CSS_STYLE, HAND_3D_STRUCTURE, HAND_3D_JS
```

## Avantages de cette séparation

1. **Maintenance facilitée** : Modifications CSS/JS sans toucher au code métier
2. **Réutilisabilité** : Les styles peuvent être partagés entre applications
3. **Lisibilité** : Code principal plus court et concentré sur la logique
4. **Collaboration** : Designers et développeurs peuvent travailler séparément
5. **Versionnement** : Historique Git plus clair des changements visuels vs logiques

## Modification des styles

Pour modifier l'apparence :
1. Ouvrez `dashboard_styles.py`
2. Modifiez les variables `CSS_STYLE`, `HAND_3D_STRUCTURE` ou `HAND_3D_JS`
3. Relancez l'application

Aucune modification du code principal n'est nécessaire !
