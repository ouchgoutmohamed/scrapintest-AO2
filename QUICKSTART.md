# Guide de démarrage rapide - PMMP Scraper

## 🚀 Installation rapide

### 1. Cloner et configurer

```powershell
cd "c:\Users\ouchg\OneDrive\Documents\scraping"

# Créer l'environnement virtuel
python -m venv venv
.\venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt

# Installer les navigateurs Playwright
playwright install chromium
```

### 2. Configuration de la base de données

```powershell
# Copier le fichier d'environnement
copy .env.example .env

# Éditer .env avec vos paramètres PostgreSQL
notepad .env
```

**Configuration PostgreSQL locale:**
- Installer PostgreSQL 15+
- Créer une base de données `pmmp_db`
- Mettre à jour DATABASE_URL dans `.env`

### 3. Initialiser la base de données

```powershell
python scripts\init_database.py
```

### 4. Tester le scraper

```powershell
# Test simple (sans sauvegarde DB)
python scripts\test_scraper.py

# Extraction réelle (sauvegarde en DB)
cd scraper
scrapy crawl consultations_spider -a statut=en_cours
```

### 5. Lancer l'API

```powershell
cd api
uvicorn main:app --reload
```

Accéder à: http://localhost:8000/docs

## 🐳 Démarrage avec Docker

```powershell
# Démarrer tous les services
docker-compose up -d

# Vérifier les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

## 📊 Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **API**: http://localhost:8000/docs

## 📝 Commandes utiles

```powershell
# Exporter les données
python scripts\export_data.py

# Lancer les tests
pytest tests/

# Voir les logs
cat logs\scraper.log
```

## ⚠️ Important

1. **Respecter les délais**: Le scraper est configuré avec des délais de 2-5s entre requêtes
2. **User-Agent**: Modifier dans `.env` avec vos coordonnées
3. **Légal**: Consulter les conditions d'utilisation du site PMMP

## 🆘 Résolution de problèmes

### Erreur de connexion PostgreSQL
```powershell
# Vérifier que PostgreSQL est démarré
Get-Service postgresql*
```

### Erreur Playwright
```powershell
playwright install chromium --with-deps
```

### Erreur d'import
```powershell
# Vérifier le PYTHONPATH
$env:PYTHONPATH = "c:\Users\ouchg\OneDrive\Documents\scraping"
```

## 📧 Contact

Pour toute question: contact@votredomaine.com
