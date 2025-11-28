#!/usr/bin/env python3
# apps/demo_parallel_movements.py

"""
Démonstration des mouvements parallèles (fluides) vs séquentiels.
Compare l'ancien comportement avec le nouveau.
"""

import sys
import time
from pathlib import Path

# Ajout du dossier V2.0 dans le PYTHONPATH
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.hand_controller import HandController


def main():
    print("=" * 60)
    print("DÉMONSTRATION : MOUVEMENTS PARALLÈLES (FLUIDES)")
    print("=" * 60)
    print("\nCe script compare les modes séquentiels et parallèles.")
    print("\nIMPORTANT :")
    print("  1) ALIM 5V DES SERVOS COUPÉE avant de lancer ce script.")
    print("  2) Main en position OUVERTE manuellement (doigts tendus).")
    print("=" * 60)
    
    controller = HandController()
    
    print("\n[INFO] Les servos sont au NEUTRE côté PCA9685.")
    input("[ENTRÉE] quand tu es prêt à ALLUMER l'alim 5V servos... ")
    
    print("\n[INFO] Tu peux maintenant allumer l'alimentation 5V des servos.")
    input("[ENTRÉE] après avoir allumé l'alim et vérifié que rien ne bouge... ")
    
    try:
        while True:
            print("\n" + "=" * 60)
            print("MENU DE DÉMONSTRATION")
            print("=" * 60)
            print("1. Fermeture SÉQUENTIELLE (ancien mode, lent)")
            print("2. Fermeture PARALLÈLE (nouveau mode, rapide et fluide)")
            print("3. Ouverture SÉQUENTIELLE")
            print("4. Ouverture PARALLÈLE")
            print("5. Test de doigts individuels en parallèle")
            print("6. Comparaison chronométrée (séquentiel vs parallèle)")
            print("0. STOP ALL (arrêt d'urgence)")
            print("q. Quitter")
            print("=" * 60)
            
            choice = input("\nChoix : ").strip().lower()
            
            if choice == "1":
                print("\n[TEST] Fermeture SÉQUENTIELLE (lente)...")
                start = time.time()
                controller.close_hand(parallel=False)
                elapsed = time.time() - start
                print(f"✓ Terminé en {elapsed:.2f}s")
                
            elif choice == "2":
                print("\n[TEST] Fermeture PARALLÈLE (rapide et fluide)...")
                start = time.time()
                controller.close_hand(parallel=True)
                elapsed = time.time() - start
                print(f"✓ Terminé en {elapsed:.2f}s")
                
            elif choice == "3":
                print("\n[TEST] Ouverture SÉQUENTIELLE (lente)...")
                start = time.time()
                controller.open_hand(parallel=False)
                elapsed = time.time() - start
                print(f"✓ Terminé en {elapsed:.2f}s")
                
            elif choice == "4":
                print("\n[TEST] Ouverture PARALLÈLE (rapide et fluide)...")
                start = time.time()
                controller.open_hand(parallel=True)
                elapsed = time.time() - start
                print(f"✓ Terminé en {elapsed:.2f}s")
                
            elif choice == "5":
                print("\n[TEST] Doigts individuels en parallèle...")
                print("Les 4 doigts vont se fermer en MÊME TEMPS !")
                input("Appuie sur ENTRÉE pour démarrer...")
                
                # Lancer tous les doigts en parallèle
                controller.close_finger("pouce_articulation", parallel=True)
                controller.close_finger("index", parallel=True)
                controller.close_finger("majeur", parallel=True)
                controller.close_finger("annulaire_auriculaire", parallel=True)
                
                print("✓ Mouvements lancés !")
                time.sleep(0.5)  # Laisser un peu de temps
                
                print("\nMaintenant, ouverture en parallèle...")
                controller.open_finger("pouce_articulation", parallel=True)
                controller.open_finger("index", parallel=True)
                controller.open_finger("majeur", parallel=True)
                controller.open_finger("annulaire_auriculaire", parallel=True)
                print("✓ Terminé !")
                
            elif choice == "6":
                print("\n[TEST] COMPARAISON CHRONOMÉTRÉE")
                print("-" * 60)
                
                # D'abord ouvrir la main
                print("Préparation : ouverture...")
                controller.open_hand(parallel=True)
                time.sleep(1)
                
                # Test séquentiel
                print("\n1️⃣  MODE SÉQUENTIEL (ancien)...")
                start = time.time()
                controller.close_hand(parallel=False)
                time_seq = time.time() - start
                print(f"   Temps : {time_seq:.2f}s")
                time.sleep(1)
                
                # Réouvrir
                controller.open_hand(parallel=True)
                time.sleep(1)
                
                # Test parallèle
                print("\n2️⃣  MODE PARALLÈLE (nouveau)...")
                start = time.time()
                controller.close_hand(parallel=True)
                time_par = time.time() - start
                print(f"   Temps : {time_par:.2f}s")
                
                # Résultats
                print("\n" + "=" * 60)
                print("RÉSULTATS DE LA COMPARAISON")
                print("=" * 60)
                print(f"Séquentiel : {time_seq:.2f}s")
                print(f"Parallèle  : {time_par:.2f}s")
                if time_seq > time_par:
                    gain = ((time_seq - time_par) / time_seq) * 100
                    print(f"\n✓ Gain de performance : {gain:.1f}% plus rapide !")
                print("=" * 60)
                
            elif choice == "0":
                print("\n[EMERGENCY] STOP ALL !")
                controller.stop_all()
                print("✓ Tous les servos sont au neutre.")
                
            elif choice == "q":
                print("\n[INFO] Sortie du programme...")
                break
                
            else:
                print("[ERREUR] Choix invalide.")
                
    except KeyboardInterrupt:
        print("\n[CTRL+C] Arrêt demandé.")
    finally:
        print("\n[SHUTDOWN] Arrêt propre...")
        controller.shutdown()
        print("✓ Programme terminé.")


if __name__ == "__main__":
    main()
