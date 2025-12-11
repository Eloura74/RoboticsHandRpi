# --------------------------------------------------------------------
# SYSTÈME DE PRESETS DE GESTES
# --------------------------------------------------------------------
"""
Module pour gérer des gestes prédéfinis de la main robotique.

Permet de :
- Stocker des positions/gestes nommés
- Exécuter rapidement des poses communes
- Charger/sauvegarder des presets personnalisés
- Créer des séquences de mouvements

Usage :
    from core.gesture_presets import GesturePresets
    
    presets = GesturePresets(controller)
    presets.execute('peace_sign')
    presets.execute('fist')
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


# ================================================================
# STRUCTURE D'UN GESTE
# ================================================================

@dataclass
class Gesture:
    """
    Représente un geste/pose de la main.
    
    Attributes:
        name: Nom du geste (ex: "peace_sign", "fist")
        description: Description textuelle
        fingers: État de chaque doigt ('open' ou 'close')
        thumb_angle: Angle du pouce (0-180°), optionnel
        duration: Durée pour atteindre la pose (secondes)
    """
    name: str
    description: str
    fingers: Dict[str, str]  # {'index': 'open', 'majeur': 'close', ...}
    thumb_angle: Optional[float] = None  # Angle du servo rotation pouce
    duration: float = 1.0


# ================================================================
# PRESETS PAR DÉFAUT
# ================================================================

DEFAULT_GESTURES = {
    'rest': Gesture(
        name='rest',
        description='Main au repos, tous doigts ouverts',
        fingers={
            'pouce_articulation': 'open',
            'index': 'open',
            'majeur': 'open',
            'annulaire_auriculaire': 'open'
        },
        thumb_angle=90.0,  # Position neutre
        duration=0.8
    ),
    
    'fist': Gesture(
        name='fist',
        description='Poing fermé complet',
        fingers={
            'pouce_articulation': 'close',
            'index': 'close',
            'majeur': 'close',
            'annulaire_auriculaire': 'close'
        },
        thumb_angle=60.0,  # Pouce rentré
        duration=1.2
    ),
    
    'peace_sign': Gesture(
        name='peace_sign',
        description='Signe de paix (index + majeur levés)',
        fingers={
            'pouce_articulation': 'close',
            'index': 'open',
            'majeur': 'open',
            'annulaire_auriculaire': 'close'
        },
        thumb_angle=90.0,
        duration=1.0
    ),
    
    'ok_sign': Gesture(
        name='ok_sign',
        description='Signe OK (pouce + index en cercle)',
        fingers={
            'pouce_articulation': 'close',  # Pouce fermé pour "toucher" index
            'index': 'close',
            'majeur': 'open',
            'annulaire_auriculaire': 'open'
        },
        thumb_angle=120.0,  # Angle pour former cercle
        duration=1.0
    ),
    
    'thumbs_up': Gesture(
        name='thumbs_up',
        description='Pouce levé',
        fingers={
            'pouce_articulation': 'open',
            'index': 'close',
            'majeur': 'close',
            'annulaire_auriculaire': 'close'
        },
        thumb_angle=180.0,  # Pouce complètement levé
        duration=1.0
    ),
    
    'pointing': Gesture(
        name='pointing',
        description='Index pointant',
        fingers={
            'pouce_articulation': 'close',
            'index': 'open',
            'majeur': 'close',
            'annulaire_auriculaire': 'close'
        },
        thumb_angle=90.0,
        duration=0.9
    ),
    
    'rock': Gesture(
        name='rock',
        description='Signe rock (index + auriculaire)',
        fingers={
            'pouce_articulation': 'close',
            'index': 'open',
            'majeur': 'close',
            'annulaire_auriculaire': 'open'
        },
        thumb_angle=90.0,
        duration=1.0
    ),
}


# ================================================================
# GESTIONNAIRE DE PRESETS
# ================================================================

class GesturePresets:
    """
    Gère l'exécution et le stockage de gestes prédéfinis.
    """
    
    def __init__(self, controller, presets_file: Optional[str] = None):
        """
        Initialise le gestionnaire de presets.
        
        Args:
            controller: Instance de HandController.
            presets_file: Chemin vers fichier JSON de presets personnalisés.
        """
        self.controller = controller
        self.gestures = DEFAULT_GESTURES.copy()
        
        # Chemin fichier presets
        if presets_file is None:
            base_dir = Path(__file__).resolve().parents[1]
            self.presets_file = base_dir / 'config' / 'gesture_presets.json'
        else:
            self.presets_file = Path(presets_file)
        
        # Charger presets personnalisés si existants
        self.load_custom_gestures()
    
    def execute(self, gesture_name: str, parallel: bool = True) -> bool:
        """
        Exécute un geste prédéfini.
        
        Args:
            gesture_name: Nom du geste à exécuter.
            parallel: Si True, mouvements parallèles (plus rapide).
        
        Returns:
            bool: True si succès, False si geste inconnu.
        """
        if gesture_name not in self.gestures:
            print(f"[PRESETS] Geste inconnu : {gesture_name}")
            return False
        
        gesture = self.gestures[gesture_name]
        print(f"[PRESETS] Exécution du geste : {gesture.description}")
        
        # 1. Positionner le pouce si angle défini
        if gesture.thumb_angle is not None:
            # Convertir angle (0-180) en valeur 0..1
            # Mapping inversé : angle_max=ouvert(0), angle_min=fermé(1)
            # Pour simplification, on utilise _set_thumb_angle directement
            self.controller._set_thumb_angle(gesture.thumb_angle)
        
        # 2. Positionner chaque doigt
        for finger, state in gesture.fingers.items():
            if finger not in self.controller.servos_conf:
                continue
            
            # Ignorer le servo de rotation pouce (géré séparément)
            if finger == 'pouce_rotation':
                continue
            
            if state == 'open':
                self.controller.open_finger(finger, parallel=parallel)
            elif state == 'close':
                self.controller.close_finger(finger, parallel=parallel)
        
        # 3. Attendre la fin des mouvements si parallèle
        if parallel:
            time.sleep(gesture.duration)
        
        return True
    
    def list_gestures(self) -> List[str]:
        """
        Retourne la liste des noms de gestes disponibles.
        
        Returns:
            List[str]: Liste des noms de gestes.
        """
        return list(self.gestures.keys())
    
    def get_gesture_info(self, gesture_name: str) -> Optional[Gesture]:
        """
        Retourne les informations sur un geste.
        
        Args:
            gesture_name: Nom du geste.
        
        Returns:
            Gesture: Objet Gesture ou None si inexistant.
        """
        return self.gestures.get(gesture_name)
    
    def add_custom_gesture(self, gesture: Gesture) -> None:
        """
        Ajoute un geste personnalisé.
        
        Args:
            gesture: Objet Gesture à ajouter.
        """
        self.gestures[gesture.name] = gesture
        print(f"[PRESETS] Geste ajouté : {gesture.name}")
    
    def save_custom_gestures(self) -> bool:
        """
        Sauvegarde tous les gestes (y compris personnalisés) dans un fichier JSON.
        
        Returns:
            bool: True si succès, False sinon.
        """
        try:
            # Créer le dossier config si nécessaire
            self.presets_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convertir tous les gestes en dict
            gestures_dict = {}
            for name, gesture in self.gestures.items():
                gestures_dict[name] = asdict(gesture)
            
            # Sauvegarder en JSON
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(gestures_dict, f, indent=2, ensure_ascii=False)
            
            print(f"[PRESETS] Gestes sauvegardés dans : {self.presets_file}")
            return True
        
        except Exception as e:
            print(f"[PRESETS] Erreur sauvegarde : {e}")
            return False
    
    def load_custom_gestures(self) -> bool:
        """
        Charge les gestes personnalisés depuis le fichier JSON.
        
        Returns:
            bool: True si succès, False si fichier absent ou erreur.
        """
        if not self.presets_file.exists():
            print(f"[PRESETS] Pas de fichier de presets personnalisés (OK)")
            return False
        
        try:
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                gestures_dict = json.load(f)
            
            # Convertir en objets Gesture
            for name, data in gestures_dict.items():
                self.gestures[name] = Gesture(**data)
            
            print(f"[PRESETS] {len(gestures_dict)} gestes chargés depuis {self.presets_file}")
            return True
        
        except Exception as e:
            print(f"[PRESETS] Erreur chargement : {e}")
            return False
    
    def create_sequence(self, gesture_names: List[str], delay: float = 0.5) -> None:
        """
        Exécute une séquence de gestes avec délai entre chaque.
        
        Args:
            gesture_names: Liste des noms de gestes à exécuter.
            delay: Délai en secondes entre chaque geste.
        """
        print(f"[PRESETS] Exécution séquence : {' -> '.join(gesture_names)}")
        
        for i, gesture_name in enumerate(gesture_names):
            if self.execute(gesture_name, parallel=True):
                # Attendre avant le prochain geste
                if i < len(gesture_names) - 1:
                    time.sleep(delay)


# ================================================================
# EXPORTS
# ================================================================
__all__ = [
    'Gesture',
    'GesturePresets',
    'DEFAULT_GESTURES'
]
