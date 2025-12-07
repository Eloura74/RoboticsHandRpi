#!/bin/bash
# Script d'installation automatique pour PC (Linux/Mac)
# Usage: bash install_pc.sh

set -e

echo "==========================================="
echo "  Installation Hand Tracker - PC"
echo "==========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Vérifier Python
echo -e "${GREEN}[1/3] Vérification de Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "Python 3 n'est pas installé !"
    echo "Installer Python 3.9+ depuis https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION ✓"

# 2. Création de l'environnement virtuel
echo -e "${GREEN}[2/3] Création de l'environnement virtuel...${NC}"
if [ -d "venv" ]; then
    echo "venv existe déjà, suppression..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

# 3. Installation des packages
echo -e "${GREEN}[3/3] Installation des packages Python...${NC}"
pip install --upgrade pip
pip install -r requirements-pc.txt

echo -e "${GREEN}Packages installés :${NC}"
pip list | grep -E "opencv-python|mediapipe"

# Résumé
echo ""
echo "==========================================="
echo -e "${GREEN}✓ Installation terminée !${NC}"
echo "==========================================="
echo ""
echo "Prochaines étapes :"
echo ""
echo "1. Éditer hand_tracker.py pour mettre l'IP du Raspberry Pi"
echo "   UDP_IP = '192.168.1.XX'  # IP de ton RPi"
echo ""
echo "2. Activer le venv :"
echo "   source venv/bin/activate"
echo ""
echo "3. Lancer le tracker :"
echo "   python3 hand_tracker.py"
echo ""
echo "Voir README.md pour plus de détails."
