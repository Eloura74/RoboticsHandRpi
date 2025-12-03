# apps/styles/dashboard_stylesV2.py
"""
Module visuel - Style: FUSION NEON V8.4 (Solid-Core Holo)
- Base V8.3 fonctionnelle (auto-rig, bloom léger).
- CHANGEMENT 1 : Rotation automatique désactivée.
- CHANGEMENT 2 : La paume utilise un matériau différent, opaque et solide,
  pour se distinguer des doigts holographiques.
"""

CSS_STYLE = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');

    :root {
        --neon-cyan: #00f3ff;
        --neon-magenta: #ff00ff;
        --bg-dark: #010205;
    }

    body {
        background-color: var(--bg-dark);
        color: var(--neon-cyan);
        font-family: 'Rajdhani', sans-serif;
        overflow: hidden;
        margin: 0;
    }

    #canvas-container {
        width: 100%;
        height: 100%;
        position: relative;
        background: radial-gradient(circle at 50% 50%, #0a101a 0%, #000000 90%);
    }

    #loading-msg {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-family: 'Orbitron';
        color: var(--neon-cyan);
        font-size: 14px;
        letter-spacing: 4px;
        text-align: center;
    }

    .hud-header {
        background: linear-gradient(180deg, rgba(0,10,20,0.95) 0%, rgba(0,0,0,0.9) 100%);
        border-bottom: 1px solid rgba(0, 243, 255, 0.2);
        box-shadow: 0 5px 25px rgba(0, 243, 255, 0.1);
        z-index: 10;
    }

    .cyber-btn {
        background: linear-gradient(90deg, transparent 0%, rgba(0, 243, 255, 0.1) 50%, transparent 100%);
        border: 1px solid rgba(0, 243, 255, 0.4);
        color: var(--neon-cyan);
        font-family: 'Orbitron';
        font-size: 11px;
        text-transform: uppercase;
        transition: all 0.3s;
    }

    .cyber-btn:hover {
        border-color: var(--neon-cyan);
        background: rgba(0, 243, 255, 0.2);
    }
    .danger-btn {
        background: rgba(40, 0, 0, 0.5);
        border: 1px solid #ff3333;
        color: #ff3333;
        font-family: 'Orbitron';
    }
</style>
'''

HAND_3D_STRUCTURE = r'''
<div id="canvas-container">
    <div id="loading-msg">CALIBRATION V8.4...</div>
    <div style="position:absolute; bottom:30px; right:30px; text-align:right; pointer-events:none; z-index:5;">
        <div style="font-family:'Rajdhani'; font-weight:700; color:#fff; font-size:32px; letter-spacing:2px; text-shadow:0 0 10px #00f3ff;">
            NEURO-HAND <span style="color:#00f3ff; font-size:16px;">V8.4</span>
        </div>
        <div style="font-family:'Orbitron'; color:rgba(0, 243, 255, 0.6); font-size:10px; letter-spacing: 1px;">SOLID-CORE HOLOGRAPHIC</div>
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
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const MODEL_PATH = '/assets/main_fusion.glb';
const PALETTE = {
    cyanBright: 0x00ffff,
    cyanDeep: 0x004488,
    magenta: 0xff0088,
    bgDark: 0x020408
};

let camera, scene, renderer, controls, composer;

let fingers = {
    pouce:       { segments: [], joints: [] },
    index:       { segments: [], joints: [] },
    majeur:      { segments: [], joints: [] },
    annulaire:   { segments: [], joints: [] },
    auriculaire: { segments: [], joints: [] },
};
let palmMesh = null;
let targetAngles  = { pouce: 0, index: 0, majeur: 0, annulaire: 0, auriculaire: 0 };
let currentAngles = { pouce: 0, index: 0, majeur: 0, annulaire: 0, auriculaire: 0 };

// ---------------------------------------------------------------------------
// MATERIAUX
// ---------------------------------------------------------------------------

// 1. Matériau Holographique (pour les DOIGTS) - Transparent
const matHoloFingers = new THREE.MeshPhysicalMaterial({
    color: 0x000000,
    emissive: PALETTE.cyanDeep,
    emissiveIntensity: 0.5,
    metalness: 0.8,
    roughness: 0.1,
    transmission: 0.6,           // Transparent
    opacity: 0.4,
    transparent: true,
    side: THREE.DoubleSide,
    depthWrite: false,
});

// 2. NOUVEAU Matériau Solide (pour la PAUME) - Opaque
const matSolidPalm = new THREE.MeshPhysicalMaterial({
    color: PALETTE.cyanDeep,     // Couleur de base plus présente
    emissive: PALETTE.cyanDeep,
    emissiveIntensity: 0.2,      // Moins lumineux de l'intérieur
    metalness: 0.7,
    roughness: 0.4,              // Plus mat
    transmission: 0.0,           // Opaque (pas d'effet verre)
    opacity: 0.95,               // Quasiment solide
    transparent: false,          // Traité comme un objet solide par le moteur
    side: THREE.DoubleSide,
});

// 3. Matériau Wireframe (Commun)
const matWire = new THREE.MeshBasicMaterial({
    color: PALETTE.cyanBright,
    wireframe: true,
    transparent: true,
    opacity: 0.5,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
});

// ---------------------------------------------------------------------------
// INIT
// ---------------------------------------------------------------------------
function init() {
    const container = document.getElementById('canvas-container');
    if (!container) { setTimeout(init, 100); return; }

    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(PALETTE.bgDark, 0.02);

    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 5, 45);

    renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true, powerPreference: "high-performance" });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ReinhardToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0x222222));
    const lightMain = new THREE.PointLight(PALETTE.cyanBright, 3, 100);
    lightMain.position.set(20, 30, 20);
    scene.add(lightMain);
    const lightRim = new THREE.PointLight(PALETTE.magenta, 2, 80);
    lightRim.position.set(-20, -10, 10);
    scene.add(lightRim);

    composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloomPass = new UnrealBloomPass(
        new THREE.Vector2(container.clientWidth, container.clientHeight),
        0.2, 0.3, 0.2
    );
    composer.addPass(bloomPass);
    composer.addPass(new OutputPass());

    loadFusionModel();

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    // --- MODIFICATION ICI : ROTATION DESACTIVEE ---
    controls.autoRotate = false;
    // ----------------------------------------------

    window.addEventListener('resize', onWindowResize);
    animate();
}

function onWindowResize() {
    const container = document.getElementById('canvas-container');
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
    composer.setSize(container.clientWidth, container.clientHeight);
}

function loadFusionModel() {
    const loader = new GLTFLoader();
    loader.load(MODEL_PATH, (gltf) => {
        const model = gltf.scene;
        const meshesToProcess = [];
        model.traverse((child) => { if (child.isMesh) meshesToProcess.push(child); });

        meshesToProcess.forEach((child) => {
            const name = child.name.toLowerCase();

            // --- MODIFICATION ICI : APPLICATION DES MATERIAUX ---
            if (name.includes('paume') || name.includes('palm')) {
                palmMesh = child;
                // La paume reçoit le matériau solide
                child.material = matSolidPalm;
            } else {
                // Les doigts reçoivent le matériau holographique
                child.material = matHoloFingers;
            }
            // ----------------------------------------------------

            // Ajout du wireframe pour tout le monde pour le style
            const wire = new THREE.Mesh(child.geometry, matWire);
            child.add(wire);

            const m = name.match(/(pouce|index|majeur|annulaire|auriculaire)_?(\d+)?/);
            if (m) {
                const fingerName = m[1];
                const order = m[2] ? parseInt(m[2]) : 0;
                fingers[fingerName].segments.push({ mesh: child, order });
            }
        });

        model.updateWorldMatrix(true, true);
        buildFingerHierarchy(model);

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
        document.getElementById('loading-msg').innerHTML = 'ERREUR: ' + e.message;
    });
}

function computeJointPosition(parentMesh, childMesh) {
    const parentBox = new THREE.Box3().setFromObject(parentMesh);
    const childBox = new THREE.Box3().setFromObject(childMesh);
    const parentCenter = parentBox.getCenter(new THREE.Vector3());
    const childCenter = childBox.getCenter(new THREE.Vector3());
    let dir = childCenter.clone().sub(parentCenter);
    dir.lengthSq() === 0 ? dir.set(0, 1, 0) : dir.normalize();
    const halfSize = parentBox.getSize(new THREE.Vector3()).multiplyScalar(0.5);
    const absDir = new THREE.Vector3(Math.abs(dir.x), Math.abs(dir.y), Math.abs(dir.z));
    let offset = new THREE.Vector3();
    if (absDir.y >= absDir.x && absDir.y >= absDir.z) offset.set(0, Math.sign(dir.y) * halfSize.y, 0);
    else if (absDir.x >= absDir.z) offset.set(Math.sign(dir.x) * halfSize.x, 0, 0);
    else offset.set(0, 0, Math.sign(dir.z) * halfSize.z);
    return parentCenter.add(offset);
}

function buildFingerHierarchy(model) {
    const baseCenters = {};
    for (const fName in fingers) {
        const baseSeg = fingers[fName].segments.find((s) => s.order === 1 || s.order === 0);
        if (baseSeg) baseCenters[fName] = new THREE.Box3().setFromObject(baseSeg.mesh).getCenter(new THREE.Vector3());
    }
    let palmNormal = new THREE.Vector3(0, 0, 1);
    const iC = baseCenters['index'], mC = baseCenters['majeur'], aC = baseCenters['annulaire'];
    if (iC && mC && aC) palmNormal = iC.clone().sub(mC).cross(aC.clone().sub(mC)).normalize();
    if (!Number.isFinite(palmNormal.x)) palmNormal.set(0, 0, 1);

    for (const fName in fingers) {
        const finger = fingers[fName];
        if (finger.segments.length === 0) continue;
        finger.segments.sort((a, b) => a.order - b.order);
        for (let i = 0; i < finger.segments.length; i++) {
            const segMesh = finger.segments[i].mesh;
            const parentMesh = i === 0 ? (palmMesh || segMesh) : finger.segments[i - 1].mesh;
            const jointPos = computeJointPosition(parentMesh, segMesh);
            const joint = new THREE.Object3D();
            joint.name = `${fName}_joint_${i + 1}`;
            joint.position.copy(jointPos);
            model.add(joint);
            joint.attach(segMesh);
            if (i > 0) finger.joints[i - 1].attach(joint);

            const parentCenter = new THREE.Box3().setFromObject(parentMesh).getCenter(new THREE.Vector3());
            const childCenter = new THREE.Box3().setFromObject(segMesh).getCenter(new THREE.Vector3());
            let dir = childCenter.clone().sub(parentCenter);
            dir.lengthSq() === 0 ? dir.set(0, 1, 0) : dir.normalize();
            let hingeWorld = palmNormal.clone().cross(dir).normalize();
            if (!Number.isFinite(hingeWorld.x)) hingeWorld.set(1, 0, 0);
            const tmp = joint.worldToLocal(joint.position.clone().add(hingeWorld));
            joint.userData.hingeAxis = tmp.sub(joint.position).normalize();
            joint.userData.baseQuat = joint.quaternion.clone();
            finger.joints.push(joint);
        }
    }
}

const _tmpQuat = new THREE.Quaternion();

function animate() {
    requestAnimationFrame(animate);

    const smooth = 0.15;
    for (const key in targetAngles) {
        currentAngles[key] += (targetAngles[key] - currentAngles[key]) * smooth;
    }

    ['index', 'majeur', 'annulaire', 'auriculaire'].forEach((name) => {
        const val = currentAngles[name];
        fingers[name].joints.forEach((joint, idx) => {
            const axis = joint.userData.hingeAxis;
            if (!axis) return;
            const factor = 1.0 - idx * 0.25;
            const angle = val * (-Math.PI / 2.2) * factor;
            joint.quaternion.copy(joint.userData.baseQuat);
            _tmpQuat.setFromAxisAngle(axis, angle);
            joint.quaternion.multiply(_tmpQuat);
        });
    });

    const tVal = currentAngles['pouce'];
    fingers['pouce'].joints.forEach((joint, idx) => {
        const axis = joint.userData.hingeAxis;
        if (!axis) return;
        const factor = 1.0 - idx * 0.2;
        const angle = tVal * (-Math.PI / 3.0) * factor;
        joint.quaternion.copy(joint.userData.baseQuat);
        _tmpQuat.setFromAxisAngle(axis, angle);
        joint.quaternion.multiply(_tmpQuat);
    });

    controls.update();
    if (composer) composer.render();
}

window.updateHandData = function (jsonStr) {
    try {
        const data = JSON.parse(jsonStr);
        if (data.index !== undefined) targetAngles.index = data.index;
        if (data.majeur !== undefined) targetAngles.majeur = data.majeur;
        if (data.annulaire_auriculaire !== undefined) {
            targetAngles.annulaire = data.annulaire_auriculaire;
            targetAngles.auriculaire = data.annulaire_auriculaire;
        }
        if (data.pouce_articulation !== undefined) targetAngles.pouce = data.pouce_articulation;
    } catch (e) {}
};

setTimeout(init, 100);
</script>
'''