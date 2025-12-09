# tests/conftest.py
"""
Configuration pytest et fixtures partagées.
"""

import pytest
from unittest.mock import Mock, MagicMock
import sys


@pytest.fixture
def mock_servokit():
    """
    Fixture pour mocker ServoKit (Adafruit).
    Évite dépendance matérielle dans les tests.
    """
    mock_kit = Mock()
    mock_kit.frequency = 50
    
    # Mock des servos continus (canaux 0-15)
    continuous_servos = {}
    for channel in range(16):
        servo = Mock()
        servo.throttle = 0.0
        continuous_servos[channel] = servo
    
    mock_kit.continuous_servo = continuous_servos
    
    # Mock des servos positionnels (canaux 0-15)
    angle_servos = {}
    for channel in range(16):
        servo = Mock()
        servo.angle = 90.0
        angle_servos[channel] = servo
    
    mock_kit.servo = angle_servos
    
    return mock_kit


@pytest.fixture
def mock_gpio():
    """
    Fixture pour mocker RPi.GPIO.
    """
    gpio_mock = MagicMock()
    gpio_mock.BCM = 11
    gpio_mock.OUT = 0
    gpio_mock.IN = 1
    gpio_mock.HIGH = 1
    gpio_mock.LOW = 0
    
    return gpio_mock


@pytest.fixture
def sample_servo_config():
    """
    Fixture retournant une configuration servo de test valide.
    """
    return {
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
            },
            "pouce_rotation": {
                "channel": 3,
                "neutral": 0.35,
                "mode": "angle",
                "angle_min": 0.0,
                "angle_max": 180.0,
                "angle_neutral": 90.0,
                "angle_step": 5.0,
                "exclude_from_global": True
            }
        }
    }


@pytest.fixture
def sample_yaml_config():
    """
    Fixture retournant une configuration YAML complète de test.
    """
    return {
        'network': {
            'pc_ip': '192.168.1.10',
            'mjpeg_port': 8090,
            'rpi_ip': '192.168.1.60',
            'rpi_camera_port': 8091,
            'rpi_camera_enabled': True,
            'udp_ip': '0.0.0.0',
            'udp_port': 5005,
            'lost_timeout': 2.0
        },
        'servos': {
            'open_threshold': 0.3,
            'close_threshold': 0.7,
            'thumb_anti_flutter': 0.02
        },
        'fingers': [
            'pouce_articulation',
            'index',
            'majeur',
            'annulaire_auriculaire'
        ],
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


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset des singletons entre chaque test pour éviter contamination.
    """
    # Si le module config_loader a été importé, réinitialiser
    if 'core.config_loader' in sys.modules:
        from core.config_loader import load_config
        # Force reload de la config pour chaque test
    
    yield
    
    # Cleanup après test (si nécessaire)


@pytest.fixture
def mock_mediapipe_hands():
    """
    Fixture pour mocker MediaPipe Hands.
    """
    mock_hands = Mock()
    mock_hands.process = Mock(return_value=Mock(multi_hand_landmarks=None))
    return mock_hands


@pytest.fixture
def sample_hand_landmarks():
    """
    Fixture retournant des landmarks de main simulés.
    """
    landmarks = []
    # 21 landmarks pour une main
    for i in range(21):
        lm = Mock()
        lm.x = 0.5 + (i * 0.01)
        lm.y = 0.5 + (i * 0.01)
        lm.z = 0.0
        landmarks.append(lm)
    
    hand_landmarks = Mock()
    hand_landmarks.landmark = landmarks
    
    return hand_landmarks
