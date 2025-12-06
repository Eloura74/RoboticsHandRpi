# --------------------------------------------------------------------
# COMPOSANTS D'INTERFACE UTILISATEUR (NICEGUI)
# --------------------------------------------------------------------
"""
Ce module contient tous les composants de l'interface NiceGUI :
- Header avec badge de statut
- Panneau vidéo (caméra MJPEG)
- Panneau de contrôle (boutons, rotation pouce, urgence)
- Panneau 3D de visualisation de la main
- Boucle de mise à jour de l'interface
"""

import json
import time
import math
from nicegui import ui

from apps.dashboard_config import MJPEG_URL, FINGERS, UI_UPDATE_INTERVAL
from apps.dashboard_network import state, state_lock


# --------------------------------------------------------------------
# COMPOSANTS UI
# --------------------------------------------------------------------

def build_header():
    """
    Construit le header de l'interface (logo + titre + badge de statut).
    
    Returns:
        ui.label: Le label de statut pour mise à jour ultérieure.
    """
    with ui.row().classes(
        'hud-header w-full h-[3vh] min-h-[40px] '
        'items-center justify-between px-6 sm:px-8'
    ):
        # Logo et titre principal
        with ui.row().classes('items-center gap-4'):
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

        # Animation Ligne de Vie (ECG - SVG)
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

        # Badge de statut (ONLINE/OFFLINE)
        status_label = ui.label('INIT') \
            .classes(
                'text-xs px-3 py-1 bg-red-900/40 text-red-400 '
                'border border-red-500 rounded font-bold'
            )
    
    return status_label


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
                on_click=lambda: controller.open_hand()
            ).classes('w-full h-12 cyber-btn-glitch cyber-btn-open text-base')

            ui.button(
                'CLOSE',
                icon='back_hand',
                on_click=lambda: controller.close_hand()
            ).classes('w-full h-12 cyber-btn-glitch cyber-btn-close text-base')

            def toggle_sim():
                """Bascule le mode simulation (génération sinusoïdale des valeurs)."""
                with state_lock:
                    state['simu_mode'] = not state['simu_mode']

            ui.button(
                'SIMULATION MODE',
                icon='memory',
                on_click=toggle_sim
            ).classes('w-full h-12 cyber-btn-glitch cyber-btn-sim text-xs')

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
