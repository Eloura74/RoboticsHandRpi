# tests/test_config_loader.py
"""
Tests unitaires pour ConfigLoader.
Teste le chargement et validation de config.yaml.
"""

import unittest
from unittest.mock import patch, mock_open
import yaml
from pathlib import Path


class TestConfigLoader(unittest.TestCase):
    """Suite de tests pour le module config_loader."""
    
    def setUp(self):
        """Configuration de test valide."""
        self.valid_config = {
            'network': {
                'pc_ip': '192.168.1.10',
                'mjpeg_port': 8090,
                'udp_ip': '0.0.0.0',
                'udp_port': 5005,
                'lost_timeout': 2.0
            },
            'servos': {
                'open_threshold': 0.3,
                'close_threshold': 0.7,
                'thumb_anti_flutter': 0.02
            },
            'fingers': ['pouce_articulation', 'index', 'majeur', 'annulaire_auriculaire'],
            'ui': {
                'web_port': 8080,
                'update_interval': 0.05
            },
            'security': {
                'enable_hmac': False,
                'rate_limit_requests': 100,
                'rate_limit_window': 1.0
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/neurohand.log',
                'max_bytes': 10485760,
                'backup_count': 5
            }
        }
    
    def test_load_config_from_valid_yaml(self):
        """Teste le chargement d'un fichier YAML valide."""
        yaml_content = yaml.dump(self.valid_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('pathlib.Path.exists', return_value=True):
                from core.config_loader import load_config
                config = load_config()
                
                self.assertIsNotNone(config)
                self.assertEqual(config.network.pc_ip, '192.168.1.10')
                self.assertEqual(config.network.udp_port, 5005)
    
    def test_network_config_properties(self):
        """Teste les propriétés de NetworkConfig."""
        yaml_content = yaml.dump(self.valid_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('pathlib.Path.exists', return_value=True):
                from core.config_loader import load_config
                config = load_config()
                
                # Test propriété mjpeg_url
                expected_url = 'http://192.168.1.10:8090/cam.mjpg'
                self.assertEqual(config.network.mjpeg_url, expected_url)
                
                # Test propriété rpi_camera_url
                self.assertIn('stream.mjpg', config.network.rpi_camera_url)
    
    def test_config_with_missing_file_uses_defaults(self):
        """Teste que des valeurs par défaut sont utilisées si fichier absent."""
        with patch('pathlib.Path.exists', return_value=False):
            from core.config_loader import load_config
            config = load_config()
            
            # Doit retourner config avec valeurs par défaut
            self.assertIsNotNone(config)
            self.assertEqual(config.network.udp_port, 5005)  # Valeur par défaut
    
    def test_config_with_partial_data(self):
        """Teste que la config gère les données partielles avec fallback."""
        partial_config = {
            'network': {
                'udp_port': 9999  # Seulement un champ
            }
        }
        yaml_content = yaml.dump(partial_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('pathlib.Path.exists', return_value=True):
                from core.config_loader import load_config
                config = load_config()
                
                # Champ spécifié doit être pris en compte
                self.assertEqual(config.network.udp_port, 9999)
                
                # Champs manquants doivent avoir valeurs par défaut
                self.assertEqual(config.network.pc_ip, '192.168.1.10')
    
    def test_fingers_list_is_loaded(self):
        """Teste que la liste des doigts est correctement chargée."""
        yaml_content = yaml.dump(self.valid_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('pathlib.Path.exists', return_value=True):
                from core.config_loader import load_config
                config = load_config()
                
                self.assertEqual(len(config.fingers), 4)
                self.assertIn('index', config.fingers)
                self.assertIn('majeur', config.fingers)
    
    def test_logging_config_values(self):
        """Teste la configuration du logging."""
        yaml_content = yaml.dump(self.valid_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('pathlib.Path.exists', return_value=True):
                from core.config_loader import load_config
                config = load_config()
                
                self.assertEqual(config.logging.level, 'INFO')
                self.assertEqual(config.logging.max_bytes, 10485760)
                self.assertEqual(config.logging.backup_count, 5)
    
    def test_security_config_values(self):
        """Teste la configuration de sécurité."""
        yaml_content = yaml.dump(self.valid_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('pathlib.Path.exists', return_value=True):
                from core.config_loader import load_config
                config = load_config()
                
                self.assertFalse(config.security.enable_hmac)
                self.assertEqual(config.security.rate_limit_requests, 100)
                self.assertEqual(config.security.rate_limit_window, 1.0)
    
    def test_malformed_yaml_returns_defaults(self):
        """Teste qu'un YAML malformé retourne la config par défaut."""
        malformed_yaml = "network:\n  - invalid: yaml: syntax"
        
        with patch('builtins.open', mock_open(read_data=malformed_yaml)):
            with patch('pathlib.Path.exists', return_value=True):
                from core.config_loader import load_config
                config = load_config()
                
                # Doit retourner config par défaut sans crasher
                self.assertIsNotNone(config)


if __name__ == '__main__':
    unittest.main()
