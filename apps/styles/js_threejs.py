# --------------------------------------------------------------------
# JAVASCRIPT THREE.JS - Code de visualisation 3D
# --------------------------------------------------------------------
"""
Ce module contient tout le code JavaScript pour la visualisation 3D avec Three.js :
- Import des modules Three.js (via CDN)
- Configuration de la scène, caméra, renderer
- Chargement du modèle 3D GLB
- Matériaux holographiques (doigts transparents, paume sombre)
- Hiérarchie des doigts avec articulations
- Animation et mise à jour en temps réel
- API JavaScript appelée depuis Python
- Barres de télémétrie
- Terminal de logs
"""

# Note : Ce fichier contient du code JavaScript brut.
# Il sera injecté dans la page HTML via NiceGUI.

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

// =====================================================================
// CONSTANTES
// =====================================================================
const MODEL_PATH = '/assets/main_fusion.glb';
const PALETTE = {
    cyanBright: 0x00ffff,
    cyanDeep:   0x004488,
    magenta:    0xff0088,
    bgDark:     0x020408,
};

// =====================================================================
// VARIABLES GLOBALES
// =====================================================================
let camera, scene, renderer, controls, composer;
let particles;

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

// =====================================================================
// MATÉRIAUX
// =====================================================================
// Doigts : holographiques, transparents, très "néon"
const matHoloFingers = new THREE.MeshPhysicalMaterial({
    color: 0x000000,
    emissive: PALETTE.cyanDeep,
    emissiveIntensity: 0.6,
    metalness: 0.85,
    roughness: 0.1,
    transmission: 0.7,
    opacity: 0.45,
    transparent: true,
    side: THREE.DoubleSide,
    depthWrite: false,
});

// Paume : bloc sombre, peu lumineux
const matSolidPalm = new THREE.MeshPhysicalMaterial({
    color: 0x001018,
    emissive: 0x001822,
    emissiveIntensity: 0.08,
    metalness: 0.4,
    roughness: 0.8,
    transmission: 0.0,
    opacity: 0.9,
    transparent: true,
    side: THREE.DoubleSide,
    depthWrite: true,
});

// Wireframe des doigts : bien visible
const matWire = new THREE.MeshBasicMaterial({
    color: PALETTE.cyanBright,
    wireframe: true,
    transparent: true,
    opacity: 0.7,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
});

// Wireframe de la paume : discret
const matWirePalm = new THREE.MeshBasicMaterial({
    color: 0x006688,
    wireframe: true,
    transparent: true,
    opacity: 0.18,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
});

// =====================================================================
// INITIALISATION
// =====================================================================
function init() {
    const container = document.getElementById('canvas-container');
    if (!container) { setTimeout(init, 100); return; }

    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000000, 0.02);

    camera = new THREE.PerspectiveCamera(
        45,
        container.clientWidth / container.clientHeight,
        0.1,
        1000,
    );
    camera.position.set(0, 5, 45);

    renderer = new THREE.WebGLRenderer({
        antialias: false,
        alpha: true,
        powerPreference: 'high-performance',
    });
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
    composer.addPass(
        new UnrealBloomPass(
            new THREE.Vector2(container.clientWidth, container.clientHeight),
            0.2,
            0.3,
            0.2,
        ),
    );
    composer.addPass(new OutputPass());

    loadFusionModel();
    createParticles();

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.autoRotate = false;

    window.addEventListener('resize', onWindowResize);

    animate();
}

function onWindowResize() {
    const container = document.getElementById('canvas-container');
    if (!container) return;

    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();

    renderer.setSize(container.clientWidth, container.clientHeight);
    composer.setSize(container.clientWidth, container.clientHeight);
}

// =====================================================================
// CHARGEMENT DU MODÈLE 3D
// =====================================================================
function loadFusionModel() {
    const loader = new GLTFLoader();

    loader.load(
        MODEL_PATH,
        (gltf) => {
            const model = gltf.scene;

            const meshesToProcess = [];
            model.traverse((child) => {
                if (child.isMesh) meshesToProcess.push(child);
            });

            meshesToProcess.forEach((child) => {
                const name = child.name.toLowerCase();

                if (name.includes('paume') || name.includes('palm')) {
                    palmMesh = child;
                    child.material = matSolidPalm;

                    const wirePalm = new THREE.Mesh(child.geometry, matWirePalm);
                    child.add(wirePalm);
                } else {
                    child.material = matHoloFingers;

                    const wire = new THREE.Mesh(child.geometry, matWire);
                    child.add(wire);
                }

                const m = name.match(
                    /(pouce|index|majeur|annulaire|auriculaire)_?(\d+)?/,
                );
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
            const maxDim = Math.max(size.x, size.y, size.z);

            model.position.sub(center);
            model.scale.setScalar(15.0 / maxDim);
            model.rotation.x = -Math.PI / 2;

            scene.add(model);

            const loading = document.getElementById('loading-msg');
            if (loading) loading.style.display = 'none';
        },
        undefined,
        (e) => {
            console.error(e);
            const loading = document.getElementById('loading-msg');
            if (loading) loading.innerHTML = 'ERREUR: ' + e.message;
        },
    );
}

// =====================================================================
// HIÉRARCHIE DES DOIGTS
// =====================================================================
function computeJointPosition(parentMesh, childMesh) {
    const parentBox = new THREE.Box3().setFromObject(parentMesh);
    const childBox = new THREE.Box3().setFromObject(childMesh);

    const parentCenter = parentBox.getCenter(new THREE.Vector3());
    const childCenter = childBox.getCenter(new THREE.Vector3());

    let dir = childCenter.clone().sub(parentCenter);
    if (dir.lengthSq() === 0) dir.set(0, 1, 0);
    else dir.normalize();

    const halfSize = parentBox.getSize(new THREE.Vector3()).multiplyScalar(0.5);
    const absDir = new THREE.Vector3(
        Math.abs(dir.x),
        Math.abs(dir.y),
        Math.abs(dir.z),
    );

    let offset = new THREE.Vector3();
    if (absDir.y >= absDir.x && absDir.y >= absDir.z) {
        offset.set(0, Math.sign(dir.y) * halfSize.y, 0);
    } else if (absDir.x >= absDir.z) {
        offset.set(Math.sign(dir.x) * halfSize.x, 0, 0);
    } else {
        offset.set(0, 0, Math.sign(dir.z) * halfSize.z);
    }

    return parentCenter.add(offset);
}

function buildFingerHierarchy(model) {
    const baseCenters = {};

    for (const fName in fingers) {
        const baseSeg = fingers[fName].segments.find(
            (s) => s.order === 1 || s.order === 0,
        );
        if (baseSeg) {
            const box = new THREE.Box3().setFromObject(baseSeg.mesh);
            baseCenters[fName] = box.getCenter(new THREE.Vector3());
        }
    }

    let palmNormal = new THREE.Vector3(0, 0, 1);
    const iC = baseCenters['index'];
    const mC = baseCenters['majeur'];
    const aC = baseCenters['annulaire'];

    if (iC && mC && aC) {
        const v1 = iC.clone().sub(mC);
        const v2 = aC.clone().sub(mC);
        palmNormal = v1.cross(v2).normalize();
    }
    if (!Number.isFinite(palmNormal.x)) palmNormal.set(0, 0, 1);

    for (const fName in fingers) {
        const finger = fingers[fName];
        if (finger.segments.length === 0) continue;

        finger.segments.sort((a, b) => a.order - b.order);

        for (let i = 0; i < finger.segments.length; i++) {
            const segMesh = finger.segments[i].mesh;
            const parentMesh =
                i === 0 ? (palmMesh || segMesh) : finger.segments[i - 1].mesh;

            const joint = new THREE.Object3D();
            joint.name = `${fName}_joint_${i + 1}`;
            joint.position.copy(computeJointPosition(parentMesh, segMesh));

            model.add(joint);
            joint.attach(segMesh);

            if (i > 0) {
                finger.joints[i - 1].attach(joint);
            }

            const parentCenter = new THREE.Box3()
                .setFromObject(parentMesh)
                .getCenter(new THREE.Vector3());
            const childCenter = new THREE.Box3()
                .setFromObject(segMesh)
                .getCenter(new THREE.Vector3());

            let dir = childCenter.clone().sub(parentCenter);
            if (dir.lengthSq() === 0) dir.set(0, 1, 0);
            else dir.normalize();

            let hingeWorld = palmNormal.clone().cross(dir).normalize();
            if (
                !Number.isFinite(hingeWorld.x) ||
                !Number.isFinite(hingeWorld.y) ||
                !Number.isFinite(hingeWorld.z)
            ) {
                hingeWorld.set(1, 0, 0);
            }

            const tmp = joint.worldToLocal(
                joint.position.clone().add(hingeWorld),
            );
            const hingeLocal = tmp.sub(joint.position).normalize();

            joint.userData.hingeAxis = hingeLocal;
            joint.userData.baseQuat = joint.quaternion.clone();

            finger.joints.push(joint);
        }
    }
}

function createParticles() {
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    for (let i = 0; i < 2000; i++) {
        vertices.push(
            (Math.random() - 0.5) * 100,
            (Math.random() - 0.5) * 100,
            (Math.random() - 0.5) * 100
        );
    }
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    const material = new THREE.PointsMaterial({ color: PALETTE.cyanDeep, size: 0.1, transparent: true, opacity: 0.6 });
    particles = new THREE.Points(geometry, material);
    scene.add(particles);
}



// =====================================================================
// ANIMATION
// =====================================================================
const _tmpQuat = new THREE.Quaternion();

function animate() {
    requestAnimationFrame(animate);

    const smooth = 0.15;
    for (const key in targetAngles) {
        currentAngles[key] += (targetAngles[key] - currentAngles[key]) * smooth;
    }

    ['index', 'majeur', 'annulaire', 'auriculaire'].forEach((name) => {
        const val = currentAngles[name];
        const finger = fingers[name];

        finger.joints.forEach((joint, idx) => {
            const axis = joint.userData.hingeAxis;
            if (!axis) return;

            const maxAngle = -Math.PI / 2.2;
            const factor = 1.0 - idx * 0.25;

            const angle = val * maxAngle * factor;

            joint.quaternion.copy(joint.userData.baseQuat);
            _tmpQuat.setFromAxisAngle(axis, angle);
            joint.quaternion.multiply(_tmpQuat);
        });
    });

    const tVal = currentAngles['pouce'];
    fingers['pouce'].joints.forEach((joint, idx) => {
        const axis = joint.userData.hingeAxis;
        if (!axis) return;

        const maxAngle = -Math.PI / 3.0;
        const factor = 1.0 - idx * 0.2;

        const angle = tVal * maxAngle * factor;

        joint.quaternion.copy(joint.userData.baseQuat);
        _tmpQuat.setFromAxisAngle(axis, angle);
        joint.quaternion.multiply(_tmpQuat);
    });

    if (particles) {
        particles.rotation.y += 0.001;
        particles.rotation.x += 0.0005;
    }



    if (matHoloFingers) {
        matHoloFingers.emissiveIntensity = 0.6 + Math.sin(Date.now() * 0.003) * 0.2;
    }

    controls.update();
    if (composer) composer.render();
}

// =====================================================================
// API JS APPELÉE PAR PYTHON
// =====================================================================
window.updateHandData = function (jsonStr) {
    try {
        const data = JSON.parse(jsonStr);

        if (data.index !== undefined) targetAngles.index = data.index;
        if (data.majeur !== undefined) targetAngles.majeur = data.majeur;
        if (data.annulaire_auriculaire !== undefined) {
            targetAngles.annulaire = data.annulaire_auriculaire;
            targetAngles.auriculaire = data.annulaire_auriculaire;
        }
        if (data.pouce_articulation !== undefined) {
            targetAngles.pouce = data.pouce_articulation;
        }

        updateBar('pouce',       targetAngles.pouce);
        updateBar('index',       targetAngles.index);
        updateBar('majeur',      targetAngles.majeur);
        updateBar('annulaire',   targetAngles.annulaire);
        updateBar('auriculaire', targetAngles.auriculaire);
    } catch (e) {
        console.error('updateHandData ERROR:', e, jsonStr);
    }
};

function updateBar(id, val) {
    const pct = Math.min(Math.max(val * 100, 0), 100);
    const bar = document.getElementById('bar-' + id);
    const txt = document.getElementById('txt-' + id);
    if (bar) bar.style.width = pct + '%';
    if (txt) txt.innerText = Math.round(pct) + '%';
}

// =====================================================================
// LOG TERMINAL
// =====================================================================
window.addSystemLog = function (msg, type = 'sys') {
    const term = document.getElementById('terminal-content');
    if (!term) return;

    const div = document.createElement('div');
    div.className = 'log-line log-' + type;

    const now = new Date();
    const time =
        now.getHours().toString().padStart(2, '0') +
        ':' +
        now.getMinutes().toString().padStart(2, '0') +
        ':' +
        now.getSeconds().toString().padStart(2, '0');

    div.innerText = '[' + time + '] ' + msg;
    term.appendChild(div);

    if (term.childNodes.length > 8) {
        term.removeChild(term.firstChild);
    }
};

setTimeout(init, 100);

</script>
'''
