"""
Module header pour le dashboard NEURO-HAND.
Construit le header avec logo, ECG animé, tabs de navigation et badge de statut.
"""

from nicegui import ui


def build_header():
    """
    Construit le header de l'interface (logo + titre + tabs par-dessus ECG + badge de statut).
    
    Returns:
        tuple: (status_label, tabs)
            - status_label: Le label de statut pour mise à jour ultérieure.
            - tabs: L'objet tabs pour la navigation.
    """
    with ui.header().classes('bg-transparent p-0 elevation-0'):
        # Container avec position relative pour permettre le positionnement absolu de l'ECG
        with ui.element('div').classes('relative w-full h-[8vh] min-h-[60px] overflow-hidden'):
            # ECG en arrière-plan absolu (couvre TOUT le conteneur)
            _build_ecg_background()
            
            # Contenu au premier plan (logo, tabs, badge) - une seule ligne
            with ui.row().classes(
                'hud-header w-full h-full '
                'items-center justify-between px-6 sm:px-8 relative'
            ).style('z-index: 10;'):
                # Partie Gauche : Logo + Titre
                _build_logo_title()

                # Partie Centrale : Tabs (flottent par-dessus l'ECG)
                with ui.tabs().classes('text-cyan-400 bg-transparent') as tabs:
                    ui.tab('DASHBOARD', icon='dashboard').classes('text-xs tracking-widest')
                    ui.tab('CONFIG', icon='settings').classes('text-xs tracking-widest')
                    ui.tab('TELEMETRY', icon='analytics').classes('text-xs tracking-widest')

                # Partie Droite : Badge de statut
                status_label = ui.label('INIT').classes(
                    'text-xs px-3 py-1 bg-red-900/40 text-red-400 '
                    'border border-red-500 rounded font-bold'
                )
    
    return status_label, tabs


def _build_ecg_background():
    """Construit l'animation ECG en arrière-plan."""
    ui.html('''
        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 0; pointer-events: none; display: flex; align-items: center; justify-content: stretch;">
            <svg class="ecg-svg" viewBox="0 0 1000 100" preserveAspectRatio="none" style="width: 100%; height: 50%; opacity: 0.4;">
                <path class="ecg-path" d="
                    M0,50 L100,50 
                    L110,50 L120,40 L130,60 L140,50 
                    L150,50 L160,50 L165,40 L170,50 L180,50 L185,20 L190,80 L195,50 L205,50 
                    L215,50 L220,40 L225,60 L235,50 
                    L300,50
                    L310,50 L320,40 L330,60 L340,50 
                    L350,50 L360,50 L365,40 L370,50 L380,50 L385,20 L390,80 L395,50 L405,50 
                    L415,50 L420,40 L425,60 L435,50 
                    L500,50
                    L510,50 L520,40 L530,60 L540,50 
                    L550,50 L560,50 L565,40 L570,50 L580,50 L585,20 L590,80 L595,50 L605,50 
                    L615,50 L620,40 L625,60 L635,50 
                    L700,50
                    L710,50 L720,40 L730,60 L740,50 
                    L750,50 L760,50 L765,40 L770,50 L780,50 L785,20 L790,80 L795,50 L805,50 
                    L815,50 L820,40 L825,60 L835,50 
                    L1000,50
                " />
            </svg>
        </div>
    ''', sanitize=False)


def _build_logo_title():
    """Construit le logo et le titre."""
    with ui.row().classes('items-center gap-4'):
        ui.html('''
            <svg class="logo-glow" width="32" height="32" viewBox="0 0 100 100" fill="none" stroke="#00f3ff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M50 20 L80 35 L80 65 L50 80 L20 65 L20 35 Z" />
                <circle cx="50" cy="50" r="12" fill="#00f3ff" fill-opacity="0.3" />
                <path d="M50 50 L50 20 M50 50 L80 65 M50 50 L20 65" stroke-width="4" opacity="0.8" />
            </svg>
        ''', sanitize=False)
        
        with ui.column().classes('gap-0'):
            ui.label('NEURO-HAND V2.0').classes('text-lg sm:text-xl text-cyan-400 font-black tracking-widest title-glow uppercase')
            ui.label('NEURO-LINK // SYSTEM ONLINE').classes('text-[10px] text-gray-400 tracking-wider')
