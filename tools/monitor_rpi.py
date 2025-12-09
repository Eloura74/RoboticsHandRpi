#!/usr/bin/env python3
# tools/monitor_rpi.py
"""
Monitoring système temps réel pour Raspberry Pi.
Affiche CPU, RAM, température, charge réseau.

Usage:
    python tools/monitor_rpi.py
    python tools/monitor_rpi.py --interval 2.0
    python tools/monitor_rpi.py --export metrics.json
"""

import sys
import time
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

try:
    import psutil
except ImportError:
    print("[ERROR] psutil requis : pip install psutil")
    sys.exit(1)


class RPiMonitor:
    """
    Moniteur système pour Raspberry Pi.
    
    Collecte métriques CPU, RAM, disque, température, réseau.
    """
    
    def __init__(self):
        """Initialise le moniteur."""
        self.start_time = time.time()
        self.last_net_io = psutil.net_io_counters()
        self.last_check_time = time.time()
    
    def get_cpu_temperature(self) -> Optional[float]:
        """
        Récupère la température du CPU Raspberry Pi.
        
        Returns:
            Température en °C, ou None si erreur.
        """
        try:
            # Chemin standard sur Raspberry Pi OS
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_millidegrees = int(f.read().strip())
                return temp_millidegrees / 1000.0
        except (FileNotFoundError, ValueError, PermissionError):
            # Fallback : tenter via psutil (si disponible)
            try:
                temps = psutil.sensors_temperatures()
                if 'cpu_thermal' in temps:
                    return temps['cpu_thermal'][0].current
            except (AttributeError, KeyError):
                pass
            return None
    
    def get_network_stats(self) -> Dict[str, float]:
        """
        Calcule les statistiques réseau depuis le dernier appel.
        
        Returns:
            Dict avec bytes_sent_per_sec et bytes_recv_per_sec.
        """
        current_net_io = psutil.net_io_counters()
        current_time = time.time()
        
        elapsed = current_time - self.last_check_time
        if elapsed == 0:
            elapsed = 0.001  # Éviter division par zéro
        
        # Calcul des débits en octets/sec
        bytes_sent_rate = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / elapsed
        bytes_recv_rate = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / elapsed
        
        # Mise à jour pour le prochain calcul
        self.last_net_io = current_net_io
        self.last_check_time = current_time
        
        return {
            'bytes_sent_per_sec': bytes_sent_rate,
            'bytes_recv_per_sec': bytes_recv_rate,
            'packets_sent': current_net_io.packets_sent,
            'packets_recv': current_net_io.packets_recv
        }
    
    def get_disk_usage(self, path='/') -> Dict[str, float]:
        """
        Récupère l'utilisation disque.
        
        Args:
            path: Point de montage à vérifier (par défaut /)
        
        Returns:
            Dict avec total, used, free, percent.
        """
        usage = psutil.disk_usage(path)
        return {
            'total_gb': usage.total / (1024**3),
            'used_gb': usage.used / (1024**3),
            'free_gb': usage.free / (1024**3),
            'percent': usage.percent
        }
    
    def get_all_metrics(self) -> Dict:
        """
        Collecte toutes les métriques système.
        
        Returns:
            Dictionnaire complet des métriques.
        """
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_per_core = psutil.cpu_percent(interval=0.5, percpu=True)
        cpu_freq = psutil.cpu_freq()
        
        # RAM
        ram = psutil.virtual_memory()
        
        # Température
        temp = self.get_cpu_temperature()
        
        # Réseau
        network = self.get_network_stats()
        
        # Disque
        disk = self.get_disk_usage()
        
        # Uptime
        uptime_seconds = time.time() - self.start_time
        
        return {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': uptime_seconds,
            'cpu': {
                'percent_total': cpu_percent,
                'percent_per_core': cpu_per_core,
                'frequency_mhz': cpu_freq.current if cpu_freq else None,
                'load_average': psutil.getloadavg()  # 1min, 5min, 15min
            },
            'memory': {
                'total_mb': ram.total / (1024**2),
                'used_mb': ram.used / (1024**2),
                'available_mb': ram.available / (1024**2),
                'percent': ram.percent
            },
            'temperature': {
                'cpu_celsius': temp
            },
            'network': network,
            'disk': disk
        }
    
    def format_metrics_console(self, metrics: Dict) -> str:
        """
        Formate les métriques pour affichage console.
        
        Args:
            metrics: Dictionnaire de métriques.
        
        Returns:
            String formaté pour affichage.
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"  RPi Monitor - {metrics['timestamp']}")
        lines.append("=" * 60)
        
        # CPU
        cpu = metrics['cpu']
        lines.append(f"CPU Total    : {cpu['percent_total']:5.1f}%")
        
        core_str = " | ".join([f"Core{i}: {p:4.1f}%" for i, p in enumerate(cpu['percent_per_core'])])
        lines.append(f"CPU Cores    : {core_str}")
        
        if cpu['frequency_mhz']:
            lines.append(f"Fréquence    : {cpu['frequency_mhz']:.0f} MHz")
        
        load_avg = cpu['load_average']
        lines.append(f"Load Average : {load_avg[0]:.2f} | {load_avg[1]:.2f} | {load_avg[2]:.2f}")
        
        # RAM
        mem = metrics['memory']
        lines.append(f"RAM          : {mem['percent']:5.1f}% ({mem['used_mb']:.0f} MB / {mem['total_mb']:.0f} MB)")
        
        # Température
        temp = metrics['temperature']['cpu_celsius']
        if temp:
            temp_status = "⚠️  CHAUD" if temp > 70 else ("🔥 CRITIQUE" if temp > 80 else "✅ OK")
            lines.append(f"Température  : {temp:.1f}°C {temp_status}")
        
        # Réseau
        net = metrics['network']
        lines.append(f"Réseau TX    : {net['bytes_sent_per_sec'] / 1024:.1f} KB/s")
        lines.append(f"Réseau RX    : {net['bytes_recv_per_sec'] / 1024:.1f} KB/s")
        
        # Disque
        disk = metrics['disk']
        lines.append(f"Disque /     : {disk['percent']:5.1f}% ({disk['free_gb']:.1f} GB libres)")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Monitoring système Raspberry Pi temps réel"
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=2.0,
        help='Intervalle de rafraîchissement en secondes (défaut: 2.0)'
    )
    parser.add_argument(
        '--export',
        type=str,
        help='Fichier JSON pour exporter les métriques'
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=None,
        help='Nombre de samples à collecter avant arrêt (défaut: infini)'
    )
    
    args = parser.parse_args()
    
    monitor = RPiMonitor()
    metrics_history = []
    
    print(f"[MONITOR] Démarrage du monitoring système (intervalle: {args.interval}s)")
    if args.export:
        print(f"[MONITOR] Export activé vers : {args.export}")
    print("[MONITOR] Ctrl+C pour arrêter\n")
    
    sample_count = 0
    
    try:
        while True:
            # Collecter métriques
            metrics = monitor.get_all_metrics()
            metrics_history.append(metrics)
            
            # Afficher dans la console
            print("\033[2J\033[H")  # Clear screen
            print(monitor.format_metrics_console(metrics))
            
            # Export si demandé
            if args.export and len(metrics_history) % 10 == 0:
                with open(args.export, 'w') as f:
                    json.dump(metrics_history, f, indent=2)
                print(f"\n[EXPORT] {len(metrics_history)} samples exportés vers {args.export}")
            
            sample_count += 1
            
            # Arrêt si nombre de samples atteint
            if args.samples and sample_count >= args.samples:
                print(f"\n[MONITOR] {args.samples} samples collectés, arrêt.")
                break
            
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print("\n\n[MONITOR] Arrêt demandé par l'utilisateur")
    
    finally:
        # Export final si demandé
        if args.export and metrics_history:
            with open(args.export, 'w') as f:
                json.dump(metrics_history, f, indent=2)
            print(f"[EXPORT] {len(metrics_history)} samples exportés vers {args.export}")
        
        print("[MONITOR] Terminé.")


if __name__ == "__main__":
    main()
