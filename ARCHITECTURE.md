# Architecture Technique - Système PMMP

## Vue d'ensemble

Le système d'extraction des marchés publics marocains est composé de 5 modules principaux:

```
┌─────────────────────────────────────────────────────────────────┐
│                        PMMP SCRAPER SYSTEM                       │
└─────────────────────────────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
   ┌────▼────┐           ┌───────▼───────┐        ┌──────▼──────┐
   │ Scraper │           │   Database    │        │  API REST   │
   │ Module  │──────────▶│  PostgreSQL   │◀───────│   FastAPI   │
   └────┬────┘           └───────────────┘        └─────────────┘
        │                        │
   ┌────▼────────┐       ┌───────▼────────┐
   │  Airflow    │       │   Monitoring   │
   │Orchestration│       │ Prometheus +   │
   └─────────────┘       │    Grafana     │
                         └────────────────┘
```

## 1. Module Scraper

### Technologies
- **Scrapy 2.11**: Framework de scraping
- **Playwright**: Rendu JavaScript et interaction avec formulaires
- **Python 3.11**: Langage principal

### Composants

#### Spiders
- `consultations_spider.py`: Extraction des appels d'offres
- `pv_spider.py`: Extraction des procès-verbaux
- `attributions_spider.py`: Extraction des résultats

#### Pipelines (ordre d'exécution)
1. **ValidationPipeline**: Vérifie les champs obligatoires
2. **CleaningPipeline**: Nettoie et normalise les données
3. **DeduplicationPipeline**: Évite les doublons
4. **ArchivePipeline**: Sauvegarde les pages HTML
5. **DatabasePipeline**: Insertion en base de données
6. **MetricsPipeline**: Collecte des métriques

#### Middlewares
- **CustomUserAgentMiddleware**: Gestion du User-Agent
- **DelayMiddleware**: Délais aléatoires (2-5s)
- **RetryWithDelayMiddleware**: Retry avec backoff exponentiel

### Flux de données

```
URL → Playwright → HTML → Scrapy → Item → Pipelines → PostgreSQL
                                     │
                                     └──→ Metrics → Prometheus
```

## 2. Module Base de données

### Schéma relationnel

```sql
consultations (table principale)
├── id_interne (PK)
├── ref_consultation (UNIQUE)
├── organisme_acronyme
├── titre, objet
├── type_marche (ENUM)
├── statut (ENUM)
├── dates (publication, limite, seance)
├── montants
└── metadata

lots (1:N avec consultations)
├── id_lot (PK)
├── ref_consultation (FK)
├── numero_lot
└── détails

pv_extraits (1:N avec consultations)
├── id_pv (PK)
├── ref_consultation (FK)
└── contenu

attributions (1:N avec consultations)
├── id_attribution (PK)
├── ref_consultation (FK)
├── entreprise_nom
└── montants

achevements (1:N avec consultations)
├── id_achevement (PK)
├── ref_consultation (FK)
└── détails

extraction_logs (logging)
├── id_log (PK)
├── spider_name
├── statistiques
└── erreurs
```

### Index optimisés
- `ref_consultation` (UNIQUE)
- `date_publication` + `statut`
- `organisme_acronyme` + `date_publication`
- `type_marche` + `date_publication`

### Vues matérialisées
- `v_stats_consultations`: Stats par mois/type/statut
- `v_top_organismes`: Organismes les plus actifs
- `v_top_attributaires`: Entreprises gagnantes

## 3. Module API REST

### Stack technique
- **FastAPI**: Framework web
- **Pydantic**: Validation des données
- **SQLAlchemy**: ORM
- **Uvicorn**: Serveur ASGI

### Endpoints principaux

```
GET /api/v1/consultations
  ?statut=en_cours
  &type_marche=travaux
  &organisme=ONEE
  &date_debut=2024-01-01
  &date_fin=2024-12-31
  &limit=100
  &offset=0

GET /api/v1/consultations/{ref}
  → Détails + lots + PV + attributions

GET /api/v1/consultations/search?q=route

GET /api/v1/pv
  ?ref_consultation=...
  &organisme=...

GET /api/v1/attributions
  ?entreprise=...
  &montant_min=1000000

GET /api/v1/stats
  → Statistiques globales

GET /api/v1/stats/organismes
  → Top organismes

GET /api/v1/export/csv
  → Export CSV
```

### Réponses
- Format JSON (Pydantic schemas)
- Pagination
- Filtres multiples
- Documentation Swagger auto-générée

## 4. Module Orchestration (Airflow)

### DAGs

#### `pmmp_daily_extraction` (quotidien)
```
2h du matin (heure creuse)
│
├─ check_database
├─ scrape_consultations (parallèle)
├─ scrape_pv (parallèle)
├─ scrape_attributions (parallèle)
└─ analyze_results
```

#### `pmmp_historical_extraction` (manuel)
```
Extraction complète 3 ans
│
└─ extract_historical_data
```

### Configuration
- Retries: 3 fois avec délai de 30 min
- Timeout: 2h par tâche
- Email alerts en cas d'échec

## 5. Module Monitoring

### Métriques Prometheus

```python
# Spiders
pmmp_spider_started_total
pmmp_spider_closed_total
pmmp_active_spiders

# Requêtes
pmmp_requests_total
pmmp_responses_total{status}

# Items
pmmp_items_scraped_total{spider, type}
pmmp_items_processed_total{type}
pmpm_items_saved_total{type}
pmpm_items_dropped_total{reason}

# Erreurs
pmmp_spider_errors_total
```

### Alertes configurées
1. **NoConsultationsExtracted**: Aucune extraction pendant 3j
2. **HighErrorRate**: Taux d'erreur > 10%
3. **APIDown**: API indisponible > 5min
4. **SpiderStuck**: Spider bloqué > 30min
5. **RateLimitExceeded**: 429 reçus

### Dashboard Grafana
- Items extraits (total, par type)
- Taux d'erreur
- Spiders actifs
- Durée d'extraction
- Taux de succès

## Déploiement

### Docker Compose
```yaml
services:
  - postgres (DB)
  - scraper (Scrapy + Playwright)
  - api (FastAPI)
  - airflow (orchestration)
  - prometheus (métriques)
  - grafana (visualisation)
```

### Variables d'environnement
Voir `.env.example` pour la configuration complète.

## Sécurité et conformité

### Bonnes pratiques
- ✅ Rate limiting: 0.5 req/s
- ✅ Délais aléatoires: 2-5s
- ✅ User-Agent identifiable
- ✅ Respect robots.txt
- ✅ Archivage pour preuve
- ✅ Logs détaillés
- ✅ Retry avec backoff

### Respect de la législation
- Contact: marchespublics@tgr.gov.ma
- Données publiques uniquement
- Pas de contournement d'authentification
- Extraction planifiée (heures creuses)

## Performance

### Optimisations
- Index DB optimisés
- Pagination efficace
- Cache des refs en mémoire (déduplication)
- Connexion pooling (SQLAlchemy)
- Compression gzip (API)

### Scalabilité
- Scrapy concurrent: 1 req/s max
- API workers: 4 (configurable)
- DB connections pool: 10 + 20 overflow
- Airflow: LocalExecutor (scalable vers CeleryExecutor)

## Maintenance

### Logs
- `logs/scraper.log`: Scrapy
- `logs/api.log`: FastAPI
- `airflow/logs/`: DAGs

### Backup
- DB: `pg_dump` quotidien recommandé
- Archives HTML: Rotation après 6 mois
- Logs: Rotation après 1 mois

---

**Version**: 1.0.0  
**Dernière mise à jour**: 2025-10-23
