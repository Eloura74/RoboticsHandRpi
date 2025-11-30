# apps/neuro_dashboard.py

import sys
import json
import socket
import time
import threading
import os
import signal
import subprocess
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
# 3. GESTION ÉTAT & THREADS
# --------------------------------------------------------------------
def kill_port_hog(port):
    pass

state_lock = threading.Lock()
state = {
    'values': {f: 0.0 for f in FINGERS},
    'udp_connected': False,
    'last_message': 'Système prêt.',
    'fps': 0,
    'packet_count': 0,
    'simu_mode': False
}

# --- THREAD RÉCEPTION (UDP PARTAGÉ) ---
def receiver_thread():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind((UDP_IP, UDP_PORT))
    except Exception as e:
        print(f"[ERREUR] Socket: {e}")
        return

    sock.setblocking(False)
    packet_cnt = 0
    t0 = time.time()
    last_rx = time.time()
    
    while True:
        now = time.time()
        if state['udp_connected'] and (now - last_rx > LOST_TIMEOUT):
            with state_lock:
                state['udp_connected'] = False
                state['last_message'] = "⚠️ PERTE SIGNAL"
        
        data = None
        try:
            while True:
                chunk, _ = sock.recvfrom(4096)
                data = chunk
        except: pass
        
        if data:
            last_rx = now
            packet_cnt += 1
            if now - t0 > 1.0:
                with state_lock: state['fps'] = packet_cnt
                packet_cnt = 0
                t0 = now
            
            try:
                msg = json.loads(data.decode())
                with state_lock:
                    if not state['simu_mode']:
                        state['udp_connected'] = True
                        state['packet_count'] += 1
                        for f in FINGERS:
                            if f in msg:
                                state['values'][f] = max(0.0, min(1.0, float(msg[f])))
            except: pass
        time.sleep(0.001)

# --- THREAD HARDWARE (ROBOT) ---
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
                    if val > CLOSE_THRESHOLD and curr != 'close':
                        ctrl.close_finger(f, parallel=True)
                        logical[f] = 'close'
                    elif val < OPEN_THRESHOLD and curr != 'open':
                        ctrl.open_finger(f, parallel=True)
                        logical[f] = 'open'
            except: pass
        time.sleep(0.05)

# --------------------------------------------------------------------
# 4. RESSOURCES GRAPHIQUES (V12 - CINÉMATIQUE CORRIGÉE)
# --------------------------------------------------------------------

# PARTIE 1 : STRUCTURE SVG
# Note: Thumb is on LEFT (Translate X < 0) for a Left Hand Palm View or Right Hand Back View.
# Adjusted translations to spread fingers naturally.
HAND_SVG_STRUCTURE = r'''
<div style="width:100%; height:100%; position:relative; display:flex; justify-content:center; align-items:center; overflow:hidden;">
    
    <svg style="position:absolute; width:100%; height:100%; opacity:0.1; pointer-events:none;">
        <defs><pattern id="g" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0 L0 0 0 40" fill="none" stroke="#00f3ff" stroke-width="0.5"/></pattern></defs>
        <rect width="100%" height="100%" fill="url(#g)" />
    </svg>

    <div id="js-heartbeat" style="position:absolute; top:10px; right:10px; width:8px; height:8px; border-radius:50%; background:#333; z-index:100;"></div>

    <!-- MAIN ROBOTIQUE (Vue de Face) -->
    <svg id="robot-hand" viewBox="-200 -450 400 500" style="height:95%; width:auto; z-index:10; filter:drop-shadow(0 10px 20px rgba(0,0,0,0.8));">
        <defs>
            <linearGradient id="pla-grey" x1="0" x2="1" y1="0" y2="0"><stop offset="0%" stop-color="#4a4a4a"/><stop offset="50%" stop-color="#808080"/><stop offset="100%" stop-color="#3a3a3a"/></linearGradient>
            <linearGradient id="tendon-glow" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#00f3ff" stop-opacity="0"/><stop offset="100%" stop-color="#00f3ff" stop-opacity="0.8"/></linearGradient>
        </defs>

        <!-- Poignet / Avant-bras -->
        <g transform="translate(0, 50)">
            <path d="M-60,0 L-50,-80 L50,-80 L60,0 L60,100 L-60,100 Z" fill="#222" stroke="#111" stroke-width="2"/>
            <!-- Servo Thumb Base -->
            <rect x="-80" y="-70" width="40" height="60" rx="5" fill="#111" stroke="#333" />
        </g>

        <!-- Paume -->
        <path d="M-55,-30 L-70,-130 L-45,-180 L45,-180 L70,-130 L55,-30 Z" fill="url(#pla-grey)" stroke="#222" stroke-width="2" />
        
        <!-- Decoration Paume -->
        <path d="M-40,-40 L-50,-120 L40,-40" fill="none" stroke="#222" stroke-width="1" opacity="0.5"/>

        <!-- DOIGTS (Placement en éventail) -->
        <!-- Pouce (Gauche) -->
        <g id="grp-pouce" transform="translate(-75, -90) rotate(-30)"></g>
        
        <!-- Index -->
        <g id="grp-index" transform="translate(-45, -180) rotate(-5)"></g>
        
        <!-- Majeur -->
        <g id="grp-majeur" transform="translate(0, -185)"></g>
        
        <!-- Annulaire -->
        <g id="grp-annulaire" transform="translate(50, -175) rotate(5)"></g>
    </svg>
</div>
'''

# PARTIE 2 : JS (Cinématique Realiste 2D)
HAND_ANIMATION_JS = r'''
<script>
(function() {
    const fingers = ['pouce', 'index', 'majeur', 'annulaire'];
    const fingerMap = {
        'pouce_articulation': 'pouce', 'index': 'index', 
        'majeur': 'majeur', 'annulaire_auriculaire': 'annulaire'
    };
    
    // Valeurs cibles (0=ouvert, 1=fermé)
    let targets = { pouce: 0, index: 0, majeur: 0, annulaire: 0 };
    let currents = { pouce: 0, index: 0, majeur: 0, annulaire: 0 };
    let hbState = false;

    function createFingerDOM(id, isThumb) {
        const g = document.getElementById('grp-' + id);
        if(!g) return;
        
        // Dimensions adaptées aux phalanges imprimées 3D
        // P1 (Base), P2 (Milieu), P3 (Bout)
        // Les phalanges se dessinent vers le HAUT (Y négatif)
        
        const w = isThumb ? 28 : 24; 
        const h1 = isThumb ? 50 : 60;
        const h2 = isThumb ? 40 : 50;
        const h3 = isThumb ? 35 : 40;
        
        let html = `
        <!-- Tendon Visual -->
        <line x1="0" y1="0" x2="0" y2="-150" stroke="url(#tendon-glow)" stroke-width="2" opacity="0" class="tendon-fx" />
        
        <!-- P1 -->
        <g class="p1">
            <rect x="${-w/2}" y="${-h1}" width="${w}" height="${h1}" rx="4" fill="url(#pla-grey)" stroke="#222" />
            <circle cx="0" cy="${-h1+10}" r="2" fill="#111" opacity="0.5"/>
            
            <!-- P2 -->
            <g class="p2" transform="translate(0, ${-h1})">
                <circle cx="0" cy="0" r="${w/2 - 2}" fill="#333" />
                <rect x="${-w/2+2}" y="${-h2}" width="${w-4}" height="${h2}" rx="3" fill="url(#pla-grey)" stroke="#222" />
                
                <!-- P3 -->
                <g class="p3" transform="translate(0, ${-h2})">
                    <circle cx="0" cy="0" r="${w/2 - 4}" fill="#333" />
                    <path d="M${-w/2+4},0 L${-w/2+4},${-h3+10} Q0,${-h3} ${w/2-4},${-h3+10} L${w/2-4},0 Z" fill="url(#pla-grey)" stroke="#222" />
                </g>
            </g>
        </g>`;
        g.innerHTML = html;
    }

    window.updateHandData = function(jsonStr) {
        try {
            const data = JSON.parse(jsonStr);
            for(const [key, val] of Object.entries(data)) {
                if(fingerMap[key]) targets[fingerMap[key]] = val;
            }
        } catch(e) {}
    };

    function animate() {
        const alpha = 0.2; // Vitesse de lissage
        
        // Clignotement LED verte si actif
        const hb = document.getElementById('js-heartbeat');
        if(hb) {
            hbState = !hbState;
            hb.style.background = hbState ? '#00ff00' : '#004400';
        }

        fingers.forEach(f => {
            // Interpolation
            let diff = targets[f] - currents[f];
            if(Math.abs(diff) < 0.001) currents[f] = targets[f];
            else currents[f] += diff * alpha;
            
            const val = currents[f];
            const g = document.getElementById('grp-' + f);
            if(!g) return;
            
            // Effet visuel du tendon qui se tend
            const tendon = g.querySelector('.tendon-fx');
            if(tendon) tendon.style.opacity = val * 0.8;

            const p1 = g.querySelector('.p1');
            const p2 = g.querySelector('.p2');
            const p3 = g.querySelector('.p3');

            if(f === 'pouce') {
                // CINEMATIQUE POUCE (Rotation 2D vers la paume)
                // Le pouce tourne à sa base pour "entrer" dans la main
                const rotBase = val * 90; // 0 -> 90 degrés (fermeture)
                const rotP2 = val * 40;
                const rotP3 = val * 60;
                
                if(p1) p1.setAttribute('transform', `rotate(${rotBase})`);
                if(p2) p2.setAttribute('transform', `translate(0, -50) rotate(${rotP2})`);
                if(p3) p3.setAttribute('transform', `translate(0, -40) rotate(${rotP3})`);
                
            } else {
                // CINEMATIQUE DOIGTS (Foreshortening / Raccourcissement visuel)
                // Pour simuler un doigt qui se plie VERS la caméra en 2D, on réduit sa hauteur (Scale Y)
                // et on décale légèrement Y pour simuler l'enroulement.
                
                // P1: Reste fixe mais bascule un peu vers l'avant (Scale Y 90%)
                const s1 = 1.0 - (val * 0.1);
                
                // P2: Se plie beaucoup (Scale Y diminue -> effet de perspective) + Rotation légère pour courber
                const s2 = 1.0 - (val * 0.4); 
                const r2 = val * 10; // Légère courbure naturelle
                
                // P3: Le bout se replie (Scale Y diminue fort) + Rotation pour "rentrer"
                const s3 = 1.0 - (val * 0.5);
                const r3 = val * 20;

                // Application
                if(p1) p1.setAttribute('transform', `scale(1, ${s1})`);
                if(p2) p2.setAttribute('transform', `translate(0, -60) rotate(${r2}) scale(1, ${s2})`);
                if(p3) p3.setAttribute('transform', `translate(0, -50) rotate(${r3}) scale(1, ${s3})`);
            }
        });
        
        requestAnimationFrame(animate);
    }

    function init() {
        if(document.getElementById('robot-hand')) {
            fingers.forEach(f => createFingerDOM(f, f==='pouce'));
            animate();
            console.log("V12 Engine Running");
        } else {
            setTimeout(init, 50);
        }
    }
    init();
})();
</script>
'''

# --------------------------------------------------------------------
# 5. UI PRINCIPALE
# --------------------------------------------------------------------
def build_ui():
    ui.add_head_html('''
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&display=swap');
        body { background: #080a10; color: #e0e0e0; font-family: 'Orbitron', sans-serif; overflow: hidden; }
        .pip-cam { border: 2px solid #00f3ff; box-shadow: 0 0 15px rgba(0, 243, 255, 0.3); }
        .panel { background: rgba(20, 25, 35, 0.95); border: 1px solid #334455; }
    </style>
    ''')

    with ui.row().classes('w-full h-[6vh] items-center justify-between px-4 bg-[#05070a] border-b border-[#334455]'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('fingerprint', color='cyan-400').classes('text-xl')
            ui.label('NEURO-LINK // V12 CINEMATICS').classes('text-xl font-bold tracking-widest text-gray-200')
        with ui.row().classes('items-center gap-4'):
            ui.label(f'HOST: {LOCAL_IP}').classes('text-xs font-mono text-gray-500')
            status = ui.label('INIT').classes('text-xs px-2 py-1 bg-gray-800 rounded font-bold')

    with ui.row().classes('w-full h-[94vh] p-0 gap-0'):
        
        # ZONE VISUELLE
        with ui.card().classes('w-full h-full bg-gradient-to-b from-[#1a1c24] to-[#0a0c10] p-0 items-center justify-center relative'):
            
            # 1. Structure SVG (Statique)
            ui.html(HAND_SVG_STRUCTURE, sanitize=False).classes('w-full h-full')
            # 2. Injection JS (Animation)
            ui.add_body_html(HAND_ANIMATION_JS)
            
            # PIP
            with ui.element('div').classes('absolute bottom-6 right-6 w-64 h-48 bg-black z-50 pip-cam rounded-lg overflow-hidden'):
                ui.label('OPTICAL FEED').classes('absolute top-0 left-0 bg-cyan-900/90 text-cyan-100 text-[10px] px-2 z-10')
                ui.image(MJPEG_URL).classes('w-full h-full object-cover opacity-80')

            # CONTROL PANEL
            with ui.column().classes('absolute top-6 left-6 w-52 p-4 panel rounded-lg gap-2'):
                ui.label('MANUAL OVERRIDE').classes('text-xs font-bold text-cyan-400 mb-2')
                ui.button('OUVRIR', on_click=lambda: controller.open_hand()).classes('w-full bg-cyan-700 h-8 text-xs')
                ui.button('FERMER', on_click=lambda: controller.close_hand()).classes('w-full bg-red-700 h-8 text-xs')
                ui.separator().classes('bg-gray-600 my-2')
                
                def toggle_sim():
                    with state_lock: state['simu_mode'] = not state['simu_mode']
                ui.button('AUTO-TEST (SIMU)', on_click=toggle_sim).classes('w-full bg-purple-700 h-8 text-xs')

                ui.label('DEBUG DATA:').classes('text-[10px] text-gray-500 mt-2')
                debug_lbl = ui.label('...').classes('text-[9px] font-mono text-cyan-300 break-all')

    # BOUCLE PYTHON -> JS
    def update_loop():
        try:
            with state_lock:
                if state['simu_mode']:
                    t = time.time()
                    for i, f in enumerate(FINGERS):
                        state['values'][f] = (math.sin(t*3 + i) + 1) / 2
                
                vals = state['values']
                connected = state['udp_connected'] or state['simu_mode']
                curr_fps = state['fps']
                pkts = state['packet_count']

            json_data = json.dumps(vals)
            ui.run_javascript(f"if(window.updateHandData) window.updateHandData('{json_data}');")

            if connected:
                status.text = f"ONLINE ({curr_fps} PPS)"
                status.classes(replace='bg-green-900 text-green-300')
            else:
                status.text = "OFFLINE"
                status.classes(replace='bg-red-900 text-red-300')
            
            debug_lbl.text = f"P:{pkts} | {vals['index']:.2f}"
        except: pass

    ui.timer(0.05, update_loop)

# --------------------------------------------------------------------
# 6. RUN
# --------------------------------------------------------------------
if __name__ in {"__main__", "__mp_main__"}:
    try: controller = HandController()
    except: sys.exit(1)

    threading.Thread(target=receiver_thread, daemon=True).start()
    threading.Thread(target=hardware_thread, args=(controller,), daemon=True).start()

    build_ui()
    ui.run(host='0.0.0.0', port=8080, dark=True, reload=False, title='NEURO-LINK V12')