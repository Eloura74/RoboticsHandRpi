"""Test rapide pour vérifier l'état partagé"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

# Import depuis network
from apps.dashboard_network import state as state_net, state_lock as lock_net

# Import depuis ui
from apps.dashboard_ui import state as state_ui, state_lock as lock_ui

print("État network ID:", id(state_net))
print("État UI ID:     ", id(state_ui))
print("Même objet?", state_net is state_ui)

print("\nLock network ID:", id(lock_net))
print("Lock UI ID:     ", id(lock_ui))
print("Même lock?", lock_net is lock_ui)
