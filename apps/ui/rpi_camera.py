"""
Module UI pour le panneau webcam RPi.
Affiche un overlay toggle-able avec le flux MJPEG de la webcam locale du Raspberry Pi.
"""
from nicegui import ui
from core.config_loader import config


def build_rpi_camera_overlay(visible_state):
    """
    Construit un panneau overlay affichable/masquable avec le flux webcam du RPi.
    
    Positionné en haut gauche du canvas 3D, ce panneau permet de visualiser
    la main robotique en temps réel depuis la webcam locale du Raspberry Pi.
    
    Args:
        visible_state: Dictionnaire réactif avec clé 'show' (bool) pour l'affichage.
    
    Returns:
        L'élément overlay créé.
    """
    # Construction de l'URL du flux MJPEG depuis la config
    mjpeg_url = config.network.rpi_camera_url
    
    # Conteneur overlay avec positionnement absolu
    with ui.element('div').classes(
        'rpi-camera-overlay absolute top-4 left-4 z-50 '
        'transition-all duration-300'
    ).bind_visibility_from(visible_state, 'show') as overlay:
        
        # Card avec style futuriste cohérent
        with ui.card().classes(
            'w-[320px] h-auto hud-panel p-0 overflow-hidden '
            'border-2 border-cyan-500/60 shadow-lg shadow-cyan-500/20'
        ):
            # Bandeau titre avec label CAM-02 et bouton fermeture
            with ui.row().classes(
                'w-full px-3 py-1 bg-black/60 items-center justify-between'
            ):
                ui.label('RPi WEBCAM') \
                    .classes('text-[10px] text-cyan-400 font-orbitron tracking-[0.2em]')
                
                ui.label('CAM-02') \
                    .classes('text-[10px] px-2 py-[1px] rounded-full '
                             'border border-cyan-500/60 text-cyan-300 font-orbitron')
                
                # Bouton fermeture ×
                ui.button(
                    icon='close',
                    on_click=lambda: visible_state.update({'show': False})
                ).props('flat dense round size=sm').classes(
                    'text-cyan-400 hover:text-cyan-200 hover:bg-cyan-900/30 '
                    'transition-colors duration-200'
                )
            
            # Flux MJPEG de la webcam RPi
            ui.image(mjpeg_url).classes(
                'w-full h-[240px] object-cover bg-black'
            )
            
            # Overlay HUD : coins animés
            ui.html('''
                <div class="video-hud-frame" style="pointer-events: none;">
                    <div class="video-hud-corner vh-tl"></div>
                    <div class="video-hud-corner vh-tr"></div>
                    <div class="video-hud-corner vh-bl"></div>
                    <div class="video-hud-corner vh-br"></div>
                </div>
            ''')
    
    return overlay
