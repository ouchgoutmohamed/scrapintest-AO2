-- Script d'initialisation de la base de données PMMP
-- Ce script est exécuté automatiquement au premier démarrage de PostgreSQL

-- Création de la base de données principale
CREATE DATABASE pmmp_db;

-- Création de la base de données pour Airflow (si utilisé)
CREATE DATABASE airflow_db;

-- Connexion à pmmp_db
\c pmmp_db;

-- Création d'extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Pour recherche full-text

-- Création d'un rôle de lecture seule (pour l'API)
CREATE ROLE pmmp_readonly;
GRANT CONNECT ON DATABASE pmmp_db TO pmmp_readonly;
GRANT USAGE ON SCHEMA public TO pmmp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO pmmp_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO pmmp_readonly;

-- Index pour améliorer les performances de recherche full-text
-- (À exécuter après la création des tables par SQLAlchemy)

-- CREATE INDEX IF NOT EXISTS idx_consultations_titre_trgm ON consultations USING gin (titre gin_trgm_ops);
-- CREATE INDEX IF NOT EXISTS idx_consultations_objet_trgm ON consultations USING gin (objet gin_trgm_ops);
-- CREATE INDEX IF NOT EXISTS idx_attributions_entreprise_trgm ON attributions USING gin (entreprise_nom gin_trgm_ops);

-- Vue pour les statistiques
CREATE OR REPLACE VIEW v_stats_consultations AS
SELECT 
    DATE_TRUNC('month', date_publication) AS mois,
    type_marche,
    statut,
    COUNT(*) AS nombre_consultations,
    SUM(montant_estime) AS montant_total_estime,
    AVG(montant_estime) AS montant_moyen_estime
FROM consultations
GROUP BY DATE_TRUNC('month', date_publication), type_marche, statut
ORDER BY mois DESC;

-- Vue pour les organismes les plus actifs
CREATE OR REPLACE VIEW v_top_organismes AS
SELECT 
    organisme_acronyme,
    organisme_nom_complet,
    COUNT(*) AS nombre_consultations,
    SUM(montant_estime) AS montant_total_estime
FROM consultations
GROUP BY organisme_acronyme, organisme_nom_complet
ORDER BY nombre_consultations DESC;

-- Vue pour les entreprises gagnantes
CREATE OR REPLACE VIEW v_top_attributaires AS
SELECT 
    entreprise_nom,
    entreprise_ville,
    COUNT(*) AS nombre_marches,
    SUM(montant_ttc) AS montant_total_ttc,
    AVG(montant_ttc) AS montant_moyen_ttc
FROM attributions
GROUP BY entreprise_nom, entreprise_ville
ORDER BY nombre_marches DESC;

-- Fonction pour nettoyer les anciennes données d'extraction
CREATE OR REPLACE FUNCTION clean_old_extraction_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM extraction_logs 
    WHERE date_execution < NOW() - INTERVAL '6 months';
END;
$$ LANGUAGE plpgsql;

-- Commentaires sur les tables (documentation)
COMMENT ON TABLE consultations IS 'Table principale des appels d''offres et consultations';
COMMENT ON TABLE lots IS 'Détails des lots pour les marchés subdivisés';
COMMENT ON TABLE pv_extraits IS 'Extraits des procès-verbaux publiés';
COMMENT ON TABLE attributions IS 'Résultats définitifs et attributions des marchés';
COMMENT ON TABLE achevements IS 'Rapports d''achèvement des marchés';
COMMENT ON TABLE extraction_logs IS 'Logs des exécutions du scraper pour monitoring';

-- Permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pmmp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pmmp_user;

-- Message de confirmation
DO $$
BEGIN
    RAISE NOTICE 'Base de données PMMP initialisée avec succès!';
END
$$;
