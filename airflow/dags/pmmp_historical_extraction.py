"""
DAG Airflow pour l'extraction historique complète (3 ans)
À exécuter manuellement pour la première extraction
"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

default_args = {
    'owner': 'pmmp',
    'depends_on_past': False,
    'email': ['admin@votredomaine.com'],
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(hours=1),
    'execution_timeout': timedelta(hours=24),
}

dag = DAG(
    'pmmp_historical_extraction',
    default_args=default_args,
    description='Extraction historique complète (3 ans) - À exécuter manuellement',
    schedule_interval=None,  # Pas de planification automatique
    start_date=days_ago(1),
    catchup=False,
    tags=['pmmp', 'scraping', 'historical', 'manual'],
)

# Extraction complète avec période de 3 ans
task_historical = BashOperator(
    task_id='extract_historical_data',
    bash_command='cd /app && scrapy crawl consultations_spider -a periode=3ans -a statut=tous',
    dag=dag,
)

task_historical
