# --------------------------------------------------------------------
# THREADS RÉSEAU ET CONTRÔLE MATÉRIEL
# --------------------------------------------------------------------
"""
Ce module gère :
- Le thread de réception UDP (valeurs des doigts depuis le PC)
- Le thread de contrôle matériel (pilotage des servos)
- Les fonctions utilitaires de parsing et contrôle
"""

import json
import socket
import time
import threading
from typing import Optional

from apps.dashboard_config import (
    UDP_IP, UDP_PORT, LOST_TIMEOUT, FINGERS,
    OPEN_THRESHOLD, CLOSE_THRESHOLD, THUMB_ANTI_FLUTTER
)


# --------------------------------------------------------------------
# ÉTAT PARTAGÉ (thread-safe)
# --------------------------------------------------------------------
state_lock = threading.Lock()
state = {
    'values': {f: 0.0 for f in FINGERS},
    'udp_connected': False,
    'fps': 0,
    'packet_count': 0,
    'simu_mode': False,
}


# --------------------------------------------------------------------
# UTILITAIRES RÉSEAU
# --------------------------------------------------------------------

def get_local_ip() -> str:
    """
    Retourne l'IP locale du Raspberry Pi.
    Utilisé pour afficher l'adresse UDP à laquelle le PC doit envoyer.
    
    Returns:
        str: Adresse IP locale ou "127.0.0.1" en cas d'erreur.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _setup_udp_socket() -> Optional[socket.socket]:
    """
    Configure et initialise le socket UDP pour la réception des données.
    
    Returns:
        socket.socket: Socket UDP configuré et prêt à recevoir.
        None: En cas d'erreur d'initialisation.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Options socket pour réutilisation du port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        
        # Bind et mode non-bloquant
        sock.bind((UDP_IP, UDP_PORT))
        sock.setblocking(False)
        
        local_ip = get_local_ip()
        print(f"[UDP] Thread UDP démarré - écoute sur {UDP_IP}:{UDP_PORT}")
        print(f"[UDP] IP locale du Raspberry Pi: {local_ip}")
        print(f"[UDP] Le PC doit envoyer les données UDP à: {local_ip}:{UDP_PORT}")
        
        return sock
    except Exception as e:
        print(f"[ERROR] Impossible de démarrer le thread UDP: {e}")
        return None


def _parse_udp_data(data: bytes):
    """
    Parse les données UDP reçues (JSON) et met à jour l'état global.
    
    Args:
        data: Données brutes reçues via UDP (format JSON).
    """
    try:
        msg = json.loads(data.decode())
        with state_lock:
            # Ne traiter que si pas en mode simulation
            if not state['simu_mode']:
                if not state['udp_connected']:
                    print("[UDP] CONNEXION ÉTABLIE - Réception de données depuis le PC")
                
                state['udp_connected'] = True
                state['packet_count'] += 1
                
                # Mise à jour des valeurs de chaque doigt (clamp 0..1)
                for f in FINGERS:
                    if f in msg:
                        try:
                            v = float(msg[f])
                            state['values'][f] = max(0.0, min(1.0, v))
                        except Exception:
                            pass
    except Exception as e:
        print(f"[UDP] Erreur de parsing: {e}")


# --------------------------------------------------------------------
# THREAD UDP
# --------------------------------------------------------------------

def receiver_thread():
    """
    Thread de réception UDP :
    - Écoute les paquets UDP contenant les valeurs des doigts (0..1),
    - Détecte les timeouts (perte de connexion),
    - Calcule le FPS de réception.
    """
    sock = _setup_udp_socket()
    if not sock:
        return

    # Variables de suivi de la réception
    packet_cnt = 0
    t0 = time.time()
    last_rx = time.time()
    rx_count = 0

    while True:
        now = time.time()

        # Détection de perte de signal (timeout)
        if state['udp_connected'] and (now - last_rx > LOST_TIMEOUT):
            print(f"[UDP] TIMEOUT - Pas de données depuis {LOST_TIMEOUT}s. Déconnexion.")
            with state_lock:
                state['udp_connected'] = False

        # Vidage du buffer UDP pour garder uniquement le dernier paquet reçu
        data = None
        try:
            while True:
                chunk, _ = sock.recvfrom(4096)
                data = chunk
        except Exception:
            pass

        # Traitement du paquet reçu
        if data:
            last_rx = now
            packet_cnt += 1
            rx_count += 1

            # Calcul du "FPS" UDP (paquets/sec)
            if now - t0 > 1.0:
                with state_lock:
                    state['fps'] = packet_cnt
                print(f"[UDP] {packet_cnt} paquets/sec reçus (total: {rx_count})")
                packet_cnt = 0
                t0 = now

            # Parsing et mise à jour de l'état
            _parse_udp_data(data)

        time.sleep(0.001)


# --------------------------------------------------------------------
# CONTRÔLE MATÉRIEL
# --------------------------------------------------------------------

def _control_thumb_rotation(ctrl, v_thumb: float, last_value: float) -> float:
    """
    Pilote la rotation du pouce (servo MG90S) avec lissage anti-flutter.
    
    Args:
        ctrl: Instance du contrôleur matériel (HandController).
        v_thumb: Valeur cible du pouce (0..1).
        last_value: Dernière valeur appliquée.
    
    Returns:
        float: Nouvelle valeur de référence pour le pouce.
    """
    # Seuil anti-flutter : on ne bouge que si variation > seuil
    if abs(v_thumb - last_value) > THUMB_ANTI_FLUTTER:
        # Mapping 0..1 -> angle_min..angle_max (défini dans servos_v2.json)
        ctrl.thumb_from_value(v_thumb)
        return v_thumb
    return last_value


def _control_continuous_fingers(ctrl, targets: dict, logical: dict):
    """
    Pilote les doigts à servos continus (open/close) selon les valeurs reçues.
    
    Args:
        ctrl: Instance du contrôleur matériel (HandController).
        targets: Dictionnaire des valeurs cibles (0..1) par doigt.
        logical: Dictionnaire de l'état logique actuel ('open' ou 'close') par doigt.
    """
    for f, val in targets.items():
        curr_state = logical.get(f, 'open')

        # Fermeture si valeur > seuil haut
        if val > CLOSE_THRESHOLD and curr_state != 'close':
            ctrl.close_finger(f, parallel=True)
            logical[f] = 'close'

        # Ouverture si valeur < seuil bas
        elif val < OPEN_THRESHOLD and curr_state != 'open':
            ctrl.open_finger(f, parallel=True)
            logical[f] = 'open'


# --------------------------------------------------------------------
# THREAD MATÉRIEL
# --------------------------------------------------------------------

def hardware_thread(ctrl):
    """
    Boucle de contrôle matérielle (thread séparé) :
    - Convertit les valeurs 0..1 reçues en actions open/close pour les servos continus,
    - Pilote la rotation du pouce (MG90S) de manière fluide via thumb_from_value().
    
    Args:
        ctrl: Instance de HandController pour piloter les servos.
    """
    # État logique des doigts (open/close)
    logical = {f: 'open' for f in FINGERS}
    # Dernière valeur du pouce (pour lissage)
    last_thumb_value = 0.0

    while True:
        # Snapshot de l'état courant (thread-safe)
        with state_lock:
            targets = state['values'].copy()
            active = state['udp_connected'] or state['simu_mode']

        if active:
            try:
                # 1) Pilotage rotation pouce (servo positionnel MG90S)
                v_thumb = float(targets.get('pouce_articulation', 0.0))
                last_thumb_value = _control_thumb_rotation(ctrl, v_thumb, last_thumb_value)

                # 2) Pilotage des doigts continus (ouverture/fermeture)
                _control_continuous_fingers(ctrl, targets, logical)

            except Exception as e:
                print(f"[HARDWARE] Erreur dans hardware_thread: {e}")
                import traceback
                traceback.print_exc()

        time.sleep(0.05)
