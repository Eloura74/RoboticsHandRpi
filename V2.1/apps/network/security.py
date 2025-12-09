"""
Module de sécurité pour les communications UDP.
Fournit authentification HMAC, rate limiting et validation des données.
"""

import hmac
import hashlib
import time
from collections import deque
from typing import Dict
import os

# Clé secrète partagée (stockée en variable d'environnement pour la production)
SECRET_KEY = os.getenv('NEUROHAND_SECRET_KEY', 'default-dev-key-change-me')


class UDPAuthenticator:
    """
    Authentification HMAC-SHA256 pour paquets UDP.
    
    Usage:
        auth = UDPAuthenticator()
        signature = auth.sign_packet(data)
        is_valid = auth.verify_packet(data, signature)
    """
    
    @staticmethod
    def sign_packet(data: bytes) -> str:
        """
        Signe un paquet avec HMAC-SHA256.
        
        Args:
            data: Données brutes à signer
            
        Returns:
            Signature hexadécimale (64 caractères)
        """
        return hmac.new(
            SECRET_KEY.encode(),
            data,
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_packet(data: bytes, signature: str) -> bool:
        """
        Vérifie la signature d'un paquet.
        
        Args:
            data: Données brutes
            signature: Signature fournie
            
        Returns:
            True si la signature est valide
        """
        expected = UDPAuthenticator.sign_packet(data)
        return hmac.compare_digest(expected, signature)


class RateLimiter:
    """
    Rate limiting pour prévenir les attaques DoS.
    
    Usage:
        limiter = RateLimiter(max_requests=100, window=1.0)
        if limiter.allow_request():
            # Traiter la requête
        else:
            # Rejeter
    """
    
    def __init__(self, max_requests: int = 100, window: float = 1.0):
        """
        Args:
            max_requests: Nombre maximum de requêtes par fenêtre
            window: Durée de la fenêtre en secondes
        """
        self.requests = deque()
        self.max_requests = max_requests
        self.window = window
    
    def allow_request(self) -> bool:
        """
        Vérifie si une nouvelle requête est autorisée.
        
        Returns:
            True si autorisé, False si limite dépassée
        """
        now = time.time()
        
        # Supprimer les requêtes hors de la fenêtre temporelle
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()
        
        # Vérifier la limite
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False


def validate_finger_values(data: dict) -> Dict[str, float]:
    """
    Valide et nettoie les valeurs de doigts reçues par UDP.
    
    Args:
        data: Dictionnaire {finger_name: value}
        
    Returns:
        Dictionnaire validé avec valeurs float entre 0.0 et 1.0
        
    Raises:
        ValueError: Si le format est invalide (nom de doigt, type, ou plage)
    """
    # Doigts valides pour NEURO-HAND (depuis config)
    try:
        from core.config_loader import config
        VALID_FINGERS = set(config.fingers)
    except Exception:
        # Fallback si config non disponible
        VALID_FINGERS = {'pouce_articulation', 'index', 'majeur', 'annulaire_auriculaire'}
    
    validated = {}
    
    for finger, value in data.items():
        # Ignorer les champs metadata (visible, tracking, etc.)
        # qui ne sont pas des doigts
        if finger not in VALID_FINGERS:
            continue  # Passer au champ suivant sans erreur
        
        # Vérifier le type
        if not isinstance(value, (int, float)):
            raise ValueError(f"Invalid value type for {finger}: {type(value)}")
        
        # Vérifier la plage [0.0, 1.0]
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Value out of range for {finger}: {value} (must be 0.0-1.0)")
        
        # Convertir en float et ajouter
        validated[finger] = float(value)
    
    return validated
