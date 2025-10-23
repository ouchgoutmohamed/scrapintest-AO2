"""
Script pour exporter les données vers différents formats
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from database.models import Consultation, Attribution
import csv
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def export_consultations_to_csv(output_file='consultations_export.csv'):
    """Exporte toutes les consultations en CSV"""
    db = SessionLocal()
    
    try:
        consultations = db.query(Consultation).all()
        logger.info(f"📊 Export de {len(consultations)} consultations...")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # En-têtes
            writer.writerow([
                'Référence', 'Titre', 'Organisme', 'Type', 'Statut',
                'Date Publication', 'Date Limite', 'Montant Estimé'
            ])
            
            # Données
            for c in consultations:
                writer.writerow([
                    c.ref_consultation,
                    c.titre,
                    c.organisme_acronyme,
                    c.type_marche,
                    c.statut,
                    c.date_publication.isoformat() if c.date_publication else '',
                    c.date_limite.isoformat() if c.date_limite else '',
                    c.montant_estime or ''
                ])
        
        logger.info(f"✅ Export CSV réussi: {output_file}")
    
    finally:
        db.close()


def export_attributions_to_json(output_file='attributions_export.json'):
    """Exporte toutes les attributions en JSON"""
    db = SessionLocal()
    
    try:
        attributions = db.query(Attribution).all()
        logger.info(f"📊 Export de {len(attributions)} attributions...")
        
        data = []
        for a in attributions:
            data.append({
                'ref_consultation': a.ref_consultation,
                'organisme': a.organisme_acronyme,
                'entreprise': a.entreprise_nom,
                'montant_ttc': float(a.montant_ttc) if a.montant_ttc else None,
                'date_attribution': a.date_attribution.isoformat() if a.date_attribution else None,
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Export JSON réussi: {output_file}")
    
    finally:
        db.close()


if __name__ == "__main__":
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    export_consultations_to_csv(f'data/exports/consultations_{timestamp}.csv')
    export_attributions_to_json(f'data/exports/attributions_{timestamp}.json')
    
    logger.info("🎉 Exports terminés!")
