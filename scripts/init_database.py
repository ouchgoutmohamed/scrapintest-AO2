"""
Script d'initialisation de la base de données
Crée les tables et charge les données de référence
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, check_connection, init_db
from database.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialise la base de données"""
    logger.info("🚀 Initialisation de la base de données PMMP...")
    
    # Vérifier la connexion
    if not check_connection():
        logger.error("❌ Impossible de se connecter à PostgreSQL")
        logger.error("Vérifiez que PostgreSQL est démarré et que les paramètres de connexion sont corrects")
        sys.exit(1)
    
    logger.info("✅ Connexion PostgreSQL établie")
    
    # Créer les tables
    try:
        init_db()
        logger.info("✅ Tables créées avec succès")
        
        # Afficher les tables créées
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"📊 Tables disponibles: {', '.join(tables)}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création des tables: {e}")
        sys.exit(1)
    
    logger.info("🎉 Initialisation terminée avec succès!")


if __name__ == "__main__":
    main()
