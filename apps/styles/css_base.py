# --------------------------------------------------------------------
# CSS BASE - Variables, Body, Fond Tactique
# --------------------------------------------------------------------
"""
Ce module contient les styles CSS de base :
- Import des polices (Orbitron, Rajdhani)
- Variables CSS (couleurs néon)
- Style du body
- Fond tactique avec grille
- Cercles HUD décoratifs
- Message de chargement
"""

CSS_BASE = '''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');

    /* ================================================================
       VARIABLES CSS GLOBALES
       ================================================================ */
    :root {
        --neon-cyan: #00f3ff;
        --neon-blue: #0066ff;
        --neon-red: #ff3333;
        --bg-dark: #010205;
        --glass-panel: rgba(0, 10, 20, 0.85);
    }

    /* ================================================================
       BODY - Style de base
       ================================================================ */
    body {
        background-color: var(--bg-dark);
        color: var(--neon-cyan);
        font-family: 'Rajdhani', sans-serif;
        overflow: hidden;
        margin: 0;
    }

    /* ================================================================
       FOND TACTIQUE - Grille + Vignette radiale
       ================================================================ */
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

    /* ================================================================
       CERCLES HUD - Décoration concentrique
       ================================================================ */
    .hud-ring {
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        border: 1px solid rgba(0, 243, 255, 0.05);
        border-radius: 50%;
        pointer-events: none;
    }

    /* ================================================================
       MESSAGE DE CHARGEMENT
       ================================================================ */
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
</style>
'''
