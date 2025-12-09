# --------------------------------------------------------------------
# PANNEAU DE GESTES PRÉDÉFINIS
# --------------------------------------------------------------------
"""
Interface UI pour les presets de gestes.

Affiche une grille de boutons pour exécuter rapidement des gestes
prédéfinis (peace, fist, ok, etc.).
"""

from nicegui import ui
from core.gesture_presets import GesturePresets


def build_gesture_panel(controller):
    """
    Construit un panneau compact avec les gestes prédéfinis.
    
    Peut être intégré dans le panneau gauche ou dans un onglet séparé.
    
    Args:
        controller: Instance de HandController.
    """
    # Initialiser le gestionnaire de presets
    presets = GesturePresets(controller)
    
    with ui.card().classes(
        'w-full panel-3d-bg px-4 py-3 flex flex-col gap-2 relative overflow-hidden'
    ).style('min-height: 140px;'):
        
        # HUD Overlay
        ui.html('''
            <div class="hud-overlay">
                <div class="hud-corner hud-tl"></div>
                <div class="hud-corner hud-tr"></div>
                <div class="hud-corner hud-bl"></div>
                <div class="hud-corner hud-br"></div>
            </div>
        ''')
        
        # Header avec marqueur visuel
        with ui.row().classes('items-center gap-1 z-20'):
            # Barre verticale cyan
            ui.html('<div style="width:3px; height:12px; background:linear-gradient(to bottom, #22d3ee, transparent); box-shadow:0 0 8px #22d3ee;"></div>')
            ui.label('QUICK GESTURES').classes(
                'hud-section-title text-[10px] tracking-[0.25em] uppercase'
            )
        
        # ================================================================
        # GRILLE DE BOUTONS - Gestes les plus courants (style cyberpunk)
        # ================================================================
        gestures_display = {
            'rest': {'label': 'REST', 'symbol': '◯'},
            'fist': {'label': 'FIST', 'symbol': '●'},
            'peace_sign': {'label': 'PEACE', 'symbol': '⎔'},
            'ok_sign': {'label': 'OK', 'symbol': '◎'},
            'thumbs_up': {'label': 'LIKE', 'symbol': '▲'},
            'pointing': {'label': 'POINT', 'symbol': '▶'},
        }
        
        with ui.grid(columns=3).classes('w-full gap-1 z-20 mt-2'):
            for gesture_name, display in gestures_display.items():
                # Callback d'exécution du geste
                def execute_gesture(name=gesture_name):
                    success = presets.execute(name, parallel=True)
                    if success:
                        ui.notify(
                            f"Executing: {name.replace('_', ' ').title()}",
                            type='positive',
                            position='top',
                            timeout=1000
                        )
                
                # Bouton minimaliste cyberpunk
                with ui.button(
                    on_click=execute_gesture
                ).props('flat dense').classes(
                    'h-11 flex flex-col items-center justify-center gap-[2px] '
                    'border border-cyan-700/40 hover:border-cyan-500/60 '
                    'bg-black/20 hover:bg-cyan-900/20 '
                    'transition-all duration-200'
                ):
                    ui.label(display['symbol']).classes('text-lg leading-none text-cyan-400 font-bold')
                    ui.label(display['label']).classes('text-[7px] leading-none tracking-[0.15em] opacity-60 text-cyan-300')
        
        # ================================================================
        # BOUTON SÉQUENCE DEMO (optionnel)
        # ================================================================
        ui.html('<div class="w-full h-[1px] bg-cyan-900/30 my-1 mt-2"></div>')
        
        def run_demo_sequence():
            """Exécute une séquence de démo avec tous les gestes."""
            ui.notify("Starting demo sequence...", type='info', position='top')
            # Séquence asynchrone pour ne pas bloquer l'UI
            import threading
            def demo():
                sequence = ['rest', 'fist', 'peace_sign', 'thumbs_up', 'rest']
                presets.create_sequence(sequence, delay=1.5)
                ui.notify("Demo sequence completed!", type='positive', position='top')
            
            threading.Thread(target=demo, daemon=True).start()
        
        ui.button(
            'RUN DEMO',
            icon='play_circle_outline',
            on_click=run_demo_sequence
        ).props('flat dense outline').classes(
            'w-full h-7 text-[9px] font-bold tracking-wider text-cyan-400 '
            'border-cyan-500/40 hover:border-cyan-400 z-20'
        )


def build_gesture_tab_panel(controller):
    """
    Construit un panneau complet de gestion des gestes pour un onglet dédié.
    
    Inclut :
    - Grille de tous les gestes
    - Prévisualisation des gestes
    - Création de gestes personnalisés
    - Gestion de séquences
    
    Args:
        controller: Instance de HandController.
    """
    presets = GesturePresets(controller)
    
    with ui.column().classes('w-full h-full p-6 gap-6 overflow-y-auto'):
        
        # ================================================================
        # SECTION 1 : Gestes prédéfinis
        # ================================================================
        ui.label('GESTURE LIBRARY').classes('hud-section-title text-xl')
        ui.label('Pre-configured hand poses for quick execution') \
            .classes('text-sm text-gray-400 -mt-4 mb-2')
        
        # Grille étendue avec TOUS les gestes
        with ui.grid(columns=4).classes('w-full gap-3'):
            for gesture_name in presets.list_gestures():
                gesture = presets.get_gesture_info(gesture_name)
                
                with ui.card().classes(
                    'config-card p-4 flex flex-col items-center gap-2 hover:scale-105 '
                    'transition-transform cursor-pointer'
                ):
                    # Icône/emoji (à personnaliser)
                    icons = {
                        'rest': '🖐️', 'fist': '✊', 'peace_sign': '✌️',
                        'ok_sign': '👌', 'thumbs_up': '👍', 'pointing': '👉',
                        'rock': '🤘'
                    }
                    icon = icons.get(gesture_name, '🤖')
                    
                    ui.label(icon).classes('text-4xl')
                    ui.label(gesture_name.replace('_', ' ').upper()) \
                        .classes('text-xs text-cyan-400 font-bold tracking-wider')
                    ui.label(gesture.description) \
                        .classes('text-[10px] text-gray-500 text-center')
                    
                    # Bouton d'exécution
                    ui.button(
                        'EXECUTE',
                        on_click=lambda g=gesture_name: presets.execute(g)
                    ).props('flat outline size=sm').classes(
                        'w-full text-[10px] border-cyan-500/40 text-cyan-400'
                    )
        
        # ================================================================
        # SECTION 2 : Créateur de séquence
        # ================================================================
        ui.html('<div class="w-full h-[2px] bg-cyan-900/30 my-4"></div>')
        
        ui.label('SEQUENCE BUILDER').classes('hud-section-title text-lg')
        ui.label('Create custom gesture sequences') \
            .classes('text-sm text-gray-400 -mt-2 mb-2')
        
        # Interface de création de séquence
        sequence_gestures = []
        
        with ui.card().classes('config-card p-4'):
            with ui.row().classes('w-full gap-4 items-start'):
                # Colonne gauche : sélection de gestes
                with ui.column().classes('flex-1 gap-2'):
                    ui.label('Select gestures:').classes('text-sm text-cyan-400')
                    
                    gesture_select = ui.select(
                        presets.list_gestures(),
                        label='Gesture',
                        value=presets.list_gestures()[0]
                    ).classes('w-full').props('dark outlined')
                    
                    delay_input = ui.number(
                        'Delay (s)',
                        value=1.0,
                        min=0.1,
                        max=5.0,
                        step=0.1
                    ).classes('w-full').props('dark outlined')
                    
                    def add_to_sequence():
                        gesture = gesture_select.value
                        sequence_gestures.append(gesture)
                        sequence_display.set_text(' → '.join(sequence_gestures))
                        ui.notify(f"Added: {gesture}", type='positive')
                    
                    ui.button(
                        '+ ADD TO SEQUENCE',
                        on_click=add_to_sequence
                    ).classes('w-full').props('flat outline')
                
                # Colonne droite : visualisation et contrôles
                with ui.column().classes('flex-1 gap-2'):
                    ui.label('Current sequence:').classes('text-sm text-cyan-400')
                    
                    sequence_display = ui.label('(empty)') \
                        .classes('text-xs text-gray-400 p-2 border border-cyan-900/40 rounded min-h-[60px]')
                    
                    with ui.row().classes('w-full gap-2'):
                        def clear_sequence():
                            sequence_gestures.clear()
                            sequence_display.set_text('(empty)')
                            ui.notify('Sequence cleared', type='info')
                        
                        def execute_sequence():
                            if not sequence_gestures:
                                ui.notify('Sequence is empty', type='warning')
                                return
                            
                            delay = delay_input.value
                            ui.notify('Executing sequence...', type='info')
                            
                            import threading
                            def run():
                                presets.create_sequence(sequence_gestures, delay=delay)
                                ui.notify('Sequence completed!', type='positive')
                            
                            threading.Thread(target=run, daemon=True).start()
                        
                        ui.button('CLEAR', on_click=clear_sequence) \
                            .props('flat outline color=orange')
                        
                        ui.button('▶ RUN', on_click=execute_sequence) \
                            .props('flat outline color=green')


# ================================================================
# EXPORTS
# ================================================================
__all__ = [
    'build_gesture_panel',
    'build_gesture_tab_panel'
]
