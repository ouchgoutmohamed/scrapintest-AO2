"""
Configuration centralisée de l'application
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Charger les variables d'environnement
load_dotenv()

# Chemins
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'
ARCHIVE_DIR = DATA_DIR / 'archives'
EXPORTS_DIR = DATA_DIR / 'exports'

# Créer les répertoires s'ils n'existent pas
for directory in [DATA_DIR, LOGS_DIR, ARCHIVE_DIR, EXPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Base de données
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://pmmp_user:pmmp_password@localhost:5432/pmmp_db')

# Scraper
SCRAPER_DELAY = float(os.getenv('SCRAPER_DELAY', 2.5))
SCRAPER_USER_AGENT = os.getenv('SCRAPER_USER_AGENT', 'PMMP-DataCollector/1.0 (+mailto:contact@votredomaine.com)')
MAX_REQUESTS_PER_SECOND = float(os.getenv('MAX_REQUESTS_PER_SECOND', 0.5))

# URLs PMMP
PMMP_BASE_URL = os.getenv('PMMP_BASE_URL', 'https://www.marchespublics.gov.ma')

# API
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))

# Monitoring
PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', 9090))

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Alertes
ALERT_EMAIL = os.getenv('ALERT_EMAIL', 'admin@votredomaine.com')

# Archivage
ENABLE_ARCHIVING = os.getenv('ENABLE_ARCHIVING', 'True') == 'True'
ARCHIVE_STORAGE_PATH = os.getenv('ARCHIVE_STORAGE_PATH', str(ARCHIVE_DIR))
