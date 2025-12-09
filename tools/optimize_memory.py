#!/usr/bin/env python3
# --------------------------------------------------------------------
# SCRIPT D'OPTIMISATION MÉMOIRE AUTOMATIQUE
# --------------------------------------------------------------------
"""
Applique des optimisations pour réduire la consommation RAM du système.

Actions :
- Nettoie le cache système
- Libère la RAM inutilisée
- Identifie et propose de tuer les processus gourmands
- Configure le swap si absent
"""

import psutil
import os
import sys
import subprocess
import platform


def get_current_memory_percent():
    """Retourne le pourcentage de RAM utilisée."""
    return psutil.virtual_memory().percent


def clear_system_cache():
    """
    Nettoie le cache système (Linux uniquement).
    Nécessite les droits sudo.
    """
    if platform.system() != 'Linux':
        print("⚠️ Nettoyage cache disponible uniquement sur Linux")
        return False
    
    try:
        print("🧹 Nettoyage du cache système...")
        
        # sync + drop_caches (nécessite sudo)
        # On propose la commande à l'utilisateur
        print("\n💡 Exécuter cette commande pour nettoyer le cache :")
        print("   sudo sync")
        print("   echo 3 | sudo tee /proc/sys/vm/drop_caches")
        print()
        
        return True
    
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage cache : {e}")
        return False


def kill_process_by_pid(pid, name):
    """
    Tue un processus par son PID après confirmation.
    
    Args:
        pid: PID du processus.
        name: Nom du processus.
    
    Returns:
        bool: True si tué, False sinon.
    """
    try:
        proc = psutil.Process(pid)
        
        # Demander confirmation
        response = input(f"Tuer le processus '{name}' (PID {pid}) ? [y/N] : ")
        
        if response.lower() == 'y':
            proc.terminate()
            proc.wait(timeout=3)
            print(f"✅ Processus {name} (PID {pid}) terminé")
            return True
        else:
            print(f"⏭️  Processus {name} (PID {pid}) conservé")
            return False
    
    except psutil.NoSuchProcess:
        print(f"⚠️ Processus {pid} n'existe plus")
        return False
    
    except Exception as e:
        print(f"❌ Erreur lors de la terminaison de {pid} : {e}")
        return False


def identify_killable_processes():
    """
    Identifie les processus qui peuvent être tués sans risque.
    
    Exclut :
    - Processus système critiques
    - Le processus Python actuel
    - Les processus avec PID < 1000
    
    Returns:
        list: Liste de processus tuables triés par consommation RAM.
    """
    current_pid = os.getpid()
    killable = []
    
    # Processus à ne JAMAIS tuer
    critical_processes = [
        'systemd', 'init', 'sshd', 'ssh', 'NetworkManager',
        'dbus', 'kernel', 'kworker', 'ksoftirqd', 'migration'
    ]
    
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent']):
        try:
            info = proc.info
            pid = info['pid']
            name = info['name']
            
            # Ignorer processus critiques
            if pid == current_pid:
                continue
            if pid < 1000:  # Processus système
                continue
            if any(crit in name.lower() for crit in critical_processes):
                continue
            
            mem_mb = info['memory_info'].rss / (1024 * 1024)
            mem_percent = info.get('memory_percent', 0)
            
            # Ne garder que si > 50 MB
            if mem_mb > 50:
                killable.append({
                    'pid': pid,
                    'name': name,
                    'memory_mb': mem_mb,
                    'memory_percent': mem_percent
                })
        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Trier par consommation RAM décroissante
    killable.sort(key=lambda x: x['memory_mb'], reverse=True)
    
    return killable


def optimize_swap():
    """
    Vérifie et propose d'optimiser le swap.
    
    Returns:
        bool: True si swap OK, False sinon.
    """
    swap = psutil.swap_memory()
    
    print("\n💾 ANALYSE DU SWAP")
    print("-" * 60)
    
    if swap.total == 0:
        print("❌ AUCUN SWAP CONFIGURÉ")
        print("\n💡 Pour créer un swap de 2GB sur Linux :")
        print("   sudo fallocate -l 2G /swapfile")
        print("   sudo chmod 600 /swapfile")
        print("   sudo mkswap /swapfile")
        print("   sudo swapon /swapfile")
        print("   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab")
        print()
        return False
    
    else:
        total_gb = swap.total / (1024**3)
        used_gb = swap.used / (1024**3)
        
        print(f"✅ Swap configuré : {total_gb:.2f} GB")
        print(f"   Utilisé : {used_gb:.2f} GB ({swap.percent:.1f}%)")
        
        if total_gb < 2:
            print(f"⚠️ Swap trop petit (< 2GB), augmenter recommandé")
        
        if swap.percent > 50:
            print(f"⚠️ Swap utilisé à {swap.percent:.1f}% - Système ralenti")
            print("   → Ajouter de la RAM physique recommandé")
        
        print()
        return True


def suggest_dashboard_optimizations():
    """
    Propose des optimisations spécifiques au dashboard NEURO-HAND.
    """
    print("\n⚙️ OPTIMISATIONS DASHBOARD NEURO-HAND")
    print("-" * 60)
    print()
    print("✂️ 1. Réduire intervalle de mise à jour UI")
    print("   Fichier : config.yaml")
    print("   Modifier : update_interval: 0.05 → 0.10 (ou 0.15)")
    print("   Gain attendu : ~5-10% RAM")
    print()
    
    print("🎨 2. Désactiver effets visuels lourds (hand_tracker.py)")
    print("   ENABLE_HAND_MASK = False")
    print("   GLOW_ENABLED = False")
    print("   SCANLINE_ENABLED = False")
    print("   Gain attendu : ~10-15% RAM")
    print()
    
    print("📹 3. Réduire qualité streaming vidéo")
    print("   hand_tracker.py ligne 90 :")
    print("   JPEG_QUALITY = 75 → 60")
    print("   Gain attendu : ~5% RAM")
    print()
    
    print("🤖 4. MediaPipe modèle léger")
    print("   hand_tracker.py ligne 130 :")
    print("   model_complexity=1 → 0")
    print("   Gain attendu : ~15-20% RAM")
    print()
    
    print("🌐 5. Fermer onglets navigateur inutilisés")
    print("   Garder seulement le dashboard ouvert")
    print("   Gain attendu : ~20-30% RAM si Chrome/Firefox fermés")
    print()
    
    print("🔄 6. Redémarrer le dashboard périodiquement")
    print("   Créer un cron job pour redémarrer toutes les 6h")
    print("   Évite les fuites mémoire lentes")
    print()


def run_optimization():
    """
    Exécute le processus d'optimisation complet.
    """
    print("=" * 70)
    print("⚡ OPTIMISATION MÉMOIRE - NEURO-HAND V2.1")
    print("=" * 70)
    print()
    
    # État initial
    initial_percent = get_current_memory_percent()
    print(f"📊 RAM actuelle : {initial_percent:.1f}%")
    print()
    
    # ================================================================
    # ÉTAPE 1 : Analyser le swap
    # ================================================================
    optimize_swap()
    
    # ================================================================
    # ÉTAPE 2 : Nettoyer le cache (si Linux)
    # ================================================================
    clear_system_cache()
    
    # ================================================================
    # ÉTAPE 3 : Identifier processus tuables
    # ================================================================
    print("\n🔍 IDENTIFICATION DES PROCESSUS GOURMANDS")
    print("-" * 60)
    
    killable = identify_killable_processes()
    
    if not killable:
        print("✅ Aucun processus gourmand non-essentiel détecté")
    else:
        print(f"Trouvé {len(killable)} processus > 50 MB :\n")
        print(f"{'PID':<8} {'NOM':<30} {'RAM (MB)':<12} {'%':<8}")
        print("-" * 60)
        
        for proc in killable[:10]:  # Top 10
            print(f"{proc['pid']:<8} {proc['name']:<30} {proc['memory_mb']:<12.2f} {proc['memory_percent']:<8.2f}")
        
        print()
        
        # Demander si on veut tuer des processus
        response = input("Voulez-vous tuer certains processus ? [y/N] : ")
        
        if response.lower() == 'y':
            print("\nProcessus à tuer (entrez les PIDs séparés par des espaces, ou 'all' pour tout) :")
            pids_input = input("PIDs : ")
            
            if pids_input.lower() == 'all':
                for proc in killable[:5]:  # Seulement top 5 pour sécurité
                    kill_process_by_pid(proc['pid'], proc['name'])
            else:
                try:
                    pids = [int(p.strip()) for p in pids_input.split()]
                    
                    for pid in pids:
                        # Trouver le nom du processus
                        proc_info = next((p for p in killable if p['pid'] == pid), None)
                        
                        if proc_info:
                            kill_process_by_pid(pid, proc_info['name'])
                        else:
                            print(f"⚠️ PID {pid} non trouvé dans la liste")
                
                except ValueError:
                    print("❌ Format de PID invalide")
    
    # ================================================================
    # ÉTAPE 4 : Proposer optimisations dashboard
    # ================================================================
    suggest_dashboard_optimizations()
    
    # ================================================================
    # RÉSULTAT FINAL
    # ================================================================
    print("\n" + "=" * 70)
    
    final_percent = get_current_memory_percent()
    
    print(f"📊 RAM finale : {final_percent:.1f}%")
    
    if final_percent < initial_percent:
        saved = initial_percent - final_percent
        print(f"✅ RAM libérée : {saved:.1f}%")
    else:
        print(f"⚠️ Pas de réduction détectée (variations normales)")
    
    print()
    print("💡 PROCHAINES ÉTAPES :")
    print("   1. Appliquer les optimisations dashboard suggérées")
    print("   2. Redémarrer le système si RAM > 85%")
    print("   3. Envisager ajout de RAM physique si problème persiste")
    print()
    print("=" * 70)


# ================================================================
# POINT D'ENTRÉE
# ================================================================
if __name__ == "__main__":
    try:
        run_optimization()
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Optimisation interrompue par l'utilisateur.")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Erreur lors de l'optimisation : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
