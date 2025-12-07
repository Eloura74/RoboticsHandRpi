# --------------------------------------------------------------------
# CSS COMPONENTS - Styles des composants UI
# --------------------------------------------------------------------
"""
Ce module contient tous les styles CSS des composants d'interface :
- Boutons (cyber-btn, danger-btn, sim-btn, thumb-btn, emergency-btn)
- Cadre vidéo HUD (video-hud-frame, coins, scan-line)
- Panneaux HUD (hud-panel, hud-chip, hud-divider)
- Télémétrie (barres de progression des doigts)
- Terminal de logs
"""

CSS_COMPONENTS = '''
<style>
    /* ================================================================
       BOUTONS CYBER
       ================================================================ */
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

    /* ================================================================
       BOUTONS DANGER
       ================================================================ */
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

    /* ================================================================
       CADRE VIDÉO HUD (Style Terminator)
       ================================================================ */
    .video-hud-frame {
        position: absolute;
        inset: 0;
        pointer-events: none;
        z-index: 20;
        border: 1px solid rgba(0, 243, 255, 0.3);
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
        opacity: 0.7;
    }

    @keyframes scan { 0% {top:0;} 50% {opacity: 1;} 100% {top:100%; opacity: 0.7;} }

    /* ================================================================
       TÉLÉMÉTRIE - Barres de progression servos
       ================================================================ */
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
        background: repeating-linear-gradient(
            90deg,
            var(--neon-cyan),
            var(--neon-cyan) 4px,
            transparent 4px,
            transparent 6px
        );
        box-shadow: 0 0 10px var(--neon-cyan);
        transition: width 0.1s linear;
    }

    /* ================================================================
       TERMINAL DE LOGS
       ================================================================ */
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

    /* ================================================================
       PANNEAUX HUD
       ================================================================ */
    .hud-panel {
        background: var(--glass-panel);
        border: 1px solid rgba(0, 243, 255, 0.18);
        box-shadow:
            0 0 30px rgba(0, 0, 0, 0.9),
            0 0 18px rgba(0, 243, 255, 0.15),
            inset 0 0 20px rgba(0, 243, 255, 0.05);
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

    /* ================================================================
       BOUTONS DE CONTRÔLE (NiceGUI)
       ================================================================ */
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

    /* ================================================================
       BOUTON D'URGENCE
       ================================================================ */
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

    /* ================================================================
       ANIMATION LIGNE DE VIE (HEADER - SVG)
       ================================================================ */
    .lifeline-container {
        flex: 1;
        height: 50px;
        margin: 0 20px;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        opacity: 0.9;
    }

    .ecg-svg {
        width: 100%;
        height: 100%;
    }

    .ecg-path {
        fill: none;
        stroke: var(--neon-cyan);
        stroke-width: 2;
        stroke-linecap: round;
        stroke-linejoin: round;
        filter: drop-shadow(0 0 4px var(--neon-cyan));
        stroke-dasharray: 2000;
        stroke-dashoffset: 2000;
        animation: draw-ecg 6s linear infinite;
    }

    @keyframes draw-ecg {
        0% { stroke-dashoffset: 2000; opacity: 0; }
        5% { opacity: 1; }
        90% { opacity: 1; }
        100% { stroke-dashoffset: 0; opacity: 0; }
    }

    /* ================================================================
       LOGO & TITRE ENHANCEMENTS
       ================================================================ */
    .logo-glow {
        filter: drop-shadow(0 0 5px var(--neon-cyan));
        animation: logo-pulse 4s ease-in-out infinite;
    }

    @keyframes logo-pulse {
        0%, 100% { filter: drop-shadow(0 0 5px var(--neon-cyan)); }
        50% { filter: drop-shadow(0 0 12px var(--neon-cyan)); }
    }

    .title-glow {
        text-shadow: 0 0 10px rgba(0, 243, 255, 0.6);
        letter-spacing: 3px !important;
    }

    /* ================================================================
       CONTROL PANEL STYLES
       ================================================================ */
    .tech-panel-bg {
        background: 
            linear-gradient(135deg, rgba(0, 20, 30, 0.9) 0%, rgba(0, 10, 15, 0.95) 100%),
            repeating-linear-gradient(90deg, rgba(0, 243, 255, 0.03) 0px, rgba(0, 243, 255, 0.03) 1px, transparent 1px, transparent 20px),
            repeating-linear-gradient(0deg, rgba(0, 243, 255, 0.03) 0px, rgba(0, 243, 255, 0.03) 1px, transparent 1px, transparent 20px);
        border: 1px solid rgba(0, 243, 255, 0.2);
        box-shadow: inset 0 0 20px rgba(0, 243, 255, 0.05);
        position: relative;
    }
    
    .tech-panel-bg::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--neon-cyan), transparent);
        opacity: 0.5;
    }

    .cyber-btn-glitch {
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: bold;
        clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
    }

    .cyber-btn-glitch::after {
        content: '';
        position: absolute;
        top: -50%; left: -50%; width: 200%; height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        transform: rotate(45deg) translateY(-100%);
        transition: transform 0.5s;
    }

    .cyber-btn-glitch:hover::after {
        transform: rotate(45deg) translateY(100%);
    }

    .cyber-btn-open {
        background: rgba(0, 243, 255, 0.1) !important;
        border: 1px solid rgba(0, 243, 255, 0.5) !important;
        color: var(--neon-cyan) !important;
    }
    .cyber-btn-open:hover {
        background: rgba(0, 243, 255, 0.2) !important;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.4);
        text-shadow: 0 0 8px var(--neon-cyan);
    }

    .cyber-btn-close {
        background: rgba(255, 0, 60, 0.1) !important;
        border: 1px solid rgba(255, 0, 60, 0.5) !important;
        color: #ff003c !important;
    }
    .cyber-btn-close:hover {
        background: rgba(255, 0, 60, 0.2) !important;
        box-shadow: 0 0 15px rgba(255, 0, 60, 0.4);
        text-shadow: 0 0 8px #ff003c;
    }

    .cyber-btn-sim {
        background: rgba(138, 43, 226, 0.1) !important;
        border: 1px solid rgba(138, 43, 226, 0.5) !important;
        color: #8a2be2 !important;
    }
    .cyber-btn-sim:hover {
        background: rgba(138, 43, 226, 0.2) !important;
        box-shadow: 0 0 15px rgba(138, 43, 226, 0.4);
        text-shadow: 0 0 8px #8a2be2;
    }

    .thumb-actuator {
        background: rgba(0, 20, 30, 0.8);
        border: 1px solid rgba(0, 243, 255, 0.3);
        color: var(--neon-cyan);
        transition: all 0.2s;
    }
    .thumb-actuator:hover {
        background: rgba(0, 243, 255, 0.2);
        border-color: var(--neon-cyan);
    }

    .thumb-display {
        background: rgba(0, 0, 0, 0.6);
        border: 1px solid rgba(0, 243, 255, 0.1);
        color: var(--neon-cyan);
        font-family: 'Courier New', monospace;
        letter-spacing: 1px;
    }

    /* ================================================================
       3D PANEL & HUD STYLES
       ================================================================ */
    .panel-3d-bg {
        background-color: #000;
        background-image: 
            radial-gradient(circle at center, transparent 0%, #000 90%),
            linear-gradient(0deg, rgba(0, 243, 255, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 243, 255, 0.05) 1px, transparent 1px);
        background-size: 100% 100%, 40px 40px, 40px 40px;
        background-position: center, center, center;
        position: relative;
        box-shadow: inset 0 0 50px #000;
    }

    .hud-overlay {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        pointer-events: none; /* Let clicks pass through to 3D canvas */
        z-index: 10;
    }

    .hud-corner {
        position: absolute;
        width: 40px;
        height: 40px;
        border: 2px solid var(--neon-cyan);
        opacity: 0.6;
        transition: all 0.3s;
    }

    .hud-tl { top: 20px; left: 20px; border-right: none; border-bottom: none; }
    .hud-tr { top: 20px; right: 20px; border-left: none; border-bottom: none; }
    .hud-bl { bottom: 20px; left: 20px; border-right: none; border-top: none; }
    .hud-br { bottom: 20px; right: 20px; border-left: none; border-top: none; }

    .hud-crosshair {
        position: absolute;
        top: 50%; left: 50%;
        width: 200px; height: 200px;
        transform: translate(-50%, -50%);
        border: 1px solid rgba(0, 243, 255, 0.2);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .hud-crosshair::before {
        content: '';
        width: 180px; height: 180px;
        border: 1px dashed rgba(0, 243, 255, 0.3);
        border-radius: 50%;
        animation: spin-slow 20s linear infinite;
    }

    .hud-crosshair::after {
        content: '';
        width: 10px; height: 10px;
        background: var(--neon-cyan);
        border-radius: 50%;
        box-shadow: 0 0 10px var(--neon-cyan);
    }

    .hud-scan-line {
        position: absolute;
        top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--neon-cyan), transparent);
        opacity: 0.3;
        animation: scan-vertical 4s linear infinite;
    }

    @keyframes spin-slow {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    @keyframes scan-vertical {
        0% { top: 0%; opacity: 0; }
        10% { opacity: 0.5; }
        90% { opacity: 0.5; }
        100% { top: 100%; opacity: 0; }
    }
    /* ================================================================
       CONFIG PANEL STYLES
       ================================================================ */
    .config-card {
        background: rgba(0, 10, 15, 0.85);
        border: 1px solid rgba(0, 243, 255, 0.2);
        box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.8);
        position: relative;
        overflow: hidden;
    }

    .config-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 10px; height: 10px;
        border-top: 2px solid var(--neon-cyan);
        border-left: 2px solid var(--neon-cyan);
    }

    .config-card::after {
        content: '';
        position: absolute;
        bottom: 0; right: 0;
        width: 10px; height: 10px;
        border-bottom: 2px solid var(--neon-cyan);
        border-right: 2px solid var(--neon-cyan);
    }

    .config-input .q-field__control {
        background: rgba(0, 243, 255, 0.05) !important;
        border-bottom: 1px solid rgba(0, 243, 255, 0.3) !important;
        border-radius: 4px 4px 0 0 !important;
    }

    .config-input .q-field__control:before {
        border-bottom: 1px solid rgba(0, 243, 255, 0.5) !important;
    }

    .config-input .q-field__control:after {
        background: var(--neon-cyan) !important;
        height: 1px !important;
    }

    .config-input .q-field__label {
        color: rgba(0, 243, 255, 0.7) !important;
        font-family: 'Orbitron', sans-serif;
        font-size: 10px;
        letter-spacing: 1px;
    }

    .config-input .q-field__native {
        color: var(--neon-cyan) !important;
        font-family: 'Share Tech Mono', monospace;
        font-weight: bold;
    }
</style>
'''
