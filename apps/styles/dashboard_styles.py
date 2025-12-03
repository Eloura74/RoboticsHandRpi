# apps/styles/dashboard_styles.py
"""
Module contenant tous les éléments visuels (CSS, HTML, JS) 
pour le dashboard neuro_dashboard.py
Style: CLEAN CRYSTAL / STATIC 3D
"""

# --------------------------------------------------------------------
# CSS STYLES (Deep Space & Neon)
# --------------------------------------------------------------------

CSS_STYLE = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');
    
    :root { 
        --neon-cyan: #00f3ff; 
        --neon-blue: #0066ff; 
        --bg-dark: #020408; 
    }
    
    body { 
        background-color: #000; 
        color: var(--neon-cyan); 
        font-family: 'Rajdhani', sans-serif; 
        overflow: hidden; 
        margin: 0; 
    }
    
    /* HUD General */
    .hud-header { 
        background: linear-gradient(180deg, rgba(0,20,40,0.9) 0%, rgba(0,0,0,0.8) 100%);
        border-bottom: 1px solid rgba(0, 243, 255, 0.15);
        box-shadow: 0 5px 20px rgba(0, 243, 255, 0.05);
        z-index: 10;
    }
    
    .hud-panel { 
        background: rgba(4, 12, 24, 0.7); 
        border: 1px solid rgba(0, 243, 255, 0.1); 
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
        backdrop-filter: blur(8px);
        border-radius: 2px;
    }
    
    /* Decors HUD */
    .hud-panel::before, .hud-panel::after {
        content: ''; position: absolute; width: 8px; height: 8px;
        border: 1px solid var(--neon-cyan); transition: all 0.3s; opacity: 0.5;
    }
    .hud-panel::before { top: 0; left: 0; border-right: none; border-bottom: none; }
    .hud-panel::after { bottom: 0; right: 0; border-left: none; border-top: none; }

    /* Boutons High-Tech */
    .cyber-btn { 
        background: linear-gradient(90deg, transparent 0%, rgba(0, 243, 255, 0.1) 50%, transparent 100%);
        border: 1px solid rgba(0, 243, 255, 0.3);
        color: var(--neon-cyan);
        font-family: 'Orbitron';
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        position: relative;
        overflow: hidden;
        transition: all 0.3s;
    }
    .cyber-btn::before {
        content: ''; position: absolute; top:0; left:-100%; width:100%; height:100%;
        background: linear-gradient(90deg, transparent, rgba(0,243,255,0.4), transparent);
        transition: 0.5s;
    }
    .cyber-btn:hover { 
        border-color: var(--neon-cyan); 
        text-shadow: 0 0 8px var(--neon-cyan);
        background: rgba(0, 243, 255, 0.15);
    }
    .cyber-btn:hover::before { left: 100%; }
    
    .danger-btn { 
        background: rgba(30, 0, 0, 0.4); 
        border: 1px solid #ff3333; 
        color: #ff3333; 
        font-family: 'Orbitron'; 
    }
    
    /* Canvas Zone */
    #canvas-container { 
        width: 100%; height: 100%; position: relative; 
        background: radial-gradient(circle at 50% 50%, #051020 0%, #000000 90%);
    }
    
    #loading-msg {
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        font-family: 'Orbitron'; color: var(--neon-cyan); font-size: 14px; letter-spacing: 4px;
        text-shadow: 0 0 20px var(--neon-cyan);
    }
</style>
'''

# --------------------------------------------------------------------
# HTML STRUCTURE
# --------------------------------------------------------------------

HAND_3D_STRUCTURE = r'''
<div id="canvas-container">
    <div id="loading-msg">SYSTEM READY.</div>
    
    <div style="position:absolute; bottom:30px; right:30px; text-align:right; pointer-events:none; z-index:5;">
        <div style="font-family:'Rajdhani'; font-weight:700; color:#fff; font-size:32px; letter-spacing:2px; text-shadow:0 0 15px #00f3ff;">PLEXUS <span style="color:#00f3ff; font-size:16px;">V4.1</span></div>
        <div style="font-family:'Orbitron'; color:rgba(255,255,255,0.4); font-size:10px;">STATIC MESH RENDER</div>
    </div>
</div>
'''

# --------------------------------------------------------------------
# JAVASCRIPT 3D ENGINE (THREE.JS - CLEAN 3D STYLE)
# --------------------------------------------------------------------

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

// CONFIG
const PALETTE = {
    cyan: 0x00f3ff,
    blue: 0x0044ff,
    white: 0xffffff
};

let camera, scene, renderer, controls;
let handGroup, palmCore;
let fingers = {}; 
let targetAngles = { pouce: 0, index: 0, majeur: 0, annulaire: 0, auriculaire: 0 };
let currentAngles = { pouce: 0, index: 0, majeur: 0, annulaire: 0, auriculaire: 0 };
let particles;

// --- MATERIAUX (Modifiés pour plus de volume 3D) ---

// 1. Le Wireframe (Cage externe)
const matWire = new THREE.MeshBasicMaterial({ 
    color: PALETTE.cyan, 
    wireframe: true, 
    transparent: true, 
    opacity: 0.4, // Un peu plus visible
    blending: THREE.AdditiveBlending 
});

// 2. Le Coeur (Volume interne) - C'EST ICI QUE LE VOLUME SE CRÉE
// Utilisation de MeshPhongMaterial au lieu de Basic pour réagir à la lumière
const matCoreVolume = new THREE.MeshPhongMaterial({
    color: PALETTE.blue,        // Couleur de base
    emissive: PALETTE.blue,     // Couleur émise (le "glow")
    emissiveIntensity: 0.3,     // Intensité du glow
    transparent: true,
    opacity: 0.3,               // Assez opaque pour voir les facettes
    flatShading: true,          // CRUCIAL : Donne l'aspect "cristal" facetté
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    depthWrite: false
});

// 3. Les Articulations (Points brillants)
const matJoint = new THREE.MeshBasicMaterial({
    color: PALETTE.white,
    transparent: true,
    opacity: 1.0,
    blending: THREE.AdditiveBlending
});

function init() {
    const container = document.getElementById('canvas-container');
    const loadingMsg = document.getElementById('loading-msg');
    
    if (!container) { setTimeout(init, 100); return; }

    try {
        scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x000000, 0.015);

        camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
        camera.position.set(0, 2, 35); 

        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setClearColor(0x000000, 0); 
        container.appendChild(renderer.domElement);

        // --- ECLAIRAGE (Crucial pour le volume 3D) ---
        const ambient = new THREE.AmbientLight(0x112233); // Lumière globale faible
        scene.add(ambient);

        // Lumières ponctuelles pour faire briller les facettes
        const light1 = new THREE.PointLight(PALETTE.cyan, 2, 50);
        light1.position.set(15, 15, 20);
        scene.add(light1);

        const light2 = new THREE.PointLight(PALETTE.blue, 1.5, 50);
        light2.position.set(-15, -10, 20);
        scene.add(light2);

        handGroup = new THREE.Group();
        scene.add(handGroup);

        buildPlexusHand();
        createDataParticles();

        controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.autoRotate = false; // STOP ROTATION AUTOMATIQUE
        controls.maxDistance = 60;
        
        if(loadingMsg) loadingMsg.style.display = 'none';
        window.addEventListener('resize', onWindowResize);
        animate();
    
    } catch(e) { console.error(e); }
}

// Générateur de phalange "Cristal 3D"
function createCrystalBone(length, radiusStart, radiusEnd) {
    const group = new THREE.Group();

    // Géométrie Icosaèdre (Facettes triangulaires)
    // Detail = 0 pour de grosses facettes bien visibles
    const geo = new THREE.IcosahedronGeometry(radiusStart, 0); 
    
    // Étirement
    geo.applyMatrix4(new THREE.Matrix4().makeScale(1, length / (radiusStart*1.4), 1));
    
    // Pivot à la base
    geo.translate(0, length/2, 0);
    geo.rotateX(-Math.PI/2);

    // 1. Cage filaire
    const meshWire = new THREE.Mesh(geo, matWire);
    group.add(meshWire);

    // 2. Volume interne facetté (Réagit à la lumière maintenant)
    const meshCore = new THREE.Mesh(geo, matCoreVolume);
    meshCore.scale.set(0.95, 0.95, 0.95); // Légèrement plus petit pour éviter le z-fighting
    group.add(meshCore);

    return group;
}

function createJointNode(size) {
    const group = new THREE.Group();
    const coreGeo = new THREE.IcosahedronGeometry(size * 0.5, 2);
    const core = new THREE.Mesh(coreGeo, matJoint);
    group.add(core);
    
    // Petit halo externe
    const haloGeo = new THREE.IcosahedronGeometry(size * 0.8, 1);
    const halo = new THREE.Mesh(haloGeo, new THREE.MeshBasicMaterial({
        color: PALETTE.blue, wireframe: true, transparent: true, opacity: 0.3
    }));
    group.add(halo);

    return group;
}

function buildPlexusHand() {
    const palmGroup = new THREE.Group();
    handGroup.add(palmGroup);

    // --- PAUME ---
    // Juste le noyau central, plus propre, sans anneaux
    const coreGeo = new THREE.IcosahedronGeometry(2.8, 1);
    // On utilise aussi le matériau Phomg pour le noyau pour le volume
    palmCore = new THREE.Mesh(coreGeo, matCoreVolume.clone());
    // On ajoute le wireframe par dessus
    palmCore.add(new THREE.Mesh(coreGeo, matWire));
    
    palmCore.position.set(0, 0, 3.5);
    palmCore.scale.set(1.2, 0.8, 1); // Un peu aplati
    palmGroup.add(palmCore);
    
    // Connecteur Poignet
    const wrist = createJointNode(1.5);
    wrist.position.set(0, 0, 8);
    palmGroup.add(wrist);

    // Lignes de connexion (Poignet -> Doigts)
    const lineGeo = new THREE.BufferGeometry();
    const points = [];
    [-2.2, -1, 0, 1, 2.2].forEach(x => {
        points.push(0, 0, 8); // Start
        points.push(x, 0, 1); // End
    });
    lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(points, 3));
    const lines = new THREE.LineSegments(lineGeo, new THREE.LineBasicMaterial({ color: PALETTE.blue, opacity: 0.3, transparent: true }));
    palmGroup.add(lines);

    // --- DOIGTS ---
    const specs = [
        { name: 'index', x: -2.2, len: 1.0 },
        { name: 'majeur', x: 0,    len: 1.1 },
        { name: 'annulaire', x: 2.2, len: 1.0 },
        { name: 'auriculaire', x: 4.2, len: 0.8 }
    ];

    specs.forEach(s => {
        const root = new THREE.Group();
        root.position.set(s.x, 0, 0.5);

        root.add(createJointNode(0.5));

        const p1Len = 2.8 * s.len;
        const p1 = createCrystalBone(p1Len, 0.65, 0.55); // Un peu plus épais pour le volume
        root.add(p1);

        const p2Group = new THREE.Group();
        p2Group.position.set(0, 0, -p1Len);
        p1.add(p2Group);
        p2Group.add(createJointNode(0.4));
        
        const p2Len = 2.2 * s.len;
        const p2 = createCrystalBone(p2Len, 0.55, 0.45);
        p2Group.add(p2);

        const p3Group = new THREE.Group();
        p3Group.position.set(0, 0, -p2Len);
        p2.add(p3Group);
        p3Group.add(createJointNode(0.35));

        const tipLen = 1.5 * s.len;
        const p3 = createCrystalBone(tipLen, 0.45, 0.1);
        p3Group.add(p3);

        handGroup.add(root);
        fingers[s.name] = { root: root, p1: p1, p2: p2Group, p3: p3Group };
    });

    // --- POUCE ---
    const thumbRoot = new THREE.Group();
    thumbRoot.position.set(-3.5, -0.5, 5.0);
    thumbRoot.rotation.y = Math.PI / 3.5;
    thumbRoot.rotation.z = -Math.PI / 8;
    
    thumbRoot.add(createJointNode(0.6));
    
    const t1 = createCrystalBone(2.8, 0.7, 0.6);
    thumbRoot.add(t1);

    const t2Group = new THREE.Group();
    t2Group.position.set(0, 0, -2.8);
    t1.add(t2Group);
    t2Group.add(createJointNode(0.5));

    const t2 = createCrystalBone(2.5, 0.6, 0.4);
    t2Group.add(t2);

    handGroup.add(thumbRoot);
    fingers['pouce'] = { root: thumbRoot, p1: t1, p2: t2Group, p3: null };

    handGroup.rotation.x = Math.PI / 2;
}

function createDataParticles() {
    const count = 250;
    const geo = new THREE.BufferGeometry();
    const pos = [];
    for(let i=0; i<count; i++) {
        pos.push((Math.random()-0.5)*50, (Math.random()-0.5)*50, (Math.random()-0.5)*40);
    }
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    particles = new THREE.Points(geo, new THREE.PointsMaterial({
        color: PALETTE.cyan, size: 0.12, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending
    }));
    scene.add(particles);
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
    // PLUS DE ROTATION AUTOMATIQUE DE LA MAIN
    // PLUS D'ANIMATION DES ANNEAUX

    // Juste une très légère respiration du noyau central
    if(palmCore) {
        const time = Date.now() * 0.001;
        palmCore.scale.setScalar(1 + Math.sin(time*1.5)*0.02);
    }

    // Interpolation Angles (inchangé)
    const smooth = 0.15;
    for (const key in targetAngles) {
        currentAngles[key] += (targetAngles[key] - currentAngles[key]) * smooth;
    }
    
    ['index', 'majeur', 'annulaire', 'auriculaire'].forEach(name => {
        const val = currentAngles[name];
        const f = fingers[name];
        f.p1.rotation.x = val * (Math.PI / 1.8);
        f.p2.rotation.x = val * (Math.PI / 2.0);
        f.p3.rotation.x = val * (Math.PI / 2.2);
    });

    const tVal = currentAngles['pouce'];
    const thumb = fingers['pouce'];
    thumb.p1.rotation.x = tVal * (Math.PI / 3); 
    thumb.root.rotation.y = (Math.PI / 3.5) - (tVal * 0.5); 
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