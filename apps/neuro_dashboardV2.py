# apps/neuro_dashboardV2.py

import sys
import json
import socket
import time
import threading
import os
import signal
import math
import traceback
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

try:
    from apps.styles.dashboard_stylesV2 import CSS_STYLE, HAND_3D_STRUCTURE, HAND_3D_JS
except ImportError:
    print("[ERROR] Cannot import dashboard styles")
    sys.exit(1)

# --------------------------------------------------------------------
# 2. CONFIGURATION
# --------------------------------------------------------------------
PC_IP = '192.168.1.10'
MJPEG_PORT = 8090
MJPEG_URL = f'http://{PC_IP}:{MJPEG_PORT}/cam.mjpg'

UDP_IP = '0.0.0.0'
UDP_PORT = 5005
LOST_TIMEOUT = 2.0
FINGERS = ['pouce_articulation', 'index', 'majeur', 'annulaire_auriculaire']

controller = None

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()

# --------------------------------------------------------------------
# 3. GESTION ÉTAT & SÉCURITÉ
# --------------------------------------------------------------------
state_lock = threading.Lock()
state = {
    'values': {f: 0.0 for f in FINGERS},
    'udp_connected': False,
    'fps': 0,
    'packet_count': 0,
    'simu_mode': False,
}

def signal_handler(signum, frame):
    print("\n[SYSTEM] Shutdown sequence initiated...")
    try:
        if controller:
            controller.open_hand()
            time.sleep(0.5)
    except: pass
    app.shutdown()
    sys.exit(0)

# Le thread receiver_thread reste inchangé
def receiver_thread():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind((UDP_IP, UDP_PORT))
        sock.setblocking(False)
        print(f"[UDP] Thread UDP démarré - écoute sur {UDP_IP}:{UDP_PORT}")
        print(f"[UDP] IP locale du Raspberry Pi: {LOCAL_IP}")
        print(f"[UDP] Le PC doit envoyer les données UDP à: {LOCAL_IP}:{UDP_PORT}")
    except Exception as e:
        print(f"[ERROR] Impossible de démarrer le thread UDP: {e}")
        return

    packet_cnt = 0
    t0 = time.time()
    last_rx = time.time()
    rx_count = 0

    while True:
        now = time.time()
        if state['udp_connected'] and (now - last_rx > LOST_TIMEOUT):
            print(f"[UDP] TIMEOUT - Pas de données depuis {LOST_TIMEOUT}s. Déconnexion.")
            with state_lock: state['udp_connected'] = False

        data = None
        try:
            while True:
                chunk, _ = sock.recvfrom(4096)
                data = chunk
        except: pass

        if data:
            last_rx = now
            packet_cnt += 1
            rx_count += 1
            
            if now - t0 > 1.0:
                with state_lock: state['fps'] = packet_cnt
                print(f"[UDP] {packet_cnt} paquets/sec reçus (total: {rx_count})")
                packet_cnt = 0
                t0 = now
            try:
                msg = json.loads(data.decode())
                with state_lock:
                    if not state['simu_mode']:
                        if not state['udp_connected']:
                            print(f"[UDP] CONNEXION ÉTABLIE - Réception de données depuis le PC")
                        state['udp_connected'] = True
                        state['packet_count'] += 1
                        for f in FINGERS:
                            if f in msg:
                                state['values'][f] = max(0.0, min(1.0, float(msg[f])))
            except Exception as e:
                print(f"[UDP] Erreur de parsing: {e}")
        time.sleep(0.001)

# Le thread hardware_thread reste inchangé
def hardware_thread(ctrl):
    logical = {f: 'open' for f in FINGERS}
    while True:
        targets = {}
        with state_lock:
            targets = state['values'].copy()
            active = state['udp_connected'] or state['simu_mode']

        if active:
            try:
                for f, val in targets.items():
                    curr = logical.get(f, 'open')
                    if val > 0.7 and curr != 'close':
                        ctrl.close_finger(f, parallel=True)
                        logical[f] = 'close'
                    elif val < 0.3 and curr != 'open':
                        ctrl.open_finger(f, parallel=True)
                        logical[f] = 'open'
            except: pass
        time.sleep(0.05)

# --------------------------------------------------------------------
# 4. RESSOURCES GRAPHIQUES (Inchangé)
# --------------------------------------------------------------------

# --------------------------------------------------------------------
# 5. UI PRINCIPALE (Mise à jour du titre)
# --------------------------------------------------------------------
def build_ui():
    ui.add_head_html(CSS_STYLE)

    with ui.row().classes('hud-header w-full h-[8vh] min-h-[60px] items-center justify-between px-6 sm:px-8'):
        with ui.row().classes('items-center gap-3'):
            ui.icon('hub', color='cyan-400').classes('text-2xl')
            with ui.column().classes('gap-0'):
                ui.label('NEURO-LINK // SYSTEM V2.0').classes('text-sm sm:text-lg text-cyan-400 font-bold tracking-widest') # Titre V2.0
                ui.label('ASSET CORE • OBJ IMPORT').classes('text-[10px] text-gray-400 tracking-wider') # Sous-titre
        
        status_label = ui.label('INIT').classes('text-xs px-3 py-1 bg-cyan-900/40 text-cyan-300 border border-cyan-500 rounded font-bold')

    with ui.row().classes('w-full h-[92vh] p-4 gap-4 bg-transparent'):
        with ui.column().classes('w-[25%] min-w-[260px] h-full gap-4'):
            with ui.card().classes('w-full h-[30%] hud-panel p-0 overflow-hidden relative'):
                ui.label('OPTICAL FEED').classes('absolute top-2 left-2 text-[10px] text-cyan-500 bg-black/50 px-2 rounded z-10')
                ui.image(MJPEG_URL).classes('w-full h-full object-cover opacity-80')
            
            with ui.card().classes('w-full flex-1 hud-panel p-4 flex flex-col gap-3'):
                ui.label('SERVO CONTROL').classes('text-cyan-400 font-bold text-sm')
                ui.button('OUVRIR', on_click=lambda: controller.open_hand()).classes('w-full cyber-btn h-10')
                ui.button('FERMER', on_click=lambda: controller.close_hand()).classes('w-full cyber-btn h-10')
                
                def toggle_sim():
                    with state_lock: state['simu_mode'] = not state['simu_mode']
                ui.button('SIMULATION', on_click=toggle_sim).classes('w-full cyber-btn h-10')
                ui.button("STOP URGENCE", on_click=lambda: controller.open_hand()).classes('w-full danger-btn h-12 mt-auto')

        with ui.card().classes('flex-1 h-full hud-panel p-0 overflow-hidden relative bg-black'):
            ui.html(HAND_3D_STRUCTURE, sanitize=False).classes('w-full h-full')
            ui.add_body_html(HAND_3D_JS)

    loop_count = [0]
    
    def update_loop():
        try:
            loop_count[0] += 1
            if loop_count[0] % 20 == 0:
                print(f"[DEBUG] update_loop appelé {loop_count[0]} fois")
            
            with state_lock:
                if state['simu_mode']:
                    t = time.time()
                    for i, f in enumerate(FINGERS): state['values'][f] = (math.sin(t * 2 + i) + 1) / 2
                vals = state['values'].copy()
                connected = state['udp_connected'] or state['simu_mode']
                fps = state['fps']

            if loop_count[0] % 20 == 0:
                print(f"[DEBUG] vals={vals}, connected={connected}, fps={fps}")

            json_data = json.dumps(vals)
            ui.run_javascript(f"try {{ if(typeof window.updateHandData === 'function') window.updateHandData('{json_data}'); }} catch(e) {{ console.error('updateHandData error:', e); }}")

            status_label.text = f"ONLINE ({fps} TPS)" if connected else "OFFLINE"
            status_label.classes(replace='text-xs px-3 py-1 bg-green-900/40 text-green-300 border border-green-500' if connected else 'text-xs px-3 py-1 bg-red-900/40 text-red-500 border border-red-500')
        except Exception as e:
            print(f"[ERROR] update_loop: {e}")
            traceback.print_exc()

    ui.timer(0.05, update_loop)

# --------------------------------------------------------------------
# 6. RUN
# --------------------------------------------------------------------
if __name__ in {"__main__", "__mp_main__"}:
    signal.signal(signal.SIGINT, signal_handler)
    try: controller = HandController()
    except: sys.exit(1)

    print("[INIT] Démarrage des threads de communication...")
    threading.Thread(target=receiver_thread, daemon=True).start()
    threading.Thread(target=hardware_thread, args=(controller,), daemon=True).start()
    time.sleep(0.5)

    # --- NOUVEAU : Exposer le dossier assets pour le chargement 3D ---
    ASSETS_DIR = BASE_DIR / 'assets'
    if not ASSETS_DIR.exists():
        print(f"[WARNING] Le dossier '/assets' n'existe pas. Créez-le et placez-y main_modele.obj.")
        ASSETS_DIR.mkdir(exist_ok=True) # Crée le dossier s'il n'existe pas
    
    app.add_static_files('/assets', ASSETS_DIR)
    print(f"[ASSET] Dossier '/assets' exposé pour le chargement 3D.")

    @ui.page('/')
    def index():
        build_ui()
    
    ui.run(host='0.0.0.0', port=8080, dark=True, reload=False, title='NEURO-LINK V2.0')