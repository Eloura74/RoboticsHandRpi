# apps/neuro_dashboard_pro.py
# Interface moderne NEUROLINK CORE avec design industrial/aerospace

import sys
import json
import socket
import time
import threading
import os
import signal
import subprocess
import psutil
from pathlib import Path
from nicegui import ui, app

# --------------------------------------------------------------------
# 1. SETUP & IMPORTS
# --------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from core.hand_controller import HandController
except ImportError:
    class HandController:
        def open_hand(self, parallel=True): pass
        def close_hand(self, parallel=True): pass
        def open_finger(self, f, parallel=False): pass
        def close_finger(self, f, parallel=False): pass
        def stop_all(self): pass
        def shutdown(self): pass

# --------------------------------------------------------------------
# 2. CONFIGURATION
# --------------------------------------------------------------------
PC_IP = '192.168.1.10'
MJPEG_PORT = 8090
MJPEG_URL = f'http://{PC_IP}:{MJPEG_PORT}/cam.mjpg'

UDP_IP = '0.0.0.0'
UDP_PORT = 5005

OPEN_THRESHOLD = 0.30
CLOSE_THRESHOLD = 0.70
LOST_TIMEOUT = 3.0

FINGERS = ['pouce_articulation', 'index', 'majeur', 'annulaire_auriculaire']

controller = None 

# --------------------------------------------------------------------
# 3. GESTION DES PROCESSUS FANTÔMES
# --------------------------------------------------------------------
def kill_port_hog(port):
    try:
        cmd = f"lsof -t -i:{port}"
        pid = subprocess.check_output(cmd, shell=True).decode().strip()
        if pid:
            current_pid = str(os.getpid())
            if pid != current_pid:
                print(f"[SYSTEM] Processus fantôme détecté sur le port {port} (PID {pid}). TERMINATION...")
                os.kill(int(pid), signal.SIGKILL)
                time.sleep(1)
                print("[SYSTEM] Port libéré.")
    except Exception:
        pass 

# --------------------------------------------------------------------
# 4. ÉTAT PARTAGÉ & LOGIQUE UDP
# --------------------------------------------------------------------
state_lock = threading.Lock()
state = {
    'values': {name: 0.0 for name in FINGERS},
    'udp_connected': False,
    'last_message': 'Système en attente...',
    'fps': 0,
    'cpu': 0,
    'mem': 0,
    'temp': 0,
    'voltage': 5.1,
    'history': [],  # Historique pour graphique
    'uptime': 0,
    'total_packets': 0,
    'errors': 0,
    'hand_detected': False
}

def udp_worker(ctrl_ref):
    """Thread UDP avec mouvements parallèles"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((UDP_IP, UDP_PORT))
    except OSError as e:
        print(f"[FATAL] Impossible de lier le port {UDP_PORT}: {e}")
        return

    sock.settimeout(0.2)
    print(f"[UDP] Réception active sur {UDP_PORT}")

    logical_state = {name: 'open' for name in FINGERS}
    last_packet_time = time.time()
    hand_visible = False
    packet_counter = 0
    t0 = time.time()
    start_time = time.time()
    total_packets = 0
    error_count = 0

    while True:
        now = time.time()

        # Watchdog
        if hand_visible and (now - last_packet_time > LOST_TIMEOUT):
            try: 
                ctrl_ref.open_hand(parallel=True)
            except: pass
            hand_visible = False
            logical_state = {name: 'open' for name in FINGERS}
            with state_lock:
                state['values'] = {name: 0.0 for name in FINGERS}
                state['udp_connected'] = False
                state['hand_detected'] = False
                state['last_message'] = '⚠️ SIGNAL PERDU - SÉCURITÉ'

        # Réception UDP
        try:
            data, _ = sock.recvfrom(4096)
        except socket.timeout:
            continue
        except Exception:
            time.sleep(0.05)
            continue

        # Calcul FPS et statistiques
        packet_counter += 1
        total_packets += 1
        if now - t0 > 1.0:
            with state_lock: 
                state['fps'] = packet_counter
                state['uptime'] = int(now - start_time)
                state['total_packets'] = total_packets
                state['errors'] = error_count
            packet_counter = 0
            t0 = now

        raw = data.decode('utf-8', errors='ignore').strip()
        if not raw: 
            error_count += 1
            continue
        
        try: msg = json.loads(raw)
        except: 
            error_count += 1
            continue

        hand_visible = True
        last_packet_time = now

        # Mise à jour valeurs & Hardware
        with state_lock:
            state['udp_connected'] = True
            state['hand_detected'] = True
            
        temp_values = state['values'].copy()
        
        for finger in FINGERS:
            if finger not in msg: continue
            try:
                val = float(msg[finger])
                val = max(0.0, min(1.0, val))
                temp_values[finger] = val
                
                current = logical_state.get(finger, 'open')
                if val > CLOSE_THRESHOLD and current != 'close':
                    ctrl_ref.close_finger(finger, parallel=True)
                    logical_state[finger] = 'close'
                elif val < OPEN_THRESHOLD and current != 'open':
                    ctrl_ref.open_finger(finger, parallel=True)
                    logical_state[finger] = 'open'
            except: continue
            
        with state_lock:
            state['values'] = temp_values
            if packet_counter % 20 == 0:
                state['last_message'] = 'Tracking actif - Données reçues'

# Thread système monitoring
def system_monitor():
    """Monitore CPU, MEM, TEMP"""
    while True:
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            
            # Température (Raspberry Pi)
            try:
                temp_output = subprocess.check_output(['vcgencmd', 'measure_temp']).decode()
                temp = float(temp_output.replace('temp=', '').replace("'C\n", ''))
            except:
                temp = 0
            
            with state_lock:
                state['cpu'] = cpu
                state['mem'] = mem
                state['temp'] = temp
                
                # Historique charge globale (moyenne des servos)
                avg = sum(state['values'].values()) / len(state['values']) if state['values'] else 0
                state['history'].append(avg * 100)
                if len(state['history']) > 100:
                    state['history'].pop(0)
                    
        except Exception as e:
            print(f"[MONITOR] Erreur: {e}")
        
        time.sleep(1)

# --------------------------------------------------------------------
# 5. INTERFACE MODERNE
# --------------------------------------------------------------------
def build_ui():
    # CSS Modern Industrial
    ui.add_head_html('''
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
        
        :root {
            --primary: #00d4ff;
            --secondary: #0a7ea4;
            --danger: #ff3860;
            --success: #00ff9d;
            --warning: #ffb800;
            --bg-dark: #0a0e1a;
            --bg-panel: #111827;
            --bg-card: #1a202c;
            --border: #2d3748;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
        }

        * {
            font-family: 'Inter', sans-serif;
        }

        .mono {
            font-family: 'JetBrains Mono', monospace;
        }

        body {
            background: var(--bg-dark);
            color: var(--text-primary);
            overflow: hidden;
            margin: 0;
        }

        .panel {
            background: var(--bg-panel);
            border: 1px solid var(--border);
            border-radius: 8px;
        }

        .progress-bar {
            height: 20px;
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid var(--border);
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            transition: width 0.1s ease-out;
            box-shadow: 0 0 10px var(--primary);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
        }

        .status-online { 
            background: var(--success); 
            box-shadow: 0 0 8px var(--success);
            animation: pulse-online 2s ease-in-out infinite;
        }
        .status-offline { 
            background: var(--danger);
            opacity: 0.5;
        }
        
        @keyframes pulse-online {
            0%, 100% { box-shadow: 0 0 8px var(--success); }
            50% { box-shadow: 0 0 16px var(--success); }
        }

        .btn-modern {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 12px 24px;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-modern:hover {
            background: var(--bg-panel);
            border-color: var(--primary);
        }

        .btn-danger {
            background: rgba(255, 56, 96, 0.2);
            border-color: var(--danger);
            color: var(--danger);
        }

        .btn-danger:hover {
            background: var(--danger);
            color: white;
        }

        .terminal {
            background: #000000;
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            line-height: 1.4;
            color: var(--success);
            max-height: 200px;
            overflow-y: auto;
        }

        .terminal::-webkit-scrollbar {
            width: 6px;
        }

        .terminal::-webkit-scrollbar-track {
            background: #000;
        }

        .terminal::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 3px;
        }

        .slider-modern {
            width: 100%;
        }

        .value-label {
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            color: var(--primary);
            font-weight: 600;
        }
    </style>
    ''')

    finger_names = {
        'pouce_articulation': 'THUMB',
        'index': 'INDEX',
        'majeur': 'MIDDLE',
        'annulaire_auriculaire': 'RING'
    }

    # Refs UI
    status_dot = None
    status_text = None
    voltage_label = None
    fps_label = None
    servo_bars = {}
    servo_labels = {}
    terminal_label = None
    cpu_label = None
    mem_label = None
    temp_label = None
    chart_container = None
    stats_uptime = None
    stats_packets = None
    stats_errors = None
    hand_indicator = None

    # ============= HEADER =============
    with ui.row().classes('w-full h-14 items-center justify-between px-6 border-b').style(
        'background: var(--bg-panel); border-color: var(--border);'
    ):
        # Logo + Titre
        with ui.row().classes('items-center gap-3'):
            ui.html('<div style="width:32px;height:32px;background:linear-gradient(135deg,var(--primary),var(--secondary));border-radius:6px;display:flex;align-items:center;justify-content:center;font-weight:bold;">N</div>', sanitize=False)
            with ui.column().classes('gap-0'):
                ui.label('NEUROLINK').classes('text-xl font-bold').style('color: var(--primary); letter-spacing: 1px;')
                ui.label('CORE SYSTEM V3.3').classes('text-[0.6rem]').style('color: var(--text-secondary); letter-spacing: 2px;')

        # Status
        with ui.row().classes('items-center gap-6'):
            with ui.row().classes('items-center gap-2'):
                status_dot = ui.html('<span class="status-dot status-offline"></span>', sanitize=False)
                status_text = ui.label('OFFLINE').classes('text-xs font-semibold mono').style('color: var(--text-secondary);')
            
            with ui.row().classes('items-center gap-2'):
                ui.icon('speed', size='18px').style('color: var(--primary);')
                fps_label = ui.label('0 PPS').classes('text-xs mono').style('color: var(--text-secondary);')
            
            with ui.row().classes('items-center gap-2'):
                ui.icon('power', size='18px').style('color: var(--warning);')
                voltage_label = ui.label('5.1V').classes('text-xs mono').style('color: var(--text-secondary);')

            ui.button('ARRÊT D\'URGENCE', on_click=lambda: controller.stop_all() if controller else None).classes('btn-modern btn-danger text-xs font-bold px-4 py-2')

    # ============= MAIN GRID =============
    with ui.row().classes('w-full p-4 gap-4 no-wrap').style('height: calc(100vh - 56px);'):

        # ========== LEFT PANEL : TÉLÉMÉTRIE SERVOS ==========
        with ui.column().classes('panel p-4').style('width: 280px; height: 100%;'):
            ui.label('SERVO METRICS').classes('text-sm font-semibold mb-4').style('color: var(--primary);')
            
            # Barres servos
            for finger in FINGERS:
                with ui.column().classes('mb-4'):
                    with ui.row().classes('justify-between items-center mb-1'):
                        ui.label(finger_names[finger]).classes('text-xs font-medium').style('color: var(--text-secondary);')
                        servo_labels[finger] = ui.label('0%').classes('text-xs mono value-label')
                    
                    # Barre de progression personnalisée
                    with ui.element('div').classes('progress-bar'):
                        servo_bars[finger] = ui.element('div').classes('progress-fill').style('width: 0%;')

            ui.separator().classes('my-4').style('background: var(--border);')

            # Graphique charge moteur
            ui.label('CHARGE MOTEUR GLOBALE').classes('text-xs font-medium mb-2').style('color: var(--text-secondary);')
            chart_container = ui.element('div').style('width: 100%; height: 80px; position: relative;')
            ui.html('<canvas id="motor-chart" width="248" height="80"></canvas>', sanitize=False).move(chart_container)

            ui.separator().classes('my-4').style('background: var(--border);')

            # Infos système
            with ui.row().classes('justify-between'):
                ui.label('CPU RPi:').classes('text-xs').style('color: var(--text-secondary);')
                cpu_label = ui.label('0%').classes('text-xs mono value-label')
            
            with ui.row().classes('justify-between'):
                ui.label('MEM:').classes('text-xs').style('color: var(--text-secondary);')
                mem_label = ui.label('0MB').classes('text-xs mono value-label')
            
            with ui.row().classes('justify-between'):
                ui.label('UPTIME:').classes('text-xs').style('color: var(--text-secondary);')
                temp_label = ui.label('0°C').classes('text-xs mono value-label')

        # ========== CENTER : CAMERA + TERMINAL ==========
        with ui.column().classes('flex-1 gap-4').style('height: 100%;'):
            # Caméra
            with ui.element('div').classes('panel flex-1 relative').style('overflow: hidden; background: #000;'):
                # Overlay HUD simple
                ui.label('LIVE FEED').classes('absolute top-2 left-2 text-xs mono px-2 py-1').style(
                    'background: rgba(0,0,0,0.7); color: var(--primary); border-left: 2px solid var(--primary); z-index: 10;'
                )
                
                hand_indicator = ui.label('HAND DETECTED').classes('absolute bottom-2 left-2 text-xs mono px-2 py-1 font-semibold').style(
                    'background: rgba(0,255,157,0.2); color: var(--success); border-left: 2px solid var(--success); z-index: 10; display: none;'
                )
                
                # Image stream direct - SIMPLE
                with ui.element('div').classes('w-full h-full').style('display: flex; align-items: center; justify-content: center;'):
                    ui.image(MJPEG_URL).classes('w-full h-full object-contain')

            # Terminal
            with ui.element('div').classes('panel').style('height: 180px;'):
                with ui.row().classes('items-center justify-between px-3 py-2 border-b').style('border-color: var(--border);'):
                    ui.label('SYSTEM TERMINAL').classes('text-xs font-medium').style('color: var(--text-secondary);')
                
                with ui.scroll_area().classes('terminal'):
                    terminal_label = ui.label('[00:00:00] System ready...').classes('mono')

        # ========== RIGHT PANEL : PARAMÈTRES ==========
        with ui.column().classes('panel p-4 gap-4').style('width: 280px; height: 100%;'):
            ui.label('CONTROL DECK').classes('text-sm font-semibold mb-2').style('color: var(--primary);')
            
            # Boutons OUVRIR/FERMER
            with ui.row().classes('gap-2 w-full'):
                ui.button('OPEN', on_click=lambda: controller.open_hand() if controller else None).classes('btn-modern flex-1 text-xs font-semibold')
                ui.button('CLOSE', on_click=lambda: controller.close_hand() if controller else None).classes('btn-modern flex-1 text-xs font-semibold')

            ui.separator().style('background: var(--border);')

            # Mode pince précision (toggle)
            with ui.row().classes('items-center justify-between w-full p-3').style('background: var(--bg-card); border-radius: 6px;'):
                ui.label('PRECISION MODE').classes('text-xs font-medium')
                ui.switch(value=False).props('color=primary')

            ui.separator().style('background: var(--border);')

            # Sliders avec icônes
            with ui.row().classes('items-center gap-2 w-full mb-1'):
                ui.icon('volume_up', size='16px').style('color: var(--primary);')
                ui.label('Gain (Amplification)').classes('text-xs font-medium').style('color: var(--text-secondary);')
            with ui.row().classes('items-center gap-2 w-full mb-3'):
                gain_slider = ui.slider(min=0, max=100, value=66).props('color=primary dense').classes('flex-1')
                gain_label = ui.label('66%').classes('text-xs mono value-label')

            with ui.row().classes('items-center gap-2 w-full mb-1'):
                ui.icon('waves', size='16px').style('color: var(--primary);')
                ui.label('Lissage (Smoothing)').classes('text-xs font-medium').style('color: var(--text-secondary);')
            with ui.row().classes('items-center gap-2 w-full mb-3'):
                smooth_slider = ui.slider(min=0, max=100, value=48).props('color=primary dense').classes('flex-1')
                smooth_label = ui.label('48%').classes('text-xs mono value-label')

            with ui.row().classes('items-center gap-2 w-full mb-1'):
                ui.icon('speed', size='16px').style('color: var(--warning);')
                ui.label('Limite de Force').classes('text-xs font-medium').style('color: var(--text-secondary);')
            with ui.row().classes('items-center gap-2 w-full mb-3'):
                force_slider = ui.slider(min=0, max=100, value=88).props('color=warning dense').classes('flex-1')
                force_label = ui.label('88%').classes('text-xs mono value-label')
            
            # Mise à jour des labels des sliders
            gain_slider.on('update:model-value', lambda e: gain_label.set_text(f"{int(e.args)}%"))
            smooth_slider.on('update:model-value', lambda e: smooth_label.set_text(f"{int(e.args)}%"))
            force_slider.on('update:model-value', lambda e: force_label.set_text(f"{int(e.args)}%"))

            ui.separator().style('background: var(--border);')

            # Calibration
            with ui.element('div').classes('p-3').style('background: var(--bg-card); border-radius: 6px;'):
                ui.label('CALIBRATION').classes('text-xs font-semibold mb-2')
                ui.label('Last: OK - Drift: 6.3h').classes('text-[0.65rem]').style('color: var(--text-secondary); line-height: 1.3;')
                ui.button('AUTO-CALIBRATE', icon='settings').classes('btn-modern w-full mt-2 text-xs')
            
            ui.separator().style('background: var(--border);')
            
            # Statistiques en temps réel
            with ui.element('div').classes('p-3').style('background: var(--bg-card); border-radius: 6px;'):
                ui.label('STATISTICS').classes('text-xs font-semibold mb-2')
                with ui.column().classes('gap-1'):
                    stats_uptime = ui.label('Uptime: --:--:--').classes('text-[0.65rem]').style('color: var(--text-secondary);')
                    stats_packets = ui.label('Packets: 0').classes('text-[0.65rem]').style('color: var(--text-secondary);')
                    stats_errors = ui.label('Errors: 0').classes('text-[0.65rem]').style('color: var(--text-secondary);')

    # ============= UPDATE LOOP =============
    def update_ui():
        with state_lock:
            current_state = dict(state)
        
        # 1. Barres servos
        vals = current_state['values']
        for finger, bar in servo_bars.items():
            val = vals.get(finger, 0.0)
            pct = int(val * 100)
            bar.style(f'width: {pct}%;')
            servo_labels[finger].text = f'{pct}%'
        
        # 2. Status UDP
        if current_state['udp_connected']:
            status_dot.set_content('<span class="status-dot status-online"></span>')
            status_text.text = 'ONLINE'
            status_text.style('color: var(--success);')
            fps_label.text = f'{current_state.get("fps", 0)} PPS'
        else:
            status_dot.set_content('<span class="status-dot status-offline"></span>')
            status_text.text = 'OFFLINE'
            status_text.style('color: var(--text-secondary);')
            fps_label.text = '0 PPS'
        
        # 3. Système
        cpu_label.text = f'{int(current_state["cpu"])}%'
        mem_label.text = f'{int(current_state["mem"])}%'
        temp_label.text = f'{int(current_state["temp"])}°C'
        voltage_label.text = f'{current_state["voltage"]:.1f}V'
        
        # 3b. Statistiques
        uptime_sec = current_state.get('uptime', 0)
        hours = uptime_sec // 3600
        minutes = (uptime_sec % 3600) // 60
        seconds = uptime_sec % 60
        stats_uptime.text = f'Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}'
        stats_packets.text = f'Packets: {current_state.get("total_packets", 0)}'
        stats_errors.text = f'Errors: {current_state.get("errors", 0)}'
        
        # 3c. Indicateur main détectée
        if current_state.get('hand_detected', False):
            hand_indicator.style('display: block;')
        else:
            hand_indicator.style('display: none;')
        
        # 4. Terminal
        msg = current_state['last_message']
        if msg:
            ts = time.strftime('%H:%M:%S')
            terminal_label.text = f'[{ts}] {msg}\n' + (terminal_label.text or '')[:500]

        # 5. Graphique (via JS)
        history = current_state.get('history', [])
        if len(history) > 0:
            ui.run_javascript(f'''
                const canvas = document.getElementById('motor-chart');
                if (canvas) {{
                    const ctx = canvas.getContext('2d');
                    const data = {history};
                    const w = canvas.width;
                    const h = canvas.height;
                    
                    ctx.clearRect(0, 0, w, h);
                    
                    // Grille
                    ctx.strokeStyle = '#2d3748';
                    ctx.lineWidth = 1;
                    for (let i = 0; i < 5; i++) {{
                        const y = (h / 4) * i;
                        ctx.beginPath();
                        ctx.moveTo(0, y);
                        ctx.lineTo(w, y);
                        ctx.stroke();
                    }}
                    
                    // Courbe
                    ctx.strokeStyle = '#00d4ff';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    
                    const step = w / (data.length - 1);
                    data.forEach((val, i) => {{
                        const x = i * step;
                        const y = h - (val / 100) * h;
                        if (i === 0) ctx.moveTo(x, y);
                        else ctx.lineTo(x, y);
                    }});
                    
                    ctx.stroke();
                    
                    // Glow effect
                    ctx.shadowColor = '#00d4ff';
                    ctx.shadowBlur = 10;
                    ctx.stroke();
                    ctx.shadowBlur = 0;
                }}
            ''')

    ui.timer(0.05, update_ui)

# --------------------------------------------------------------------
# 6. DÉMARRAGE
# --------------------------------------------------------------------
if __name__ in {"__main__", "__mp_main__"}:
    print("--- NEUROLINK CORE V3.3 - BOOT SEQUENCE ---")
    
    kill_port_hog(UDP_PORT)
    
    try:
        controller = HandController()
        print("[HARDWARE] Servo Controller Initialized (Parallel Mode).")
    except Exception as e:
        print(f"[ERREUR CRITIQUE] Hardware: {e}")
        sys.exit(1)
    
    # Thread UDP
    t_udp = threading.Thread(target=udp_worker, args=(controller,), daemon=True)
    t_udp.start()
    
    # Thread monitoring système
    t_mon = threading.Thread(target=system_monitor, daemon=True)
    t_mon.start()
    
    build_ui()
    
    ui.run(
        host='0.0.0.0', 
        port=8080, 
        reload=False,
        dark=True, 
        title='NEUROLINK CORE V3.3'
    )
