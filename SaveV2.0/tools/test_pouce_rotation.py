# tools/test_pouce_rotation.py
"""
Test très prudent du 2e servo du pouce (MG90S sur canal 3, 'pouce_rotation').

ATTENTION :
- Lancer ce script SEUL (neuro_dashboardV2.py arrêté).
- La main doit être posée, rien qui force.
- Les déplacements sont très petits autour de la position neutre.
"""

import json
import time
from pathlib import Path

import board
import busio
from adafruit_pca9685 import PCA9685

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "config" / "servos_v2.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def norm_to_duty(norm: float) -> int:
    """Convertit un flottant [0,1] en duty_cycle 16 bits."""
    norm = max(0.0, min(1.0, float(norm)))
    return int(norm * 0xFFFF)


def main():
    cfg = load_config()
    pca_cfg = cfg.get("pca9685", {})
    servos = cfg.get("servos", {})

    if "pouce_rotation" not in servos:
        raise SystemExit("ERREUR : servo 'pouce_rotation' absent de servos_v2.json")

    s_cfg = servos["pouce_rotation"]
    channel = int(s_cfg["channel"])
    neutral = float(s_cfg["neutral"])

    # marge très petite autour du neutre pour les premiers tests
    STEP_SMALL = 0.02   # déplacement très léger
    STEP_BIG = 0.05     # déplacement un peu plus visible, à utiliser après vérif
    MIN_NORM = 0.0
    MAX_NORM = 1.0

    print("=== TEST POUCE ROTATION (MG90S canal 3) ===")
    print("Canal PCA9685 :", channel)
    print(f"Neutral (config) : {neutral:.3f}")
    print("Commandes clavier :")
    print("  n : aller au neutre")
    print("  + : tourner un peu dans un sens (+0.02)")
    print("  - : tourner un peu dans l'autre sens (-0.02)")
    print("  > : mouvement plus grand +0.05 (à n'utiliser qu'après vérification)")
    print("  < : mouvement plus grand -0.05")
    print("  q : quitter (met le servo à 0 / OFF)")
    print()

    # Initialisation I2C + PCA
    i2c = busio.I2C(board.SCL, board.SDA)
    pca = PCA9685(i2c, address=pca_cfg.get("address", 0x40))
    pca.frequency = pca_cfg.get("frequency", 50)

    try:
        # On coupe tout au départ (évite les servos qui partent tout seuls)
        print("[INFO] Mise à 0 de tous les canaux PCA au démarrage...")
        for ch in range(16):
            pca.channels[ch].duty_cycle = 0
        time.sleep(0.5)

        # On ne pilote que NOTRE servo ensuite
        current = neutral
        print("[INFO] Positionnement initial au neutre très lentement...")
        pca.channels[channel].duty_cycle = norm_to_duty(current)
        time.sleep(1.0)

        while True:
            cmd = input("Commande (n/+/-/>/</q) : ").strip().lower()

            if cmd == "q":
                print("[INFO] Arrêt, mise à 0 du canal.")
                pca.channels[channel].duty_cycle = 0
                break

            if cmd == "n":
                current = neutral
            elif cmd == "+":
                current += STEP_SMALL
            elif cmd == "-":
                current -= STEP_SMALL
            elif cmd == ">":
                current += STEP_BIG
            elif cmd == "<":
                current -= STEP_BIG
            else:
                print("Commande inconnue.")
                continue

            # bornes de sécurité
            current = max(MIN_NORM, min(MAX_NORM, current))
            print(f" -> position demandée : {current:.3f}")
            pca.channels[channel].duty_cycle = norm_to_duty(current)
            # petite pause pour voir le mouvement
            time.sleep(0.4)

    finally:
        # sécurité : on coupe ce canal au cas où
        pca.channels[channel].duty_cycle = 0
        pca.deinit()
        print("[INFO] PCA9685 désactivé, canal remis à 0.")


if __name__ == "__main__":
    main()
