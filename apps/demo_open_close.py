# apps/demo_open_close.py

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import time
from core.hand_controller import HandController


def main():
    print("===== DEMO MAIN ROBOTIQUE V2.0 (SERVOS 360°) =====")
    print("IMPORTANT :")
    print("  1) Assure-toi que l'ALIM 5V DES SERVOS EST COUPÉE avant de lancer ce script.")
    print("  2) Mets la main en position OUVERTE manuellement (doigts tendus).")
    print("  3) Lance ensuite ce script.")
    print("===================================================")

    controller = HandController()  # met seulement les PWM au neutre

    print("\n[INFO] Les servos sont au NEUTRE. Tu peux maintenant allumer l'alim 5V.")
    input("[ENTRÉE] quand l'alim 5V est allumée et stable... ")

    # Si tu as câblé un MOSFET/relais sur un GPIO, tu peux activer ici :
    # controller.enable_power()

    print("\nCommandes :")
    print("  o  -> ouvrir complètement la main")
    print("  f  -> fermer complètement la main")
    print("  s  -> stop (neutre sur tous les servos)")
    print("  q  -> quitter proprement")
    print("===================================================")

    try:
        while True:
            cmd = input("Commande (o/f/s/q) : ").strip().lower()
            if cmd == "o":
                controller.open_hand()
            elif cmd == "f":
                controller.close_hand()
            elif cmd == "s":
                controller.stop_all()
            elif cmd == "q":
                break
            else:
                print("Commande inconnue. Utiliser o/f/s/q.")
            time.sleep(0.1)
    finally:
        controller.shutdown()


if __name__ == "__main__":
    main()
