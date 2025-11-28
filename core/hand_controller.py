# core/hand_controller.py

import json
import time
import signal
import sys
import threading
from pathlib import Path
from typing import Optional, Dict

from adafruit_servokit import ServoKit  # pip install adafruit-circuitpython-servokit

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False


class HandController:
    """
    Contrôleur V2.0 pour main robotique avec servos continus (MG945 360°).

    Principes de sécurité :
    - AUCUN mouvement automatique au démarrage.
    - AUCUN mouvement automatique à l'arrêt, uniquement retour neutre.
    - Les commandes utilisateur (open/close) sont les seules qui font bouger.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        # ----------- Chargement configuration -----------
        if config_path is None:
            base_dir = Path(__file__).resolve().parents[1]  # .../V2.0
            config_file = base_dir / "config" / "servos_v2.json"
        else:
            config_file = Path(config_path).resolve()

        with open(config_file, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        pca_conf = self.config["pca9685"]
        address = pca_conf.get("address", 64)
        freq = pca_conf.get("frequency", 50)

        # ----------- PCA9685 + ServoKit -----------
        self.kit = ServoKit(channels=16, address=address)
        self.kit.frequency = freq

        # ----------- Gestion alim servos (optionnelle) -----------
        power_conf = self.config.get("power", {})
        self.power_gpio = power_conf.get("enable_gpio", None)
        self.power_high = power_conf.get("active_level_high", True)
        self.power_enabled = False

        if self.power_gpio is not None and GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(
                self.power_gpio,
                GPIO.OUT,
                initial=GPIO.LOW if self.power_high else GPIO.HIGH,
            )
        elif self.power_gpio is not None and not GPIO_AVAILABLE:
            print(
                "[AVERTISSEMENT] RPi.GPIO introuvable, la gestion de l'alim servos par GPIO est désactivée."
            )
            self.power_gpio = None

        # ----------- Config servos (par doigt) -----------
        self.servos_conf = self.config["servos"]

        # État logique par doigt : "open" ou "close"
        # Au démarrage, on suppose que tu as mis la main en position ouverte.
        self.state = {name: "open" for name in self.servos_conf}
        
        # Gestion des threads pour mouvements parallèles
        self._finger_threads: Dict[str, threading.Thread] = {}
        self._finger_locks = {name: threading.Lock() for name in self.servos_conf}
        self._stop_flags = {name: threading.Event() for name in self.servos_conf}

        # Étape 1 : Mettre tous les canaux au NEUTRE (throttle ≈ 0.0)
        # à ce moment-là tu dois avoir l'alim 5 V COUPÉE pour éviter tout choc.
        self._all_neutral()

        # IMPORTANT :
        #  - on NE touche PAS à l'alim 5 V ici (pas de enable_power()).
        #  - on NE fait NI open_hand() NI close_hand() automatiquement.

        # ----------- Gestion des signaux pour arrêt propre -----------
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    # ==================================================================
    # Alimentation servos
    # ==================================================================
    def enable_power(self) -> None:
        """Active l'alimentation des servos si un GPIO est défini."""
        if self.power_gpio is not None and GPIO_AVAILABLE:
            GPIO.output(self.power_gpio, GPIO.HIGH if self.power_high else GPIO.LOW)
            self.power_enabled = True
            print("[INFO] Alimentation servos ACTIVÉE (GPIO).")
        else:
            self.power_enabled = True
            print("[INFO] Alimentation servos supposée ACTIVE (pas de GPIO).")

    def disable_power(self) -> None:
        """Coupe l'alimentation des servos si un GPIO est défini."""
        if self.power_gpio is not None and GPIO_AVAILABLE:
            GPIO.output(self.power_gpio, GPIO.LOW if self.power_high else GPIO.HIGH)
            self.power_enabled = False
            print("[INFO] Alimentation servos COUPÉE (GPIO).")
        else:
            self.power_enabled = False
            print("[INFO] Alimentation servos à couper MANUELLEMENT (pas de GPIO).")

    # ==================================================================
    # Bas niveau : écriture throttle
    # ==================================================================
    def _set_throttle(self, channel: int, value: float) -> None:
        """
        Applique un throttle au servo continu d'un canal donné.
        Adafruit ServoKit utilise la plage [-1.0 ; 1.0], 0.0 = neutre.
        """
        value = max(-1.0, min(1.0, value))
        try:
            self.kit.continuous_servo[channel].throttle = value
        except Exception as e:
            print(f"[ERREUR] throttle canal {channel} -> {value} : {e}")

    def _all_neutral(self) -> None:
        """Met tous les servos à leur valeur 'neutral' sans supposer l'état mécanique."""
        print("[ACTION] Mise de TOUS les servos au neutre...")
        for name, conf in self.servos_conf.items():
            channel = conf["channel"]
            neutral = conf.get("neutral", 0.0)
            self._set_throttle(channel, neutral)
        time.sleep(0.05)

    # ==================================================================
    # Mouvement d'un doigt (ouverture / fermeture)
    # ==================================================================
    def _move_finger_blocking(self, name: str, action: str) -> None:
        """
        Déplace un doigt en utilisant les durées calibrées.
        action = "open" ou "close".
        Mouvement BLOQUANT, puis retour neutre.
        Si le doigt est déjà dans l'état demandé -> aucun mouvement.
        """
        if name not in self.servos_conf:
            raise ValueError(f"Doigt inconnu : {name}")

        if self.state.get(name) == action:
            return

        conf = self.servos_conf[name]
        channel = conf["channel"]
        neutral = conf.get("neutral", 0.0)
        dir_close = conf["dir_close"]
        speed_close = conf["speed_close"]
        speed_open = conf["speed_open"]
        t_close = conf["t_close"]
        t_open = conf["t_open"]

        if action == "close":
            direction = dir_close
            speed = speed_close
            duration = t_close
        elif action == "open":
            direction = -dir_close
            speed = speed_open
            duration = t_open
        else:
            raise ValueError("action doit être 'open' ou 'close'")

        throttle = neutral + direction * speed
        throttle = max(-1.0, min(1.0, throttle))

        print(
            f"[ACTION] {action} doigt '{name}' "
            f"(canal={channel}, throttle={throttle:.3f}, durée={duration:.2f}s)"
        )

        # Appliquer le throttle
        self._set_throttle(channel, throttle)
        
        # Attente interruptible par morceaux de 10ms pour permettre arrêt rapide
        start_time = time.time()
        while time.time() - start_time < duration:
            if self._stop_flags[name].is_set():
                break
            time.sleep(0.01)

        # Retour neutre
        self._set_throttle(channel, neutral)
        self.state[name] = action
        self._stop_flags[name].clear()
    
    def _move_finger_thread(self, name: str, action: str) -> None:
        """
        Wrapper thread-safe pour mouvement d'un doigt.
        Utilisé pour les mouvements parallèles.
        """
        with self._finger_locks[name]:
            try:
                self._move_finger_blocking(name, action)
            except Exception as e:
                print(f"[ERREUR] Thread doigt '{name}': {e}")

    # ==================================================================
    # API publique
    # ==================================================================
    def open_finger(self, name: str, parallel: bool = False) -> None:
        """
        Ouvre un doigt.
        
        Args:
            name: Nom du doigt
            parallel: Si True, démarre le mouvement dans un thread (non-bloquant)
                     Si False, mouvement bloquant (défaut)
        """
        if parallel:
            self._start_finger_movement(name, "open")
        else:
            self._move_finger_blocking(name, "open")

    def close_finger(self, name: str, parallel: bool = False) -> None:
        """
        Ferme un doigt.
        
        Args:
            name: Nom du doigt
            parallel: Si True, démarre le mouvement dans un thread (non-bloquant)
                     Si False, mouvement bloquant (défaut)
        """
        if parallel:
            self._start_finger_movement(name, "close")
        else:
            self._move_finger_blocking(name, "close")
    
    def _start_finger_movement(self, name: str, action: str) -> None:
        """
        Démarre un mouvement de doigt dans un thread séparé.
        Si un mouvement est déjà en cours pour ce doigt, l'annule d'abord.
        """
        # Arrêter le thread précédent s'il existe
        if name in self._finger_threads and self._finger_threads[name].is_alive():
            self._stop_flags[name].set()
            self._finger_threads[name].join(timeout=0.5)
        
        # Créer et démarrer le nouveau thread
        thread = threading.Thread(
            target=self._move_finger_thread,
            args=(name, action),
            daemon=True,
            name=f"finger_{name}_{action}"
        )
        self._finger_threads[name] = thread
        thread.start()

    def open_hand(self, parallel: bool = True, delay_between: float = 0.05) -> None:
        """
        Ouvre tous les doigts.
        
        Args:
            parallel: Si True, tous les doigts bougent en même temps (fluide)
                     Si False, mouvements séquentiels (ancien comportement)
            delay_between: Délai entre chaque doigt si parallel=False
        """
        print("[ACTION] Ouverture complète de la main...")
        if parallel:
            # Lancer tous les doigts en parallèle
            for name in self.servos_conf:
                self.open_finger(name, parallel=True)
            # Attendre que tous les threads se terminent
            self._wait_all_movements()
        else:
            # Mode séquentiel (ancien comportement)
            for name in self.servos_conf:
                self.open_finger(name, parallel=False)
                time.sleep(delay_between)

    def close_hand(self, parallel: bool = True, delay_between: float = 0.05) -> None:
        """
        Ferme tous les doigts.
        
        Args:
            parallel: Si True, tous les doigts bougent en même temps (fluide)
                     Si False, mouvements séquentiels (ancien comportement)
            delay_between: Délai entre chaque doigt si parallel=False
        """
        print("[ACTION] Fermeture complète de la main...")
        if parallel:
            # Lancer tous les doigts en parallèle
            for name in self.servos_conf:
                self.close_finger(name, parallel=True)
            # Attendre que tous les threads se terminent
            self._wait_all_movements()
        else:
            # Mode séquentiel (ancien comportement)
            for name in self.servos_conf:
                self.close_finger(name, parallel=False)
                time.sleep(delay_between)
    
    def _wait_all_movements(self, timeout: float = 5.0) -> None:
        """
        Attend que tous les threads de mouvement se terminent.
        
        Args:
            timeout: Temps maximum d'attente en secondes
        """
        start = time.time()
        for name, thread in self._finger_threads.items():
            if thread.is_alive():
                remaining = max(0.1, timeout - (time.time() - start))
                thread.join(timeout=remaining)

    def stop_all(self) -> None:
        """
        Arrête immédiatement tous les mouvements et met les servos au neutre.
        """
        print("[ACTION] STOP ALL -> arrêt threads + neutre sur tous les canaux.")
        
        # Signaler à tous les threads de s'arrêter
        for stop_flag in self._stop_flags.values():
            stop_flag.set()
        
        # Attendre les threads (court timeout)
        for thread in self._finger_threads.values():
            if thread.is_alive():
                thread.join(timeout=0.2)
        
        # Mettre tous les servos au neutre
        self._all_neutral()

    # ==================================================================
    # Arrêt propre
    # ==================================================================
    def shutdown(self) -> None:
        """
        Séquence d'arrêt sûre :
        1) arrêt de tous les threads,
        2) neutre sur tous les servos,
        3) coupure alim,
        4) cleanup GPIO.
        (PAS de mouvement d'ouverture forcé ici)
        """
        print("\n[SHUTDOWN] Arrêt de la main robotique...")
        
        # Arrêter tous les threads de mouvement
        try:
            for stop_flag in self._stop_flags.values():
                stop_flag.set()
            for thread in self._finger_threads.values():
                if thread.is_alive():
                    thread.join(timeout=0.5)
        except Exception as e:
            print(f"[AVERTISSEMENT] Erreur pendant arrêt threads : {e}")
        
        # Mettre les servos au neutre
        try:
            self._all_neutral()
        except Exception as e:
            print(f"[AVERTISSEMENT] Erreur pendant passage au neutre : {e}")

        self.disable_power()

        if GPIO_AVAILABLE and self.power_gpio is not None:
            GPIO.cleanup(self.power_gpio)

        print("[SHUTDOWN] Terminé.")

    def _signal_handler(self, signum, frame) -> None:
        print(f"\n[SIGNAL] Reçu signal {signum}, arrêt propre demandé...")
        self.shutdown()
        sys.exit(0)
