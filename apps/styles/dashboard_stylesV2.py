# apps/styles/dashboard_stylesV2.py

"""

Module visuel - Style: FUSION NEON V9.0 (HUD Complexe)

- Télémétrie (Jauges servos)

- Terminal de Logs

- Habillage Vidéo Sci-Fi

- Fond Grille Tactique

"""



CSS_STYLE = '''



<style>

    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');



    :root {

        --neon-cyan: #00f3ff;

        --neon-blue: #0066ff;

        --neon-red: #ff3333;

        --bg-dark: #010205;

        --glass-panel: rgba(0, 10, 20, 0.85);

    }



    body {

        background-color: var(--bg-dark);

        color: var(--neon-cyan);

        font-family: 'Rajdhani', sans-serif;

        overflow: hidden;

        margin: 0;

    }



    /* --- FOND TACTIQUE (GRILLE + VIGNETTE) --- */

    #canvas-container {

        width: 100%;

        height: 100%;

        position: relative;

        background-color: #000;

        background-image:

            linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),

            linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px),

            radial-gradient(circle at 50% 50%, rgba(0, 40, 80, 0.2) 0%, rgba(0,0,0,1) 90%);

        background-size: 40px 40px, 40px 40px, 100% 100%;

    }



    /* Cercles concentriques HUD (décoration) */

    .hud-ring {

        position: absolute;

        top: 50%; left: 50%;

        transform: translate(-50%, -50%);

        border: 1px solid rgba(0, 243, 255, 0.05);

        border-radius: 50%;

        pointer-events: none;

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

        text-shadow: 0 0 10px var(--neon-cyan);

        z-index: 20;

    }



    /* --- BOUTONS --- */

    .cyber-btn {

        background: linear-gradient(90deg, transparent 0%, rgba(0, 243, 255, 0.1) 50%, transparent 100%);

        border: 1px solid rgba(0, 243, 255, 0.4);

        color: var(--neon-cyan);

        font-family: 'Orbitron';

        font-size: 12px;

        letter-spacing: 1px;

        text-transform: uppercase;

        transition: all 0.3s;

        position: relative;

        overflow: hidden;

    }

    .cyber-btn::before {

        content: '';

        position: absolute;

        top: 0; left: -100%;

        width: 100%; height: 100%;

        background: linear-gradient(90deg, transparent, rgba(0,243,255,0.4), transparent);

        transition: 0.5s;

    }

    .cyber-btn:hover::before { left: 100%; }

    .cyber-btn:hover {

        border-color: var(--neon-cyan);

        background: rgba(0, 243, 255, 0.2);

        box-shadow: 0 0 15px rgba(0, 243, 255, 0.2);

    }



    .danger-btn {

        background: rgba(40, 0, 0, 0.5);

        border: 1px solid var(--neon-red);

        color: var(--neon-red);

        font-family: 'Orbitron';

        box-shadow: inset 0 0 10px rgba(255,0,0,0.1);

    }

    .danger-btn:hover {

        background: rgba(100, 0, 0, 0.6);

        box-shadow: 0 0 20px rgba(255, 0, 0, 0.4);

    }



    /* --- VIDEO HUD STYLING (Cadre Terminator) --- */

    .video-hud-frame {

        position: absolute;

        inset: 0;

        pointer-events: none;

        z-index: 20;

        border: 1px solid rgba(0, 243, 255, 0.3);

        /* Coins coupés via clip-path */

        clip-path: polygon(

            10px 0, 100% 0,

            100% calc(100% - 10px), calc(100% - 10px) 100%,

            0 100%, 0 10px

        );

    }

    .video-hud-corner {

        position: absolute;

        width: 20px; height: 20px;

        border: 2px solid var(--neon-cyan);

        opacity: 0.8;

    }

    .vh-tl { top: 0; left: 0; border-right: none; border-bottom: none; }

    .vh-tr { top: 0; right: 0; border-left: none; border-bottom: none; }

    .vh-bl { bottom: 0; left: 0; border-right: none; border-top: none; }

    .vh-br { bottom: 0; right: 0; border-left: none; border-top: none; }



    .scan-line {

        position: absolute;

        width: 100%; height: 2px;

        background: rgba(0, 243, 255, 0.3);

        top: 0;

        animation: scan 4s linear infinite;

        opacity: 0.5;

    }

    @keyframes scan { 0% {top:0;} 100% {top:100%;} }





    /* --- TELEMETRIE (BARRES DROITE) --- */

    #telemetry-panel {

        position: absolute;

        top: 20%;

        right: 40px;

        width: 220px;

        display: flex;

        flex-direction: column;

        gap: 20px;

        z-index: 5;

        background: rgba(0,0,0,0.3);

        padding: 20px;

        border-left: 2px solid rgba(0,243,255,0.2);

        backdrop-filter: blur(2px);

    }



    .telemetry-title {

        font-family: 'Orbitron';

        color: rgba(255,255,255,0.7);

        font-size: 10px;

        letter-spacing: 2px;

        border-bottom: 1px solid rgba(0,243,255,0.2);

        padding-bottom: 5px;

        margin-bottom: 5px;

    }



    .finger-meter {

        display: flex;

        flex-direction: column;

        gap: 5px;

    }



    .finger-info {

        display: flex;

        justify-content: space-between;

        font-family: 'Rajdhani';

        font-size: 14px;

        color: var(--neon-cyan);

    }



    .bar-track {

        width: 100%;

        height: 6px;

        background: rgba(255, 255, 255, 0.1);

        border: 1px solid rgba(0, 243, 255, 0.3);

        transform: skewX(-20deg);

        overflow: hidden;

    }



    .bar-fill {

        height: 100%;

        width: 0%;

        background: linear-gradient(90deg, transparent, var(--neon-cyan));

        box-shadow: 0 0 10px var(--neon-cyan);

        transition: width 0.1s linear;

    }





    /* --- TERMINAL LOGS (BAS DROITE) --- */

    #terminal-panel {

        position: absolute;

        bottom: 30px;

        right: 40px;

        width: 350px;

        height: 150px;

        background: rgba(0, 5, 10, 0.8);

        border: 1px solid rgba(0, 243, 255, 0.3);

        font-family: 'Courier New', monospace;

        font-size: 11px;

        padding: 10px;

        overflow-y: hidden;

        display: flex;

        flex-direction: column;

        justify-content: flex-end;

        z-index: 5;

    }

   

    #terminal-header {

        position: absolute;

        top: 0; left: 0; width: 100%;

        background: rgba(0, 243, 255, 0.1);

        color: var(--neon-cyan);

        font-size: 9px;

        padding: 2px 5px;

        font-family: 'Orbitron';

        letter-spacing: 1px;

    }



    .log-line { margin: 2px 0; opacity: 0.8; }

    .log-sys { color: #aaa; }

    .log-servo { color: var(--neon-cyan); }

    .log-warn { color: var(--neon-red); text-shadow: 0 0 2px red; }


    .hud-panel {

        background: var(--glass-panel);

        border: 1px solid rgba(0, 243, 255, 0.18);

        box-shadow:

            0 0 30px rgba(0, 0, 0, 0.9),

            0 0 18px rgba(0, 243, 255, 0.05);

        border-radius: 10px;

        backdrop-filter: blur(8px);

    }



    .hud-panel-header {

        display: flex;

        align-items: center;

        justify-content: space-between;

        gap: 8px;

        margin-bottom: 8px;

    }



    .hud-section-title {

        font-family: 'Orbitron', sans-serif;

        font-size: 11px;

        letter-spacing: 2px;

        text-transform: uppercase;

        color: var(--neon-cyan);

    }



    .hud-section-caption {

        font-size: 10px;

        color: rgba(255, 255, 255, 0.5);

        letter-spacing: 1px;

        text-transform: uppercase;

    }



    .hud-chip {

        font-family: 'Orbitron', sans-serif;

        font-size: 9px;

        letter-spacing: 1px;

        text-transform: uppercase;

        padding: 2px 10px;

        border-radius: 9999px;

        border: 1px solid rgba(0, 243, 255, 0.45);

        background: radial-gradient(circle at 0% 0%, rgba(0,243,255,0.35), rgba(0,0,0,0.9));

        color: var(--neon-cyan);

        white-space: nowrap;

    }



    .hud-chip-warn {

        border-color: var(--neon-red);

        color: var(--neon-red);

        background: radial-gradient(circle at 0% 0%, rgba(255,51,51,0.3), rgba(0,0,0,0.9));

    }



    .hud-mini-label {

        font-size: 9px;

        text-transform: uppercase;

        letter-spacing: 1px;

        color: rgba(200, 230, 255, 0.6);

    }



    .hud-value-strong {

        font-family: 'Orbitron', sans-serif;

        font-size: 10px;

        letter-spacing: 1px;

        color: var(--neon-cyan);

    }



    .hud-divider {

        height: 1px;

        width: 100%;

        background: linear-gradient(

            90deg,

            transparent,

            rgba(0,243,255,0.7),

            transparent

        );

        opacity: 0.5;

        margin: 8px 0 6px 0;

    }

    .control-btn {

        border-radius: 10px !important;

        border: 1px solid rgba(0, 243, 255, 0.55) !important;

        background: radial-gradient(circle at 0% 0%, rgba(0,243,255,0.18), rgba(0,0,0,0.95)) !important;

        box-shadow:

            0 0 10px rgba(0, 243, 255, 0.25),

            inset 0 0 10px rgba(0, 243, 255, 0.2);

        text-align: left;

    }



    .control-btn .q-btn__content {

        justify-content: space-between;

        width: 100%;

        font-family: 'Orbitron', sans-serif;

        letter-spacing: 1px;

        text-transform: uppercase;

        font-size: 11px;

        color: var(--neon-cyan);

    }



    .control-btn .q-icon {

        font-size: 18px;

        opacity: 0.85;

    }



    .control-btn::after {

        content: '';

        position: absolute;

        right: 8px;

        top: 50%;

        width: 36px;

        height: 1px;

        transform: translateY(-50%);

        background: linear-gradient(90deg, rgba(0,243,255,0.0), rgba(0,243,255,0.8));

        opacity: 0.7;

        pointer-events: none;

    }



    .control-btn:hover {

        box-shadow:

            0 0 16px rgba(0,243,255,0.6),

            inset 0 0 12px rgba(0,243,255,0.25);

        border-color: rgba(0, 243, 255, 0.9);

    }



    .sim-btn {

        border-radius: 10px !important;

        border: 1px dashed rgba(0, 243, 255, 0.6) !important;

        background: radial-gradient(circle at 0% 0%, rgba(0,243,255,0.10), rgba(0,0,0,0.95)) !important;

        font-family: 'Orbitron', sans-serif;

        font-size: 11px;

        letter-spacing: 1px;

        text-transform: uppercase;

    }

    .sim-btn .q-btn__content {

        justify-content: center;

        color: var(--neon-cyan);

    }


    .thumb-btn {

        border-radius: 9999px !important;

        font-size: 10px;

        text-transform: uppercase;

        letter-spacing: 1px;

    }



    .emergency-wrapper {

        margin-top: auto;

        display: flex;

        justify-content: center;

        align-items: center;

        padding-top: 4px;

    }



    .emergency-ring {

        position: relative;

        width: 130px;

        height: 130px;

        border-radius: 50%;

        border: 2px solid rgba(255, 120, 40, 0.45);

        box-shadow:

            0 0 25px rgba(255, 120, 40, 0.8),

            0 0 60px rgba(255, 80, 0, 0.5);

        display: flex;

        align-items: center;

        justify-content: center;

        background: radial-gradient(circle, rgba(255,140,40,0.1), rgba(0,0,0,0.95));

    }



    .emergency-ring::before {

        content: '';

        position: absolute;

        inset: 12px;

        border-radius: 50%;

        border: 1px dashed rgba(255, 200, 150, 0.5);

        opacity: 0.6;

    }



    .emergency-btn {

        border-radius: 9999px !important;

        width: 90px;

        height: 90px;

        font-family: 'Orbitron', sans-serif;

        font-size: 10px;

        letter-spacing: 1px;

        text-transform: uppercase;

        background: radial-gradient(circle, #ff6600, #7a0000) !important;

        border: 2px solid rgba(255,230,200,0.9) !important;

        color: #fff !important;

        box-shadow:

            0 0 25px rgba(255, 140, 40, 0.9),

            inset 0 0 20px rgba(0,0,0,0.7);

    }

    .emergency-btn .q-btn__content {

        flex-direction: column;

    }

    .emergency-btn:hover {

        transform: scale(1.03);

        box-shadow:

            0 0 35px rgba(255, 180, 80, 1),

            inset 0 0 20px rgba(0,0,0,0.8);

    }


</style>

'''



HAND_3D_STRUCTURE = r'''

<div id="canvas-container">

    <div class="hud-ring" style="width: 400px; height: 400px; opacity: 0.1;"></div>

    <div class="hud-ring" style="width: 600px; height: 600px; opacity: 0.05;"></div>



    <div id="loading-msg">SYSTEM BOOT V9.0...</div>

   

    <div style="position:absolute; bottom:30px; left:40px; pointer-events:none; z-index:5;">

        <div style="font-family:'Rajdhani'; font-weight:700; color:#fff; font-size:32px; letter-spacing:2px; text-shadow:0 0 10px #00f3ff;">

            NEURO-HAND <span style="color:#00f3ff; font-size:16px;">V9.0</span>

        </div>

        <div style="font-family:'Orbitron'; color:rgba(0, 243, 255, 0.6); font-size:10px; letter-spacing: 1px;">

            SOLID-CORE HOLOGRAPHIC // LIVE FEED

        </div>

    </div>



    <div id="telemetry-panel">

        <div class="telemetry-title">SERVO TELEMETRY</div>

       

        <div class="finger-meter">

            <div class="finger-info"><span>POUCE</span><span id="txt-pouce">0%</span></div>

            <div class="bar-track"><div id="bar-pouce" class="bar-fill"></div></div>

        </div>

        <div class="finger-meter">

            <div class="finger-info"><span>INDEX</span><span id="txt-index">0%</span></div>

            <div class="bar-track"><div id="bar-index" class="bar-fill"></div></div>

        </div>

        <div class="finger-meter">

            <div class="finger-info"><span>MAJEUR</span><span id="txt-majeur">0%</span></div>

            <div class="bar-track"><div id="bar-majeur" class="bar-fill"></div></div>

        </div>

        <div class="finger-meter">

            <div class="finger-info"><span>ANNUL.</span><span id="txt-annulaire">0%</span></div>

            <div class="bar-track"><div id="bar-annulaire" class="bar-fill"></div></div>

        </div>

        <div class="finger-meter">

            <div class="finger-info"><span>AURIC.</span><span id="txt-auriculaire">0%</span></div>

            <div class="bar-track"><div id="bar-auriculaire" class="bar-fill"></div></div>

        </div>

    </div>



    <div id="terminal-panel">

        <div id="terminal-header">SYSTEM LOGS // STREAM</div>

        <div id="terminal-content">

            <div class="log-line log-sys">[INIT] System ready.</div>

            <div class="log-line log-sys">[NET] Waiting for connection...</div>

        </div>

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

    cyanDeep:   0x004488,

    magenta:    0xff0088,

    bgDark:     0x020408,

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





// ---------------------------------------------------------------------

// MATERIAUX : doigts très lumineux, paume sombre et en retrait

// ---------------------------------------------------------------------



// Doigts : holographiques, transparents, très “néon”

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

    color: 0x001018,          // bleu-vert très foncé

    emissive: 0x001822,

    emissiveIntensity: 0.08,  // presque pas de glow

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





// ---------------------------------------------------------------------

// INIT

// ---------------------------------------------------------------------

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





// ---------------------------------------------------------------------

// CHARGEMENT DU MODELE

// ---------------------------------------------------------------------

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

                    // Paume sombre + wire discret

                    palmMesh = child;

                    child.material = matSolidPalm;



                    const wirePalm = new THREE.Mesh(child.geometry, matWirePalm);

                    child.add(wirePalm);

                } else {

                    // Doigts : matériau holographique + wireframe lumineux

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



            // centrage & scale

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





// ---------------------------------------------------------------------

// GEOMETRIE / HIÉRARCHIE

// ---------------------------------------------------------------------

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





// ---------------------------------------------------------------------

// ANIMATION

// ---------------------------------------------------------------------

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



    controls.update();

    if (composer) composer.render();

}





// ---------------------------------------------------------------------

// API JS APPELÉE PAR PYTHON

// ---------------------------------------------------------------------

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





// ---------------------------------------------------------------------

// LOG TERMINAL

// ---------------------------------------------------------------------

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