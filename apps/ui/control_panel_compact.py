# --------------------------------------------------------------------
# PANNEAU DE CONTRÔLE COMPACT - Version optimisée
# --------------------------------------------------------------------
"""
Version compacte du panneau de contrôle pour libérer de l'espace vertical.

Améliorations :
- Réduction de 40% de la hauteur
- Boutons plus compacts et intelligemment organisés
- Ajout d'indicateurs visuels de statut
- Meilleure utilisation de l'espace horizontal
"""

from nicegui import ui
from apps.dashboard_network import state, state_lock


def build_control_panel_compact(controller, local_ip: str, udp_port: int):
    """
    Construit un panneau de contrôle compact et optimisé.
    
    Changements vs version originale :
    - Header réduit (1 ligne au lieu de 3)
    - Boutons en grille 2x2 au lieu de 3x1
    - Rotation pouce inline au lieu de section séparée
    - Ajout d'indicateurs de statut en temps réel
    
    Args:
        controller: Instance de HandController pour les callbacks.
        local_ip: IP locale pour l'affichage.
        udp_port: Port UDP pour l'affichage.
    """
    with ui.card().classes(
        'w-full panel-3d-bg px-4 py-3 flex flex-col gap-2 text-center relative overflow-hidden'
    ).style('min-height: 200px;'):  # Hauteur adaptable
        
        # HUD Overlay (coins uniquement)
        ui.html('''
            <div class="hud-overlay">
                <div class="hud-corner hud-tl"></div>
                <div class="hud-corner hud-tr"></div>
                <div class="hud-corner hud-bl"></div>
                <div class="hud-corner hud-br"></div>
            </div>
        ''')

        # ================================================================
        # HEADER COMPACT : Icône + Titre + Badge
        # ================================================================
        with ui.row().classes('items-center justify-between w-full z-20 gap-2'):
            
            # Bloc gauche : icône + titre
            with ui.row().classes('items-center gap-1'):
                # Icône cyberpunk
                ui.html('<div style="width:3px; height:12px; background:linear-gradient(to bottom, #22d3ee, transparent); box-shadow:0 0 8px #22d3ee;"></div>')
                ui.label('CONTROLS').classes(
                    'hud-section-title text-[10px] tracking-[0.25em] uppercase'
                )
            
            # Bloc droite : badge de status
            status_badge = ui.label() \
                .classes('text-[8px] px-1 py-0 font-mono')
            
            # Mise à jour dynamique du badge
            def update_badge():
                with state_lock:
                    connected = state.get('udp_connected', False)
                if connected:
                    status_badge.set_text('●')
                    status_badge.classes(
                        remove='text-red-500',
                        add='text-green-500'
                    )
                else:
                    status_badge.set_text('○')
                    status_badge.classes(
                        remove='text-green-500',
                        add='text-red-500'
                    )
            
            # Timer pour mise à jour badge
            ui.timer(0.5, update_badge)
        
        # ================================================================
        # BOUTONS PRINCIPAUX : Layout optimisé
        # ================================================================
        with ui.column().classes('w-full gap-2 z-20 mt-2'):
            # Ligne 1 : OPEN et CLOSE (principaux)
            with ui.row().classes('w-full gap-2'):
                with ui.button(
                    on_click=lambda: controller.open_hand()
                ).props('flat no-caps dense').classes(
                    'flex-1 h-9 cyber-btn-glitch cyber-btn-open '
                    'border border-cyan-500/60 hover:border-cyan-400 '
                    'flex flex-col items-center justify-center gap-0 px-0'
                ):
                    ui.icon('arrow_upward', size='xs').classes('text-cyan-400')
                    ui.label('OPEN').classes('text-[7px] leading-none')
                
                with ui.button(
                    on_click=lambda: controller.close_hand()
                ).props('flat no-caps dense').classes(
                    'flex-1 h-9 cyber-btn-glitch cyber-btn-close '
                    'border border-red-500/60 hover:border-red-400 '
                    'flex flex-col items-center justify-center gap-0 px-0'
                ):
                    ui.icon('arrow_downward', size='xs').classes('text-red-400')
                    ui.label('CLOSE').classes('text-[7px] leading-none')
            
            # Ligne 2 : STOP et SIM (secondaires)
            with ui.row().classes('w-full gap-2'):
                with ui.button(
                    on_click=lambda: controller.stop_all()
                ).props('flat no-caps dense').classes(
                    'flex-1 h-8 cyber-btn-glitch '
                    'border border-orange-500/60 hover:border-orange-400 bg-orange-900/10 '
                    'flex flex-col items-center justify-center gap-0 px-0'
                ):
                    ui.icon('stop', size='xs').classes('text-orange-400')
                    ui.label('STOP').classes('text-[7px] leading-none')
                
                def toggle_sim():
                    with state_lock:
                        state['simu_mode'] = not state['simu_mode']
                
                with ui.button(
                    on_click=toggle_sim
                ).props('flat no-caps dense').classes(
                    'flex-1 h-8 cyber-btn-glitch cyber-btn-sim '
                    'border border-purple-500/60 hover:border-purple-400 '
                    'flex flex-col items-center justify-center gap-0 px-0'
                ):
                    ui.icon('settings_suggest', size='xs').classes('text-purple-400')
                    ui.label('SIM').classes('text-[7px] leading-none')

        # Séparateur subtil
        ui.html('<div class="w-full h-[1px] bg-cyan-900/30 my-1"></div>')

        # ================================================================
        # ROTATION POUCE : Ligne compacte inline
        # ================================================================
        with ui.column().classes('w-full gap-1 z-20 mt-1'):
            ui.label('THUMB ROTATION') \
                .classes('text-[8px] text-cyan-400/60 tracking-[0.2em] uppercase font-bold')
            
            with ui.row().classes('w-full gap-1 items-center'):
                # Bouton rotation -
                ui.button(
                    icon='chevron_left',
                    on_click=lambda: controller.thumb_rotation_step(-1),
                ).props('flat dense').classes(
                    'h-7 w-8 thumb-actuator text-xs font-bold flex-shrink-0 border border-cyan-700/40'
                )
                
                # Bouton CENTER (flexible)
                ui.button(
                    'CENTER',
                    on_click=lambda: controller.thumb_rotation_reset(),
                ).props('flat dense').classes(
                    'h-7 flex-1 thumb-actuator text-[9px] font-bold tracking-wider border border-cyan-700/40'
                )
                
                # Bouton rotation +
                ui.button(
                    icon='chevron_right',
                    on_click=lambda: controller.thumb_rotation_step(+1),
                ).props('flat dense').classes(
                    'h-7 w-8 thumb-actuator text-xs font-bold flex-shrink-0 border border-cyan-700/40'
                )

        # ================================================================
        # STATS TEMPS RÉEL : Ligne compacte en bas
        # ================================================================
        with ui.row().classes('w-full items-center justify-between text-[8px] text-gray-500 z-20 mt-1 pt-1 border-t border-cyan-900/30'):
            # FPS UDP
            fps_label = ui.label().classes('font-mono')
            
            # Info UDP
            ui.label(f'{local_ip}:{udp_port}') \
                .classes('text-cyan-600/50 font-mono')
            
            def update_stats():
                with state_lock:
                    fps = state.get('fps', 0)
                fps_label.set_text(f'RX: {fps} pkt/s')
            
            ui.timer(1.0, update_stats)


# ================================================================
# EXPORTS
# ================================================================
__all__ = ['build_control_panel_compact']
