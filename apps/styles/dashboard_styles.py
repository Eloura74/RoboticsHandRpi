# apps/styles/dashboard_styles.py
"""
Module contenant tous les éléments visuels (CSS, HTML, JS) 
pour le dashboard neuro_dashboard.py
Séparé pour faciliter la maintenance et les modifications visuelles
"""

# --------------------------------------------------------------------
# CSS STYLES
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

# --------------------------------------------------------------------
# HTML STRUCTURE (3D CANVAS)
# --------------------------------------------------------------------

HAND_3D_STRUCTURE = r'''
<div id="canvas-container">
    <div id="loading-msg">
        INITIALISATION NEURO-NET...<br>
        <span style="font-size:10px; color:#aaa;">CHARGEMENT HOLOGRAPHIQUE</span>
    </div>
    <div class="overlay-ui" style="top:20px; right:20px; text-align:right;">
        <div style="font-family:'Orbitron'; color:#00f3ff; font-size:12px;">VISUAL CORE</div>
        <div style="font-family:'Rajdhani'; color:#fff; font-size:20px; font-weight:bold; text-shadow: 0 0 10px #00f3ff;">V13.0 // CONSTELLATION</div>
    </div>
</div>
'''

# --------------------------------------------------------------------
# JAVASCRIPT 3D ENGINE (Three.js)
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

let camera, scene, renderer, controls;
let handGroup;
let fingers = {}; 
let targetAngles = { pouce: 0, index: 0, majeur: 0, annulaire: 0, auriculaire: 0 };
let currentAngles = { pouce: 0, index: 0, majeur: 0, annulaire: 0, auriculaire: 0 };

// --- CONFIGURATION DU DESIGN "CONSTELLATION" ---
const DESIGN = {
    colorWire: 0x00f3ff,    // Cyan Néon (Structure)
    colorNode: 0xffffff,    // Blanc (Articulations)
    colorCore: 0x001133,    // Bleu Profond (Volume intérieur)
    glowIntensity: 1.5
};

function init() {
    const container = document.getElementById('canvas-container');
    const loadingMsg = document.getElementById('loading-msg');
    
    if (!container) { setTimeout(init, 100); return; }

    try {
        // SCENE
        scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x000000, 0.02);

        // CAMERA (Position reculée pour vue d'ensemble)
        camera = new THREE.PerspectiveCamera(40, container.clientWidth / container.clientHeight, 0.1, 100);
        camera.position.set(0, -2, 45); 
        camera.lookAt(0, -3, 0);

        // RENDERER
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.toneMapping = THREE.ReinhardToneMapping;
        container.appendChild(renderer.domElement);

        // ECLAIRAGE (Pour le volume interne)
        const ambientLight = new THREE.AmbientLight(0x404040); 
        scene.add(ambientLight);
        const pointLight = new THREE.PointLight(DESIGN.colorWire, 2, 50);
        pointLight.position.set(5, 5, 5);
        scene.add(pointLight);

        // --- MATERIAUX HOLOGRAPHIQUES ---
        
        // 1. Structure Filaire (Lignes Cyan)
        const matWire = new THREE.MeshBasicMaterial({ 
            color: DESIGN.colorWire, 
            wireframe: true, 
            transparent: true, 
            opacity: 0.6 
        });

        // 2. Volume Fantôme (Intérieur sombre)
        const matCore = new THREE.MeshPhongMaterial({
            color: DESIGN.colorCore,
            transparent: true,
            opacity: 0.4,
            flatShading: true,
            side: THREE.DoubleSide
        });

        // 3. Nœuds Lumineux (Articulations) - Remplaçant le "PointsMaterial" pour plus de contrôle
        const matNode = new THREE.MeshBasicMaterial({
            color: DESIGN.colorNode,
            transparent: true,
            opacity: 0.9
        });

        // --- CONSTRUCTION ---
        handGroup = new THREE.Group();
        scene.add(handGroup);

        // Helper pour créer un segment "Tech" (Icosaèdre Low Poly)
        function createTechPart(length, width, isJoint=false) {
            const group = new THREE.Group();
            
            // Géométrie : Icosaèdre pour le look "Cristal/Low Poly"
            // Rayon approx basé sur la largeur
            const radius = width * 0.6; 
            const detail = 0; // 0 = Low Poly très anguleux
            
            // Si c'est une articulation (Joint), on fait une sphère brillante
            if (isJoint) {
                const geo = new THREE.IcosahedronGeometry(radius * 0.9, 1);
                const mesh = new THREE.Mesh(geo, matNode);
                // Petit halo filaire autour
                const halo = new THREE.Mesh(geo, matWire);
                halo.scale.set(1.2, 1.2, 1.2);
                mesh.add(halo);
                group.add(mesh);
            } 
            else {
                // Si c'est une phalange, on l'étire pour faire un os
                // On utilise un Cylindre Low Poly (6 segments) pour le style
                const geo = new THREE.CylinderGeometry(radius, radius*0.8, length, 6, 1);
                geo.rotateX(Math.PI/2);
                geo.translate(0, 0, -length/2);
                
                // Version Filaire (Exosquelette)
                const wireMesh = new THREE.Mesh(geo, matWire);
                group.add(wireMesh);
                
                // Version Volume (Noyau)
                const coreMesh = new THREE.Mesh(geo, matCore);
                // coreMesh.scale.set(0.8, 0.8, 0.9); // Noyau un peu plus petit
                group.add(coreMesh);
            }
            return group;
        }

        // PAUME (Structure centrale)
        const palmGroup = new THREE.Group();
        handGroup.add(palmGroup);
        
        // Plaque Paume (Style Chipset)
        const palmGeo = new THREE.BoxGeometry(8, 1, 6.5);
        const palmWire = new THREE.Mesh(palmGeo, matWire);
        const palmCore = new THREE.Mesh(palmGeo, matCore);
        palmGroup.add(palmWire);
        palmGroup.add(palmCore);
        
        // AVANT-BRAS (Connexion données)
        const armGeo = new THREE.CylinderGeometry(3, 4, 8, 8, 1);
        armGeo.rotateX(Math.PI/2);
        armGeo.translate(0, 0, 8);
        const armWire = new THREE.Mesh(armGeo, matWire);
        // Ajout de "lignes de flux" (anneaux)
        for(let i=0; i<3; i++) {
            const ring = new THREE.Mesh(new THREE.TorusGeometry(3.2+i*0.2, 0.05, 4, 16), matNode);
            ring.position.set(0, 0, 5 + i*2);
            armWire.add(ring);
        }
        handGroup.add(armWire);

        // DOIGTS
        const fingerSpecs = [
            { name: 'index', x: -2.2, len: 1.0 },
            { name: 'majeur', x: 0,    len: 1.1 },
            { name: 'annulaire', x: 2.2, len: 1.0 },
            { name: 'auriculaire', x: 4.2, len: 0.8 }
        ];

        fingerSpecs.forEach(spec => {
            const fingerRoot = new THREE.Group();
            fingerRoot.position.set(spec.x, 0, -3.3);
            
            // Jointure Base
            const k1 = createTechPart(0, 0.7, true); // Joint
            fingerRoot.add(k1);

            // P1
            const p1Len = 2.8 * spec.len;
            const p1 = createTechPart(p1Len, 1.0);
            fingerRoot.add(p1);

            // P2
            const p2Group = new THREE.Group();
            p2Group.position.set(0, 0, -p1Len);
            p1.add(p2Group);
            p2Group.add(createTechPart(0, 0.6, true)); // Joint

            const p2Len = 2.2 * spec.len;
            const p2 = createTechPart(p2Len, 0.9);
            p2Group.add(p2);

            // P3
            const p3Group = new THREE.Group();
            p3Group.position.set(0, 0, -p2Len);
            p2.add(p3Group);
            p3Group.add(createTechPart(0, 0.5, true)); // Joint
            
            const tipLen = 1.5 * spec.len;
            const p3 = createTechPart(tipLen, 0.8);
            p3Group.add(p3);

            handGroup.add(fingerRoot);
            fingers[spec.name] = { root: fingerRoot, p1: p1, p2: p2Group, p3: p3Group };
        });

        // POUCE
        const thumbRoot = new THREE.Group();
        thumbRoot.position.set(-4.5, -0.5, 1.5);
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
        controls.autoRotate = true;     // Rotation lente auto pour l'effet "Hologramme Showcase"
        controls.autoRotateSpeed = 1.0;
        
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
