# --------------------------------------------------------------------
# COMPOSANTS D'INTERFACE UTILISATEUR (NICEGUI)
# --------------------------------------------------------------------
"""
Ce module orchestre les composants de l'interface NiceGUI.
Les fonctions principales sont maintenant dans des modules séparés :
- apps.ui.header : Header avec badge de statut et navigation
- apps.ui.panels : Panneaux (caméra, contrôle, 3D, config)
- apps.ui.telemetry : Panneau de télémétrie
- apps.ui.components : Composants HUD réutilisables
"""

import json
import time
import math
import os
from nicegui import ui

from apps.dashboard_config import MJPEG_URL, FINGERS, UI_UPDATE_INTERVAL
from apps.dashboard_network import state, state_lock

# Import des modules UI refactorisés
from apps.ui import build_header, build_telemetry_panel, build_camera_panel, build_rpi_camera_overlay, HUDCard
from apps.dashboard_config import RPI_CAMERA_ENABLED

# Chemin vers le fichier de config servos
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'servos_v2.json')


# --------------------------------------------------------------------
# COMPOSANTS UI (à refactoriser progressivement)
# --------------------------------------------------------------------


def build_control_panel(controller, local_ip: str, udp_port: int):
    """
    Construit le panneau de contrôle avec boutons OPEN/CLOSE,
    simulation, rotation pouce, et bouton d'urgence.
    
    Args:
        controller: Instance de HandController pour les callbacks.
        local_ip: IP locale pour l'affichage.
        udp_port: Port UDP pour l'affichage.
    """
    with ui.card().classes(
        'w-full flex-1 panel-3d-bg px-6 pt-6 pb-4 flex flex-col gap-5 items-center text-center relative overflow-hidden'
    ):
        # HUD Overlay (Coins uniquement)
        ui.html('''
            <div class="hud-overlay">
                <div class="hud-corner hud-tl"></div>
                <div class="hud-corner hud-tr"></div>
                <div class="hud-corner hud-bl"></div>
                <div class="hud-corner hud-br"></div>
            </div>
        ''')

        # En-tête : titre + badge LIVE LINK
        with ui.column().classes('items-center gap-1 w-full z-20'):
            ui.label('CONTROL NODES') \
                .classes('hud-section-title text-lg')
            ui.label('HAND ACTUATOR BUS') \
                .classes('hud-section-caption')
            ui.label('LIVE LINK') \
                .classes('hud-chip mt-1')
        
        ui.html('<div class="w-full h-[1px] bg-cyan-900/50"></div>')

        # Infos de connexion UDP (Centré)
        with ui.column().classes('items-center gap-2 w-full z-20'):
            with ui.row().classes('gap-4 text-[10px] text-gray-300'):
                with ui.column().classes('items-center gap-[1px]'):
                    ui.label('UDP ROUTE').classes('hud-mini-label')
                    ui.label(f'{local_ip}:{udp_port}') \
                        .classes('hud-value-strong')
                
                with ui.column().classes('items-center gap-[1px]'):
                    ui.label('MODE').classes('hud-mini-label')
                    ui.label('TRACKING').classes('hud-value-strong')

        # Boutons principaux : OPEN / CLOSE / SIMULATION
        with ui.column().classes('gap-3 w-full max-w-[220px] z-20'):
            ui.button(
                'OPEN',
                icon='pan_tool_alt',
                color='transparent',
                on_click=lambda: controller.open_hand()
            ).props('flat').classes('w-full h-12 cyber-btn-glitch cyber-btn-open text-base border-2 border-cyan-500')

            ui.button(
                'CLOSE',
                icon='back_hand',
                color='transparent',
                on_click=lambda: controller.close_hand()
            ).props('flat').classes('w-full h-12 cyber-btn-glitch cyber-btn-close text-base border-2 border-red-500')

            def toggle_sim():
                """Bascule le mode simulation (génération sinusoïdale des valeurs)."""
                with state_lock:
                    state['simu_mode'] = not state['simu_mode']

            ui.button(
                'SIMULATION MODE',
                icon='memory',
                color='transparent',
                on_click=toggle_sim
            ).props('flat').classes('w-full h-12 cyber-btn-glitch cyber-btn-sim text-xs border-2 border-purple-500')

        ui.html('<div class="w-full h-[1px] bg-cyan-900/50"></div>')

        # Section rotation pouce (servo MG90S)
        with ui.column().classes('items-center gap-1 w-full z-20'):
            ui.label('THUMB ROTATION') \
                .classes('hud-mini-label text-cyan-300')
            ui.label('MG90S ACTUATOR CHANNEL') \
                .classes('text-[8px] text-gray-500 tracking-[0.2em] uppercase')

            with ui.row().classes('w-full max-w-[220px] gap-2 mt-2'):
                ui.button(
                    '⟲ -1°',
                    on_click=lambda: controller.thumb_rotation_step(-1),
                ).classes('flex-1 h-10 thumb-actuator font-bold text-lg')
                ui.button(
                    '+1° ⟳',
                    on_click=lambda: controller.thumb_rotation_step(+1),
                ).classes('flex-1 h-10 thumb-actuator font-bold text-lg')

            ui.button(
                'CENTER THUMB',
                on_click=lambda: controller.thumb_rotation_reset(),
            ).classes('w-full max-w-[220px] h-8 mt-1 thumb-actuator font-bold text-xs')

        # Bouton d'urgence circulaire en bas du panneau
        with ui.element('div').classes('emergency-wrapper mt-auto mb-2 z-20'):
            ui.button(
                'EMERGENCY\nSTOP',
                on_click=lambda: controller.stop_all(),
            ).classes('emergency-btn')


def build_3d_panel(hand_3d_structure: str, hand_3d_js: str):
    """
    Construit le panneau central contenant la visualisation 3D de la main.
    Injecte le HTML de la structure 3D et le JavaScript associé.
    Intègre également le panneau webcam RPi toggle-able en overlay.
    
    Args:
        hand_3d_structure: HTML de la structure 3D.
        hand_3d_js: Code JavaScript pour l'animation 3D.
    """
    # State réactif pour l'affichage du panneau webcam RPi
    rpi_cam_visible = {'show': False}
    
    with ui.card().classes(
        'flex-1 h-full hud-panel p-0 overflow-hidden relative panel-3d-bg'
    ) as panel:
        # Structure 3D (Canvas)
        ui.html(hand_3d_structure).classes('w-full h-full relative z-0')
        
        # Overlay HUD Futuriste avec bouton toggle webcam
        ui.html(f'''
            <div class="hud-overlay">
                <div class="hud-corner hud-tl"></div>
                <div class="hud-corner hud-tr"></div>
                <div class="hud-corner hud-bl"></div>
                <div class="hud-corner hud-br"></div>
                
                <div class="hud-crosshair"></div>
                <div class="hud-scan-line"></div>
                
                <div style="position: absolute; top: 20px; left: 50%; transform: translateX(-50%); 
                            color: var(--neon-cyan); font-size: 10px; letter-spacing: 2px; opacity: 0.7;">
                    SCANNING 3D OBJECT // LIVE FEED
                </div>
            </div>
        ''')
        
        # Bouton toggle pour la webcam RPi (coin haut droit)
        if RPI_CAMERA_ENABLED:
            with ui.element('div').classes(
                'absolute top-4 right-4 z-40'
            ):
                ui.button(
                    icon='videocam',
                    on_click=lambda: rpi_cam_visible.update({'show': not rpi_cam_visible['show']})
                ).props('flat round').classes(
                    'text-cyan-400 bg-black/40 hover:bg-cyan-900/30 '
                    'border border-cyan-500/40 hover:border-cyan-400 '
                    'transition-all duration-200 shadow-lg shadow-cyan-500/20'
                ).tooltip('Toggle RPi Webcam')
        
        # Panneau webcam RPi (overlay en haut gauche, affichable/masquable)
        if RPI_CAMERA_ENABLED:
            build_rpi_camera_overlay(rpi_cam_visible)

        ui.add_body_html(hand_3d_js)


def build_servo_config_panel():
    """
    Construit le panneau de configuration des servos.
    Permet de lire et modifier servos_v2.json.
    """
    # Chargement de la config
    try:
        with open(CONFIG_PATH, 'r') as f:
            config_data = json.load(f)
    except Exception as e:
        ui.notify(f"Erreur chargement config: {e}", type='negative')
        config_data = {"servos": {}}

    servos = config_data.get('servos', {})

    def save_config():
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config_data, f, indent=2)
            ui.notify("Configuration sauvegardée avec succès !", type='positive')
        except Exception as e:
            ui.notify(f"Erreur sauvegarde: {e}", type='negative')

    with ui.column().classes('w-full h-full p-6 scroll-y-auto gap-6'):
        ui.label('SERVO CONFIGURATION MATRIX').classes('hud-section-title text-xl mb-4')

        # Grille de cartes pour chaque servo
        with ui.grid(columns=2).classes('w-full gap-4'):
            for servo_name, params in servos.items():
                # Utilisation de la nouvelle classe config-card
                with ui.card().classes('config-card p-4 gap-2'):
                    ui.label(servo_name.upper()).classes('text-cyan-400 font-bold tracking-wider mb-2 text-xs border-b border-cyan-900/50 pb-1 w-full')
                    
                    # Champs communs
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        ui.number('Channel', value=params.get('channel'), 
                                 on_change=lambda e, p=params: p.update({'channel': int(e.value)}))\
                            .classes('w-full config-input').props('dark dense label-color="cyan" input-class="text-cyan-300"')
                        
                        ui.number('Neutral', value=params.get('neutral'), step=0.001, format='%.3f',
                                 on_change=lambda e, p=params: p.update({'neutral': float(e.value)}))\
                            .classes('w-full config-input').props('dark dense label-color="cyan" input-class="text-cyan-300"')

                        ui.number('Dir Close', value=params.get('dir_close'), 
                                 on_change=lambda e, p=params: p.update({'dir_close': int(e.value)}))\
                            .classes('w-full config-input').props('dark dense label-color="cyan" input-class="text-cyan-300"')

                        # Champs spécifiques pour servos continus vs positionnels
                        if 'angle_min' in params: # Servo positionnel (ex: pouce_rotation)
                             ui.number('Angle Min', value=params.get('angle_min'), step=1.0,
                                     on_change=lambda e, p=params: p.update({'angle_min': float(e.value)}))\
                                .classes('w-full config-input').props('dark dense label-color="cyan" input-class="text-cyan-300"')
                             ui.number('Angle Max', value=params.get('angle_max'), step=1.0,
                                     on_change=lambda e, p=params: p.update({'angle_max': float(e.value)}))\
                                .classes('w-full config-input').props('dark dense label-color="cyan" input-class="text-cyan-300"')
                        else: # Servos continus
                            ui.number('Speed Close', value=params.get('speed_close'), step=0.1,
                                     on_change=lambda e, p=params: p.update({'speed_close': float(e.value)}))\
                                .classes('w-full config-input').props('dark dense label-color="cyan" input-class="text-cyan-300"')
                            ui.number('Speed Open', value=params.get('speed_open'), step=0.1,
                                     on_change=lambda e, p=params: p.update({'speed_open': float(e.value)}))\
                                .classes('w-full config-input').props('dark dense label-color="cyan" input-class="text-cyan-300"')

        # Bouton de sauvegarde flottant ou en bas
        with ui.row().classes('w-full justify-end mt-4'):
            ui.button('SAVE CONFIGURATION', icon='save', on_click=save_config)\
                .classes('cyber-btn-glitch bg-cyan-700 text-white')



def create_update_loop(status_label):
    """
    Crée la boucle de mise à jour de l'interface.
    Met à jour la main 3D et le badge de statut.
    
    Args:
        status_label: Le label de statut à mettre à jour.
    """
    loop_count = [0]

    def update_loop():
        """
        Boucle exécutée régulièrement (défini par UI_UPDATE_INTERVAL) :
        - Génère des valeurs simulées si mode simu activé,
        - Envoie les valeurs vers le JS de la main 3D,
        - Met à jour le badge de statut (ONLINE/OFFLINE).
        """
        try:
            loop_count[0] += 1

            # Génération de valeurs simulées (sinusoïdes) si mode simu actif
            with state_lock:
                if state['simu_mode']:
                    t = time.time()
                    for i, f in enumerate(FINGERS):
                        state['values'][f] = (math.sin(t * 2 + i) + 1) / 2

                vals = state['values'].copy()
                connected = state['udp_connected'] or state['simu_mode']
                fps = state['fps']

            # Envoi des données vers le JS de la visualisation 3D
            json_data = json.dumps(vals)
            ui.run_javascript(
                "try { "
                "if (typeof window.updateHandData === 'function') "
                f"window.updateHandData('{json_data}'); "
                "} catch(e) { console.error('updateHandData error:', e); }"
            )

            # Mise à jour du badge de statut en fonction de la connexion
            status_label.text = f"ONLINE ({fps} TPS)" if connected else "OFFLINE"
            if connected:
                status_label.classes(
                    replace=(
                        'text-xs px-3 py-1 bg-green-900/40 text-green-300 '
                        'border border-green-500 rounded font-bold'
                    )
                )
            else:
                status_label.classes(
                    replace=(
                        'text-xs px-3 py-1 bg-red-900/40 text-red-400 '
                        'border border-red-500 rounded font-bold'
                    )
                )
        except Exception as e:
            print(f"[ERROR] update_loop: {e}")
            import traceback
            traceback.print_exc()

    # Timer NiceGUI qui déclenche update_loop régulièrement
    ui.timer(UI_UPDATE_INTERVAL, update_loop)
