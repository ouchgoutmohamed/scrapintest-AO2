# Système d'Extraction des Marchés Publics Marocains (PMMP)

## 📋 Description

Système complet d'extraction, stockage et diffusion des données du Portail Marocain des Marchés Publics (marchespublics.gov.ma) conforme aux bonnes pratiques légales et éthiques.

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Playwright    │─────▶│  Scrapy Spider   │─────▶│   PostgreSQL    │
│  (Headless)     │      │   + Pipeline     │      │    Database     │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │                         │
                                  ▼                         ▼
                         ┌──────────────────┐      ┌─────────────────┐
                         │  Apache Airflow  │      │   FastAPI       │
                         │  (Orchestration) │      │   REST API      │
                         └──────────────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   Prometheus +   │
                         │     Grafana      │
                         └──────────────────┘
```

## 📊 Structure des données

- **consultations**: Appels d'offres en cours et clôturés
- **lots**: Détail des lots par marché
- **pv_extraits**: Procès-verbaux publiés
- **attributions**: Résultats définitifs
- **achevements**: Rapports d'achèvement

## 🚀 Installation

### Prérequis
- Python 3.9+
- PostgreSQL 13+
- Docker & Docker Compose (optionnel)

### Installation locale

```powershell
# Cloner le projet
git clone <repo-url>
cd scraping

# Créer un environnement virtuel
python -m venv venv
.\venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt

# Installer Playwright browsers
playwright install chromium

# Configuration base de données
cp .env.example .env
# Éditer .env avec vos paramètres PostgreSQL
```

### Déploiement Docker

```powershell
docker-compose up -d
```

## ⚙️ Configuration

Fichier `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/pmmp_db
SCRAPER_DELAY=2.0
SCRAPER_USER_AGENT=PMMP-DataCollector/1.0 (+mailto:contact@votredomaine.com)
MAX_REQUESTS_PER_SECOND=0.5
AIRFLOW_HOME=./airflow
API_HOST=0.0.0.0
API_PORT=8000
```

## 🧪 Tests d'Extraction

### Test rapide avec vérification des URLs

```powershell
# Vérifier que les URLs détaillées sont capturées
python scripts\test_url_extraction.py
```

Ce test vérifie que chaque consultation extraite contient bien son **`url_detail`** permettant d'accéder à la page complète avec les documents.

### Test avec analyse de la structure HTML

```powershell
# 1. Extraire et analyser une page réelle
python scripts\test_extraction_real.py

# 2. Analyser la structure HTML sauvegardée
python scripts\analyze_html_structure.py logs\test_page_consultations.html
```

**Consulter le guide complet** : [TESTING_GUIDE.md](TESTING_GUIDE.md)

## 🕷️ Utilisation du Scraper

### Exécution manuelle

```powershell
# Extraction des consultations en cours
cd scraper
scrapy crawl consultations_spider -a statut=en_cours

# Extraction des PV
scrapy crawl pv_spider

# Extraction des attributions
scrapy crawl attributions_spider
```

**Important** : Chaque consultation extraite inclut le champ `url_detail` qui pointe vers la page détaillée permettant d'accéder aux documents (DCE, avis, etc.).

### Planification avec Airflow

```powershell
# Démarrer Airflow
airflow standalone

# Activer le DAG
airflow dags unpause pmmp_daily_extraction
```

## 🔌 API REST

Démarrer l'API:
```powershell
cd api
uvicorn main:app --reload
```

Endpoints disponibles:
- `GET /api/v1/consultations?statut=en_cours&limit=100`
- `GET /api/v1/consultations/{ref_consultation}`
- `GET /api/v1/pv?organisme={acronyme}`
- `GET /api/v1/attributions?date_debut=2024-01-01`
- `GET /api/v1/export/csv?type=consultations`

Documentation: http://localhost:8000/docs

## 📈 Monitoring

### Métriques Prometheus
- `pmmp_pages_scraped_total`: Nombre total de pages scrapées
- `pmmp_consultations_extracted`: Consultations extraites
- `pmmp_scraping_errors_total`: Erreurs de scraping
- `pmmp_scraping_duration_seconds`: Durée du scraping

### Dashboard Grafana
Accès: http://localhost:3000 (admin/admin)

## ⚖️ Conformité légale et éthique

### Bonnes pratiques implémentées:
✅ **User-Agent identifiable** avec contact
✅ **Limitation de débit**: 0.5 req/s maximum
✅ **Délais aléatoires** entre requêtes (2-5 secondes)
✅ **Respect robots.txt**
✅ **Archivage des pages brutes** pour preuve
✅ **Anonymisation** des données personnelles
✅ **Extraction planifiée** (quotidienne, heures creuses)

### Contact légal
- Portail PMMP: marchespublics@tgr.gov.ma
- Conditions d'utilisation: Consulter régulièrement le site

## 🧪 Tests

```powershell
# Tests unitaires
pytest tests/unit/

# Tests d'intégration
pytest tests/integration/

# Tests de charge
pytest tests/load/
```

## 📝 Logs et Alertes

Logs disponibles dans `./logs/`:
- `scraper.log`: Logs du scraper
- `airflow.log`: Logs d'orchestration
- `api.log`: Logs de l'API

Alertes configurées pour:
- Aucune nouvelle consultation pendant 3 jours
- Taux d'erreur > 10%
- Changement de structure HTML
- Blocage HTTP (429/403)

## 🔄 Maintenance

### Mise à jour des sélecteurs CSS
Si la structure du site change, éditer `scraper/selectors.py`

### Sauvegarde de la base de données
```powershell
pg_dump -U user pmmp_db > backup_$(date +%Y%m%d).sql
```

## 📞 Support

Pour toute question ou problème, contactez l'équipe technique via [contact@votredomaine.com]

## 📄 Licence

Ce projet est destiné à des fins de transparence des marchés publics. Respecter la législation marocaine en vigueur.
