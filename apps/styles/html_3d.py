# --------------------------------------------------------------------
# HTML 3D - Structure HTML de la visualisation 3D
# --------------------------------------------------------------------
"""
Ce module contient la structure HTML de la visualisation 3D de la main :
- Container principal avec anneaux HUD
- Message de chargement
- Titre NEURO-HAND
- Panneau de télémétrie (barres servos)
- Terminal de logs
"""

HAND_3D_STRUCTURE = r'''
<div id="canvas-container">
    <!-- Anneaux HUD décoratifs -->
    <div class="hud-ring" style="width: 400px; height: 400px; opacity: 0.1;"></div>
    <div class="hud-ring" style="width: 600px; height: 600px; opacity: 0.05;"></div>

    <!-- Message de chargement -->
    <div id="loading-msg">SYSTEM BOOT V9.0...</div>
   
    <!-- Titre NEURO-HAND en bas à gauche -->
    <div style="position:absolute; bottom:30px; left:40px; pointer-events:none; z-index:5;">
        <div style="font-family:'Rajdhani'; font-weight:700; color:#fff; font-size:32px; letter-spacing:2px; text-shadow:0 0 10px #00f3ff;">
            NEURO-HAND <span style="color:#00f3ff; font-size:16px;">V9.0</span>
        </div>
        <div style="font-family:'Orbitron'; color:rgba(0, 243, 255, 0.6); font-size:10px; letter-spacing: 1px;">
            SOLID-CORE HOLOGRAPHIC // LIVE FEED
        </div>
    </div>

    <!-- Panneau de télémétrie (barres de progression servos) -->
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

    <!-- Terminal de logs -->
    <div id="terminal-panel">
        <div id="terminal-header">SYSTEM LOGS // STREAM</div>
        <div id="terminal-content">
            <div class="log-line log-sys">[INIT] System ready.</div>
            <div class="log-line log-sys">[NET] Waiting for connection...</div>
        </div>
    </div>

</div>
'''
