# --------------------------------------------------------------------
# NEURO-HAND DASHBOARD V2.0 - ORCHESTRATEUR PRINCIPAL
# --------------------------------------------------------------------
"""
Dashboard de contrôle pour la main robotique NEURO-HAND.

Architecture modulaire :
- dashboard_config.py : Configuration (IPs, ports, seuils)
- dashboard_network.py : Threads réseau (UDP + contrôle matériel)
- dashboard_ui.py : Composants d'interface (NiceGUI)
- neuro_dashboardV2.py : Orchestrateur principal (ce fichier)
"""

import sys
import signal
import time
import threading
from pathlib import Path
from nicegui import ui, app

# --------------------------------------------------------------------
# SETUP DU PATH POUR LES IMPORTS
# --------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import du contrôleur matériel
try:
    from core.hand_controller import HandController
except ImportError:
    # Stub de secours pour développement sans matériel
    class HandController:
        def open_hand(self, parallel=True): pass
        def close_hand(self, parallel=True): pass
        def open_finger(self, f, parallel=False): pass
        def close_finger(self, f, parallel=False): pass
        def stop_all(self): pass
        def shutdown(self): pass
        def thumb_rotation_step(self, direction: int): pass
        def thumb_rotation_reset(self): pass
        def thumb_from_value(self, value: float): pass

# Import des styles CSS et structure 3D
try:
    from apps.styles import CSS_STYLE, HAND_3D_STRUCTURE, HAND_3D_JS
except ImportError:
    print("[ERROR] Cannot import dashboard styles")
    sys.exit(1)

# Import des modules du dashboard
from apps.dashboard_config import UDP_PORT, WEB_PORT
from apps.dashboard_network import (
    receiver_thread, 
    hardware_thread, 
    get_local_ip
)
from apps.dashboard_ui import (
    build_header,
    build_camera_panel,
    build_control_panel,
    build_3d_panel,
    build_servo_config_panel,
    build_telemetry_panel,
    create_update_loop
)

# --------------------------------------------------------------------
# VARIABLE GLOBALE : CONTRÔLEUR MATÉRIEL
# --------------------------------------------------------------------
controller = None


# --------------------------------------------------------------------
# GESTION DE L'ARRÊT PROPRE
# --------------------------------------------------------------------
def signal_handler(signum, frame):
    """Arrêt propre quand on tue le process (Ctrl+C / SIGTERM)."""
    print("\n[SYSTEM] Shutdown sequence initiated...")
    try:
        if controller:
            controller.shutdown()
    except Exception as e:
        print(f"[SYSTEM] Erreur lors du shutdown contrôleur: {e}")
    app.shutdown()
    sys.exit(0)


# --------------------------------------------------------------------
# CONSTRUCTION DE L'INTERFACE COMPLÈTE
# --------------------------------------------------------------------
def build_ui():
    """
    Construit l'interface complète du dashboard NEURO-HAND.
    Structure : header avec tabs intégrés + panneau principal avec tab_panels.
    """
    # Injection du CSS global
    ui.add_head_html(CSS_STYLE)

    # Construction du header avec badge de statut et tabs de navigation
    status_label, tabs = build_header()

    # Body principal avec gestion des onglets liés aux tabs du header
    with ui.tab_panels(tabs, value='DASHBOARD').classes('w-full h-[92vh] bg-transparent'):
        
        # --- ONGLET DASHBOARD (VUE PRINCIPALE) ---
        with ui.tab_panel('DASHBOARD').classes('w-full h-full p-4 gap-4'):
            with ui.row().classes('w-full h-full gap-4'):
                # Colonne gauche : caméra + panneau de contrôle
                with ui.column().classes('w-[26%] min-w-[300px] h-full gap-4'):
                    build_camera_panel()
                    build_control_panel(controller, get_local_ip(), UDP_PORT)

                # Zone centrale : visualisation 3D de la main
                build_3d_panel(HAND_3D_STRUCTURE, HAND_3D_JS)

        # --- ONGLET CONFIGURATION (SERVOS) ---
        with ui.tab_panel('CONFIG').classes('w-full h-full p-4'):
            build_servo_config_panel()

        # --- ONGLET TÉLÉMÉTRIE ---
        with ui.tab_panel('TELEMETRY').classes('w-full h-full p-4'):
            build_telemetry_panel()

    # Initialisation de la boucle de mise à jour UI
    create_update_loop(status_label)


# --------------------------------------------------------------------
# POINT D'ENTRÉE PRINCIPAL
# --------------------------------------------------------------------
if __name__ in {"__main__", "__mp_main__"}:
    signal.signal(signal.SIGINT, signal_handler)

    # Initialisation du contrôleur matériel
    try:
        controller = HandController()
        print("[INIT] Contrôleur matériel initialisé")
    except Exception as e:
        print(f"[ERROR] Impossible d'initialiser HandController: {e}")
        sys.exit(1)

    # Démarrage des threads de communication
    print("[INIT] Démarrage des threads de communication...")
    threading.Thread(target=receiver_thread, daemon=True).start()
    threading.Thread(target=hardware_thread, args=(controller,), daemon=True).start()
    time.sleep(0.5)

    # Exposition du dossier /assets pour le chargement 3D
    ASSETS_DIR = BASE_DIR / 'assets'
    if not ASSETS_DIR.exists():
        print("[WARNING] Le dossier '/assets' n'existe pas. Créez-le et placez-y main_modele.obj.")
        ASSETS_DIR.mkdir(exist_ok=True)
    app.add_static_files('/assets', ASSETS_DIR)
    print("[ASSET] Dossier '/assets' exposé pour le chargement 3D.")

    # Déclaration de la route principale
    @ui.page('/')
    def index():
        build_ui()

    # Lancement du serveur NiceGUI
    print(f"[WEB] Démarrage du serveur web sur le port {WEB_PORT}")
    ui.run(
        host='0.0.0.0',
        port=WEB_PORT,
        dark=True,
        reload=False,
        title='NEURO-LINK V2.0'
    )
