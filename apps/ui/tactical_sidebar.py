# --------------------------------------------------------------------
# TACTICAL SIDEBAR - Colonne de gauche unifiée style HUD
# --------------------------------------------------------------------
"""
Panneau latéral tactique unifié pour le dashboard NEURO-HAND.

Architecture :
1. OPTICAL FEED (Vision) : Flux caméra avec overlay HUD
2. ACTUATOR CONTROL (Action) : Commandes principales + rotation pouce
3. MACRO SEQUENCES (Gestes) : Grille 3x3 d'icônes
4. SYSTEM TELEMETRY (Monitoring) : Barres de progression + mini-console

Style : Cyberpunk/HUD avec cartes unifiées (cyber-card), bordures lumineuses,
       clip-path polygonal pour les boutons critiques.
"""

from nicegui import ui
from apps.dashboard_network import state, state_lock


# =====================================================================
# STYLES CSS TACTICAL SIDEBAR
# =====================================================================
CYBER_STYLES = """
<style>
    /* Carte holographique */
    .cyber-card {
        background: rgba(0, 20, 30, 0.3) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 243, 255, 0.4);
        border-radius: 6px;
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 0 20px rgba(0, 243, 255, 0.2),
            inset 0 0 20px rgba(0, 243, 255, 0.05),
            0 4px 12px rgba(0, 0, 0, 0.6);
    }
    
    /* Coin supérieur droit lumineux + effet glow global */
    .cyber-card::before {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 15px; height: 15px;
        border-top: 2px solid rgba(0, 243, 255, 1);
        border-right: 2px solid rgba(0, 243, 255, 1);
        box-shadow: 0 0 12px rgba(0, 243, 255, 0.8);
    }
    
    .cyber-card::after {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(
            circle at center,
            rgba(0, 243, 255, 0.05) 0%,
            transparent 70%
        );
        pointer-events: none;
    }
    
    /* Bouton primaire holographique avec clip-path */
    .cyber-btn-primary {
        background: rgba(0, 243, 255, 0.08) !important;
        backdrop-filter: blur(5px) !important;
        border: 1.5px solid rgba(0, 243, 255, 0.6) !important;
        color: rgb(0, 243, 255) !important;
        text-shadow: 0 0 8px rgba(0, 243, 255, 0.6);
        transition: all 0.3s ease !important;
        clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 0.15em !important;
        box-shadow: 
            0 0 15px rgba(0, 243, 255, 0.3),
            inset 0 0 10px rgba(0, 243, 255, 0.05);
    }
    
    .cyber-btn-primary:hover {
        background: rgba(0, 243, 255, 0.2) !important;
        box-shadow: 
            0 0 25px rgba(0, 243, 255, 0.8),
            inset 0 0 15px rgba(0, 243, 255, 0.15) !important;
        text-shadow: 0 0 12px rgba(0, 243, 255, 1);
        border-color: rgba(0, 243, 255, 1) !important;
        transform: translateY(-2px);
    }
    
    /* Bouton danger holographique avec clip-path */
    .cyber-btn-danger {
        background: rgba(239, 68, 68, 0.08) !important;
        backdrop-filter: blur(5px) !important;
        border: 1.5px solid rgba(239, 68, 68, 0.6) !important;
        color: rgb(248, 113, 113) !important;
        text-shadow: 0 0 8px rgba(239, 68, 68, 0.6);
        transition: all 0.3s ease !important;
        clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 0.15em !important;
        box-shadow: 
            0 0 15px rgba(239, 68, 68, 0.3),
            inset 0 0 10px rgba(239, 68, 68, 0.05);
    }
    
    .cyber-btn-danger:hover {
        background: rgba(239, 68, 68, 0.2) !important;
        box-shadow: 
            0 0 25px rgba(239, 68, 68, 0.8),
            inset 0 0 15px rgba(239, 68, 68, 0.15) !important;
        text-shadow: 0 0 12px rgba(239, 68, 68, 1);
        border-color: rgba(239, 68, 68, 1) !important;
        transform: translateY(-2px);
    }
    
    /* Boutons secondaires */
    .cyber-btn-secondary {
        background: rgba(100, 116, 139, 0.1) !important;
        border: 1px solid rgba(100, 116, 139, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    
    .cyber-btn-secondary:hover {
        background: rgba(100, 116, 139, 0.2) !important;
        border-color: rgba(0, 243, 255, 0.5) !important;
    }
    
    /* LED indicateur de connexion */
    .status-led {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        transition: all 0.3s ease;
    }
    
    .status-led.connected {
        background: #00ff00;
        box-shadow: 0 0 10px #00ff00, 0 0 20px rgba(0, 255, 0, 0.5);
    }
    
    .status-led.disconnected {
        background: #ff0000;
        box-shadow: 0 0 10px #ff0000, 0 0 20px rgba(255, 0, 0, 0.5);
    }
    
    /* Scanline effect holographique */
    .scanline {
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 1), transparent);
        opacity: 0.8;
        animation: scan 3s linear infinite;
        position: absolute;
        top: 0;
        left: 0;
        pointer-events: none;
        z-index: 10;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.8);
    }
    
    @keyframes scan {
        0% { top: 0%; }
        100% { top: 100%; }
    }
    
    /* Barre de progression système */
    .system-bar {
        height: 6px;
        background: rgba(30, 41, 59, 0.8);
        border-radius: 2px;
        overflow: hidden;
        position: relative;
    }
    
    .system-bar-fill {
        height: 100%;
        transition: width 0.5s ease;
        box-shadow: 0 0 8px currentColor;
    }
    
    /* Console de logs mini */
    .mini-console {
        background: rgba(0, 0, 0, 0.6);
        border-top: 1px solid rgba(0, 243, 255, 0.2);
        font-family: 'Share Tech Mono', monospace;
        font-size: 8px;
        color: rgba(156, 163, 175, 0.8);
        line-height: 1.3;
        overflow-y: auto;
    }
    
    .mini-console::-webkit-scrollbar {
        width: 2px;
    }
    
    .mini-console::-webkit-scrollbar-thumb {
        background: rgba(0, 243, 255, 0.3);
    }
</style>
"""


def build_tactical_sidebar(controller, local_ip: str, udp_port: int):
    """
    Construit la sidebar tactique complète pour la colonne de gauche.
    
    Sections :
    1. OPTICAL FEED : Flux caméra avec overlay HUD
    2. ACTUATOR CONTROL : Commandes principales (OPEN/CLOSE/STOP/SIM) + rotation pouce
    3. MACRO SEQUENCES : Grille 3x3 de gestes rapides
    4. SYSTEM TELEMETRY : Monitoring CPU/RAM/TEMP + mini-console
    
    Args:
        controller: Instance de HandController
        local_ip: IP locale du RPi
        udp_port: Port UDP d'écoute
    """
    # Injection des styles
    ui.add_head_html(CYBER_STYLES)
    
    with ui.column().classes('w-full h-full gap-2 p-2'):
        
        # =================================================================
        # 1. OPTICAL FEED (Vision)
        # =================================================================
        with ui.column().classes('w-full cyber-card p-0 relative group').style('height: 220px;'):
            # Flux MJPEG depuis le PC (config)
            from core.config_loader import config
            mjpeg_url = config.network.mjpeg_url  # http://{pc_ip}:{mjpeg_port}/cam.mjpg
            ui.image(mjpeg_url).classes('w-full h-full object-cover opacity-90')
            
            # Overlay HUD
            ui.label('OPTICAL FEED // CAM-01').classes(
                'absolute top-2 left-2 text-[9px] text-cyan-400 font-mono tracking-widest '
                'bg-black/70 px-2 py-1 z-10 border-l-2 border-cyan-500'
            )
            
            # Badge résolution (coin supérieur droit)
            ui.label('640x480').classes(
                'absolute top-2 right-2 text-[8px] text-gray-400 font-mono '
                'bg-black/70 px-1 z-10'
            )
            
            # Scanline effect
            ui.html('<div class="scanline"></div>')
        
        
        # =================================================================
        # 2. ACTUATOR CONTROL (Action)
        # =================================================================
        with ui.column().classes('w-full cyber-card p-2 gap-2').style('height: 220px;'):
            # Header avec LED de statut
            with ui.row().classes('w-full items-center justify-between mb-1'):
                ui.label('ACTUATOR CONTROL').classes(
                    'text-[9px] text-cyan-400 font-bold tracking-[0.25em] uppercase'
                )
                
                # LED de connexion dynamique
                status_led = ui.html('<div class="status-led disconnected"></div>')
                
                def update_connection_status():
                    """Met à jour l'indicateur de connexion UDP."""
                    with state_lock:
                        connected = state.get('udp_connected', False)
                    
                    css_class = 'connected' if connected else 'disconnected'
                    status_led.content = f'<div class="status-led {css_class}"></div>'
                
                ui.timer(1.0, update_connection_status)
            
            # Boutons principaux (Grille 2x2)
            with ui.grid(columns=2).classes('w-full gap-2'):
                # OPEN (bouton primaire)
                ui.button(
                    'OPEN',
                    on_click=lambda: controller.open_hand()
                ).props('no-caps').classes(
                    'cyber-btn-primary h-10 font-bold text-sm'
                )
                
                # CLOSE (bouton danger)
                ui.button(
                    'CLOSE',
                    on_click=lambda: controller.close_hand()
                ).props('no-caps').classes(
                    'cyber-btn-danger h-10 font-bold text-sm'
                )
                
                # STOP (secondaire)
                ui.button(
                    'STOP',
                    icon='stop',
                    on_click=lambda: controller.stop_all()
                ).props('outline no-caps dense').classes(
                    'cyber-btn-secondary h-8 text-[8px] text-orange-400 border-orange-500/50'
                )
                
                # SIMULATE (secondaire)
                def toggle_sim():
                    with state_lock:
                        state['simu_mode'] = not state['simu_mode']
                
                ui.button(
                    'SIM',
                    icon='dns',
                    on_click=toggle_sim
                ).props('outline no-caps dense').classes(
                    'cyber-btn-secondary h-8 text-[8px] text-purple-400 border-purple-500/50'
                )
            
            # Contrôle du pouce (Slider horizontal avec chevrons)
            ui.label('THUMB ROTATION AXIS').classes(
                'text-[7px] text-gray-500 mt-1 tracking-wider uppercase'
            )
            
            with ui.row().classes('w-full items-center gap-1'):
                # Bouton rotation gauche
                ui.button(
                    icon='chevron_left',
                    on_click=lambda: controller.thumb_rotation_step(-1)
                ).props('flat dense').classes(
                    'text-cyan-400 hover:text-cyan-300 w-7 h-7'
                )
                
                # Barre de visualisation de l'axe (avec reset au clic)
                with ui.element('div').classes(
                    'flex-1 h-1.5 bg-gray-800/50 rounded-sm overflow-hidden relative cursor-pointer '
                    'hover:bg-gray-700/50 transition-colors border border-cyan-900/30'
                ).on('click', lambda: controller.thumb_rotation_reset()):
                    # Indicateur central (position neutre)
                    ui.html('''
                        <div style="
                            position: absolute;
                            left: 50%;
                            transform: translateX(-50%);
                            width: 30%;
                            height: 100%;
                            background: linear-gradient(90deg, transparent, #00f3ff, transparent);
                            opacity: 0.4;
                        "></div>
                    ''')
                
                # Bouton rotation droite
                ui.button(
                    icon='chevron_right',
                    on_click=lambda: controller.thumb_rotation_step(1)
                ).props('flat dense').classes(
                    'text-cyan-400 hover:text-cyan-300 w-7 h-7'
                )
        
        
        # =================================================================
        # 3. MACRO SEQUENCES (Gestes rapides)
        # =================================================================
        with ui.column().classes('w-full cyber-card p-2 gap-1'):
            ui.label('MACRO SEQUENCES').classes(
                'text-[9px] text-cyan-400 font-bold tracking-[0.25em] uppercase'
            )
            
            # Grille 3x3 d'icônes compacte
            gestures = [
                ('pan_tool_alt', 'REST', 'rest'),
                ('sports_mma', 'FIST', 'fist'),
                ('waving_hand', 'WAVE', 'peace_sign'),
                ('thumb_up', 'LIKE', 'thumbs_up'),
                ('ads_click', 'POINT', 'pointing'),
                ('check_circle', 'OK', 'ok_sign')
            ]
            
            with ui.grid(columns=3).classes('w-full gap-1 mt-1'):
                for icon_name, label, gesture_key in gestures:
                    def execute_gesture(key=gesture_key):
                        """Exécute un geste pré-enregistré."""
                        from core.gesture_presets import GesturePresets
                        presets = GesturePresets(controller)
                        success = presets.execute(key, parallel=True)
                        if success:
                            ui.notify(f"Executing: {label}", type='positive', position='top', timeout=800)
                    
                    with ui.button(
                        on_click=execute_gesture
                    ).props('flat dense').classes(
                        'h-11 bg-slate-800/30 border border-cyan-700/30 '
                        'hover:border-cyan-400/60 hover:bg-cyan-900/20 transition-all '
                        'p-0 flex flex-col items-center justify-center gap-[1px]'
                    ).style('backdrop-filter: blur(5px);'):
                        ui.icon(icon_name, size='xs').classes('text-cyan-300/80')
                        ui.label(label).classes('text-[6px] text-cyan-400/70 leading-none tracking-wider')
        
        
        # =================================================================
        # 4. SYSTEM TELEMETRY (Monitoring)
        # =================================================================
        with ui.column().classes('w-full cyber-card p-2 gap-1'):
            ui.label('SYSTEM TELEMETRY').classes(
                'text-[9px] text-cyan-400 font-bold tracking-[0.25em] uppercase'
            )
            
            # Fonction helper pour les barres de progression
            def create_status_bar(label: str, color: str):
                """Crée une barre de progression système."""
                with ui.row().classes('w-full items-center gap-2 text-[8px] mt-1'):
                    ui.label(label).classes('w-9 text-gray-400 font-mono text-right')
                    
                    with ui.element('div').classes('flex-1 system-bar'):
                        bar = ui.element('div').classes(f'system-bar-fill {color}')
                        bar.style('width: 0%')  # Sera mis à jour dynamiquement
                    
                    value_label = ui.label('--').classes(
                        f'w-7 text-right font-mono font-bold text-[8px] {color.replace("bg-", "text-")}'
                    )
                
                return bar, value_label
            
            # Créer les barres
            cpu_bar, cpu_label = create_status_bar('CPU', 'bg-cyan-500')
            ram_bar, ram_label = create_status_bar('RAM', 'bg-purple-500')
            temp_bar, temp_label = create_status_bar('TEMP', 'bg-orange-500')
            
            # Fonction de mise à jour des métriques
            def update_telemetry():
                """Met à jour les barres de progression système."""
                try:
                    from apps.ui.system_health_panel import get_system_metrics
                    metrics = get_system_metrics()
                    
                    # CPU
                    cpu_pct = metrics['cpu_percent']
                    cpu_bar.style(f'width: {cpu_pct}%')
                    cpu_label.set_text(f'{cpu_pct:.0f}%')
                    
                    # RAM
                    ram_pct = metrics['ram_percent']
                    ram_bar.style(f'width: {ram_pct}%')
                    ram_label.set_text(f'{ram_pct:.0f}%')
                    
                    # Température
                    temp = metrics['temp_celsius']
                    if temp:
                        temp_normalized = min(temp, 100)  # Normaliser à 100°C max
                        temp_bar.style(f'width: {temp_normalized}%')
                        temp_label.set_text(f'{temp:.0f}C')
                    else:
                        temp_bar.style('width: 0%')
                        temp_label.set_text('N/A')
                except Exception as e:
                    print(f"[WARN] Telemetry update error: {e}")
            
            # Timer de mise à jour
            ui.timer(2.0, update_telemetry)
            
            # Mini-console de logs
            with ui.element('div').classes('w-full mini-console mt-1 p-1').style('height: 35px;'):
                ui.label('[SYS] Daemon ready').classes('block text-[7px]')
                ui.label(f'[NET] UDP:{udp_port}').classes('block text-[7px]')
