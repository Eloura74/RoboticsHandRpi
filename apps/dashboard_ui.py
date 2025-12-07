# --------------------------------------------------------------------
# COMPOSANTS D'INTERFACE UTILISATEUR (NICEGUI)
# --------------------------------------------------------------------
"""
Ce module contient tous les composants de l'interface NiceGUI :
- Header avec badge de statut et navigation
- Panneau vidéo (caméra MJPEG)
- Panneau de contrôle (boutons, rotation pouce, urgence)
- Panneau 3D de visualisation de la main
- Panneau de configuration des servos
- Panneau de télémétrie
- Boucle de mise à jour de l'interface
"""

import json
import time
import math
import os
from nicegui import ui

from apps.dashboard_config import MJPEG_URL, FINGERS, UI_UPDATE_INTERVAL
from apps.dashboard_network import state, state_lock

# Chemin vers le fichier de config servos
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'servos_v2.json')


# --------------------------------------------------------------------
# COMPOSANTS UI
# --------------------------------------------------------------------

def build_header():
    """
    Construit le header de l'interface (logo + titre + badge de statut + bouton menu).
    
    Returns:
        tuple: (status_label, menu_button)
            - status_label: Le label de statut pour mise à jour ultérieure.
            - menu_button: Le bouton pour ouvrir le menu latéral.
    """
    with ui.header().classes('bg-transparent p-0 elevation-0'):
        with ui.row().classes(
            'hud-header w-full h-[6vh] min-h-[50px] '
            'items-center justify-between px-6 sm:px-8'
        ):
            # Partie Gauche : Bouton Menu + Logo + Titre
            with ui.row().classes('items-center gap-4'):
                # Bouton Menu (Burger)
                menu_button = ui.button(icon='menu').classes('text-cyan-400 bg-transparent')
                
                # Logo SVG personnalisé (Nœud Neuronal Hexagonal)
                ui.html('''
                    <svg class="logo-glow" width="32" height="32" viewBox="0 0 100 100" fill="none" stroke="#00f3ff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M50 20 L80 35 L80 65 L50 80 L20 65 L20 35 Z" />
                        <circle cx="50" cy="50" r="12" fill="#00f3ff" fill-opacity="0.3" />
                        <path d="M50 50 L50 20 M50 50 L80 65 M50 50 L20 65" stroke-width="4" opacity="0.8" />
                    </svg>
                ''', sanitize=False)
                
                with ui.column().classes('gap-0'):
                    ui.label('NEURO-HAND V1.0') \
                        .classes('text-lg sm:text-xl text-cyan-400 font-black tracking-widest title-glow uppercase')
                    ui.label('NEURO-LINK // SYSTEM ONLINE') \
                        .classes('text-[10px] text-gray-400 tracking-wider')

            # Partie Centrale : Animation Ligne de Vie (ECG - SVG) - Version Large Restaurée
            with ui.element('div').classes('lifeline-container'):
                ui.html('''
                    <svg class="ecg-svg" viewBox="0 0 1000 100" preserveAspectRatio="none">
                        <path class="ecg-path" d="
                            M0,50 L100,50 
                            L110,50 L120,40 L130,60 L140,50 
                            L150,50 L160,50 L165,40 L170,50 L180,50 L185,20 L190,80 L195,50 L205,50 
                            L215,50 L220,40 L225,60 L235,50 
                            L300,50
                            L310,50 L320,40 L330,60 L340,50 
                            L350,50 L360,50 L365,40 L370,50 L380,50 L385,20 L390,80 L395,50 L405,50 
                            L415,50 L420,40 L425,60 L435,50 
                            L500,50
                            L510,50 L520,40 L530,60 L540,50 
                            L550,50 L560,50 L565,40 L570,50 L580,50 L585,20 L590,80 L595,50 L605,50 
                            L615,50 L620,40 L625,60 L635,50 
                            L700,50
                            L710,50 L720,40 L730,60 L740,50 
                            L750,50 L760,50 L765,40 L770,50 L780,50 L785,20 L790,80 L795,50 L805,50 
                            L815,50 L820,40 L825,60 L835,50 
                            L1000,50
                        " />
                    </svg>
                ''', sanitize=False).classes('w-full h-full')

            # Partie Droite : Badge de statut (ONLINE/OFFLINE)
            status_label = ui.label('INIT') \
                .classes(
                    'text-xs px-3 py-1 bg-red-900/40 text-red-400 '
                    'border border-red-500 rounded font-bold'
                )
    
    return status_label, menu_button


def build_camera_panel():
    """
    Construit le panneau vidéo avec flux MJPEG et overlay HUD.
    """
    with ui.card().classes(
        'w-full h-[32vh] min-h-[220px] hud-panel p-0 overflow-hidden '
        'relative video-panel'
    ):
        # Bandeau titre avec indicateur CAM-01
        with ui.row().classes(
            'absolute top-0 left-0 right-0 z-20 px-3 py-1 '
            'items-center justify-between bg-black/40'
        ):
            ui.label('OPTICAL FEED') \
                .classes('text-[10px] text-cyan-400 font-orbitron tracking-[0.2em]')
            ui.label('CAM-01') \
                .classes('text-[10px] px-2 py-[1px] rounded-full '
                         'border border-cyan-500/60 text-cyan-300 font-orbitron')

        # Flux MJPEG depuis le PC
        ui.image(MJPEG_URL).classes('w-full h-full object-cover')

        # Overlay HUD : cadre + coins + ligne de scan animée
        ui.html('''
            <div class="video-hud-frame">
                <div class="video-hud-corner vh-tl"></div>
                <div class="video-hud-corner vh-tr"></div>
                <div class="video-hud-corner vh-bl"></div>
                <div class="video-hud-corner vh-br"></div>
                <div class="scan-line"></div>
            </div>
        ''', sanitize=False)


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
        ''', sanitize=False)

        # En-tête : titre + badge LIVE LINK
        with ui.column().classes('items-center gap-1 w-full z-20'):
            ui.label('CONTROL NODES') \
                .classes('hud-section-title text-lg')
            ui.label('HAND ACTUATOR BUS') \
                .classes('hud-section-caption')
            ui.label('LIVE LINK') \
                .classes('hud-chip mt-1')
        
        ui.html('<div class="w-full h-[1px] bg-cyan-900/50"></div>', sanitize=False)

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

        ui.html('<div class="w-full h-[1px] bg-cyan-900/50"></div>', sanitize=False)

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
    
    Args:
        hand_3d_structure: HTML de la structure 3D.
        hand_3d_js: Code JavaScript pour l'animation 3D.
    """
    with ui.card().classes(
        'flex-1 h-full hud-panel p-0 overflow-hidden relative panel-3d-bg'
    ):
        # Structure 3D (Canvas)
        ui.html(hand_3d_structure, sanitize=False).classes('w-full h-full relative z-0')
        
        # Overlay HUD Futuriste
        ui.html('''
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
        ''', sanitize=False)

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


def build_telemetry_panel():
    """
    Construit le panneau de télémétrie système.
    """
    with ui.column().classes('w-full h-full p-6 gap-6'):
        ui.label('SYSTEM TELEMETRY').classes('hud-section-title text-xl mb-4')

        # Section Réseau
        with ui.card().classes('hud-panel w-full p-4'):
            ui.label('NETWORK STATUS').classes('text-cyan-400 font-bold mb-4')
            
            with ui.row().classes('w-full justify-around'):
                # Jauge FPS
                with ui.column().classes('items-center'):
                    fps_label = ui.label('0').classes('text-4xl font-mono text-green-400')
                    ui.label('UDP PACKETS/SEC').classes('text-xs text-gray-400')
                
                # Compteur total
                with ui.column().classes('items-center'):
                    count_label = ui.label('0').classes('text-4xl font-mono text-blue-400')
                    ui.label('TOTAL PACKETS').classes('text-xs text-gray-400')

        # Section Hardware (Placeholders)
        with ui.grid(columns=3).classes('w-full gap-4'):
            # Voltage
            with ui.card().classes('hud-panel p-4 items-center'):
                ui.icon('battery_charging_full', size='lg', color='yellow-400')
                ui.label('VOLTAGE').classes('text-xs text-gray-400 mt-2')
                ui.label('5.1 V').classes('text-2xl font-mono text-yellow-400') # Mock
            
            # Current
            with ui.card().classes('hud-panel p-4 items-center'):
                ui.icon('electric_bolt', size='lg', color='red-400')
                ui.label('CURRENT').classes('text-xs text-gray-400 mt-2')
                ui.label('1.2 A').classes('text-2xl font-mono text-red-400') # Mock

            # CPU Temp (Rpi)
            with ui.card().classes('hud-panel p-4 items-center'):
                ui.icon('thermostat', size='lg', color='orange-400')
                ui.label('CPU TEMP').classes('text-xs text-gray-400 mt-2')
                ui.label('42°C').classes('text-2xl font-mono text-orange-400') # Mock

        # Timer pour mettre à jour les stats réelles
        def update_telemetry():
            with state_lock:
                fps_label.text = str(state['fps'])
                count_label.text = str(state['packet_count'])

        ui.timer(0.5, update_telemetry)


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
