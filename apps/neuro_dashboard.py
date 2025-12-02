# apps/neuro_dashboard.py

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
    rx_count = 0  # Compteur total de paquets reçus

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
# 4. RESSOURCES GRAPHIQUES (3D ENGINE V13.1)
# --------------------------------------------------------------------

CSS_STYLE = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;500;700&display=swap');
    :root { --neon-cyan: #00f3ff; --neon-blue: #0066ff; --bg-dark: #000000; }
    body { background-color: var(--bg-dark); color: var(--neon-cyan); font-family: 'Rajdhani', sans-serif; overflow: hidden; margin: 0; }
    
    .hud-header { backdrop-filter: blur(10px); background: linear-gradient(90deg, rgba(0,0,0,0.9), rgba(0,20,40,0.8), rgba(0,0,0,0.9)); border-bottom: 1px solid rgba(0,243,255,0.3); }
    .hud-panel { background: rgba(5, 10, 20, 0.85); border: 1px solid rgba(0,243,255, 0.15); border-radius: 6px; box-shadow: 0 0 25px rgba(0,0,0,0.95); position: relative; }
    
    .cyber-btn { background: rgba(0,243,255,0.05); border: 1px solid var(--neon-cyan); color: #fff; font-family: 'Orbitron'; letter-spacing: 1px; transition: all 0.2s; }
    .cyber-btn:hover { background: var(--neon-cyan); color: #000; box-shadow: 0 0 20px var(--neon-cyan); }
    .danger-btn { background: rgba(220,38,38,0.2); border: 1px solid #ef4444; color: #fee2e2; font-family: 'Orbitron'; font-weight: bold; }
    
    #canvas-container { width: 100%; height: 100%; overflow: hidden; position: relative; background: radial-gradient(circle at 50% 50%, #0a1020 0%, #000000 100%); }
    canvas { display: block; outline: none; }
    
    .overlay-ui { position: absolute; pointer-events: none; }
    
    #loading-msg {
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        font-family: 'Orbitron', sans-serif; color: #00f3ff; font-size: 14px; text-align: center;
        background: rgba(0,0,0,0.8); padding: 20px; border: 1px solid #00f3ff; border-radius: 8px; z-index: 100;
        box-shadow: 0 0 30px rgba(0,243,255,0.2);
    }
</style>
'''

HAND_3D_STRUCTURE = r'''
<div id="canvas-container">
    <div id="loading-msg">
        INITIALISATION NEURO-NET...<br>
        <span style="font-size:10px; color:#aaa;">CHARGEMENT ARCHITECTURE</span>
    </div>
    <div class="overlay-ui" style="top:20px; right:20px; text-align:right;">
        <div style="font-family:'Orbitron'; color:#00f3ff; font-size:12px;">VISUAL CORE</div>
        <div style="font-family:'Rajdhani'; color:#fff; font-size:20px; font-weight:bold; text-shadow: 0 0 10px #00f3ff;">V13.1 // HEX-PALM</div>
    </div>
</div>
'''

HAND_3D_JS = r'''
<script type="importmap">
  {
    "imports": {
      "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
      "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
    }
  }
</script>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

let camera, scene, renderer, controls;
let handGroup, palmGroup;
let fingers = {}; 
let targetAngles = { pouce: 0, index: 0, majeur: 0, annulaire: 0, auriculaire: 0 };
let currentAngles = { pouce: 0, index: 0, majeur: 0, annulaire: 0, auriculaire: 0 };

const DESIGN = {
    colorWire: 0x00f3ff,
    colorNode: 0xffffff,
    colorCore: 0x001133,
    colorGlow: 0x00f3ff
};

// Système de particules
let particleSystem = null;

function init() {
    const container = document.getElementById('canvas-container');
    const loadingMsg = document.getElementById('loading-msg');
    
    if (!container) { setTimeout(init, 100); return; }

    try {
        scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x000000, 0.02);

        camera = new THREE.PerspectiveCamera(40, container.clientWidth / container.clientHeight, 0.1, 100);
        camera.position.set(0, -2, 45); 
        camera.lookAt(0, -3, 0);

        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.toneMapping = THREE.ReinhardToneMapping;
        container.appendChild(renderer.domElement);

        const ambientLight = new THREE.AmbientLight(0x404040); 
        scene.add(ambientLight);
        const pointLight = new THREE.PointLight(DESIGN.colorWire, 2, 50);
        pointLight.position.set(5, 5, 5);
        scene.add(pointLight);

        // MATERIAUX
        const matWire = new THREE.MeshBasicMaterial({ color: DESIGN.colorWire, wireframe: true, transparent: true, opacity: 0.5 });
        const matCore = new THREE.MeshPhongMaterial({ color: DESIGN.colorCore, transparent: true, opacity: 0.5, flatShading: true, side: THREE.DoubleSide });
        const matNode = new THREE.MeshBasicMaterial({ color: DESIGN.colorNode, transparent: true, opacity: 0.9 });

        handGroup = new THREE.Group();
        scene.add(handGroup);

        // --- FONCTIONS HELPER ---
        function createTechPart(length, width, isJoint=false) {
            const group = new THREE.Group();
            const radius = width * 0.6; 
            
            if (isJoint) {
                const geo = new THREE.IcosahedronGeometry(radius * 0.9, 0);
                const mesh = new THREE.Mesh(geo, matNode);
                const halo = new THREE.Mesh(geo, matWire);
                halo.scale.set(1.3, 1.3, 1.3);
                mesh.add(halo);
                group.add(mesh);
            } else {
                const geo = new THREE.CylinderGeometry(radius, radius*0.8, length, 6, 1);
                geo.rotateX(Math.PI/2);
                geo.translate(0, 0, -length/2);
                group.add(new THREE.Mesh(geo, matWire));
                group.add(new THREE.Mesh(geo, matCore));
            }
            return group;
        }

        // --- CONSTRUCTION PAUME AVANCÉE (HEX-TECH) ---
        palmGroup = new THREE.Group();
        handGroup.add(palmGroup);

        // 1. Plaque Dorsale (Forme Hexagonale aplatie)
        // Utilisation d'un cylindre à 6 côtés aplati pour faire un hexagone
        const palmPlateGeo = new THREE.CylinderGeometry(4.0, 3.5, 1.5, 6, 1);
        palmPlateGeo.rotateX(Math.PI/2); // À plat face caméra
        palmPlateGeo.rotateY(Math.PI/6); // Pointe vers le haut
        palmPlateGeo.scale(1.2, 1.0, 0.3); // Large et plat
        palmPlateGeo.translate(0, 0, 3.5); // Position centrale
        
        const plateWire = new THREE.Mesh(palmPlateGeo, matWire);
        const plateCore = new THREE.Mesh(palmPlateGeo, matCore);
        palmGroup.add(plateWire);
        palmGroup.add(plateCore);

        // 2. Base du Pouce (Module Thénar)
        const thumbBaseGeo = new THREE.IcosahedronGeometry(2.0, 0);
        thumbBaseGeo.scale(1, 1.5, 0.8);
        thumbBaseGeo.translate(-3.5, -0.5, 4.0);
        const thumbBase = new THREE.Mesh(thumbBaseGeo, matCore);
        thumbBase.add(new THREE.Mesh(thumbBaseGeo, matWire));
        palmGroup.add(thumbBase);
        
        // 3. Base du Petit Doigt (Module Hypothénar)
        const pinkyBaseGeo = new THREE.IcosahedronGeometry(1.5, 0);
        pinkyBaseGeo.scale(0.8, 1.5, 0.6);
        pinkyBaseGeo.translate(3.5, -0.5, 4.0);
        const pinkyBase = new THREE.Mesh(pinkyBaseGeo, matCore);
        pinkyBase.add(new THREE.Mesh(pinkyBaseGeo, matWire));
        palmGroup.add(pinkyBase);

        // 4. Connecteur Poignet (Cuff)
        const cuffGeo = new THREE.TorusGeometry(3.0, 0.3, 4, 8);
        cuffGeo.translate(0, 0, 8.0);
        const cuff = new THREE.Mesh(cuffGeo, matWire);
        palmGroup.add(cuff);


        // --- DOIGTS ---
        const fingerSpecs = [
            { name: 'index', x: -2.2, len: 1.0 },
            { name: 'majeur', x: 0,    len: 1.1 },
            { name: 'annulaire', x: 2.2, len: 1.0 },
            { name: 'auriculaire', x: 4.2, len: 0.8 }
        ];

        fingerSpecs.forEach(spec => {
            const fingerRoot = new THREE.Group();
            fingerRoot.position.set(spec.x, 0, -0.5); // Attachés en haut de l'hexagone
            
            const k1 = createTechPart(0, 0.7, true); 
            fingerRoot.add(k1);

            const p1Len = 2.8 * spec.len;
            const p1 = createTechPart(p1Len, 1.0);
            fingerRoot.add(p1);

            const p2Group = new THREE.Group();
            p2Group.position.set(0, 0, -p1Len);
            p1.add(p2Group);
            p2Group.add(createTechPart(0, 0.6, true));

            const p2Len = 2.2 * spec.len;
            const p2 = createTechPart(p2Len, 0.9);
            p2Group.add(p2);

            const p3Group = new THREE.Group();
            p3Group.position.set(0, 0, -p2Len);
            p2.add(p3Group);
            p3Group.add(createTechPart(0, 0.5, true));
            
            const tipLen = 1.5 * spec.len;
            const p3 = createTechPart(tipLen, 0.8);
            p3Group.add(p3);

            handGroup.add(fingerRoot);
            fingers[spec.name] = { root: fingerRoot, p1: p1, p2: p2Group, p3: p3Group };
        });

        // POUCE
        const thumbRoot = new THREE.Group();
        thumbRoot.position.set(-4.5, -0.5, 2.5); // Attaché au module Thénar
        thumbRoot.rotation.y = Math.PI / 3.5; 
        thumbRoot.rotation.z = -Math.PI / 8;

        const tK1 = createTechPart(0, 0.8, true);
        thumbRoot.add(tK1);
        const t1 = createTechPart(2.8, 1.2);
        thumbRoot.add(t1);
        const t2Group = new THREE.Group();
        t2Group.position.set(0, 0, -2.8);
        t1.add(t2Group);
        t2Group.add(createTechPart(0, 0.7, true));
        const t2 = createTechPart(2.5, 1.0);
        t2Group.add(t2);

        handGroup.add(thumbRoot);
        fingers['pouce'] = { root: thumbRoot, p1: t1, p2: t2Group, p3: null };

        // ORIENTATION GLOBALE
        handGroup.rotation.x = Math.PI / 2;

        // CONTROLS
        controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.autoRotate = false; // DÉSACTIVÉ pour éviter le vertige
        
        if(loadingMsg) loadingMsg.style.display = 'none';
        window.addEventListener('resize', onWindowResize);
        animate();
    
    } catch(e) {
        if(loadingMsg) loadingMsg.innerHTML = "ERREUR 3D: " + e.message;
        console.error(e);
    }
}

function onWindowResize() {
    const container = document.getElementById('canvas-container');
    if(!container) return;
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

function animate() {
    requestAnimationFrame(animate);

    // --- ANIMATION DE ROTATION DOUCE (Balancier) ---
    // Amplitude de 0.15 radians (~8 degrés)
    // Vitesse dépendant du temps
    const time = Date.now() * 0.0005; 
    if(handGroup) {
        handGroup.rotation.y = Math.sin(time) * 0.15;
    }

    const smooth = 0.15;
    for (const key in targetAngles) {
        currentAngles[key] += (targetAngles[key] - currentAngles[key]) * smooth;
    }
    
    ['index', 'majeur', 'annulaire', 'auriculaire'].forEach(name => {
        const val = currentAngles[name];
        const f = fingers[name];
        f.p1.rotation.x = val * (Math.PI / 2.2);
        f.p2.rotation.x = val * (Math.PI / 2.5);
        f.p3.rotation.x = val * (Math.PI / 3);
    });

    const tVal = currentAngles['pouce'];
    const thumb = fingers['pouce'];
    thumb.p1.rotation.x = tVal * (Math.PI / 4); 
    thumb.root.rotation.y = (Math.PI / 3.5) - (tVal * 0.3);
    thumb.p2.rotation.x = tVal * (Math.PI / 2);

    controls.update();
    renderer.render(scene, camera);
}

window.updateHandData = function(jsonStr) {
    try {
        const data = JSON.parse(jsonStr);
        if(data['pouce_articulation'] !== undefined) targetAngles.pouce = data['pouce_articulation'];
        if(data['index'] !== undefined) targetAngles.index = data['index'];
        if(data['majeur'] !== undefined) targetAngles.majeur = data['majeur'];
        if(data['annulaire_auriculaire'] !== undefined) {
            targetAngles.annulaire = data['annulaire_auriculaire'];
            targetAngles.auriculaire = data['annulaire_auriculaire'];
        }
    } catch(e) {}
};

setTimeout(init, 100);
</script>
'''

# --------------------------------------------------------------------
# 5. UI PRINCIPALE
# --------------------------------------------------------------------
def build_ui():
    ui.add_head_html(CSS_STYLE)

    with ui.row().classes('hud-header w-full h-[8vh] min-h-[60px] items-center justify-between px-6 sm:px-8'):
        with ui.row().classes('items-center gap-3'):
            ui.icon('hub', color='cyan-400').classes('text-2xl')
            with ui.column().classes('gap-0'):
                ui.label('NEURO-LINK // SYSTEM V13.1').classes('text-sm sm:text-lg text-cyan-400 font-bold tracking-widest')
                ui.label('HOLOGRAPHIC CORE • HEX-PALM').classes('text-[10px] text-gray-400 tracking-wider')
        
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
            # ATTENTION : sanitize=False est vital
            ui.html(HAND_3D_STRUCTURE, sanitize=False).classes('w-full h-full')
            # Injection JS
            ui.add_body_html(HAND_3D_JS)

    loop_count = [0]  # Compteur pour debug
    
    def update_loop():
        try:
            loop_count[0] += 1
            if loop_count[0] % 20 == 0:  # Log toutes les secondes
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

    # Démarrer les threads AVANT build_ui() pour qu'ils ne soient créés qu'une fois
    print("[INIT] Démarrage des threads de communication...")
    threading.Thread(target=receiver_thread, daemon=True).start()
    threading.Thread(target=hardware_thread, args=(controller,), daemon=True).start()
    time.sleep(0.5)  # Laisser les threads démarrer

    # NiceGUI en mode app (pas multi-session)
    @ui.page('/')
    def index():
        build_ui()
    
    ui.run(host='0.0.0.0', port=8080, dark=True, reload=False, title='NEURO-LINK V13.1')