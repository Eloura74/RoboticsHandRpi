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
# 3. GESTION ÉTAT & SÉCURITÉ
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

# --- GESTIONNAIRE D'ARRÊT PROPRE (CTRL+C) ---
def signal_handler(signum, frame):
    print("\n[SYSTEM] Interruption reçue (Ctrl+C). Mise en sécurité...")
    try:
        if controller:
            print("[SYSTEM] Ouverture main de sécurité...")
            controller.open_hand()
            time.sleep(0.5) # Laisser le temps aux servos
    except: pass
    
    print("[SYSTEM] Arrêt du serveur.")
    # On force la fermeture de l'app et du process
    app.shutdown()
    sys.exit(0)

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
# 4. RESSOURCES GRAPHIQUES (V16 - MECHANICAL THUMB)
# --------------------------------------------------------------------

HAND_SVG_STRUCTURE = r'''
<div style="width:100%; height:100%; position:relative; display:flex; justify-content:center; align-items:center; overflow:hidden;">
    
    <!-- Fond Tech -->
    <svg style="position:absolute; width:100%; height:100%; pointer-events:none;">
        <defs>
            <radialGradient id="bg-grad" cx="0.5" cy="0.5" r="0.8">
                <stop offset="0%" stop-color="#1a2333" stop-opacity="1"/>
                <stop offset="100%" stop-color="#080a10" stop-opacity="1"/>
            </radialGradient>
            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M50 0 L0 0 0 50" fill="none" stroke="#00f3ff" stroke-width="0.2" opacity="0.3"/>
            </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#bg-grad)" />
        <rect width="100%" height="100%" fill="url(#grid)" />
    </svg>

    <div id="js-heartbeat" style="position:absolute; top:15px; right:15px; width:6px; height:6px; background:#00ff00; border-radius:50%; box-shadow:0 0 8px #00ff00;"></div>

    <!-- ROBOT HAND (Vue Face/Paume) -->
    <svg id="robot-hand" viewBox="-250 -500 500 600" style="height:95%; width:auto; z-index:10; filter:drop-shadow(0 20px 30px rgba(0,0,0,0.9));">
        <defs>
            <linearGradient id="pla-base" x1="0" x2="1" y1="0" y2="0">
                <stop offset="0%" stop-color="#2a2a2a"/>
                <stop offset="20%" stop-color="#4a4a4a"/>
                <stop offset="50%" stop-color="#606060"/>
                <stop offset="80%" stop-color="#4a4a4a"/>
                <stop offset="100%" stop-color="#2a2a2a"/>
            </linearGradient>
            <linearGradient id="metal-dark" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#111"/>
                <stop offset="100%" stop-color="#333"/>
            </linearGradient>
        </defs>

        <!-- AVANT-BRAS -->
        <g transform="translate(0, 80)">
            <path d="M-70,0 L-60,-100 L60,-100 L70,0 L70,120 L-70,120 Z" fill="#1a1a1a" stroke="#000" stroke-width="2"/>
            <rect x="-50" y="-80" width="100" height="60" rx="4" fill="#0f0f0f" stroke="#333"/>
        </g>

        <!-- PAUME -->
        <g transform="translate(0, -20)">
            <path d="M-60,-10 L-75,-140 L-50,-200 L50,-200 L75,-140 L60,-10 Z" fill="url(#metal-dark)" stroke="#555" stroke-width="2"/>
            
            <!-- Servo Pouce (Le moteur fixe) -->
            <g transform="translate(-65, -50) rotate(0)">
                <rect x="-25" y="-30" width="50" height="40" rx="2" fill="#111" stroke="#444"/>
                <rect x="-20" y="-25" width="40" height="15" fill="#600" opacity="0.6"/>
                <!-- Axe Servo -->
                <circle cx="0" cy="-20" r="4" fill="#888"/>
            </g>
        </g>

        <!-- DOIGTS -->
        <g id="grp-pouce" transform="translate(-65, -70)"></g>
        <g id="grp-index" transform="translate(-55, -200) rotate(-8)"></g>
        <g id="grp-majeur" transform="translate(0, -210)"></g>
        <g id="grp-annulaire" transform="translate(55, -200) rotate(8)"></g>
        <g id="grp-auriculaire" transform="translate(95, -160) rotate(20)"></g>
    </svg>
</div>
'''

HAND_ANIMATION_JS = r'''
<script>
(function() {
    const fingers = ['pouce', 'index', 'majeur', 'annulaire', 'auriculaire'];
    let targets = { pouce: 0, index: 0, majeur: 0, annulaire: 0, auriculaire: 0 };
    let currents = { pouce: 0, index: 0, majeur: 0, annulaire: 0, auriculaire: 0 };
    let hbState = false;

    function createFingerDOM(id, isThumb, isPinky) {
        const g = document.getElementById('grp-' + id);
        if(!g) return;
        
        let scale = 1.0;
        if(isPinky) scale = 0.85;
        if(isThumb) scale = 1.1;

        const w = 26 * scale; 
        const h1 = 65 * scale;
        const h2 = 50 * scale;
        const h3 = 40 * scale;
        
        g.dataset.h1 = h1;
        g.dataset.h2 = h2;
        
        let p1Content = `<path d="M${-w/2},0 L${-w/2},${-h1} L${w/2},${-h1} L${w/2},0 Z" fill="url(#pla-base)" stroke="#111" stroke-width="1"/>`;
        if(isThumb) {
             p1Content = `
                <path d="M${-w/2-8},0 L${-w/2},${-h1} L${w/2},${-h1} L${w/2+2},0 L${-w/2-8},0 Z" fill="url(#pla-base)" stroke="#111" stroke-width="1"/>
                <rect x="${-w/2}" y="-10" width="${w}" height="10" fill="#333" opacity="0.3"/>
             `;
        }

        let html = `
        <g class="finger-scale">
            <line x1="0" y1="0" x2="0" y2="${-h1*3}" stroke="#00f3ff" stroke-width="1.5" opacity="0.4" class="tendon-fx"/>
            <g class="p1">
                ${p1Content}
                <circle cx="0" cy="${-h1+8}" r="3" fill="#222"/> 
                <g class="p2" transform="translate(0, ${-h1})">
                    <path d="M${-w/2+2},0 L${-w/2+2},${-h2} L${w/2-2},${-h2} L${w/2-2},0 Z" fill="url(#pla-base)" stroke="#111" stroke-width="1"/>
                    <circle cx="0" cy="${-h2+6}" r="2.5" fill="#222"/>
                    <g class="p3" transform="translate(0, ${-h2})">
                        <path d="M${-w/2+3},0 L${-w/2+3},${-h3+10} L0,${-h3} L${w/2-3},${-h3+10} L${w/2-3},0 Z" fill="url(#pla-base)" stroke="#111" stroke-width="1"/>
                        <path d="M${-5},${-15} L0,${-25} L${5},${-15} L${5},${-5} L${-5},${-5} Z" fill="#222" opacity="0.6"/>
                    </g>
                </g>
            </g>
        </g>`;
        g.innerHTML = html;
    }

    window.updateHandData = function(jsonStr) {
        try {
            const data = JSON.parse(jsonStr);
            if(data['pouce_articulation'] !== undefined) targets.pouce = data['pouce_articulation'];
            if(data['index'] !== undefined) targets.index = data['index'];
            if(data['majeur'] !== undefined) targets.majeur = data['majeur'];
            if(data['annulaire_auriculaire'] !== undefined) {
                targets.annulaire = data['annulaire_auriculaire'];
                targets.auriculaire = data['annulaire_auriculaire'];
            }
        } catch(e) {}
    };

    function animate() {
        const alpha = 0.20; 
        
        const hb = document.getElementById('js-heartbeat');
        if(hb) {
            hbState = !hbState;
            hb.style.background = hbState ? '#00ff00' : '#004400';
        }

        fingers.forEach(f => {
            let diff = targets[f] - currents[f];
            if(Math.abs(diff) < 0.001) currents[f] = targets[f];
            else currents[f] += diff * alpha;
            
            const val = currents[f];
            const g = document.getElementById('grp-' + f);
            if(!g) return;

            const h1 = parseFloat(g.dataset.h1);
            const h2 = parseFloat(g.dataset.h2);

            const tendon = g.querySelector('.tendon-fx');
            if(tendon) tendon.style.opacity = 0.3 + (val * 0.7);

            const p1 = g.querySelector('.p1');
            const p2 = g.querySelector('.p2');
            const p3 = g.querySelector('.p3');

            if(f === 'pouce') {
                const startAngle = -85; 
                const endAngle = 10;
                const rotBase = startAngle + (val * (endAngle - startAngle));
                
                const rotP2 = val * 40; 
                const rotP3 = val * 50;
                
                if(p1) p1.setAttribute('transform', `rotate(${rotBase})`);
                if(p2) p2.setAttribute('transform', `translate(0, ${-h1}) rotate(${rotP2})`);
                if(p3) p3.setAttribute('transform', `translate(0, ${-h2}) rotate(${rotP3})`);
            } else {
                const s1 = 1.0 - (val * 0.15);
                const s2 = 1.0 - (val * 0.45);
                const r2 = val * 15;
                const s3 = 1.0 - (val * 0.60);
                const r3 = val * 30;

                if(p1) p1.setAttribute('transform', `scale(1, ${s1})`);
                if(p2) p2.setAttribute('transform', `translate(0, ${-h1}) rotate(${r2}) scale(1, ${s2})`);
                if(p3) p3.setAttribute('transform', `translate(0, ${-h2}) rotate(${r3}) scale(1, ${s3})`);
            }
        });
        requestAnimationFrame(animate);
    }

    function init() {
        if(document.getElementById('robot-hand')) {
            fingers.forEach(f => createFingerDOM(f, f==='pouce', f==='auriculaire'));
            animate();
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
        .blinking-btn { animation: blink 1s infinite; }
        @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.8; } 100% { opacity: 1; } }
    </style>
    ''')

    # --- FONCTION D'ARRET D'URGENCE ---
    def emergency_stop():
        # 1. Reset Logiciel
        with state_lock:
            state['simu_mode'] = False
            for f in FINGERS:
                state['values'][f] = 0.0 # Force 0 dans le state
        
        # 2. Reset Physique
        if controller:
            controller.open_hand()
        
        # 3. Notification UI
        ui.notify("ARRÊT D'URGENCE ACTIVÉ - MAIN OUVERTE", type='negative', close_button=True)

    with ui.row().classes('w-full h-[6vh] items-center justify-between px-4 bg-[#05070a] border-b border-[#334455]'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('fingerprint', color='cyan-400').classes('text-xl')
            ui.label('NEURO-LINK // V17 SAFETY').classes('text-xl font-bold tracking-widest text-gray-200')
        with ui.row().classes('items-center gap-4'):
            ui.label(f'HOST: {LOCAL_IP}').classes('text-xs font-mono text-gray-500')
            status = ui.label('INIT').classes('text-xs px-2 py-1 bg-gray-800 rounded font-bold')

    with ui.row().classes('w-full h-[94vh] p-0 gap-0'):
        with ui.card().classes('w-full h-full bg-black p-0 items-center justify-center relative'):
            
            ui.html(HAND_SVG_STRUCTURE, sanitize=False).classes('w-full h-full')
            ui.add_body_html(HAND_ANIMATION_JS)
            
            with ui.element('div').classes('absolute bottom-6 right-6 w-64 h-48 bg-black z-50 pip-cam rounded-lg overflow-hidden'):
                ui.label('OPTICAL FEED').classes('absolute top-0 left-0 bg-cyan-900/90 text-cyan-100 text-[10px] px-2 z-10')
                ui.image(MJPEG_URL).classes('w-full h-full object-cover opacity-80')

            with ui.column().classes('absolute top-6 left-6 w-52 p-4 panel rounded-lg gap-2'):
                ui.label('MANUAL OVERRIDE').classes('text-xs font-bold text-cyan-400 mb-2')
                ui.button('OUVRIR', on_click=lambda: controller.open_hand()).classes('w-full bg-cyan-700 h-8 text-xs')
                ui.button('FERMER', on_click=lambda: controller.close_hand()).classes('w-full bg-red-700 h-8 text-xs')
                ui.separator().classes('bg-gray-600 my-2')
                
                def toggle_sim():
                    with state_lock: state['simu_mode'] = not state['simu_mode']
                ui.button('AUTO-TEST (SIMU)', on_click=toggle_sim).classes('w-full bg-purple-700 h-8 text-xs')

                # --- BOUTONS DE SÉCURITÉ AJOUTÉS ---
                ui.separator().classes('bg-gray-600 my-2')
                ui.button("ARRÊT D'URGENCE", on_click=emergency_stop).classes('w-full bg-red-600 text-white font-bold h-10 text-xs blinking-btn')
                ui.button('QUITTER SYSTEME', on_click=app.shutdown).classes('w-full bg-gray-700 text-gray-300 h-8 text-xs')

                ui.label('DATA STREAM:').classes('text-[10px] text-gray-500 mt-2')
                debug_lbl = ui.label('...').classes('text-[9px] font-mono text-cyan-300 break-all')

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
    # Enregistrement du gestionnaire CTRL+C
    signal.signal(signal.SIGINT, signal_handler)
    
    try: controller = HandController()
    except: sys.exit(1)

    threading.Thread(target=receiver_thread, daemon=True).start()
    threading.Thread(target=hardware_thread, args=(controller,), daemon=True).start()

    build_ui()
    ui.run(host='0.0.0.0', port=8080, dark=True, reload=False, title='NEURO-LINK V17')