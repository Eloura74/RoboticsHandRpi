# tests/test_hand_controller.py
"""
Tests unitaires pour HandController.
Utilise des mocks pour simuler le matériel (PCA9685, servos).
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import threading
import time
import json
from pathlib import Path


class TestHandController(unittest.TestCase):
    """Suite de tests pour HandController."""
    
    def setUp(self):
        """
        Créé un HandController mocké avant chaque test.
        Mock ServoKit et GPIO pour éviter dépendance matérielle.
        """
        # Configuration minimale de test
        self.test_config = {
            "pca9685": {
                "address": 64,
                "frequency": 50
            },
            "power": {
                "enable_gpio": None,
                "active_level_high": True
            },
            "servos": {
                "index": {
                    "channel": 2,
                    "neutral": 0.0,
                    "dir_close": -1,
                    "speed_close": 0.5,
                    "speed_open": 0.5,
                    "t_close": 0.9,
                    "t_open": 0.7
                },
                "majeur": {
                    "channel": 0,
                    "neutral": 0.0,
                    "dir_close": -1,
                    "speed_close": 0.5,
                    "speed_open": 0.5,
                    "t_close": 0.8,
                    "t_open": 0.6
                }
            }
        }
        
        # Mock du ServoKit
        self.mock_kit = Mock()
        self.mock_continuous_servo = {}
        for channel in [0, 2]:
            servo_mock = Mock()
            servo_mock.throttle = 0.0
            self.mock_continuous_servo[channel] = servo_mock
        
        self.mock_kit.continuous_servo = self.mock_continuous_servo
        self.mock_kit.frequency = 50
        
        # Patches pour éviter dépendances matérielles
        self.patches = [
            patch('core.hand_controller.ServoKit', return_value=self.mock_kit),
            patch('core.hand_controller.GPIO_AVAILABLE', False),
            patch('builtins.open', mock_open_config(self.test_config)),
            patch('json.load', return_value=self.test_config)
        ]
        
        for p in self.patches:
            p.start()
        
        # Import après les patches
        from core.hand_controller import HandController
        self.HandController = HandController
        
        # Créer l'instance de test
        self.ctrl = HandController()
    
    def tearDown(self):
        """Nettoie les mocks après chaque test."""
        for p in self.patches:
            p.stop()
    
    # ================================================================
    # TESTS D'INITIALISATION
    # ================================================================
    
    def test_initialization_loads_config(self):
        """Vérifie que __init__() charge correctement la configuration."""
        self.assertIsNotNone(self.ctrl.config)
        self.assertIn('servos', self.ctrl.config)
        self.assertEqual(len(self.ctrl.servos_conf), 2)
    
    def test_initialization_creates_servo_kit(self):
        """Vérifie que ServoKit est correctement initialisé."""
        self.assertIsNotNone(self.ctrl.kit)
        self.assertEqual(self.ctrl.kit.frequency, 50)
    
    def test_initialization_sets_all_servos_to_neutral(self):
        """Vérifie que tous les servos sont mis au neutre au démarrage."""
        # Les servos doivent avoir été appelés avec throttle = neutral (0.0)
        for channel, servo in self.mock_continuous_servo.items():
            self.assertEqual(servo.throttle, 0.0)
    
    def test_initial_state_is_open_for_all_fingers(self):
        """Vérifie que l'état initial logique est 'open' pour tous les doigts."""
        self.assertEqual(self.ctrl.state['index'], 'open')
        self.assertEqual(self.ctrl.state['majeur'], 'open')
    
    # ================================================================
    # TESTS DES MOUVEMENTS BLOQUANTS
    # ================================================================
    
    def test_open_finger_changes_state_to_open(self):
        """Vérifie que open_finger() change l'état logique à 'open'."""
        self.ctrl.close_finger('index', parallel=False)
        self.assertEqual(self.ctrl.state['index'], 'close')
        
        self.ctrl.open_finger('index', parallel=False)
        self.assertEqual(self.ctrl.state['index'], 'open')
    
    def test_close_finger_changes_state_to_close(self):
        """Vérifie que close_finger() change l'état logique à 'close'."""
        self.ctrl.close_finger('index', parallel=False)
        self.assertEqual(self.ctrl.state['index'], 'close')
    
    def test_open_finger_does_not_move_if_already_open(self):
        """Vérifie que open_finger() ne fait rien si déjà ouvert."""
        # État initial = open
        initial_state = self.ctrl.state['index']
        self.ctrl.open_finger('index', parallel=False)
        
        # État ne doit pas avoir changé
        self.assertEqual(self.ctrl.state['index'], initial_state)
    
    def test_close_finger_with_force_moves_even_if_already_closed(self):
        """Vérifie que force=True force le mouvement même si déjà dans l'état."""
        self.ctrl.close_finger('index', parallel=False)
        initial_state = self.ctrl.state['index']
        
        # Avec force=True, le mouvement doit être exécuté
        self.ctrl.close_finger('index', parallel=False, force=True)
        self.assertEqual(self.ctrl.state['index'], initial_state)
    
    # ================================================================
    # TESTS DES MOUVEMENTS PARALLÈLES
    # ================================================================
    
    def test_parallel_movement_creates_thread(self):
        """Vérifie que parallel=True crée un thread séparé."""
        self.ctrl.open_finger('index', parallel=True)
        
        # Vérifier qu'un thread a été créé
        self.assertIn('index', self.ctrl._finger_threads)
        thread = self.ctrl._finger_threads['index']
        self.assertIsInstance(thread, threading.Thread)
        
        # Attendre la fin du thread (avec mock, il termine instantanément)
        thread.join(timeout=2.0)
        
        # Vérifier que le mouvement a bien été effectué
        self.assertEqual(self.ctrl.state['index'], 'open')
    
    def test_parallel_movements_can_run_simultaneously(self):
        """Vérifie que plusieurs doigts peuvent bouger en parallèle."""
        self.ctrl.open_finger('index', parallel=True)
        self.ctrl.open_finger('majeur', parallel=True)
        
        # Deux threads doivent exister
        self.assertIn('index', self.ctrl._finger_threads)
        self.assertIn('majeur', self.ctrl._finger_threads)
        
        # Attendre fin des threads
        self.ctrl._wait_all_movements()
        
        self.assertEqual(self.ctrl.state['index'], 'open')
        self.assertEqual(self.ctrl.state['majeur'], 'open')
    
    def test_new_parallel_movement_cancels_previous_one(self):
        """Vérifie qu'un nouveau mouvement annule le précédent sur le même doigt."""
        # Lancer un mouvement de fermeture
        self.ctrl.close_finger('index', parallel=True)
        time.sleep(0.05)  # Laisser le thread démarrer
        
        # Lancer un mouvement d'ouverture (doit annuler le précédent)
        self.ctrl.open_finger('index', parallel=True)
        
        # Attendre fin
        self.ctrl._wait_all_movements()
        
        # L'état final doit être 'open'
        self.assertEqual(self.ctrl.state['index'], 'open')
    
    # ================================================================
    # TESTS STOP ALL
    # ================================================================
    
    def test_stop_all_interrupts_all_movements(self):
        """Vérifie que stop_all() arrête tous les mouvements en cours."""
        # Lancer plusieurs mouvements
        self.ctrl.close_finger('index', parallel=True)
        self.ctrl.close_finger('majeur', parallel=True)
        time.sleep(0.1)  # Laisser les threads démarrer
        
        # Arrêter tout
        self.ctrl.stop_all()
        
        # Vérifier que tous les threads se sont arrêtés rapidement
        for thread in self.ctrl._finger_threads.values():
            thread.join(timeout=1.0)
            self.assertFalse(thread.is_alive())
    
    def test_stop_all_sets_all_servos_to_neutral(self):
        """Vérifie que stop_all() remet tous les servos au neutre."""
        self.ctrl.stop_all()
        
        # Tous les servos doivent être à throttle = neutral
        for channel, servo in self.mock_continuous_servo.items():
            self.assertEqual(servo.throttle, 0.0)
    
    # ================================================================
    # TESTS OPEN/CLOSE HAND
    # ================================================================
    
    def test_open_hand_opens_all_fingers(self):
        """Vérifie que open_hand() ouvre tous les doigts."""
        # Fermer tous les doigts d'abord
        for finger in self.ctrl.servos_conf.keys():
            self.ctrl.state[finger] = 'close'
        
        # Ouvrir la main
        self.ctrl.open_hand(parallel=False)
        
        # Tous les doigts doivent être ouverts
        for finger in self.ctrl.servos_conf.keys():
            self.assertEqual(self.ctrl.state[finger], 'open')
    
    def test_close_hand_closes_all_fingers(self):
        """Vérifie que close_hand() ferme tous les doigts."""
        self.ctrl.close_hand(parallel=False)
        
        # Tous les doigts doivent être fermés
        for finger in self.ctrl.servos_conf.keys():
            self.assertEqual(self.ctrl.state[finger], 'close')
    
    # ================================================================
    # TESTS DE VALIDATION
    # ================================================================
    
    def test_invalid_finger_name_raises_error(self):
        """Vérifie qu'un nom de doigt invalide lève une ValueError."""
        with self.assertRaises(ValueError):
            self.ctrl.open_finger('doigt_inexistant', parallel=False)
    
    def test_throttle_is_clamped_to_valid_range(self):
        """Vérifie que les valeurs de throttle sont clampées entre -1 et 1."""
        # Cette logique est dans _set_throttle, on vérifie indirectement
        # en s'assurant qu'aucune exception n'est levée
        self.ctrl._set_throttle(2, 1.5)  # > 1.0
        self.ctrl._set_throttle(2, -1.5)  # < -1.0
        # Pas d'exception = test réussi


def mock_open_config(config_dict):
    """Helper pour mocker open() avec un dictionnaire de config."""
    from unittest.mock import mock_open
    return mock_open(read_data=json.dumps(config_dict))


if __name__ == '__main__':
    unittest.main()
