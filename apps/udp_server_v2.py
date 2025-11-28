# apps/udp_server_v2.py

import sys
import json
import socket
import time
from pathlib import Path

# Ajout du dossier V2.0 dans le PYTHONPATH
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.hand_controller import HandController


UDP_IP = "0.0.0.0"
UDP_PORT = 5005

# Seuils d'hystérésis pour ouvrir / fermer (0.0 = ouvert, 1.0 = fermé)
OPEN_THRESHOLD = 0.30    # en-dessous -> ouvrir
CLOSE_THRESHOLD = 0.70   # au-dessus -> fermer

# Timeouts de sécurité
LOST_TIMEOUT = 1.0       # après 1 s sans paquet -> main ouverte + neutre

FINGERS = [
    "pouce_articulation",
    "index",
    "majeur",
    "annulaire_auriculaire",
]


def main():
    print("===== SERVEUR UDP MAIN ROBOTIQUE V2.0 =====")
    print(f"Écoute sur {UDP_IP}:{UDP_PORT}")
    print("")
    print("IMPORTANT :")
    print("  1) ALIM 5V DES SERVOS COUPÉE avant de lancer ce script.")
    print("  2) Main en position OUVERTE manuellement (doigts tendus).")
    print("  3) Puis lancer ce script sur le Raspberry Pi.")
    print("===================================================")

    controller = HandController()  # met les PWM au neutre uniquement

    print("\n[INFO] Les servos sont au NEUTRE côté PCA9685.")
    input("[ENTRÉE] quand tu es prêt à ALLUMER l'alim 5V servos... ")

    # Si tu rajoutes plus tard un MOSFET/relais sur GPIO pour le 5 V,
    # tu pourras activer ici :
    # controller.enable_power()

    print("\n[INFO] Tu peux maintenant allumer l'alimentation 5V des servos.")
    input("[ENTRÉE] après avoir allumé l'alim et vérifié que rien ne bouge... ")

    # Initialisation UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(0.2)  # on ne bloque jamais trop longtemps

    print("\n[READY] Serveur UDP prêt. Envoie des paquets depuis hand_tracker.py")
    print("       Ctrl+C pour arrêter proprement.\n")

    # État logique local des doigts
    logical_state = {name: "open" for name in FINGERS}

    # Watchdog main visible / perdue
    last_packet_time = time.time()
    hand_visible = False  # passe à True dès qu'on reçoit des paquets "valides"
    safe_open_done = False  # pour éviter de répéter open_hand en boucle

    try:
        while True:
            now = time.time()

            # --------- Watchdog "perte de main / perte de tracking" ---------
            if hand_visible and (now - last_packet_time > LOST_TIMEOUT):
                print(
                    f"[WATCHDOG] Plus de paquets depuis {now - last_packet_time:.2f}s -> "
                    "ouverture de sécurité + neutre."
                )
                try:
                    controller.open_hand()
                    controller.stop_all()
                except Exception as e:
                    print(f"[ERREUR] Pendant l'ouverture de sécurité : {e}")
                # On considère la main comme "non visible"
                hand_visible = False
                safe_open_done = True
                # On remet l'état logique à "open" pour tout le monde
                for name in logical_state:
                    logical_state[name] = "open"

            # --------- Lecture UDP (non bloquante longue) ---------
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                # Pas de paquet cette itération
                time.sleep(0.01)
                continue
            except Exception as e:
                print(f"[ERREUR] recvfrom : {e}")
                time.sleep(0.05)
                continue

            raw = data.decode("utf-8", errors="ignore").strip()
            if not raw:
                continue

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                print(f"[WARN] Paquet non JSON : {raw!r}")
                continue

            now = time.time()
            last_packet_time = now

            # Certains hand_tracker envoient parfois un flag explicite
            # ex: {"visible": false} ou {"tracking": false}
            explicit_not_visible = False
            if isinstance(msg, dict):
                if str(msg.get("visible", "")).lower() in ("false", "0", "no"):
                    explicit_not_visible = True
                if str(msg.get("tracking", "")).lower() in ("false", "0", "no"):
                    explicit_not_visible = True

            if explicit_not_visible:
                # Main explicitement perdue -> même logique que watchdog
                if hand_visible:
                    print("[UDP] Flag 'visible=false' ou 'tracking=false' -> ouverture sécurité")
                    try:
                        controller.open_hand()
                        controller.stop_all()
                    except Exception as e:
                        print(f"[ERREUR] Pendant l'ouverture de sécurité (flag) : {e}")
                    hand_visible = False
                    safe_open_done = True
                    for name in logical_state:
                        logical_state[name] = "open"
                # On ne traite pas plus ce paquet
                continue

            # Si on arrive ici, on considère que la main est "visible"
            hand_visible = True
            safe_open_done = False

            # Traitement des doigts
            for finger in FINGERS:
                if finger not in msg:
                    continue

                try:
                    v = float(msg[finger])
                except (TypeError, ValueError):
                    continue

                # Clamp 0.0 - 1.0
                if v < 0.0:
                    v = 0.0
                elif v > 1.0:
                    v = 1.0

                current_state = logical_state.get(finger, "open")

                # Hystérésis : on ne change d'état que si on dépasse un seuil
                # Utilisation de parallel=True pour des mouvements fluides et simultanés
                if v > CLOSE_THRESHOLD and current_state != "close":
                    print(f"[UDP] {finger}: v={v:.2f} -> CLOSE")
                    controller.close_finger(finger, parallel=True)
                    logical_state[finger] = "close"

                elif v < OPEN_THRESHOLD and current_state != "open":
                    print(f"[UDP] {finger}: v={v:.2f} -> OPEN")
                    controller.open_finger(finger, parallel=True)
                    logical_state[finger] = "open"

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[CTRL+C] Arrêt demandé par l'utilisateur.")
    finally:
        # Séquence d'arrêt : main ouverte + neutre + coupure alim dans shutdown()
        try:
            # On force une fois l'ouverture en sortie si ce n'était pas déjà fait
            if not safe_open_done:
                controller.open_hand()
                controller.stop_all()
        except Exception as e:
            print(f"[AVERTISSEMENT] Erreur pendant l'ouverture finale : {e}")

        controller.shutdown()
        sock.close()
        print("[FIN] Serveur UDP V2.0 arrêté proprement.")
        

if __name__ == "__main__":
    main()
