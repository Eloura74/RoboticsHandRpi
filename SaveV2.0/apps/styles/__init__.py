# --------------------------------------------------------------------
# STYLES - Point d'entrée unifié
# --------------------------------------------------------------------
"""
Module de styles pour le dashboard NEURO-HAND.

Architecture modulaire :
- css_base.py : Variables CSS, body, fond tactique
- css_components.py : Styles des composants UI (boutons, panneaux, HUD)
- html_3d.py : Structure HTML de la visualisation 3D
- js_threejs.py : Code JavaScript Three.js pour la main 3D

Ce fichier réassemble tous les modules et exporte :
- CSS_STYLE : Styles CSS complets
- HAND_3D_STRUCTURE : Structure HTML 3D
- HAND_3D_JS : Code JavaScript Three.js
"""

from .css_base import CSS_BASE
from .css_components import CSS_COMPONENTS
from .html_3d import HAND_3D_STRUCTURE
from .js_threejs import HAND_3D_JS

# =====================================================================
# ASSEMBLAGE DU CSS COMPLET
# =====================================================================
CSS_STYLE = CSS_BASE + '\n' + CSS_COMPONENTS

# =====================================================================
# EXPORTS
# =====================================================================
__all__ = ['CSS_STYLE', 'HAND_3D_STRUCTURE', 'HAND_3D_JS']
