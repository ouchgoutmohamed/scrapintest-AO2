#!/bin/bash
# Script d'installation pour Linux/Mac

echo "========================================"
echo "  PMMP Scraper - Installation"
echo "========================================"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Vérifier Python
echo -e "${YELLOW}[1/8] Vérification de Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}  ✓ Python trouvé: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}  ✗ Python 3 n'est pas installé!${NC}"
    exit 1
fi

# Vérifier pip
echo -e "${YELLOW}[2/8] Vérification de pip...${NC}"
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}  ✓ pip trouvé${NC}"
else
    echo -e "${RED}  ✗ pip n'est pas installé!${NC}"
    exit 1
fi

# Créer l'environnement virtuel
echo -e "${YELLOW}[3/8] Création de l'environnement virtuel...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}  ! L'environnement virtuel existe déjà${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}  ✓ Environnement virtuel créé${NC}"
fi

# Activer l'environnement virtuel
echo -e "${YELLOW}[4/8] Activation de l'environnement virtuel...${NC}"
source venv/bin/activate
echo -e "${GREEN}  ✓ Environnement activé${NC}"

# Installer les dépendances
echo -e "${YELLOW}[5/8] Installation des dépendances Python...${NC}"
pip install --upgrade pip -q
pip install -r requirements.txt -q
if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ Dépendances installées${NC}"
else
    echo -e "${RED}  ✗ Erreur lors de l'installation des dépendances${NC}"
    exit 1
fi

# Installer Playwright
echo -e "${YELLOW}[6/8] Installation de Playwright...${NC}"
playwright install chromium
if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ Playwright installé${NC}"
else
    echo -e "${RED}  ✗ Erreur lors de l'installation de Playwright${NC}"
fi

# Créer le fichier .env
echo -e "${YELLOW}[7/8] Configuration de l'environnement...${NC}"
if [ -f ".env" ]; then
    echo -e "${YELLOW}  ! Le fichier .env existe déjà${NC}"
else
    cp .env.example .env
    echo -e "${GREEN}  ✓ Fichier .env créé (à configurer)${NC}"
fi

# Vérifier PostgreSQL
echo -e "${YELLOW}[8/8] Vérification de PostgreSQL...${NC}"
if command -v psql &> /dev/null; then
    echo -e "${GREEN}  ✓ PostgreSQL trouvé${NC}"
else
    echo -e "${YELLOW}  ! PostgreSQL non détecté (optionnel pour Docker)${NC}"
fi

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}  Installation terminée!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

echo -e "${CYAN}Prochaines étapes:${NC}"
echo -e "  1. Configurer .env avec vos paramètres PostgreSQL"
echo -e "  2. Initialiser la base de données:"
echo -e "     ${YELLOW}python scripts/init_database.py${NC}"
echo -e "  3. Tester le scraper:"
echo -e "     ${YELLOW}python scripts/test_scraper.py${NC}"
echo -e "  4. Lancer l'API:"
echo -e "     ${YELLOW}uvicorn api.main:app --reload${NC}"
echo ""
echo -e "${CYAN}Alternative Docker:${NC}"
echo -e "  ${YELLOW}docker-compose up -d${NC}"
echo ""
echo -e "Documentation: README.md | QUICKSTART.md"
echo ""
