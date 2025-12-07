"""
Module de télémétrie système pour le dashboard NEURO-HAND.
Affiche les statistiques réseau et système en temps réel.
"""

import psutil
from nicegui import ui

from apps.dashboard_network import state, state_lock
from apps.ui.components import HUDCard, StatDisplay, ProgressBar


def build_telemetry_panel():
    """
    Construit le panneau de télémétrie système avec graphiques temps réel.
    Style HUD futuriste cohérent avec le reste du dashboard.
    """
    with ui.column().classes('w-full h-full p-6 gap-6 bg-transparent'):
        # Titre avec style HUD
        with ui.row().classes('w-full items-center gap-4 mb-2'):
            ui.label('SYSTEM TELEMETRY').classes('hud-section-title text-2xl tracking-[0.3em]')
            ui.label('MONITORING ACTIVE').classes('hud-chip text-[10px]')

        # Section Réseau - Utilisation de HUDCard
        with HUDCard('w-full p-6'):
            with ui.column().classes('gap-4 z-10 relative'):
                ui.label('NETWORK STATUS').classes('text-cyan-400 font-bold tracking-[0.2em] text-sm border-b border-cyan-900/50 pb-2')
                
                with ui.row().classes('w-full justify-around gap-8'):
                    # Jauge FPS - Style holographique
                    with ui.column().classes('items-center justify-center gap-2 flex-1'):
                        ui.label('UDP PACKETS/SEC').classes('hud-mini-label text-[10px]')
                        fps_label = ui.label('0').classes('text-5xl font-mono text-cyan-400 tracking-wider title-glow')
                        with ui.row().classes('gap-1 mt-1 items-center justify-center'):
                            ui.html('<div class="w-2 h-2 bg-cyan-500 rounded-full animate-pulse" style="box-shadow: 0 0 10px #00f3ff;"></div>')
                            ui.label('ACTIVE').classes('text-[8px] text-cyan-400')
                    
                    # Diviseur vertical
                    ui.html('<div class="w-[1px] h-16 bg-cyan-500/30" style="box-shadow: 0 0 5px rgba(0,243,255,0.3);"></div>')
                    
                    # Compteur total
                    with ui.column().classes('items-center justify-center gap-2 flex-1'):
                        ui.label('TOTAL PACKETS').classes('hud-mini-label text-[10px]')
                        count_label = ui.label('0').classes('text-5xl font-mono text-cyan-400 tracking-wider title-glow')
                        ui.label('RECEIVED').classes('text-[8px] text-gray-500')

        # Section Hardware - Utilisation de HUDCard, StatDisplay et ProgressBar
        with ui.row().classes('w-full gap-4'):
            # CPU Usage
            with HUDCard('flex-1 p-6 flex items-center justify-center'):
                with ui.column().classes('w-full'):
                    cpu_display = StatDisplay('memory', 'CPU USAGE', '0%', 'cyan', '4xl')
                    cpu_progress = ProgressBar('cpu-bar', 'cyan')
            
            # RAM Usage
            with HUDCard('flex-1 p-6 flex items-center justify-center'):
                with ui.column().classes('w-full'):
                    ram_display = StatDisplay('storage', 'RAM USAGE', '0%', 'blue', '4xl')
                    ram_progress = ProgressBar('ram-bar', 'blue')

            # CPU Freq
            with HUDCard('flex-1 p-6 flex items-center justify-center'):
                freq_display = StatDisplay('speed', 'CPU FREQUENCY', '0 MHz', 'teal', '4xl')

        # Graphique temps réel - Palette holographique
        with ui.card().classes('hud-panel w-full h-80 p-6 relative overflow-hidden'):
            ui.html('''
                <div class="hud-overlay">
                    <div class="hud-corner hud-tl"></div>
                    <div class="hud-corner hud-tr"></div>
                    <div class="hud-corner hud-bl"></div>
                    <div class="hud-corner hud-br"></div>
                </div>
            ''')
            
            with ui.column().classes('w-full h-full z-10 relative'):
                with ui.row().classes('w-full items-center justify-between mb-3'):
                    ui.label('SYSTEM LOAD HISTORY').classes('text-cyan-400 font-bold tracking-[0.2em] text-sm')
                    with ui.row().classes('gap-4 text-[10px]'):
                        ui.html('<div class="flex items-center gap-2"><div class="w-3 h-[2px] bg-cyan-400" style="box-shadow: 0 0 4px #00f3ff;"></div><span class="text-gray-400">CPU</span></div>')
                        ui.html('<div class="flex items-center gap-2"><div class="w-3 h-[2px] bg-blue-400" style="box-shadow: 0 0 4px #60a5fa;"></div><span class="text-gray-400">RAM</span></div>')
                
                chart = ui.echart({
                    'backgroundColor': 'transparent',
                    'grid': {
                        'left': '5%', 
                        'right': '5%', 
                        'top': '10%',
                        'bottom': '10%', 
                        'containLabel': True
                    },
                    'xAxis': {
                        'type': 'category', 
                        'boundaryGap': False, 
                        'data': [],
                        'axisLine': {'lineStyle': {'color': '#0e7490'}},
                        'axisLabel': {'color': '#6b7280', 'fontSize': 10},
                        'splitLine': {'show': False}
                    },
                    'yAxis': {
                        'type': 'value', 
                        'max': 100,
                        'axisLine': {'lineStyle': {'color': '#0e7490'}},
                        'axisLabel': {'color': '#6b7280', 'fontSize': 10, 'formatter': '{value}%'},
                        'splitLine': {'lineStyle': {'color': '#1e3a4a', 'type': 'dashed'}}
                    },
                    'series': [
                        {
                            'name': 'CPU', 
                            'type': 'line', 
                            'smooth': True, 
                            'data': [], 
                            'lineStyle': {'color': '#06b6d4', 'width': 2, 'shadowColor': 'rgba(6,182,212,0.5)', 'shadowBlur': 10},
                            'areaStyle': {
                                'color': {
                                    'type': 'linear',
                                    'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                                    'colorStops': [
                                        {'offset': 0, 'color': 'rgba(6, 182, 212, 0.4)'},
                                        {'offset': 1, 'color': 'rgba(6, 182, 212, 0)'}
                                    ]
                                }
                            },
                            'symbol': 'none'
                        },
                        {
                            'name': 'RAM', 
                            'type': 'line', 
                            'smooth': True, 
                            'data': [], 
                            'lineStyle': {'color': '#60a5fa', 'width': 2, 'shadowColor': 'rgba(96,165,250,0.5)', 'shadowBlur': 10},
                            'areaStyle': {
                                'color': {
                                    'type': 'linear',
                                    'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                                    'colorStops': [
                                        {'offset': 0, 'color': 'rgba(96, 165, 250, 0.4)'},
                                        {'offset': 1, 'color': 'rgba(96, 165, 250, 0)'}
                                    ]
                                }
                            },
                            'symbol': 'none'
                        }
                    ],
                    'tooltip': {
                        'trigger': 'axis',
                        'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                        'borderColor': '#00f3ff',
                        'borderWidth': 1,
                        'textStyle': {'color': '#fff'}
                    }
                }).classes('w-full flex-1')

        # Historique pour le graphique
        history_len = 30
        cpu_history = [0] * history_len
        ram_history = [0] * history_len

        # Timer pour mettre à jour les stats réelles
        def update_telemetry():
            # Network stats
            with state_lock:
                fps_label.text = str(state['fps'])
                count_label.text = str(state['packet_count'])

            # System stats (psutil)
            cpu_percent = psutil.cpu_percent()
            ram_percent = psutil.virtual_memory().percent
            cpu_freq = psutil.cpu_freq()
            freq_val = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A"

            # Utilisation des méthodes update des composants
            cpu_display.update(f"{cpu_percent:.1f}%")
            ram_display.update(f"{ram_percent:.1f}%")
            freq_display.update(freq_val)

            # Update progress bars avec les méthodes
            cpu_progress.update(cpu_percent)
            ram_progress.update(ram_percent)

            # Update Chart
            cpu_history.pop(0)
            cpu_history.append(cpu_percent)
            ram_history.pop(0)
            ram_history.append(ram_percent)
            
            chart.options['series'][0]['data'] = cpu_history
            chart.options['series'][1]['data'] = ram_history
            chart.update()

        ui.timer(1.0, update_telemetry)
