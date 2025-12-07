#!/bin/bash
# Script d'installation automatique pour Raspberry Pi
# Usage: bash install_rpi.sh

set -e  # Arrêt en cas d'erreur

echo "==========================================="
echo "  Installation Robotic Hand V2.0 - RPi"
echo "==========================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier qu'on est sur Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}[AVERTISSEMENT] Ce script est conçu pour Raspberry Pi.${NC}"
    read -p "Continuer quand même ? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. Mise à jour du système
echo -e "${GREEN}[1/6] Mise à jour du système...${NC}"
sudo apt update
sudo apt upgrade -y

# 2. Installation des dépendances système
echo -e "${GREEN}[2/6] Installation des dépendances système...${NC}"
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    i2c-tools \
    git

# 3. Activation I2C
echo -e "${GREEN}[3/6] Vérification I2C...${NC}"
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "Activation I2C..."
    sudo raspi-config nonint do_i2c 0
    echo -e "${YELLOW}I2C activé. Un redémarrage sera nécessaire.${NC}"
    NEED_REBOOT=1
else
    echo "I2C déjà activé ✓"
fi

# 4. Création de l'environnement virtuel
echo -e "${GREEN}[4/6] Création de l'environnement virtuel...${NC}"
if [ -d "venv" ]; then
    echo "venv existe déjà, suppression..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

# 5. Installation des packages Python
echo -e "${GREEN}[5/6] Installation des packages Python...${NC}"
pip install --upgrade pip
pip install -r requirements-rpi.txt

echo -e "${GREEN}Packages installés :${NC}"
pip list | grep -E "adafruit|nicegui|RPi.GPIO"

# 6. Vérification I2C
echo -e "${GREEN}[6/6] Vérification du PCA9685...${NC}"
if command -v i2cdetect &> /dev/null; then
    echo "Scan I2C (le PCA9685 doit apparaître à 0x40) :"
    i2cdetect -y 1 || echo -e "${YELLOW}Erreur : Vérifier le câblage I2C${NC}"
else
    echo -e "${YELLOW}i2c-tools non disponible, passer...${NC}"
fi

# Résumé
echo ""
echo "==========================================="
echo -e "${GREEN}✓ Installation terminée !${NC}"
echo "==========================================="
echo ""
echo "Prochaines étapes :"
echo ""
echo "1. Vérifier la configuration dans config/servos_v2.json"
echo "2. Éditer apps/neuro_dashboard.py pour mettre l'IP du PC"
echo "3. Activer le venv : source venv/bin/activate"
echo "4. Lancer le dashboard : python3 apps/neuro_dashboard.py"
echo ""

if [ -n "$NEED_REBOOT" ]; then
    echo -e "${YELLOW}⚠️  REDÉMARRAGE REQUIS pour activer I2C${NC}"
    read -p "Redémarrer maintenant ? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo reboot
    fi
fi

echo "Voir README.md pour plus de détails."
