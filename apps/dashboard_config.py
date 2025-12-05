# --------------------------------------------------------------------
# CONFIGURATION GLOBALE DU DASHBOARD NEURO-HAND
# --------------------------------------------------------------------
"""
Ce fichier centralise toutes les constantes de configuration du dashboard.
Modifier ici pour ajuster les paramètres réseau, seuils, etc.
"""

# --------------------------------------------------------------------
# RÉSEAU - PC (Caméra MJPEG)
# --------------------------------------------------------------------
PC_IP = '192.168.1.10'
MJPEG_PORT = 8090
MJPEG_URL = f'http://{PC_IP}:{MJPEG_PORT}/cam.mjpg'

# --------------------------------------------------------------------
# RÉSEAU - UDP (Réception tracking main)
# --------------------------------------------------------------------
UDP_IP = '0.0.0.0'  # Écoute sur toutes les interfaces
UDP_PORT = 5005
LOST_TIMEOUT = 2.0  # Timeout de déconnexion en secondes

# --------------------------------------------------------------------
# SEUILS DE CONTRÔLE DES DOIGTS
# --------------------------------------------------------------------
# Seuils pour déclencher l'ouverture/fermeture des servos continus
OPEN_THRESHOLD = 0.3   # En dessous : ouverture
CLOSE_THRESHOLD = 0.7  # Au dessus : fermeture

# Seuil anti-flutter pour la rotation du pouce (servo MG90S)
THUMB_ANTI_FLUTTER = 0.02  # Variation minimale pour bouger le servo

# --------------------------------------------------------------------
# DOIGTS PILOTÉS
# --------------------------------------------------------------------
# Liste des doigts contrôlés par servos continus
FINGERS = ['pouce_articulation', 'index', 'majeur', 'annulaire_auriculaire']

# --------------------------------------------------------------------
# INTERFACE UTILISATEUR
# --------------------------------------------------------------------
# Port du serveur web NiceGUI
WEB_PORT = 8080
# Intervalle de mise à jour de l'interface (en secondes)
UI_UPDATE_INTERVAL = 0.05  # 50ms = 20 FPS
