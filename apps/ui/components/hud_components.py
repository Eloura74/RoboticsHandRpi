"""
Composants HUD réutilisables pour éviter la duplication de code.

Ce module fournit des composants UI stylisés pour le dashboard NEURO-HAND.
"""
from nicegui import ui
from typing import Optional


class HUDCard:
    """
    Carte HUD avec coins animés et style cyberpunk.
    
    Usage:
        with HUDCard('w-full p-6') as card:
            ui.label('Contenu')
    
    Args:
        classes: Classes CSS Tailwind additionnelles
        with_corners: Afficher les coins HUD animés (défaut: True)
    """
    def __init__(self, classes: str = "", with_corners: bool = True):
        self.classes = classes
        self.with_corners = with_corners
        self.container = None
    
    def __enter__(self):
        """Ouverture du contexte : crée la carte."""
        self.container = ui.card().classes(f'hud-panel {self.classes} relative overflow-hidden')
        self.container.__enter__()
        
        if self.with_corners:
            ui.html('''
                <div class="hud-overlay">
                    <div class="hud-corner hud-tl"></div>
                    <div class="hud-corner hud-tr"></div>
                    <div class="hud-corner hud-bl"></div>
                    <div class="hud-corner hud-br"></div>
                </div>
            ''', sanitize=False)
        
        return self.container
    
    def __exit__(self, *args):
        """Fermeture du contexte."""
        if self.container:
            self.container.__exit__(*args)


class StatDisplay:
    """
    Affichage de statistique avec icône, label et valeur.
    
    Args:
        icon: Nom de l'icône Material (ex: 'memory', 'storage')
        label: Texte du label
        value: Valeur initiale à afficher
        color: Couleur du thème (cyan, blue, teal, red, yellow, purple)
        size: Taille du texte de la valeur (2xl, 3xl, 4xl, 5xl)
    """
    def __init__(
        self, 
        icon: str, 
        label: str, 
        value: str = "0", 
        color: str = "cyan",
        size: str = "4xl"
    ):
        self.color = color
        self.value_label = None
        
        with ui.column().classes('items-center justify-center gap-3 z-10 relative w-full'):
            ui.icon(icon, size='xl').classes(f'text-{color}-400')
            ui.label(label).classes('hud-mini-label text-[10px]')
            self.value_label = ui.label(value).classes(
                f'text-{size} font-mono text-{color}-400 title-glow'
            )
    
    def update(self, value: str):
        """
        Met à jour la valeur affichée.
        
        Args:
            value: Nouvelle valeur à afficher
        """
        if self.value_label:
            self.value_label.text = value


class ProgressBar:
    """
    Barre de progression holographique avec effet glow.
    
    Args:
        bar_id: Identifiant unique pour le DOM (requis pour mise à jour JS)
        color: Couleur du thème (cyan, blue, red, yellow, etc.)
        height: Hauteur de la barre (h-1, h-2, etc.)
    """
    def __init__(self, bar_id: str, color: str = "cyan", height: str = "h-1"):
        self.bar_id = bar_id
        self.color = color
        
        # Palette de couleurs pour le glow
        glow_colors = {
            'cyan': 'rgba(0,243,255,0.6)',
            'blue': 'rgba(96,165,250,0.6)',
            'red': 'rgba(248,113,113,0.6)',
            'yellow': 'rgba(250,204,21,0.6)',
            'teal': 'rgba(20,184,166,0.6)',
            'purple': 'rgba(168,85,247,0.6)',
        }
        
        glow = glow_colors.get(color, glow_colors['cyan'])
        
        ui.html(f'''
            <div class="w-full {height} bg-gray-900/50 rounded-full overflow-hidden" 
                 style="border: 1px solid rgba(0,243,255,0.3);">
                <div id="{bar_id}" 
                     class="h-full bg-gradient-to-r from-{color}-600 to-{color}-400" 
                     style="width: 0%; transition: width 0.5s; box-shadow: 0 0 10px {glow};"></div>
            </div>
        ''', sanitize=False)
    
    def update(self, percent: float):
        """
        Met à jour le pourcentage de la barre.
        
        Args:
            percent: Pourcentage (0-100)
        """
        # Clamp entre 0 et 100
        percent = max(0, min(100, percent))
        ui.run_javascript(
            f"document.getElementById('{self.bar_id}').style.width = '{percent}%';"
        )
