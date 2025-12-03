# apps/styles/dashboard_stylesV2.py
"""
Module visuel - Style: FUSION NEURAL V8.1 (Bugfix + Lasers)
Correction du plantage au chargement.
Maintient les liaisons visuelles (lasers) même si les pièces flottent.
"""

CSS_STYLE = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');
    :root { --neon-cyan: #00f3ff; --neon-blue: #0066ff; --bg-dark: #020408; }
    body { background-color: #000; color: var(--neon-cyan); font-family: 'Rajdhani', sans-serif; overflow: hidden; margin: 0; }
    #canvas-container { width: 100%; height: 100%; position: relative; background: radial-gradient(circle at 50% 50%, #051020 0%, #000000 90%); }
    #loading-msg { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-family: 'Orbitron'; color: var(--neon-cyan); font-size: 14px; letter-spacing: 4px; text-align: center; }
    .hud-header { background: linear-gradient(180deg, rgba(0,20,40,0.9) 0%, rgba(0,0,0,0.8) 100%); border-bottom: 1px solid rgba(0, 243, 255, 0.15); box-shadow: 0 5px 20px rgba(0, 243, 255, 0.05); z-index: 10; }
    .cyber-btn { background: linear-gradient(90deg, transparent 0%, rgba(0, 243, 255, 0.1) 50%, transparent 100%); border: 1px solid rgba(0, 243, 255, 0.3); color: var(--neon-cyan); font-family: 'Orbitron'; font-size: 11px; text-transform: uppercase; transition: all 0.3s; }
    .cyber-btn:hover { border-color: var(--neon-cyan); background: rgba(0, 243, 255, 0.15); }
    .danger-btn { background: rgba(30, 0, 0, 0.4); border: 1px solid #ff3333; color: #ff3333; font-family: 'Orbitron'; }
</style>
'''

HAND_3D_STRUCTURE = r'''
<div id="canvas-container">
    <div id="loading-msg">SYSTEME NEURAL V8.1...</div>
    <div style="position:absolute; bottom:30px; right:30px; text-align:right; pointer-events:none; z-index:5;">
        <div style="font-family:'Rajdhani'; font-weight:700; color:#fff; font-size:32px; letter-spacing:2px; text-shadow:0 0 15px #00f3ff;">NEURO-HAND <span style="color:#00f3ff; font-size:16px;">V8.1</span></div>
        <div style="font-family:'Orbitron'; color:rgba(255,255,255,0.4); font-size:10px;">MAGNETIC FIELD LINKS</div>
    </div>
</div>
'''

HAND_3D_JS = r'''
<script type="importmap">
  { "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js", "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/" } }
</script>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const MODEL_PATH = '/assets/main_fusion.glb'; 
const PALETTE = { cyan: 0x00f3ff, blue: 0x0044ff, laser: 0x00ffff };

let camera, scene, renderer, controls;
let fingers = { 
    pouce: {parts:[]}, index: {parts:[]}, majeur: {parts:[]}, annulaire: {parts:[]}, auriculaire: {parts:[]} 
};
let neuralLines = []; 

let targetAngles = { pouce: 0, index: 0, majeur: 0, annulaire: 0, auriculaire: 0 };
let currentAngles = { pouce: 0, index: 0, majeur: 0, annulaire: 0, auriculaire: 0 };

const matSolid = new THREE.MeshPhongMaterial({ 
    color: 0x001133, emissive: 0x0044ff, emissiveIntensity: 0.6, 
    flatShading: false, transparent: true, opacity: 0.8, side: THREE.DoubleSide
});
const matWire = new THREE.MeshBasicMaterial({ color: PALETTE.cyan, wireframe: true, transparent: true, opacity: 0.15 });
const matLine = new THREE.LineBasicMaterial({ color: PALETTE.laser, transparent: true, opacity: 0.6, linewidth: 2 });

function init() {
    const container = document.getElementById('canvas-container');
    if (!container) { setTimeout(init, 100); return; }

    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.02);

    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 5, 45); 

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(renderer.domElement);

    const light = new THREE.PointLight(PALETTE.cyan, 3, 100);
    light.position.set(20, 20, 20);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0xffffff, 0.5));

    loadFusionModel();

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    
    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
    animate();
}

function loadFusionModel() {
    const loader = new GLTFLoader();
    
    loader.load(MODEL_PATH, (gltf) => {
        const model = gltf.scene;
        
        // 1. COLLECTE SÉCURISÉE (On liste d'abord, on modifie après)
        // C'est ça qui corrige le bug du chargement infini
        const meshesToProcess = [];
        model.traverse((child) => {
            if (child.isMesh) meshesToProcess.push(child);
        });

        // 2. Traitement des pièces
        meshesToProcess.forEach(child => {
            child.material = matSolid;
            // On ajoute le wireframe maintenant qu'on ne traverse plus
            child.add(new THREE.Mesh(child.geometry, matWire));
            
            const name = child.name.toLowerCase();
            const fingerNames = ['pouce', 'index', 'majeur', 'annulaire', 'auriculaire'];
            
            fingerNames.forEach(fName => {
                if (name.includes(fName)) {
                    fingers[fName].parts.push(child);
                }
            });
        });

        // 3. Création des Lasers (Neural Links)
        for(let fName in fingers) {
            // On trie les pièces (1, 2, 3) pour que le laser suive le doigt
            fingers[fName].parts.sort((a, b) => a.name.localeCompare(b.name));
            
            if (fingers[fName].parts.length > 0) {
                createNeuralChain(fingers[fName].parts);
            }
        }

        // 4. Centrage
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        model.position.sub(center); 
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 15.0 / maxDim; 
        model.scale.set(scale, scale, scale);
        model.rotation.x = -Math.PI / 2; 

        scene.add(model);
        document.getElementById('loading-msg').style.display = 'none';

    }, undefined, (e) => { 
        console.error(e); 
        document.getElementById('loading-msg').innerHTML = "ERREUR: " + e.message;
    });
}

function createNeuralChain(partsList) {
    const count = partsList.length;
    if (count < 2) return;

    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3); 
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const line = new THREE.Line(geometry, matLine);
    line.userData.targets = partsList; 
    scene.add(line);
    neuralLines.push(line);
}

function updateNeuralLines() {
    neuralLines.forEach(line => {
        const targets = line.userData.targets;
        const positions = line.geometry.attributes.position.array;
        
        targets.forEach((mesh, i) => {
            const worldPos = new THREE.Vector3();
            mesh.getWorldPosition(worldPos);
            
            positions[i * 3] = worldPos.x;
            positions[i * 3 + 1] = worldPos.y;
            positions[i * 3 + 2] = worldPos.z;
        });
        line.geometry.attributes.position.needsUpdate = true;
    });
}

function animate() {
    requestAnimationFrame(animate);
    
    const smooth = 0.15;
    for (const key in targetAngles) {
        currentAngles[key] += (targetAngles[key] - currentAngles[key]) * smooth;
    }

    ['index', 'majeur', 'annulaire', 'auriculaire'].forEach(name => {
        const val = currentAngles[name];
        fingers[name].parts.forEach(mesh => {
            // Rotation propre sans parentage complexe (évite les bugs)
            mesh.rotation.x = val * (Math.PI / 2.2);
        });
    });
    
    const tVal = currentAngles['pouce'];
    fingers['pouce'].parts.forEach(mesh => {
         mesh.rotation.x = tVal * (Math.PI / 3);
    });

    updateNeuralLines();
    controls.update();
    renderer.render(scene, camera);
}

window.updateHandData = function(jsonStr) {
    try {
        const data = JSON.parse(jsonStr);
        if(data.index !== undefined) targetAngles.index = data.index;
        if(data.majeur !== undefined) targetAngles.majeur = data.majeur;
        if(data.annulaire_auriculaire !== undefined) {
             targetAngles.annulaire = data.annulaire_auriculaire;
             targetAngles.auriculaire = data.annulaire_auriculaire;
        }
        if(data.pouce_articulation !== undefined) targetAngles.pouce = data.pouce_articulation;
    } catch(e) {}
};

setTimeout(init, 100);
</script>
'''