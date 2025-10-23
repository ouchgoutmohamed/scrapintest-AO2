"""
Configuration et connexion à la base de données PostgreSQL
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import logging

# Charger les variables d'environnement
load_dotenv()

# Configuration du logger
logger = logging.getLogger(__name__)

# Récupération de l'URL de connexion
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://pmmp_user:pmmp_password@localhost:5432/pmmp_db')

# Configuration du moteur SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Vérifie la connexion avant utilisation
    pool_recycle=3600,   # Recycle les connexions après 1 heure
    echo=os.getenv('DEBUG', 'False') == 'True'  # Log SQL si DEBUG=True
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Session thread-safe pour utilisation concurrente
ScopedSession = scoped_session(SessionLocal)


def get_db():
    """
    Générateur de session pour dependency injection (FastAPI)
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialise la base de données en créant toutes les tables
    """
    from database.models import Base
    
    logger.info("Création des tables dans la base de données...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables créées avec succès!")


def drop_all_tables():
    """
    ATTENTION: Supprime toutes les tables de la base de données
    À utiliser uniquement en développement!
    """
    from database.models import Base
    
    logger.warning("ATTENTION: Suppression de toutes les tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Tables supprimées!")


def check_connection():
    """
    Vérifie la connexion à la base de données
    
    Returns:
        bool: True si la connexion est réussie, False sinon
    """
    try:
        connection = engine.connect()
        connection.close()
        logger.info("Connexion à la base de données réussie!")
        return True
    except Exception as e:
        logger.error(f"Erreur de connexion à la base de données: {e}")
        return False


if __name__ == "__main__":
    # Test de connexion
    logging.basicConfig(level=logging.INFO)
    
    if check_connection():
        print("✅ Connexion PostgreSQL OK")
        
        # Initialisation des tables (décommentez si nécessaire)
        # init_db()
    else:
        print("❌ Échec de connexion PostgreSQL")
