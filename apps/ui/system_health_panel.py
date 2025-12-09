# --------------------------------------------------------------------
# PANNEAU DE SANTÉ SYSTÈME
# --------------------------------------------------------------------
"""
Panneau de monitoring système pour le dashboard.

Affiche en temps réel :
- CPU, RAM, température
- Statistiques réseau (UDP)
- État des servos
- Alertes automatiques
"""

from nicegui import ui
from apps.dashboard_network import state, state_lock
import psutil
import platform


def get_system_metrics():
    """
    Récupère les métriques système actuelles.
    
    Returns:
        dict: Dictionnaire avec métriques CPU, RAM, température, etc.
    """
    metrics = {
        'cpu_percent': 0,
        'ram_percent': 0,
        'ram_used_mb': 0,
        'ram_total_mb': 0,
        'temp_celsius': None,
        'disk_percent': 0,
        'uptime_seconds': 0
    }
    
    try:
        # CPU
        metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
        
        # RAM
        ram = psutil.virtual_memory()
        metrics['ram_percent'] = ram.percent
        metrics['ram_used_mb'] = ram.used / (1024 * 1024)
        metrics['ram_total_mb'] = ram.total / (1024 * 1024)
        
        # Température (Raspberry Pi ou Windows avec psutil.sensors_temperatures)
        try:
            # Essai 1 : Raspberry Pi
            if platform.machine().startswith('arm') or platform.machine().startswith('aarch'):
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp_str = f.read().strip()
                    metrics['temp_celsius'] = int(temp_str) / 1000.0
            # Essai 2 : Windows/Linux avec sensors (psutil)
            elif hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Prendre la première température disponible
                    for name, entries in temps.items():
                        if entries:
                            metrics['temp_celsius'] = entries[0].current
                            break
        except:
            pass  # Pas de capteur de température disponible
        
        # Disque
        disk = psutil.disk_usage('/')
        metrics['disk_percent'] = disk.percent
        
        # Uptime
        boot_time = psutil.boot_time()
        import time
        metrics['uptime_seconds'] = time.time() - boot_time
    
    except Exception as e:
        print(f"[HEALTH] Erreur récupération métriques : {e}")
    
    return metrics


def format_uptime(seconds):
    """
    Formate le temps d'uptime en chaîne lisible.
    
    Args:
        seconds: Nombre de secondes.
    
    Returns:
        str: Chaîne formatée (ex: "2h 15m")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def build_system_health_compact():
    """
    Construit un panneau compact de santé système.
    
    À intégrer dans le panneau gauche sous les contrôles.
    Hauteur ~100px.
    """
    with ui.card().classes(
        'w-full panel-3d-bg px-4 py-3 flex flex-col gap-2 relative overflow-hidden'
    ).style('min-height: 90px;'):
        
        # HUD Overlay
        ui.html('''
            <div class="hud-overlay">
                <div class="hud-corner hud-tl"></div>
                <div class="hud-corner hud-tr"></div>
                <div class="hud-corner hud-bl"></div>
                <div class="hud-corner hud-br"></div>
            </div>
        ''')
        
        # Header avec marqueur visuel
        with ui.row().classes('items-center gap-1 z-20'):
            # Barre verticale cyan
            ui.html('<div style="width:3px; height:12px; background:linear-gradient(to bottom, #22d3ee, transparent); box-shadow:0 0 8px #22d3ee;"></div>')
            ui.label('SYSTEM STATUS').classes(
                'hud-section-title text-[10px] tracking-[0.25em] uppercase'
            )
        
        # Grille de métriques compacte - 4 lignes
        with ui.column().classes('w-full gap-[3px] z-20 mt-2 text-[8px] font-mono'):
            # CPU
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('CPU').classes('text-gray-500 tracking-wider')
                cpu_value = ui.label('--').classes('text-cyan-400 font-bold')
            
            # RAM
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('RAM').classes('text-gray-500 tracking-wider')
                ram_value = ui.label('--').classes('text-cyan-400 font-bold')
            
            # Température
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('TEMP').classes('text-gray-500 tracking-wider')
                temp_value = ui.label('--').classes('text-cyan-400 font-bold')
            
            # FPS UDP
            with ui.row().classes('w-full justify-between items-center'):
                ui.label('UDP').classes('text-gray-500 tracking-wider')
                fps_value = ui.label('--').classes('text-cyan-400 font-bold')
        
        # Fonction de mise à jour
        def update_metrics():
            try:
                metrics = get_system_metrics()
                
                # CPU
                cpu_percent = metrics['cpu_percent']
                cpu_value.set_text(f"{cpu_percent:.0f}%")
                
                # Couleur selon niveau
                if cpu_percent > 80:
                    cpu_value.classes(remove='text-cyan-400 text-yellow-400', add='text-red-400')
                elif cpu_percent > 60:
                    cpu_value.classes(remove='text-cyan-400 text-red-400', add='text-yellow-400')
                else:
                    cpu_value.classes(remove='text-red-400 text-yellow-400', add='text-cyan-400')
                
                # RAM
                ram_percent = metrics['ram_percent']
                ram_used = metrics['ram_used_mb']
                ram_value.set_text(f"{ram_percent:.0f}% ({ram_used:.0f}M)")
                
                if ram_percent > 85:
                    ram_value.classes(remove='text-cyan-400 text-yellow-400', add='text-red-400')
                elif ram_percent > 70:
                    ram_value.classes(remove='text-cyan-400 text-red-400', add='text-yellow-400')
                else:
                    ram_value.classes(remove='text-red-400 text-yellow-400', add='text-cyan-400')
                
                # Température
                temp = metrics['temp_celsius']
                if temp is not None:
                    temp_value.set_text(f"{temp:.0f}C")
                    
                    if temp > 70:
                        temp_value.classes(remove='text-cyan-400 text-yellow-400', add='text-red-400')
                    elif temp > 55:
                        temp_value.classes(remove='text-cyan-400 text-red-400', add='text-yellow-400')
                    else:
                        temp_value.classes(remove='text-red-400 text-yellow-400', add='text-cyan-400')
                else:
                    temp_value.set_text('N/A')
                    temp_value.classes(remove='text-red-400 text-yellow-400', add='text-gray-600')
                
                # FPS UDP
                with state_lock:
                    fps = state.get('fps', 0)
                    connected = state.get('udp_connected', False)
                
                fps_value.set_text(f"{fps}pkt/s" if connected else "OFF")
                
                if not connected:
                    fps_value.classes(remove='text-cyan-400', add='text-red-400')
                else:
                    fps_value.classes(remove='text-red-400', add='text-cyan-400')
            
            except Exception as e:
                # En cas d'erreur, afficher des valeurs par défaut (ne pas bloquer l'affichage)
                print(f"[WARNING] System health metrics error: {e}")
                try:
                    cpu_value.set_text('--')
                    ram_value.set_text('--')
                    temp_value.set_text('--')
                    fps_value.set_text('--')
                except:
                    pass  # Ne pas bloquer si les labels ne sont pas encore créés
        
        # Timer pour mise à jour (démarrage immédiat puis toutes les 2 secondes)
        ui.timer(0.1, update_metrics, once=True)  # Premier update rapide
        ui.timer(2.0, update_metrics)  # Updates continus


def build_system_health_full_panel():
    """
    Construit un panneau complet de santé système pour un onglet dédié.
    
    Inclut :
    - Graphiques temps réel
    - Historique CPU/RAM
    - Alertes et recommandations
    - Statistiques détaillées
    """
    with ui.column().classes('w-full h-full p-6 gap-6 overflow-y-auto'):
        
        # ================================================================
        # HEADER
        # ================================================================
        ui.label('SYSTEM HEALTH MONITOR').classes('hud-section-title text-xl')
        ui.label('Real-time performance metrics and alerts') \
            .classes('text-sm text-gray-400 -mt-4 mb-4')
        
        # ================================================================
        # MÉTRIQUES PRINCIPALES - Cards
        # ================================================================
        with ui.row().classes('w-full gap-4'):
            # Card CPU
            with ui.card().classes('config-card flex-1 p-4'):
                ui.label('CPU USAGE').classes('text-xs text-cyan-400 font-bold tracking-wider mb-2')
                cpu_gauge = ui.linear_progress(value=0).props('size=25px color=cyan')
                cpu_text = ui.label('0%').classes('text-2xl font-bold text-cyan-400 mt-2')
                cpu_status = ui.label('Normal').classes('text-xs text-green-400')
            
            # Card RAM
            with ui.card().classes('config-card flex-1 p-4'):
                ui.label('MEMORY USAGE').classes('text-xs text-cyan-400 font-bold tracking-wider mb-2')
                ram_gauge = ui.linear_progress(value=0).props('size=25px color=purple')
                ram_text = ui.label('0%').classes('text-2xl font-bold text-purple-400 mt-2')
                ram_status = ui.label('Normal').classes('text-xs text-green-400')
            
            # Card Température
            with ui.card().classes('config-card flex-1 p-4'):
                ui.label('TEMPERATURE').classes('text-xs text-cyan-400 font-bold tracking-wider mb-2')
                temp_gauge = ui.linear_progress(value=0).props('size=25px color=orange')
                temp_text = ui.label('N/A').classes('text-2xl font-bold text-orange-400 mt-2')
                temp_status = ui.label('Normal').classes('text-xs text-green-400')
            
            # Card UDP
            with ui.card().classes('config-card flex-1 p-4'):
                ui.label('NETWORK UDP').classes('text-xs text-cyan-400 font-bold tracking-wider mb-2')
                udp_badge = ui.label('OFFLINE').classes('text-lg font-bold text-red-400 mt-4')
                udp_fps = ui.label('0 pkt/s').classes('text-sm text-gray-400 mt-2')
        
        # ================================================================
        # STATISTIQUES DÉTAILLÉES
        # ================================================================
        ui.html('<div class="w-full h-[2px] bg-cyan-900/30 my-4"></div>')
        
        ui.label('DETAILED STATISTICS').classes('hud-section-title text-lg mb-2')
        
        with ui.grid(columns=2).classes('w-full gap-4'):
            # Colonne gauche : Système
            with ui.card().classes('config-card p-4'):
                ui.label('SYSTEM INFO').classes('text-xs text-cyan-400 font-bold tracking-wider mb-3')
                
                system_info = ui.column().classes('gap-1 text-xs')
                
                # Infos statiques
                platform_info = platform.uname()
                with system_info:
                    with ui.row().classes('justify-between w-full'):
                        ui.label('Platform:').classes('text-gray-400')
                        ui.label(platform_info.system).classes('text-cyan-400')
                    
                    with ui.row().classes('justify-between w-full'):
                        ui.label('Architecture:').classes('text-gray-400')
                        ui.label(platform_info.machine).classes('text-cyan-400')
                    
                    with ui.row().classes('justify-between w-full'):
                        ui.label('Python:').classes('text-gray-400')
                        ui.label(platform.python_version()).classes('text-cyan-400')
                    
                    uptime_row = ui.row().classes('justify-between w-full')
                    with uptime_row:
                        ui.label('Uptime:').classes('text-gray-400')
                        uptime_label = ui.label('0m').classes('text-cyan-400')
            
            # Colonne droite : Réseau
            with ui.card().classes('config-card p-4'):
                ui.label('NETWORK STATS').classes('text-xs text-cyan-400 font-bold tracking-wider mb-3')
                
                network_stats = ui.column().classes('gap-1 text-xs')
                
                with network_stats:
                    with ui.row().classes('justify-between w-full'):
                        ui.label('UDP Status:').classes('text-gray-400')
                        net_status_label = ui.label('OFFLINE').classes('text-red-400')
                    
                    with ui.row().classes('justify-between w-full'):
                        ui.label('Packets/sec:').classes('text-gray-400')
                        net_fps_label = ui.label('0').classes('text-cyan-400')
                    
                    with ui.row().classes('justify-between w-full'):
                        ui.label('Total packets:').classes('text-gray-400')
                        net_total_label = ui.label('0').classes('text-cyan-400')
        
        # ================================================================
        # ALERTES ET RECOMMANDATIONS
        # ================================================================
        ui.html('<div class="w-full h-[2px] bg-cyan-900/30 my-4"></div>')
        
        ui.label('ALERTS & RECOMMENDATIONS').classes('hud-section-title text-lg mb-2')
        
        alerts_container = ui.column().classes('w-full gap-2')
        
        # ================================================================
        # FONCTION DE MISE À JOUR COMPLÈTE
        # ================================================================
        def update_full_metrics():
            metrics = get_system_metrics()
            
            # CPU
            cpu = metrics['cpu_percent']
            cpu_gauge.set_value(cpu / 100.0)
            cpu_text.set_text(f"{cpu:.0f}%")
            
            if cpu > 80:
                cpu_status.set_text('⚠️ High')
                cpu_status.classes(remove='text-green-400 text-yellow-400', add='text-red-400')
            elif cpu > 60:
                cpu_status.set_text('⚡ Elevated')
                cpu_status.classes(remove='text-green-400 text-red-400', add='text-yellow-400')
            else:
                cpu_status.set_text('✓ Normal')
                cpu_status.classes(remove='text-red-400 text-yellow-400', add='text-green-400')
            
            # RAM
            ram = metrics['ram_percent']
            ram_gauge.set_value(ram / 100.0)
            ram_text.set_text(f"{ram:.0f}%")
            
            if ram > 85:
                ram_status.set_text('⚠️ Critical')
                ram_status.classes(remove='text-green-400 text-yellow-400', add='text-red-400')
            elif ram > 70:
                ram_status.set_text('⚡ High')
                ram_status.classes(remove='text-green-400 text-red-400', add='text-yellow-400')
            else:
                ram_status.set_text('✓ Normal')
                ram_status.classes(remove='text-red-400 text-yellow-400', add='text-green-400')
            
            # Température
            temp = metrics['temp_celsius']
            if temp is not None:
                temp_gauge.set_value(min(temp / 85.0, 1.0))  # 85°C = max
                temp_text.set_text(f"{temp:.0f}°C")
                
                if temp > 70:
                    temp_status.set_text('🔥 HOT!')
                    temp_status.classes(remove='text-green-400 text-yellow-400', add='text-red-400')
                elif temp > 55:
                    temp_status.set_text('⚡ Warm')
                    temp_status.classes(remove='text-green-400 text-red-400', add='text-yellow-400')
                else:
                    temp_status.set_text('✓ Cool')
                    temp_status.classes(remove='text-red-400 text-yellow-400', add='text-green-400')
            
            # UDP
            with state_lock:
                fps = state.get('fps', 0)
                connected = state.get('udp_connected', False)
                total_packets = state.get('packet_count', 0)
            
            if connected:
                udp_badge.set_text('🟢 ONLINE')
                udp_badge.classes(remove='text-red-400', add='text-green-400')
                net_status_label.set_text('CONNECTED')
                net_status_label.classes(remove='text-red-400', add='text-green-400')
            else:
                udp_badge.set_text('🔴 OFFLINE')
                udp_badge.classes(remove='text-green-400', add='text-red-400')
                net_status_label.set_text('DISCONNECTED')
                net_status_label.classes(remove='text-green-400', add='text-red-400')
            
            udp_fps.set_text(f"{fps} pkt/s")
            net_fps_label.set_text(f"{fps}")
            net_total_label.set_text(f"{total_packets:,}")
            
            # Uptime
            uptime_label.set_text(format_uptime(metrics['uptime_seconds']))
            
            # ================================================================
            # GÉNÉRATION D'ALERTES DYNAMIQUES
            # ================================================================
            alerts_container.clear()
            
            with alerts_container:
                if cpu > 80:
                    with ui.card().classes('bg-red-900/20 border border-red-500/40 p-3'):
                        ui.label('⚠️ CPU Usage Critical').classes('text-sm text-red-400 font-bold')
                        ui.label(f'CPU at {cpu:.0f}% - Consider reducing background processes or optimizing hand_tracker.py') \
                            .classes('text-xs text-gray-400')
                
                if ram > 85:
                    with ui.card().classes('bg-red-900/20 border border-red-500/40 p-3'):
                        ui.label('⚠️ Memory Critical').classes('text-sm text-red-400 font-bold')
                        ui.label(f'RAM at {ram:.0f}% - System may become unstable. Restart recommended.') \
                            .classes('text-xs text-gray-400')
                
                if temp is not None and temp > 70:
                    with ui.card().classes('bg-orange-900/20 border border-orange-500/40 p-3'):
                        ui.label('🔥 Temperature Warning').classes('text-sm text-orange-400 font-bold')
                        ui.label(f'CPU temp at {temp:.0f}°C - Improve cooling or reduce load') \
                            .classes('text-xs text-gray-400')
                
                if not connected:
                    with ui.card().classes('bg-yellow-900/20 border border-yellow-500/40 p-3'):
                        ui.label('🔌 Network Disconnected').classes('text-sm text-yellow-400 font-bold')
                        ui.label('No UDP packets received. Check hand_tracker.py is running.') \
                            .classes('text-xs text-gray-400')
                
                # Message si tout va bien
                if cpu < 60 and ram < 70 and (temp is None or temp < 55) and connected:
                    with ui.card().classes('bg-green-900/20 border border-green-500/40 p-3'):
                        ui.label('✅ All Systems Nominal').classes('text-sm text-green-400 font-bold')
                        ui.label('System operating within normal parameters.') \
                            .classes('text-xs text-gray-400')
        
        # Timer mise à jour (toutes les 2 secondes)
        ui.timer(2.0, update_full_metrics)


# ================================================================
# EXPORTS
# ================================================================
__all__ = [
    'build_system_health_compact',
    'build_system_health_full_panel'
]
