# --------------------------------------------------------------------
# CHARGEUR DE CONFIGURATION YAML
# --------------------------------------------------------------------
"""
Module de chargement de la configuration YAML pour NEURO-HAND V2.0.

Ce module charge le fichier config.yaml et expose un objet global `config`
accessible par tous les modules du projet.

Architecture :
- Classe Config : Structure de données pour la configuration
- Fonction load_config() : Charge et valide le fichier YAML
- Objet global `config` : Instance partagée de Config

Usage :
    from core.config_loader import config
    
    # Accès aux paramètres
    udp_port = config.network.udp_port
    fingers = config.fingers
    log_level = config.logging.level
"""

import yaml
from pathlib import Path
from typing import List
import sys


# --------------------------------------------------------------------
# STRUCTURE DE CONFIGURATION
# --------------------------------------------------------------------

class NetworkConfig:
    """Configuration réseau (PC, RPi, UDP, timeouts)."""
    
    def __init__(self, data: dict):
        # Configuration PC (hand tracker)
        self.pc_ip = data.get('pc_ip', '192.168.1.10')
        self.mjpeg_port = data.get('mjpeg_port', 8090)
        
        # Configuration RPi (webcam locale)
        self.rpi_ip = data.get('rpi_ip', '192.168.1.60')
        self.rpi_camera_port = data.get('rpi_camera_port', 8091)
        self.rpi_camera_enabled = data.get('rpi_camera_enabled', True)
        
        # Configuration UDP
        self.udp_ip = data.get('udp_ip', '0.0.0.0')
        self.udp_port = data.get('udp_port', 5005)
        self.lost_timeout = data.get('lost_timeout', 2.0)
    
    @property
    def mjpeg_url(self) -> str:
        """Retourne l'URL complète du flux MJPEG du PC."""
        return f'http://{self.pc_ip}:{self.mjpeg_port}/cam.mjpg'
    
    @property
    def rpi_camera_url(self) -> str:
        """Retourne l'URL complète du flux webcam RPi."""
        return f'http://{self.rpi_ip}:{self.rpi_camera_port}/stream.mjpg'


class ServosConfig:
    """Configuration des servos (seuils, anti-flutter)."""
    
    def __init__(self, data: dict):
        self.open_threshold = data.get('open_threshold', 0.3)
        self.close_threshold = data.get('close_threshold', 0.7)
        self.thumb_anti_flutter = data.get('thumb_anti_flutter', 0.02)


class UIConfig:
    """Configuration de l'interface utilisateur."""
    
    def __init__(self, data: dict):
        self.web_port = data.get('web_port', 8080)
        self.update_interval = data.get('update_interval', 0.05)


class SecurityConfig:
    """Configuration de la sécurité réseau."""
    
    def __init__(self, data: dict):
        self.enable_hmac = data.get('enable_hmac', False)
        self.rate_limit_requests = data.get('rate_limit_requests', 100)
        self.rate_limit_window = data.get('rate_limit_window', 1.0)


class LoggingConfig:
    """Configuration du système de logging."""
    
    def __init__(self, data: dict):
        self.level = data.get('level', 'INFO')
        self.file = data.get('file', 'logs/neurohand.log')
        self.max_bytes = data.get('max_bytes', 10485760)  # 10 MB
        self.backup_count = data.get('backup_count', 5)


class Config:
    """
    Configuration globale de NEURO-HAND V2.0.
    
    Attributes:
        network: Configuration réseau (NetworkConfig)
        servos: Configuration servos (ServosConfig)
        ui: Configuration interface (UIConfig)
        security: Configuration sécurité (SecurityConfig)
        logging: Configuration logging (LoggingConfig)
        fingers: Liste des doigts pilotés (List[str])
    """
    
    def __init__(self, config_dict: dict):
        """
        Initialise la configuration depuis un dictionnaire YAML.
        
        Args:
            config_dict: Dictionnaire chargé depuis config.yaml
        """
        self.network = NetworkConfig(config_dict.get('network', {}))
        self.servos = ServosConfig(config_dict.get('servos', {}))
        self.ui = UIConfig(config_dict.get('ui', {}))
        self.security = SecurityConfig(config_dict.get('security', {}))
        self.logging = LoggingConfig(config_dict.get('logging', {}))
        
        # Liste des doigts
        self.fingers = config_dict.get('fingers', [
            'pouce_articulation',
            'index',
            'majeur',
            'annulaire_auriculaire'
        ])


# --------------------------------------------------------------------
# CHARGEMENT DE LA CONFIGURATION
# --------------------------------------------------------------------

def load_config(config_path: str = None) -> Config:
    """
    Charge la configuration depuis le fichier YAML.
    
    Args:
        config_path: Chemin vers le fichier config.yaml.
                     Si None, cherche dans le dossier racine du projet.
    
    Returns:
        Config: Objet de configuration chargé.
    
    Raises:
        FileNotFoundError: Si le fichier config.yaml n'existe pas.
        yaml.YAMLError: Si le fichier YAML est mal formaté.
    """
    # Déterminer le chemin du fichier de config
    if config_path is None:
        # Chercher config.yaml à la racine du projet (2 niveaux au-dessus de core/)
        base_dir = Path(__file__).resolve().parents[1]
        config_path = base_dir / 'config.yaml'
    else:
        config_path = Path(config_path)
    
    # Vérifier que le fichier existe
    if not config_path.exists():
        print(f"[ERREUR] Fichier de configuration non trouvé : {config_path}")
        print("[INFO] Utilisation des valeurs par défaut.")
        # Retourner une config avec valeurs par défaut
        return Config({})
    
    # Charger le fichier YAML
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        print(f"[CONFIG] Configuration chargée depuis : {config_path}")
        return Config(config_dict)
    
    except yaml.YAMLError as e:
        print(f"[ERREUR] Impossible de parser le fichier YAML : {e}")
        print("[INFO] Utilisation des valeurs par défaut.")
        return Config({})
    
    except Exception as e:
        print(f"[ERREUR] Erreur lors du chargement de la configuration : {e}")
        print("[INFO] Utilisation des valeurs par défaut.")
        return Config({})


# --------------------------------------------------------------------
# INSTANCE GLOBALE
# --------------------------------------------------------------------
# Cette instance est chargée automatiquement à l'import du module
# et peut être utilisée partout dans le projet.

config = load_config()


# --------------------------------------------------------------------
# COMPATIBILITÉ AVEC L'ANCIEN dashboard_config.py
# --------------------------------------------------------------------
# Variables exportées pour faciliter la migration progressive

PC_IP = config.network.pc_ip
MJPEG_PORT = config.network.mjpeg_port
MJPEG_URL = config.network.mjpeg_url

# Configuration RPi webcam
RPI_CAMERA_PORT = config.network.rpi_camera_port
RPI_CAMERA_URL = config.network.rpi_camera_url
RPI_CAMERA_ENABLED = config.network.rpi_camera_enabled

UDP_IP = config.network.udp_ip
UDP_PORT = config.network.udp_port
LOST_TIMEOUT = config.network.lost_timeout

OPEN_THRESHOLD = config.servos.open_threshold
CLOSE_THRESHOLD = config.servos.close_threshold
THUMB_ANTI_FLUTTER = config.servos.thumb_anti_flutter

FINGERS = config.fingers

WEB_PORT = config.ui.web_port
UI_UPDATE_INTERVAL = config.ui.update_interval


# --------------------------------------------------------------------
# EXPORTS
# --------------------------------------------------------------------
__all__ = [
    'config',
    'Config',
    'load_config',
    # Exports de compatibilité
    'PC_IP', 'MJPEG_PORT', 'MJPEG_URL',
    'RPI_CAMERA_PORT', 'RPI_CAMERA_URL', 'RPI_CAMERA_ENABLED',
    'UDP_IP', 'UDP_PORT', 'LOST_TIMEOUT',
    'OPEN_THRESHOLD', 'CLOSE_THRESHOLD', 'THUMB_ANTI_FLUTTER',
    'FINGERS', 'WEB_PORT', 'UI_UPDATE_INTERVAL'
]
