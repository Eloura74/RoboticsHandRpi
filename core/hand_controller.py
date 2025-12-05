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
    Contrôleur V2.0 pour main robotique avec :
    - servos continus (MG945 360°) pour les doigts,
    - servo angulaire (MG90S) pour la rotation du pouce (optionnel).

    Principes de sécurité :
    - AUCUN mouvement automatique au démarrage.
    - AUCUN mouvement automatique à l'arrêt, uniquement retour neutre.
    - Les commandes utilisateur (open/close ou boutons rotation) sont les seules qui font bouger.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        # ----------- Chargement configuration ----------- #
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

        # ----------- PCA9685 + ServoKit ----------- #
        self.kit = ServoKit(channels=16, address=address)
        self.kit.frequency = freq

        # ----------- Gestion alim servos (optionnelle) ----------- #
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

        # ----------- Config servos (par doigt) ----------- #
        self.servos_conf = self.config["servos"]

        # Servo dédié à la rotation du pouce (MG90S, mode angle)
        self.thumb_rot_name = "pouce_rotation"
        self.thumb_rot_angle: Optional[float] = None
        if self.thumb_rot_name in self.servos_conf:
            conf = self.servos_conf[self.thumb_rot_name]
            # On stocke l'angle courant (sera fixé au neutre dans _all_neutral)
            self.thumb_rot_angle = float(conf.get("angle_neutral", 90.0))

        # État logique par doigt : "open" ou "close"
        # Au démarrage, on suppose que la main est ouverte.
        self.state = {name: "open" for name in self.servos_conf}

        # Gestion des threads pour mouvements parallèles (servos continus)
        self._finger_threads: Dict[str, threading.Thread] = {}
        self._finger_locks = {name: threading.Lock() for name in self.servos_conf}
        self._stop_flags = {name: threading.Event() for name in self.servos_conf}

        # Étape 1 : Mettre tous les canaux au NEUTRE.
        # À ce moment-là tu dois avoir l'alim 5 V COUPÉE pour éviter tout choc.
        self._all_neutral()

        # IMPORTANT :
        #  - on NE touche PAS à l'alim 5 V ici (pas de enable_power()).
        #  - on NE fait NI open_hand() NI close_hand() automatiquement.

        # ----------- Gestion des signaux pour arrêt propre ----------- #
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
    # Bas niveau : écriture throttle / angle
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

    def _set_angle(self, channel: int, angle: float) -> None:
        """
        Positionne un servo angulaire (type MG90S) à un angle donné en degrés.
        On reste dans [0..180] car c'est la plage standard pour ServoKit.
        """
        angle = max(0.0, min(180.0, float(angle)))
        try:
            self.kit.servo[channel].angle = angle
        except Exception as e:
            print(f"[ERREUR] angle canal {channel} -> {angle}° : {e}")

    # ==================================================================
    # Neutres (servos continus + servo de pouce)
    # ==================================================================
    def _all_neutral(self) -> None:
        """
        Met tous les servos au neutre :
        - Servos continus : throttle = neutral
        - Servo angulaire de pouce : angle = angle_neutral (si configuré en mode "angle")
        """
        print("[ACTION] Mise de TOUS les servos au neutre...")
        for name, conf in self.servos_conf.items():
            channel = conf["channel"]

            # Servo angulaire (rotation pouce) en mode "angle"
            if name == self.thumb_rot_name and conf.get("mode", "continuous") == "angle":
                angle_neutral = float(conf.get("angle_neutral", 90.0))
                self.thumb_rot_angle = angle_neutral
                print(
                    f"[NEUTRE] Servo angulaire '{name}' canal {channel} -> {angle_neutral:.1f}°"
                )
                self._set_angle(channel, angle_neutral)
                continue

            # Servos continus
            neutral = conf.get("neutral", 0.0)
            print(
                f"[NEUTRE] Servo continu '{name}' canal {channel} -> throttle={neutral}"
            )
            self._set_throttle(channel, neutral)

        time.sleep(0.05)

    # ==================================================================
    # Mouvement d'un doigt (ouverture / fermeture) - servos continus
    # ==================================================================
    def _move_finger_blocking(self, name: str, action: str, force: bool = False) -> None:
        """
        Déplace un doigt en utilisant les durées calibrées.
        action = "open" ou "close".
        Mouvement BLOQUANT, puis retour neutre.
        Si le doigt est déjà dans l'état demandé -> aucun mouvement (sauf si force=True).
        """
        if name not in self.servos_conf:
            raise ValueError(f"Doigt inconnu : {name}")

        conf = self.servos_conf[name]

        # Sécurité : on ne passe pas ici pour un servo angulaire (pouce_rotation)
        if name == self.thumb_rot_name and conf.get("mode", "continuous") == "angle":
            print(f"[INFO] _move_finger_blocking ignoré pour servo angulaire '{name}'")
            return

        if not force and self.state.get(name) == action:
            return

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

    def _move_finger_thread(self, name: str, action: str, force: bool = False) -> None:
        """
        Wrapper thread-safe pour mouvement d'un doigt.
        Utilisé pour les mouvements parallèles.
        """
        with self._finger_locks[name]:
            try:
                self._move_finger_blocking(name, action, force=force)
            except Exception as e:
                print(f"[ERREUR] Thread doigt '{name}': {e}")

    # ==================================================================
    # API publique doigts (servos continus)
    # ==================================================================
    def open_finger(self, name: str, parallel: bool = False, force: bool = False) -> None:
        """Ouvre un doigt (servo continu)."""
        if parallel:
            self._start_finger_movement(name, "open", force=force)
        else:
            self._move_finger_blocking(name, "open", force=force)

    def close_finger(self, name: str, parallel: bool = False, force: bool = False) -> None:
        """Ferme un doigt (servo continu)."""
        if parallel:
            self._start_finger_movement(name, "close", force=force)
        else:
            self._move_finger_blocking(name, "close", force=force)

    def _start_finger_movement(self, name: str, action: str, force: bool = False) -> None:
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
            args=(name, action, force),
            daemon=True,
            name=f"finger_{name}_{action}",
        )
        self._finger_threads[name] = thread
        thread.start()

    def open_hand(self, parallel: bool = True, delay_between: float = 0.05) -> None:
        """
        Ouvre tous les doigts (servos continus).
        Le servo angulaire 'pouce_rotation' (exclude_from_global=true) est exclu.
        """
        print("[ACTION] Ouverture complète de la main...")
        if parallel:
            for name, conf in self.servos_conf.items():
                if conf.get("exclude_from_global", False):
                    continue
                self.open_finger(name, parallel=True)
            self._wait_all_movements()
        else:
            for name, conf in self.servos_conf.items():
                if conf.get("exclude_from_global", False):
                    continue
                self.open_finger(name, parallel=False)
                time.sleep(delay_between)

    def close_hand(self, parallel: bool = True, delay_between: float = 0.05) -> None:
        """
        Ferme tous les doigts (servos continus).
        Le servo angulaire 'pouce_rotation' (exclude_from_global=true) est exclu.
        """
        print("[ACTION] Fermeture complète de la main...")
        if parallel:
            for name, conf in self.servos_conf.items():
                if conf.get("exclude_from_global", False):
                    continue
                self.close_finger(name, parallel=True)
            self._wait_all_movements()
        else:
            for name, conf in self.servos_conf.items():
                if conf.get("exclude_from_global", False):
                    continue
                self.close_finger(name, parallel=False)
                time.sleep(delay_between)

    def _wait_all_movements(self, timeout: float = 5.0) -> None:
        """
        Attend que tous les threads de mouvement se terminent.
        """
        start = time.time()
        for name, thread in self._finger_threads.items():
            if thread.is_alive():
                remaining = max(0.1, timeout - (time.time() - start))
                thread.join(timeout=remaining)

    # ==================================================================
    # Servo rotation de pouce (MG90S angulaire)
    # ==================================================================
    def _set_thumb_angle(self, angle: float) -> None:
        """
        Applique un angle absolu au servo de rotation du pouce, en respectant
        la plage [angle_min ; angle_max] définie dans le JSON.
        """
        if self.thumb_rot_name not in self.servos_conf:
            return

        conf = self.servos_conf[self.thumb_rot_name]
        if conf.get("mode", "continuous") != "angle":
            return

        channel = conf["channel"]
        angle_min = float(conf.get("angle_min", 0.0))
        angle_max = float(conf.get("angle_max", 180.0))

        # Clamp dans la plage définie par la config
        angle = float(angle)
        angle = max(angle_min, min(angle_max, angle))

        self.thumb_rot_angle = angle
        print(f"[ACTION] Rotation pouce -> {angle:.1f}°")
        self._set_angle(channel, angle)

    def thumb_rotation_step(self, direction: int) -> None:
        """
        Fait tourner le pouce (MG90S) par petits pas angulaires.

        direction:
            > 0  -> sens +
            < 0  -> sens -
            = 0  -> ne fait rien

        L'amplitude de chaque pas est définie par angle_step dans le JSON.
        """
        if direction == 0:
            return

        if self.thumb_rot_name not in self.servos_conf:
            print("[WARN] Servo 'pouce_rotation' non configuré.")
            return

        conf = self.servos_conf[self.thumb_rot_name]
        if conf.get("mode", "continuous") != "angle":
            print("[WARN] Servo 'pouce_rotation' n'est pas en mode 'angle'.")
            return

        angle_min = float(conf.get("angle_min", 0.0))
        angle_max = float(conf.get("angle_max", 180.0))
        step = float(conf.get("angle_step", 1.0))

        if self.thumb_rot_angle is None:
            self.thumb_rot_angle = float(conf.get("angle_neutral", 90.0))

        delta = step if direction > 0 else -step
        new_angle = self.thumb_rot_angle + delta
        new_angle = max(angle_min, min(angle_max, new_angle))

        print(f"[ACTION] Rotation pouce -> {new_angle:.1f}° (delta={delta:+.1f}°)")
        self._set_thumb_angle(new_angle)

    def thumb_rotation_reset(self) -> None:
        """
        Ramène le servo de rotation du pouce à l'angle neutre défini dans la config.
        """
        if self.thumb_rot_name not in self.servos_conf:
            print("[WARN] Servo 'pouce_rotation' non configuré.")
            return

        conf = self.servos_conf[self.thumb_rot_name]
        if conf.get("mode", "continuous") != "angle":
            print("[WARN] Servo 'pouce_rotation' n'est pas en mode 'angle'.")
            return

        angle_neutral = float(conf.get("angle_neutral", 90.0))
        print(f"[ACTION] Reset rotation pouce -> {angle_neutral:.1f}°")
        self._set_thumb_angle(angle_neutral)

    def thumb_from_value(self, value: float) -> None:
        """
        Mappe une valeur 0..1 (par ex. 'pouce_articulation' venant du tracking)
        sur la rotation du pouce :

        - value = 0.0 -> angle_max (pouce ouvert)
        - value = 1.0 -> angle_min (pouce fermé / pince)

        Cela permet un mouvement fluide couplé au reste des doigts.
        """
        if self.thumb_rot_name not in self.servos_conf:
            return

        conf = self.servos_conf[self.thumb_rot_name]
        if conf.get("mode", "continuous") != "angle":
            return

        try:
            v = float(value)
        except (TypeError, ValueError):
            return

        v = max(0.0, min(1.0, v))

        angle_min = float(conf.get("angle_min", 0.0))   # fermé
        angle_max = float(conf.get("angle_max", 180.0))  # ouvert

        # v = 0 -> angle_max (ouvert), v = 1 -> angle_min (fermé)
        angle = angle_max - v * (angle_max - angle_min)
        self._set_thumb_angle(angle)

    # ==================================================================
    # STOP GLOBAL
    # ==================================================================
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

        # Mettre tous les servos au neutre (y compris rotation pouce)
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
