# --------------------------------------------------------------------
# HANDLERS UDP RÉUTILISABLES
# --------------------------------------------------------------------
"""
Module de handlers UDP pour NEURO-HAND V2.0.

Fournit des classes réutilisables pour :
- Réception et parsing des paquets UDP
- Watchdog de connexion
- Hystérésis pour contrôle des servos
- Sécurité (rate limiting, HMAC, validation)

Usage :
    from apps.network.udp_handler import UDPReceiver, ServoController
    
    receiver = UDPReceiver(config.network.udp_ip, config.network.udp_port)
    servo_ctrl = ServoController(config.servos.open_threshold, config.servos.close_threshold)
    
    while True:
        packet = receiver.receive_packet()
        if packet:
            for finger, value in packet.items():
                servo_ctrl.apply_hysteresis(finger, value, hand_controller)
"""

import json
import socket
import time
from typing import Optional, Dict
from core.logger import get_logger
from core.config_loader import config
from apps.network import UDPAuthenticator, RateLimiter, validate_finger_values

logger = get_logger(__name__)


# --------------------------------------------------------------------
# CLASSE UDPReceiver
# --------------------------------------------------------------------

class UDPReceiver:
    """
    Gère la réception et le parsing des paquets UDP avec watchdog.
    
    Fonctionnalités :
    - Configuration automatique du socket UDP
    - Réception non-bloquante avec vidage du buffer
    - Watchdog de timeout (détection perte de connexion)
    - Rate limiting et validation (optionnels)
    - Authentification HMAC (optionnelle)
    
    Attributes:
        ip: Adresse IP d'écoute
        port: Port UDP
        timeout: Timeout de watchdog (secondes)
        enable_security: Active rate limiting + validation
        sock: Socket UDP
        connected: État de connexion
        last_packet_time: Timestamp du dernier paquet reçu
    """
    
    def __init__(
        self, 
        ip: str, 
        port: int, 
        timeout: float = 2.0,
        enable_security: bool = True
    ):
        """
        Initialise le récepteur UDP.
        
        Args:
            ip: Adresse IP d'écoute (ex: "0.0.0.0")
            port: Port UDP
            timeout: Timeout watchdog en secondes
            enable_security: Active sécurité (rate limit, validation, HMAC)
        """
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.enable_security = enable_security
        
        self.sock: Optional[socket.socket] = None
        self.connected = False
        self.last_packet_time = time.time()
        
        # Sécurité réseau
        if enable_security:
            self.limiter = RateLimiter(
                max_requests=config.security.rate_limit_requests,
                window=config.security.rate_limit_window
            )
            self.authenticator = UDPAuthenticator() if config.security.enable_hmac else None
            logger.info(f"Sécurité UDP : HMAC={'activé' if config.security.enable_hmac else 'désactivé'}, "
                        f"Rate limit={config.security.rate_limit_requests} req/{config.security.rate_limit_window}s")
        else:
            self.limiter = None
            self.authenticator = None
        
        # Initialiser le socket
        self.setup_socket()
    
    def setup_socket(self) -> bool:
        """
        Configure et initialise le socket UDP.
        
        Returns:
            True si succès, False si erreur
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, 'SO_REUSEPORT'):
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            
            self.sock.bind((self.ip, self.port))
            self.sock.setblocking(False)
            
            logger.info(f"Socket UDP configuré : {self.ip}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Erreur configuration socket UDP : {e}", exc_info=True)
            return False
    
    def receive_packet(self) -> Optional[Dict[str, float]]:
        """
        Reçoit et parse un paquet UDP.
        
        Applique :
        - Vidage du buffer (garde le dernier paquet)
        - Rate limiting (si activé)
        - Vérification HMAC (si activée)
        - Parsing JSON
        - Validation des données
        
        Returns:
            Dictionnaire {finger: value} validé, ou None si pas de paquet/erreur
        """
        if not self.sock:
            return None
        
        # Vidage buffer UDP (garde uniquement le dernier paquet)
        data = None
        try:
            while True:
                chunk, _ = self.sock.recvfrom(4096)
                data = chunk
        except Exception:
            pass
        
        if not data:
            return None
        
        # Rate limiting
        if self.limiter and not self.limiter.allow_request():
            logger.warning("Rate limit dépassé, paquet ignoré")
            return None
        
        # Vérification HMAC
        payload = data
        if self.authenticator:
            if len(data) < 64:
                logger.warning(f"Paquet trop court ({len(data)} bytes), signature manquante")
                return None
            
            try:
                signature = data[:64].decode('utf-8', errors='ignore')
                payload = data[64:]
                
                if not self.authenticator.verify_packet(payload, signature):
                    logger.warning("Signature HMAC invalide")
                    return None
            except Exception as e:
                logger.warning(f"Erreur vérification HMAC : {e}")
                return None
        
        # Parsing JSON
        try:
            msg = json.loads(payload.decode('utf-8'))
        except Exception as e:
            logger.warning(f"Erreur parsing JSON : {e}")
            return None
        
        # Validation des données
        try:
            validated = validate_finger_values(msg)
        except ValueError as e:
            logger.warning(f"Données invalides : {e}")
            return None
        
        # Mise à jour watchdog
        self.last_packet_time = time.time()
        if not self.connected:
            logger.info("CONNEXION ÉTABLIE")
            self.connected = True
        
        return validated
    
    def is_connected(self) -> bool:
        """
        Vérifie si la connexion est active (watchdog).
        
        Returns:
            True si connecté, False si timeout
        """
        now = time.time()
        was_connected = self.connected
        
        # Vérifier timeout
        if self.connected and (now - self.last_packet_time > self.timeout):
            self.connected = False
            if was_connected:
                logger.warning(f"TIMEOUT - Pas de données depuis {self.timeout}s")
        
        return self.connected


# --------------------------------------------------------------------
# CLASSE ServoController
# --------------------------------------------------------------------

class ServoController:
    """
    Applique l'hystérésis et contrôle les servos.
    
    Centralise la logique de contrôle des servos avec hystérésis
    pour éviter les oscillations et les mouvements parasites.
    
    Attributes:
        open_threshold: Seuil en dessous duquel on ouvre (0..1)
        close_threshold: Seuil au dessus duquel on ferme (0..1)
        logical_state: État logique actuel de chaque doigt ('open'/'close')
    """
    
    def __init__(self, open_threshold: float = 0.3, close_threshold: float = 0.7):
        """
        Initialise le contrôleur de servos.
        
        Args:
            open_threshold: Valeur en dessous de laquelle on ouvre (défaut: 0.3)
            close_threshold: Valeur au dessus de laquelle on ferme (défaut: 0.7)
        """
        self.open_threshold = open_threshold
        self.close_threshold = close_threshold
        self.logical_state: Dict[str, str] = {}
    
    def apply_hysteresis(
        self, 
        finger: str, 
        value: float, 
        controller
    ) -> str:
        """
        Applique l'hystérésis et commande le servo.
        
        Args:
            finger: Nom du doigt
            value: Valeur de consigne (0..1)
            controller: Instance de HandController
        
        Returns:
            Action effectuée : 'open', 'close' ou 'hold'
        """
        # Récupérer l'état actuel (par défaut 'open')
        current = self.logical_state.get(finger, 'open')
        
        # Hystérésis : on ne change que si on dépasse un seuil
        if value > self.close_threshold and current != 'close':
            logger.debug(f"{finger}: v={value:.2f} -> CLOSE")
            controller.close_finger(finger, parallel=True)
            self.logical_state[finger] = 'close'
            return 'close'
        
        elif value < self.open_threshold and current != 'open':
            logger.debug(f"{finger}: v={value:.2f} -> OPEN")
            controller.open_finger(finger, parallel=True)
            self.logical_state[finger] = 'open'
            return 'open'
        
        return 'hold'
    
    def reset(self):
        """Réinitialise tous les états à 'open'."""
        for finger in self.logical_state:
            self.logical_state[finger] = 'open'
        logger.debug("États servos réinitialisés")


# --------------------------------------------------------------------
# EXPORTS
# --------------------------------------------------------------------
__all__ = ['UDPReceiver', 'ServoController']
