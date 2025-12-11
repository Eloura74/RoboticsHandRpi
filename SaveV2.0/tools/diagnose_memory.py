#!/usr/bin/env python3
# --------------------------------------------------------------------
# SCRIPT DE DIAGNOSTIC MÉMOIRE
# --------------------------------------------------------------------
"""
Analyse détaillée de la consommation mémoire du système.

Identifie :
- Processus consommant le plus de RAM
- Fuites mémoire potentielles
- État du swap
- Recommandations d'optimisation
"""

import psutil
import os
import sys
from collections import defaultdict


def format_bytes(bytes_value):
    """
    Formate une valeur en bytes en unité lisible (KB, MB, GB).
    
    Args:
        bytes_value: Valeur en bytes.
    
    Returns:
        str: Chaîne formatée (ex: "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"


def get_memory_info():
    """
    Récupère les informations mémoire système complètes.
    
    Returns:
        dict: Dictionnaire avec toutes les métriques mémoire.
    """
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        'total': mem.total,
        'available': mem.available,
        'used': mem.used,
        'percent': mem.percent,
        'free': mem.free,
        'swap_total': swap.total,
        'swap_used': swap.used,
        'swap_percent': swap.percent,
    }


def get_top_processes(n=10):
    """
    Récupère les N processus consommant le plus de RAM.
    
    Args:
        n: Nombre de processus à retourner.
    
    Returns:
        list: Liste de tuples (pid, name, memory_mb, percent).
    """
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent']):
        try:
            info = proc.info
            mem_mb = info['memory_info'].rss / (1024 * 1024)  # Convertir en MB
            mem_percent = info.get('memory_percent', 0)
            
            processes.append({
                'pid': info['pid'],
                'name': info['name'],
                'memory_mb': mem_mb,
                'memory_percent': mem_percent
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Trier par consommation mémoire décroissante
    processes.sort(key=lambda x: x['memory_mb'], reverse=True)
    
    return processes[:n]


def identify_memory_hogs():
    """
    Identifie les catégories de processus gourmands.
    
    Returns:
        dict: Catégories et leur consommation totale.
    """
    categories = defaultdict(float)
    
    for proc in psutil.process_iter(['name', 'memory_info']):
        try:
            name = proc.info['name'].lower()
            mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
            
            # Catégorisation
            if 'python' in name:
                categories['Python processes'] += mem_mb
            elif 'chrome' in name or 'firefox' in name or 'edge' in name:
                categories['Web browsers'] += mem_mb
            elif 'code' in name or 'vscode' in name:
                categories['IDE (VSCode)'] += mem_mb
            elif 'node' in name:
                categories['Node.js'] += mem_mb
            else:
                categories['Other'] += mem_mb
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return dict(categories)


def check_swap():
    """
    Vérifie l'état du swap et retourne des recommandations.
    
    Returns:
        dict: Informations sur le swap + recommandations.
    """
    swap = psutil.swap_memory()
    
    recommendations = []
    
    if swap.total == 0:
        recommendations.append("⚠️ CRITICAL: Aucun swap configuré ! Créer un fichier swap.")
    elif swap.total < 2 * 1024 * 1024 * 1024:  # < 2GB
        recommendations.append("⚠️ WARNING: Swap trop petit (< 2GB). Augmenter la taille.")
    
    if swap.percent > 50:
        recommendations.append("⚠️ WARNING: Swap utilisé à plus de 50%. Système ralenti.")
    
    return {
        'total': swap.total,
        'used': swap.used,
        'percent': swap.percent,
        'recommendations': recommendations
    }


def generate_recommendations(mem_info):
    """
    Génère des recommandations basées sur l'analyse mémoire.
    
    Args:
        mem_info: Dictionnaire des informations mémoire.
    
    Returns:
        list: Liste de recommandations.
    """
    recommendations = []
    
    percent = mem_info['percent']
    
    if percent > 90:
        recommendations.append("🔴 CRITICAL: RAM > 90%")
        recommendations.append("   → Redémarrer le système immédiatement")
        recommendations.append("   → Fermer les applications non essentielles")
        recommendations.append("   → Augmenter la RAM physique si possible")
    
    elif percent > 80:
        recommendations.append("🟠 WARNING: RAM > 80%")
        recommendations.append("   → Fermer les processus inutiles")
        recommendations.append("   → Vérifier les fuites mémoire")
    
    elif percent > 70:
        recommendations.append("🟡 CAUTION: RAM > 70%")
        recommendations.append("   → Surveiller la consommation")
    
    else:
        recommendations.append("🟢 OK: RAM < 70%")
    
    # Recommandations spécifiques au projet
    recommendations.append("\n💡 OPTIMISATIONS NEURO-HAND:")
    recommendations.append("   1. Réduire qualité streaming vidéo (JPEG quality)")
    recommendations.append("   2. Désactiver effets visuels lourds (glow, scanlines)")
    recommendations.append("   3. Augmenter intervalle de mise à jour UI (50ms → 100ms)")
    recommendations.append("   4. Utiliser MediaPipe model_complexity=0")
    recommendations.append("   5. Fermer onglets navigateur inutilisés")
    
    return recommendations


def print_report():
    """
    Affiche un rapport complet de diagnostic mémoire.
    """
    print("=" * 70)
    print("🔍 DIAGNOSTIC MÉMOIRE - NEURO-HAND V2.1")
    print("=" * 70)
    print()
    
    # ================================================================
    # SECTION 1 : Vue d'ensemble mémoire
    # ================================================================
    mem_info = get_memory_info()
    
    print("📊 VUE D'ENSEMBLE MÉMOIRE")
    print("-" * 70)
    print(f"RAM Totale        : {format_bytes(mem_info['total'])}")
    print(f"RAM Utilisée      : {format_bytes(mem_info['used'])} ({mem_info['percent']:.1f}%)")
    print(f"RAM Disponible    : {format_bytes(mem_info['available'])}")
    print(f"RAM Libre         : {format_bytes(mem_info['free'])}")
    print()
    
    # Barre de progression visuelle
    bar_length = 50
    filled = int(bar_length * mem_info['percent'] / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    if mem_info['percent'] > 90:
        color = '🔴'
    elif mem_info['percent'] > 80:
        color = '🟠'
    elif mem_info['percent'] > 70:
        color = '🟡'
    else:
        color = '🟢'
    
    print(f"{color} [{bar}] {mem_info['percent']:.1f}%")
    print()
    
    # ================================================================
    # SECTION 2 : Swap
    # ================================================================
    swap_info = check_swap()
    
    print("💾 ÉTAT DU SWAP")
    print("-" * 70)
    
    if swap_info['total'] > 0:
        print(f"Swap Totale       : {format_bytes(swap_info['total'])}")
        print(f"Swap Utilisée     : {format_bytes(swap_info['used'])} ({swap_info['percent']:.1f}%)")
    else:
        print("⚠️ AUCUN SWAP CONFIGURÉ")
    
    print()
    
    if swap_info['recommendations']:
        for rec in swap_info['recommendations']:
            print(rec)
        print()
    
    # ================================================================
    # SECTION 3 : Top processus gourmands
    # ================================================================
    print("🔝 TOP 10 PROCESSUS GOURMANDS EN RAM")
    print("-" * 70)
    print(f"{'PID':<8} {'NOM':<30} {'RAM (MB)':<12} {'%':<8}")
    print("-" * 70)
    
    top_processes = get_top_processes(10)
    
    for proc in top_processes:
        print(f"{proc['pid']:<8} {proc['name']:<30} {proc['memory_mb']:<12.2f} {proc['memory_percent']:<8.2f}")
    
    print()
    
    # ================================================================
    # SECTION 4 : Consommation par catégorie
    # ================================================================
    print("📦 CONSOMMATION PAR CATÉGORIE")
    print("-" * 70)
    
    categories = identify_memory_hogs()
    categories_sorted = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    
    for category, mem_mb in categories_sorted:
        if mem_mb > 10:  # Afficher seulement si > 10 MB
            percent = (mem_mb * 1024 * 1024) / mem_info['total'] * 100
            print(f"{category:<30} : {mem_mb:>8.2f} MB  ({percent:.1f}%)")
    
    print()
    
    # ================================================================
    # SECTION 5 : Recommandations
    # ================================================================
    print("💡 RECOMMANDATIONS")
    print("-" * 70)
    
    recommendations = generate_recommendations(mem_info)
    
    for rec in recommendations:
        print(rec)
    
    print()
    print("=" * 70)


def export_to_json():
    """
    Exporte le diagnostic en format JSON pour analyse ultérieure.
    
    Returns:
        dict: Rapport complet en format dict.
    """
    import json
    from datetime import datetime
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'memory': get_memory_info(),
        'swap': check_swap(),
        'top_processes': get_top_processes(20),
        'categories': identify_memory_hogs(),
    }
    
    # Sauvegarder dans fichier
    output_file = 'memory_diagnostic_report.json'
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Rapport sauvegardé dans : {output_file}")
    
    return report


# ================================================================
# POINT D'ENTRÉE
# ================================================================
if __name__ == "__main__":
    try:
        print_report()
        
        # Option : exporter en JSON
        if '--export' in sys.argv or '-e' in sys.argv:
            print("\n📄 Export JSON...")
            export_to_json()
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Diagnostic interrompu par l'utilisateur.")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Erreur lors du diagnostic : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
