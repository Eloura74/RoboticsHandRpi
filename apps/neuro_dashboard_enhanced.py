# --------------------------------------------------------------------
# NEURO-HAND DASHBOARD V2.1 ENHANCED - Version améliorée
# --------------------------------------------------------------------
"""
Dashboard de contrôle pour la main robotique NEURO-HAND.

🆕 AMÉLIORATIONS V2.1 Enhanced :
- Panneau de contrôle compact (gain 40% d'espace)
- Système de presets de gestes (peace, fist, ok, etc.)
- Monitoring système temps réel (CPU, RAM, température)
- Nouveaux onglets : GESTURES et HEALTH

Architecture modulaire :
- core/ : Contrôleur matériel + presets + config + logger
- apps/ui/ : Composants UI modulaires
- apps/network/ : Threads réseau
- apps/styles/ : CSS + JavaScript
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
from core.config_loader import config
from apps.dashboard_network import (
    receiver_thread, 
    hardware_thread, 
    get_local_ip
)

# Constantes depuis config unifiée
UDP_PORT = config.network.udp_port
WEB_PORT = config.ui.web_port

# ========================================
# IMPORTS UI - Version Enhanced
# ========================================
from apps.dashboard_ui import (
    build_header,
    build_camera_panel,
    build_3d_panel,
    build_servo_config_panel,
    build_telemetry_panel,
    create_update_loop
)

# 🆕 Nouveaux composants améliorés
from apps.ui.control_panel_compact import build_control_panel_compact
from apps.ui.gesture_panel import build_gesture_panel, build_gesture_tab_panel
from apps.ui.system_health_panel import (
    build_system_health_compact,
    build_system_health_full_panel
)

# 🆕 TACTICAL SIDEBAR - Colonne gauche unifiée
from apps.ui.tactical_sidebar import build_tactical_sidebar

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
# CONSTRUCTION DE L'INTERFACE COMPLÈTE ENHANCED
# --------------------------------------------------------------------
def build_ui_enhanced():
    """
    Construit l'interface complète du dashboard NEURO-HAND Enhanced.
    
    🆕 Améliorations :
    - Panneau gauche optimisé (contrôles + gestes + santé)
    - Nouveaux onglets GESTURES et HEALTH
    - Monitoring temps réel
    """
    # Injection du CSS global
    ui.add_head_html(CSS_STYLE)

    # Construction du header avec badge de statut et tabs de navigation
    # 🆕 Header modifié pour inclure nouveaux onglets
    status_label, tabs = build_header_enhanced()

    # Body principal avec gestion des onglets liés aux tabs du header
    with ui.tab_panels(tabs, value='DASHBOARD').classes('w-full h-[92vh] bg-transparent'):
        
        # ========================================
        # ONGLET DASHBOARD (VUE PRINCIPALE)
        # ========================================
        with ui.tab_panel('DASHBOARD').classes('w-full h-full p-4 gap-4'):
            with ui.row().classes('w-full h-full gap-4'):
                
                # ========================================
                # 🆕 COLONNE GAUCHE OPTIMISÉE
                # ========================================
                # 🆕 TACTICAL SIDEBAR - Colonne gauche unifiée
                # ========================================
                with ui.column().classes('w-[28%] min-w-[320px] max-w-[380px] h-full'):
                    build_tactical_sidebar(controller, get_local_ip(), UDP_PORT)

                # Zone centrale : visualisation 3D de la main - INCHANGÉ
                build_3d_panel(HAND_3D_STRUCTURE, HAND_3D_JS)

        # ========================================
        # 🆕 ONGLET GESTURES (NOUVEAU)
        # ========================================
        with ui.tab_panel('GESTURES').classes('w-full h-full p-4'):
            build_gesture_tab_panel(controller)

        # ========================================
        # 🆕 ONGLET SYSTEM HEALTH (NOUVEAU)
        # ========================================
        with ui.tab_panel('HEALTH').classes('w-full h-full p-4'):
            build_system_health_full_panel()

        # ========================================
        # ONGLET CONFIGURATION (SERVOS) - INCHANGÉ
        # ========================================
        with ui.tab_panel('CONFIG').classes('w-full h-full p-4'):
            build_servo_config_panel()

        # ========================================
        # ONGLET TÉLÉMÉTRIE - INCHANGÉ
        # ========================================
        with ui.tab_panel('TELEMETRY').classes('w-full h-full p-4'):
            build_telemetry_panel()

    # Initialisation de la boucle de mise à jour UI
    create_update_loop(status_label)


def build_header_enhanced():
    """
    Construit le header avec les nouveaux onglets GESTURES et HEALTH.
    
    Returns:
        tuple: (status_label, tabs) pour mise à jour du badge + navigation.
    """
    # Header principal
    with ui.header().classes(
        'justify-between items-center bg-[#0A0E1A] border-b-2 border-cyan-500/30 px-6 py-3 h-[8vh]'
    ):
        # Logo + Titre
        with ui.row().classes('items-center gap-4'):
            ui.label('🤖').classes('text-3xl')
            with ui.column().classes('gap-0'):
                ui.label('NEURO-HAND V2.1 Enhanced').classes('text-xl font-bold tracking-wider text-cyan-400')
                ui.label('ROBOTICS HAND / ENHANCED CONTROL').classes('text-[10px] tracking-[0.3em] text-gray-500')
        
        # Badge de statut connexion
        status_label = ui.label('OFFLINE') \
            .classes('text-xs px-3 py-1 rounded bg-red-900/40 text-red-300 border border-red-500/50')
        
        # Navigation tabs
        with ui.tabs().classes('text-cyan-400') as tabs:
            ui.tab('DASHBOARD', icon='dashboard')
            ui.tab('GESTURES', icon='gesture')  # 🆕 NOUVEAU
            ui.tab('HEALTH', icon='monitor_heart')  # 🆕 NOUVEAU
            ui.tab('CONFIG', icon='settings')
            ui.tab('TELEMETRY', icon='analytics')
    
    return status_label, tabs


# --------------------------------------------------------------------
# POINT D'ENTRÉE PRINCIPAL
# --------------------------------------------------------------------
if __name__ in {"__main__", "__mp_main__"}:
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 60)
    print("🚀 NEURO-HAND V2.1 ENHANCED DASHBOARD")
    print("=" * 60)

    # Initialisation du contrôleur matériel
    try:
        controller = HandController()
        print("[INIT] ✅ Contrôleur matériel initialisé")
    except Exception as e:
        print(f"[ERROR] ❌ Impossible d'initialiser HandController: {e}")
        print("[INFO] Mode simulation activé (stub)")
        controller = HandController()  # Stub mode

    # Démarrage des threads de communication
    print("[INIT] 🌐 Démarrage des threads de communication...")
    threading.Thread(target=receiver_thread, daemon=True).start()
    threading.Thread(target=hardware_thread, args=(controller,), daemon=True).start()
    time.sleep(0.5)

    # Exposition du dossier /assets pour le chargement 3D
    ASSETS_DIR = BASE_DIR / 'assets'
    if not ASSETS_DIR.exists():
        print("[WARNING] ⚠️  Le dossier '/assets' n'existe pas. Créez-le et placez-y main_modele.obj.")
        ASSETS_DIR.mkdir(exist_ok=True)
    app.add_static_files('/assets', ASSETS_DIR)
    print("[ASSET] 📁 Dossier '/assets' exposé pour le chargement 3D.")

    # Déclaration de la route principale
    @ui.page('/')
    def index():
        build_ui_enhanced()

    # Lancement du serveur NiceGUI
    local_ip = get_local_ip()
    
    print("\n" + "=" * 60)
    print(f"[WEB] 🌐 Serveur web démarré sur le port {WEB_PORT}")
    print(f"[WEB] 🔗 Ouvrir dans le navigateur :")
    print(f"[WEB]    → http://{local_ip}:{WEB_PORT}")
    print(f"[WEB] ⚠️  N'utilisez PAS http://127.0.0.1:{WEB_PORT}")
    print(f"[WEB]    (le flux webcam ne fonctionnera pas)")
    print("=" * 60)
    print("\n✨ NOUVELLES FONCTIONNALITÉS :")
    print("  • Panneau de contrôle compact (gain 40% espace)")
    print("  • Système de presets de gestes (onglet GESTURES)")
    print("  • Monitoring système temps réel (onglet HEALTH)")
    print("  • Quick gestures dans panneau gauche")
    print("  • Alertes CPU/RAM/Température automatiques")
    print("\n💡 Appuyez sur Ctrl+C pour arrêter proprement.")
    print("=" * 60 + "\n")
    
    ui.run(
        host='0.0.0.0',
        port=WEB_PORT,
        dark=True,
        reload=False,
        title='NEURO-HAND V2.1 Enhanced',
        show=False  # Désactive l'ouverture automatique du navigateur
    )
