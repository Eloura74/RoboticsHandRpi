"""
Module camera pour le dashboard NEURO-HAND.
Construit le panneau vidéo avec flux MJPEG et overlay HUD.
"""
from nicegui import ui
from core.config_loader import config


def build_camera_panel():
    """
    Construit le panneau vidéo avec flux MJPEG et overlay HUD.
    
    Affiche :
    - Flux vidéo MJPEG depuis le PC de tracking
    - Overlay HUD futuriste avec coins animés
    - Bandeau titre avec indicateur CAM-01
    - Ligne de scan animée
    
    Returns:
        ui.card: Le panneau caméra configuré.
    """
    with ui.card().classes(
        'w-full h-[32vh] min-h-[220px] hud-panel p-0 overflow-hidden '
        'relative video-panel'
    ) as panel:
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

        # Flux MJPEG depuis le PC (URL depuis config)
        mjpeg_url = config.network.mjpeg_url
        ui.image(mjpeg_url).classes('w-full h-full object-cover')

        # Overlay HUD : cadre + coins + ligne de scan animée
        ui.html('''
            <div class="video-hud-frame">
                <div class="video-hud-corner vh-tl"></div>
                <div class="video-hud-corner vh-tr"></div>
                <div class="video-hud-corner vh-bl"></div>
                <div class="video-hud-corner vh-br"></div>
                <div class="scan-line"></div>
            </div>
        ''')
    
    return panel
