"""
DAG Airflow pour l'extraction quotidienne des données PMMP
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable
from datetime import datetime, timedelta
import logging

# Configuration par défaut
default_args = {
    'owner': 'pmmp',
    'depends_on_past': False,
    'email': [Variable.get('ALERT_EMAIL', 'admin@votredomaine.com')],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=30),
    'execution_timeout': timedelta(hours=2),
}

# Création du DAG
dag = DAG(
    'pmmp_daily_extraction',
    default_args=default_args,
    description='Extraction quotidienne des marchés publics marocains',
    schedule_interval='0 2 * * *',  # Tous les jours à 2h du matin (heure creuse)
    start_date=days_ago(1),
    catchup=False,
    tags=['pmmp', 'scraping', 'daily'],
)


def log_execution_start():
    """Log le début de l'extraction"""
    logging.info(f"=== Début extraction PMMP - {datetime.now()} ===")


def log_execution_end():
    """Log la fin de l'extraction"""
    logging.info(f"=== Fin extraction PMMP - {datetime.now()} ===")


def check_database_connection():
    """Vérifie la connexion à la base de données"""
    from database.connection import check_connection
    if not check_connection():
        raise Exception("Impossible de se connecter à la base de données")
    logging.info("✅ Connexion DB vérifiée")


def analyze_extraction_results():
    """Analyse les résultats de l'extraction"""
    from database.connection import SessionLocal
    from database.models import ExtractionLog
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        # Récupérer les logs des dernières 24h
        since = datetime.now() - timedelta(days=1)
        logs = db.query(ExtractionLog).filter(
            ExtractionLog.date_execution >= since
        ).all()
        
        total_items = sum(log.items_extraits for log in logs)
        total_errors = sum(log.erreurs for log in logs)
        
        logging.info(f"📊 Résultats extraction:")
        logging.info(f"  - Items extraits: {total_items}")
        logging.info(f"  - Erreurs: {total_errors}")
        
        # Alerte si aucun item extrait
        if total_items == 0:
            logging.warning("⚠️ ALERTE: Aucun item extrait!")
        
    finally:
        db.close()


# ============================================================================
# TÂCHES DU DAG
# ============================================================================

# Tâche 1: Log début
task_start = PythonOperator(
    task_id='log_start',
    python_callable=log_execution_start,
    dag=dag,
)

# Tâche 2: Vérifier la connexion DB
task_check_db = PythonOperator(
    task_id='check_database',
    python_callable=check_database_connection,
    dag=dag,
)

# Tâche 3: Scraper consultations en cours
task_scrape_consultations = BashOperator(
    task_id='scrape_consultations',
    bash_command='cd /app && scrapy crawl consultations_spider -a statut=en_cours',
    dag=dag,
)

# Tâche 4: Scraper PV
task_scrape_pv = BashOperator(
    task_id='scrape_pv',
    bash_command='cd /app && scrapy crawl pv_spider',
    dag=dag,
)

# Tâche 5: Scraper attributions
task_scrape_attributions = BashOperator(
    task_id='scrape_attributions',
    bash_command='cd /app && scrapy crawl attributions_spider',
    dag=dag,
)

# Tâche 6: Analyser les résultats
task_analyze = PythonOperator(
    task_id='analyze_results',
    python_callable=analyze_extraction_results,
    dag=dag,
)

# Tâche 7: Log fin
task_end = PythonOperator(
    task_id='log_end',
    python_callable=log_execution_end,
    dag=dag,
)

# ============================================================================
# DÉFINITION DU WORKFLOW
# ============================================================================

task_start >> task_check_db >> [task_scrape_consultations, task_scrape_pv, task_scrape_attributions]
[task_scrape_consultations, task_scrape_pv, task_scrape_attributions] >> task_analyze >> task_end
