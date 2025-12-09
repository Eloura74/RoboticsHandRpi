# --------------------------------------------------------------------
# SYSTÈME DE LOGGING STRUCTURÉ
# --------------------------------------------------------------------
"""
Module de logging centralisé pour NEURO-HAND V2.0.

Ce module configure le système de logging avec :
- Rotation automatique des fichiers de log
- Handlers pour console (colorés) et fichier
- Niveaux configurables via config.yaml
- Format structuré avec timestamps

Usage :
    from core.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("Message d'information")
    logger.warning("Attention")
    logger.error("Erreur détectée", exc_info=True)
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Import de la configuration
try:
    from core.config_loader import config
    CONFIG_LOADED = True
except Exception:
    CONFIG_LOADED = False


# --------------------------------------------------------------------
# FORMATEURS DE LOG
# --------------------------------------------------------------------

class ColoredFormatter(logging.Formatter):
    """
    Formateur personnalisé avec couleurs pour la console.
    
    Codes couleur ANSI :
    - DEBUG: Cyan
    - INFO: Vert
    - WARNING: Jaune
    - ERROR: Rouge
    - CRITICAL: Rouge gras
    """
    
    # Codes couleur ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Vert
        'WARNING': '\033[33m',    # Jaune
        'ERROR': '\033[31m',      # Rouge
        'CRITICAL': '\033[1;31m', # Rouge gras
    }
    RESET = '\033[0m'
    
    def format(self, record):
        """
        Formate le message avec couleur selon le niveau.
        
        Args:
            record: Enregistrement de log à formatter.
        
        Returns:
            str: Message formaté avec couleur.
        """
        # Récupérer la couleur pour ce niveau
        color = self.COLORS.get(record.levelname, '')
        
        # Formatter le message
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# --------------------------------------------------------------------
# CONFIGURATION DU LOGGER
# --------------------------------------------------------------------

def setup_logger(name: str, force: bool = False) -> logging.Logger:
    """
    Configure et retourne un logger avec handlers console et fichier.
    
    Args:
        name: Nom du logger (généralement __name__ du module).
        force: Si True, reconfigure le logger même s'il existe déjà.
    
    Returns:
        logging.Logger: Logger configuré.
    """
    logger = logging.getLogger(name)
    
    # Si le logger a déjà des handlers et qu'on ne force pas, retourner tel quel
    if logger.handlers and not force:
        return logger
    
    # Supprimer les handlers existants si force=True
    if force and logger.handlers:
        logger.handlers.clear()
    
    # Récupérer la configuration
    if CONFIG_LOADED:
        log_level = getattr(logging, config.logging.level, logging.INFO)
        log_file = config.logging.file
        max_bytes = config.logging.max_bytes
        backup_count = config.logging.backup_count
    else:
        # Valeurs par défaut si config non disponible
        log_level = logging.INFO
        log_file = 'logs/neurohand.log'
        max_bytes = 10 * 1024 * 1024  # 10 MB
        backup_count = 5
    
    logger.setLevel(log_level)
    
    # --------------------------------------------------------------------
    # HANDLER FICHIER (avec rotation)
    # --------------------------------------------------------------------
    # Créer le dossier logs s'il n'existe pas
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # Format pour fichier : timestamp complet + niveau + nom module + message
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # --------------------------------------------------------------------
    # HANDLER CONSOLE (avec couleurs)
    # --------------------------------------------------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Format pour console : niveau coloré + nom module court + message
    console_formatter = ColoredFormatter(
        '[%(levelname)s] [%(name)s] %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Éviter la propagation vers le logger racine (évite doublons)
    logger.propagate = False
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retourne un logger configuré pour le module appelant.
    
    Args:
        name: Nom du logger (si None, utilise 'neurohand').
    
    Returns:
        logging.Logger: Logger configuré prêt à l'emploi.
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Message")
    """
    if name is None:
        name = 'neurohand'
    
    return setup_logger(name)


# --------------------------------------------------------------------
# LOGGER GLOBAL PAR DÉFAUT
# --------------------------------------------------------------------
# Logger par défaut pour usage rapide sans setup explicite

logger = get_logger('neurohand')


# --------------------------------------------------------------------
# EXPORTS
# --------------------------------------------------------------------
__all__ = [
    'get_logger',
    'setup_logger',
    'logger',  # Logger global par défaut
]
