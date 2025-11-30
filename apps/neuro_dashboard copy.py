# apps/neuro_dashboard.py

import sys
import json
import socket
import time
import threading
import os
import signal
import subprocess
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
    # Mode mockup de secours
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

# Variable globale pour l'accès UI
controller = None 

# --------------------------------------------------------------------
# 3. GESTION DES PROCESSUS FANTÔMES (AUTO-KILL)
# --------------------------------------------------------------------
def kill_port_hog(port):
    """Tue tout processus utilisant le port UDP spécifié."""
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
# 4. ÉTAT PARTAGÉ & LOGIQUE UDP (AVEC MOUVEMENTS PARALLÈLES)
# --------------------------------------------------------------------
state_lock = threading.Lock()
state = {
    'values': {name: 0.0 for name in FINGERS},
    'udp_connected': False,
    'last_message': 'Système en attente...',
    'fps': 0
}

def udp_worker(ctrl_ref):
    """Thread UDP : Reçoit les données et commande le Hardware via la référence."""
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

    while True:
        now = time.time()

        # Watchdog
        if hand_visible and (now - last_packet_time > LOST_TIMEOUT):
            try: 
                # ✨ NOUVEAU : Mode parallèle pour ouverture de sécurité rapide
                ctrl_ref.open_hand(parallel=True)
            except: pass
            hand_visible = False
            logical_state = {name: 'open' for name in FINGERS}
            with state_lock:
                state['values'] = {name: 0.0 for name in FINGERS}
                state['udp_connected'] = False
                state['last_message'] = '⚠️ SIGNAL PERDU - SÉCURITÉ'

        # Réception
        try:
            data, _ = sock.recvfrom(4096)
        except socket.timeout:
            continue
        except Exception:
            time.sleep(0.05)
            continue

        # Calcul FPS UDP
        packet_counter += 1
        if now - t0 > 1.0:
            with state_lock: state['fps'] = packet_counter
            packet_counter = 0
            t0 = now

        raw = data.decode('utf-8', errors='ignore').strip()
        if not raw: continue
        
        try: msg = json.loads(raw)
        except: continue

        hand_visible = True
        last_packet_time = now

        # Mise à jour valeurs & Hardware
        with state_lock:
            state['udp_connected'] = True
            
        temp_values = state['values'].copy()
        
        for finger in FINGERS:
            if finger not in msg: continue
            try:
                val = float(msg[finger])
                val = max(0.0, min(1.0, val))
                temp_values[finger] = val
                
                # Hardware Logic
                current = logical_state.get(finger, 'open')
                if val > CLOSE_THRESHOLD and current != 'close':
                    # ✨ NOUVEAU : parallel=True pour mouvements fluides
                    ctrl_ref.close_finger(finger, parallel=True)
                    logical_state[finger] = 'close'
                elif val < OPEN_THRESHOLD and current != 'open':
                    # ✨ NOUVEAU : parallel=True pour mouvements fluides
                    ctrl_ref.open_finger(finger, parallel=True)
                    logical_state[finger] = 'open'
            except: continue
            
        with state_lock:
            state['values'] = temp_values
            if packet_counter % 20 == 0: # Log moins fréquent
                state['last_message'] = 'Tracking actif - Données reçues'

# --------------------------------------------------------------------
# 5. INTERFACE GRAPHIQUE (CYBERPUNK THEME)
# --------------------------------------------------------------------
def build_ui():
    # --- CSS FUTURISTE ---
    ui.add_head_html('''
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Share+Tech+Mono&display=swap');
        
        :root {
            --neon-cyan: #00f3ff;
            --neon-pink: #ff0055;
            --neon-yellow: #ffcc00;
            --bg-dark: #050a14;
            --panel-bg: rgba(10, 20, 40, 0.7);
        }

        body {
            background-color: var(--bg-dark);
            background-image: 
                linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
            background-size: 40px 40px;
            font-family: 'Rajdhani', sans-serif;
            color: #e0f7fa;
            overflow: hidden;
        }

        .cyber-panel {
            background: var(--panel-bg);
            border: 1px solid rgba(0, 243, 255, 0.2);
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.05);
            backdrop-filter: blur(5px);
            position: relative;
        }

        /* Coins HUD */
        .cyber-panel::before {
            content: ''; position: absolute; top: -1px; left: -1px;
            width: 10px; height: 10px;
            border-top: 2px solid var(--neon-cyan);
            border-left: 2px solid var(--neon-cyan);
        }
        .cyber-panel::after {
            content: ''; position: absolute; bottom: -1px; right: -1px;
            width: 10px; height: 10px;
            border-bottom: 2px solid var(--neon-cyan);
            border-right: 2px solid var(--neon-cyan);
        }

        .bar-container {
            background: rgba(0,0,0,0.5);
            border: 1px solid #333;
            border-radius: 2px;
            position: relative;
            overflow: hidden;
        }

        .bar-fill {
            transition: height 0.08s ease-out; /* Très fluide */
            box-shadow: 0 0 10px currentColor;
            width: 100%;
            position: absolute;
            bottom: 0;
            opacity: 0.9;
        }

        .scanline {
            width: 100%; height: 2px;
            background: rgba(0, 243, 255, 0.3);
            position: absolute; top: 0; left: 0;
            animation: scan 3s linear infinite;
            pointer-events: none;
            z-index: 50;
        }
        @keyframes scan { 0% {top:0%;} 100% {top:100%;} }

        .header-title { font-family: 'Share Tech Mono', monospace; letter-spacing: 2px; }
    </style>
    ''')

    bars = {}
    finger_conf = [
        ('index', 'INDEX', 'var(--neon-cyan)'),
        ('majeur', 'MIDDLE', '#bd00ff'),
        ('annulaire_auriculaire', 'RING/PINKY', 'var(--neon-pink)'),
        ('pouce_articulation', 'THUMB', 'var(--neon-yellow)'),
    ]
    
    # UI REF
    udp_status = None
    log_label = None

    # --- HEADER ---
    with ui.row().classes('w-full h-[8vh] items-center justify-between px-6 border-b border-cyan-900/30 bg-[#020617]/80'):
        with ui.row().classes('items-center gap-3'):
            ui.icon('hub', color='cyan-400').classes('text-2xl animate-pulse')
            with ui.column().classes('gap-0'):
                ui.label('NEUROLINK').classes('text-2xl text-cyan-400 header-title font-bold')
                ui.label('SYSTEM V3.3 // PARALLEL MODE').classes('text-[0.6rem] text-cyan-700 tracking-[0.3em]')

        with ui.row().classes('gap-4 items-center'):
            udp_status = ui.label('UDP: DISCONNECTED').classes('text-xs font-mono px-2 py-1 border border-red-900 text-red-500 bg-red-900/10')
            ui.button('EMERGENCY STOP', on_click=lambda: controller.stop_all() if controller else None).classes('bg-red-600 text-white text-xs font-bold px-4 py-2 hover:bg-red-500 shadow-[0_0_15px_red]')

    # --- MAIN GRID ---
    with ui.row().classes('w-full h-[90vh] p-4 gap-4 no-wrap'):

        # COL 1 : BIO-METRICS (Barres)
        with ui.column().classes('w-1/4 h-full cyber-panel p-4 flex flex-col'):
            ui.label('SERVO METRICS').classes('text-cyan-500 text-sm font-bold tracking-widest mb-4 border-b border-cyan-900/50 w-full pb-1')
            
            # Zone barres
            with ui.row().classes('w-full flex-1 justify-between gap-2 items-end pb-4'):
                for fid, label, color in finger_conf:
                    with ui.column().classes('h-full flex-1 items-center justify-between'):
                        ui.label(label).classes('text-[0.6rem] text-slate-500 font-mono rotate-0')
                        
                        # Jauge
                        with ui.element('div').classes('bar-container w-full max-w-[20px] h-[80%]'):
                            # Fond quadrillé discret
                            ui.element('div').style('width:100%; height:100%; background: repeating-linear-gradient(0deg, transparent, transparent 19px, #112 20px); opacity: 0.3;')
                            # La barre dynamique
                            bar = ui.element('div').classes('bar-fill').style(f'height: 0%; background-color: {color};')
                        
                        val_label = ui.label('0%').classes('text-[0.7rem] font-mono font-bold mt-1').style(f'color: {color}')
                        bars[fid] = (bar, val_label)

            # Footer Metrics
            with ui.row().classes('w-full justify-between mt-auto border-t border-cyan-900/30 pt-2'):
                with ui.column().classes('gap-0'):
                    ui.label('VOLTAGE').classes('text-[0.5rem] text-slate-500')
                    ui.label('5.1 V').classes('text-xs text-yellow-400 font-mono')
                with ui.column().classes('gap-0 items-end'):
                    ui.label('CPU LOAD').classes('text-[0.5rem] text-slate-500')
                    ui.label('12 %').classes('text-xs text-cyan-400 font-mono')


        # COL 2 : OPTICAL FEED (Video)
        with ui.column().classes('w-2/4 h-full gap-4'):
            # Cadre Vidéo
            with ui.card().classes('cyber-panel w-full h-3/4 p-0 overflow-hidden relative flex flex-col'):
                # Overlay HUD
                ui.element('div').classes('scanline')
                ui.label('LIVE OPTICAL FEED').classes('absolute top-2 left-2 bg-black/50 px-2 text-[0.6rem] text-cyan-500 border-l-2 border-cyan-500')
                ui.label('REC ●').classes('absolute top-2 right-2 text-red-500 text-xs font-bold animate-pulse')
                
                # Image stream
                with ui.element('div').classes('w-full h-full bg-black flex items-center justify-center'):
                    ui.image(MJPEG_URL).classes('w-full h-full object-contain')
                    
                # Crosshair
                ui.element('div').style('position:absolute; top:50%; left:50%; width:20px; height:1px; background:rgba(0,255,255,0.3); transform:translate(-50%,-50%);')
                ui.element('div').style('position:absolute; top:50%; left:50%; width:1px; height:20px; background:rgba(0,255,255,0.3); transform:translate(-50%,-50%);')

            # Log Terminal
            with ui.card().classes('cyber-panel w-full h-1/4 p-2 bg-black/80 font-mono text-xs overflow-hidden flex flex-col'):
                ui.label('> SYSTEM TERMINAL').classes('text-slate-600 text-[0.6rem] mb-1')
                with ui.scroll_area().classes('w-full h-full'):
                    log_label = ui.label('> Initialisation...').classes('text-green-500/80')

        # COL 3 : CONTROLS
        with ui.column().classes('w-1/4 h-full cyber-panel p-4 flex flex-col'):
            ui.label('CONTROL DECK').classes('text-cyan-500 text-sm font-bold tracking-widest mb-4 border-b border-cyan-900/50 w-full pb-1')

            # Boutons manuels (utilisent le mode parallèle par défaut)
            with ui.column().classes('gap-3 w-full'):
                ui.button('OUVERTURE MAX', on_click=lambda: controller.open_hand() if controller else None).classes('w-full bg-cyan-900/30 border border-cyan-500 text-cyan-400 text-xs hover:bg-cyan-900/50')
                ui.button('FERMETURE MAX', on_click=lambda: controller.close_hand() if controller else None).classes('w-full bg-purple-900/30 border border-purple-500 text-purple-400 text-xs hover:bg-purple-900/50')
            
            ui.separator().classes('bg-cyan-900/30 my-4')

            # Settings (Fake sliders for UI demo)
            ui.label('PARAMÈTRES DSP').classes('text-[0.6rem] text-slate-500 mb-2')
            with ui.row().classes('items-center w-full gap-2'):
                ui.label('GAIN').classes('text-xs text-cyan-300 w-8')
                ui.slider(min=0, max=100, value=75).props('dark color=cyan').classes('flex-1')
            
            with ui.row().classes('items-center w-full gap-2 mt-2'):
                ui.label('SMOOTH').classes('text-xs text-purple-300 w-8')
                ui.slider(min=0, max=100, value=30).props('dark color=purple').classes('flex-1')

            # Footer Quit
            ui.button('SHUTDOWN SYSTEM', on_click=lambda: (controller.shutdown() if controller else None, os._exit(0))).classes('mt-auto w-full bg-slate-900 text-red-500 border border-red-900/30 text-xs')

    # --- UPDATE LOOP ---
    def update_ui():
        with state_lock:
            current_state = dict(state)
        
        # 1. Update Barres
        vals = current_state['values']
        for fid, (bar_elem, lbl_elem) in bars.items():
            val = vals.get(fid, 0.0)
            pct = int(val * 100)
            bar_elem.style(f'height: {pct}%')
            lbl_elem.text = f'{pct:02d}%'
            
        # 2. Status UDP
        if current_state['udp_connected']:
            udp_status.text = f'UDP: LINKED ({current_state.get("fps",0)} PPS)'
            udp_status.classes(remove='text-red-500 border-red-900 bg-red-900/10', add='text-cyan-400 border-cyan-500 bg-cyan-900/20')
        else:
            udp_status.text = 'UDP: NO CARRIER'
            udp_status.classes(remove='text-cyan-400 border-cyan-500 bg-cyan-900/20', add='text-red-500 border-red-900 bg-red-900/10')
            
        # 3. Log
        msg = current_state['last_message']
        if msg:
            ts = time.strftime('%H:%M:%S')
            log_label.text = f'> [{ts}] {msg}\n' + log_label.text[:300]

    ui.timer(0.05, update_ui)

# --------------------------------------------------------------------
# 6. DÉMARRAGE SÉCURISÉ (FIX MAIN THREAD)
# --------------------------------------------------------------------
if __name__ in {"__main__", "__mp_main__"}:
    print("--- BOOT SEQUENCE INITIATED (V3.3 - PARALLEL MODE) ---")
    
    # 1. KILL ZOMBIE PROCESSES
    kill_port_hog(UDP_PORT)
    
    # 2. INIT HARDWARE (DANS LE MAIN THREAD OBLIGATOIREMENT)
    try:
        controller = HandController()
        print("[HARDWARE] Servo Controller Initialized (Parallel Mode Enabled).")
    except Exception as e:
        print(f"[ERREUR CRITIQUE] Impossible d'initier le hardware: {e}")
        sys.exit(1)
    
    # 3. START UDP THREAD (AVEC REFERENCE DU CONTROLEUR)
    t = threading.Thread(target=udp_worker, args=(controller,), daemon=True)
    t.start()
    
    # 4. BUILD UI
    build_ui()
    
    # 5. RUN
    ui.run(
        host='0.0.0.0', 
        port=8080, 
        reload=False, # CRUCIAL
        dark=True, 
        title='NeuroLink V3.3 - Parallel'
    )
