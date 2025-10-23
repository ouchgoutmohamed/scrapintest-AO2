"""
Pipelines de traitement des items extraits
Validation, nettoyage, déduplication, archivage et stockage en base
"""
import os
import hashlib
import json
from datetime import datetime
from pathlib import Path
import logging
from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from database.connection import SessionLocal
from database.models import (
    Consultation, Lot, PVExtrait, Attribution, Achevement, ExtractionLog
)
from prometheus_client import Counter, Histogram


# Métriques Prometheus
items_processed = Counter('pmmp_items_processed_total', 'Total items processed', ['type'])
items_saved = Counter('pmmp_items_saved_total', 'Total items saved to database', ['type'])
items_dropped = Counter('pmmp_items_dropped_total', 'Total items dropped', ['reason'])
processing_time = Histogram('pmmp_item_processing_seconds', 'Time to process item')


class ValidationPipeline:
    """Valide que les items contiennent les champs obligatoires"""
    
    required_fields = {
        'ConsultationItem': ['ref_consultation', 'titre', 'organisme_acronyme'],
        'LotItem': ['ref_consultation', 'numero_lot'],
        'PVExtraitItem': ['ref_consultation', 'date_publication_pv'],
        'AttributionItem': ['ref_consultation', 'entreprise_nom'],
        'AchevementItem': ['ref_consultation', 'date_achevement'],
    }
    
    def process_item(self, item, spider):
        item_type = item.__class__.__name__
        required = self.required_fields.get(item_type, [])
        
        for field in required:
            if not item.get(field):
                items_dropped.labels(reason='missing_required_field').inc()
                raise DropItem(f"Champ obligatoire manquant: {field} dans {item_type}")
        
        items_processed.labels(type=item_type).inc()
        return item


class CleaningPipeline:
    """Nettoie et normalise les données"""
    
    def process_item(self, item, spider):
        # Nettoyer les chaînes de caractères
        for field, value in item.items():
            if isinstance(value, str):
                # Supprimer espaces superflus
                item[field] = ' '.join(value.split())
                # Limiter la longueur si nécessaire
                if field in ['titre', 'objet', 'designation']:
                    item[field] = value[:1000] if len(value) > 1000 else value
        
        # Convertir les montants en float si ce sont des strings
        amount_fields = ['montant_estime', 'cautionnement_provisoire', 'montant_ht', 'montant_ttc']
        for field in amount_fields:
            if field in item and isinstance(item[field], str):
                try:
                    item[field] = float(item[field].replace(',', '.'))
                except (ValueError, AttributeError):
                    item[field] = None
        
        return item


class DeduplicationPipeline:
    """Évite les doublons en utilisant un cache des refs déjà traitées"""
    
    def __init__(self):
        self.seen_refs = set()
    
    def open_spider(self, spider):
        # Charger les refs existantes depuis la DB
        db = SessionLocal()
        try:
            refs = db.query(Consultation.ref_consultation).all()
            self.seen_refs = {ref[0] for ref in refs}
            spider.logger.info(f"Chargé {len(self.seen_refs)} références existantes")
        finally:
            db.close()
    
    def process_item(self, item, spider):
        item_type = item.__class__.__name__
        
        if item_type == 'ConsultationItem':
            ref = item.get('ref_consultation')
            if ref in self.seen_refs:
                spider.logger.debug(f"Doublon détecté: {ref}")
                items_dropped.labels(reason='duplicate').inc()
                raise DropItem(f"Consultation déjà extraite: {ref}")
            self.seen_refs.add(ref)
        
        return item


class ArchivePipeline:
    """Archive les pages HTML brutes pour référence future"""
    
    def __init__(self, archive_path, enable_archiving):
        self.archive_path = Path(archive_path)
        self.enable_archiving = enable_archiving
    
    @classmethod
    def from_crawler(cls, crawler):
        archive_path = crawler.settings.get('ARCHIVE_STORAGE_PATH', './data/archives')
        enable = crawler.settings.get('ENABLE_ARCHIVING', True)
        return cls(archive_path, enable)
    
    def open_spider(self, spider):
        if self.enable_archiving:
            self.archive_path.mkdir(parents=True, exist_ok=True)
            spider.logger.info(f"Archivage activé dans {self.archive_path}")
    
    def process_item(self, item, spider):
        if not self.enable_archiving or 'page_html' not in item:
            return item
        
        try:
            # Créer un nom de fichier basé sur la ref et le hash
            ref = item.get('ref_consultation', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            html_content = item['page_html']
            
            # Hash pour garantir l'unicité
            content_hash = hashlib.md5(html_content.encode()).hexdigest()[:8]
            filename = f"{ref}_{timestamp}_{content_hash}.html"
            
            filepath = self.archive_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Stocker le chemin relatif dans l'item
            item['page_html_archivee'] = str(filepath)
            
            # Supprimer le HTML brut de l'item pour ne pas le stocker en DB
            del item['page_html']
            
            spider.logger.debug(f"Page archivée: {filename}")
        
        except Exception as e:
            spider.logger.error(f"Erreur lors de l'archivage: {e}")
        
        return item


class DatabasePipeline:
    """Stocke les items dans PostgreSQL"""
    
    def __init__(self):
        self.session = None
        self.stats = {
            'inserted': 0,
            'updated': 0,
            'errors': 0
        }
    
    def open_spider(self, spider):
        self.session = SessionLocal()
        spider.logger.info("Connexion à la base de données établie")
    
    def close_spider(self, spider):
        if self.session:
            self.session.close()
        spider.logger.info(f"Pipeline DB - Stats: {self.stats}")
    
    def process_item(self, item, spider):
        item_type = item.__class__.__name__
        
        try:
            if item_type == 'ConsultationItem':
                self._save_consultation(item, spider)
            elif item_type == 'LotItem':
                self._save_lot(item, spider)
            elif item_type == 'PVExtraitItem':
                self._save_pv(item, spider)
            elif item_type == 'AttributionItem':
                self._save_attribution(item, spider)
            elif item_type == 'AchevementItem':
                self._save_achevement(item, spider)
            
            items_saved.labels(type=item_type).inc()
            return item
        
        except Exception as e:
            self.stats['errors'] += 1
            spider.logger.error(f"Erreur DB pour {item_type}: {e}")
            items_dropped.labels(reason='database_error').inc()
            raise DropItem(f"Erreur base de données: {e}")
    
    def _save_consultation(self, item, spider):
        """Sauvegarde ou met à jour une consultation"""
        ref = item['ref_consultation']
        
        # Vérifier si existe déjà
        existing = self.session.query(Consultation).filter_by(
            ref_consultation=ref
        ).first()
        
        if existing:
            # Mise à jour
            for key, value in item.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            existing.date_derniere_maj = datetime.now()
            self.stats['updated'] += 1
            spider.logger.debug(f"Consultation mise à jour: {ref}")
        else:
            # Insertion
            consultation = Consultation(**{k: v for k, v in item.items() if k != 'page_html'})
            self.session.add(consultation)
            self.stats['inserted'] += 1
            spider.logger.debug(f"Nouvelle consultation: {ref}")
        
        self.session.commit()
    
    def _save_lot(self, item, spider):
        """Sauvegarde un lot"""
        lot = Lot(**item)
        self.session.merge(lot)  # Insert or update
        self.session.commit()
        self.stats['inserted'] += 1
    
    def _save_pv(self, item, spider):
        """Sauvegarde un PV"""
        pv = PVExtrait(**{k: v for k, v in item.items() if k != 'page_html'})
        self.session.merge(pv)
        self.session.commit()
        self.stats['inserted'] += 1
    
    def _save_attribution(self, item, spider):
        """Sauvegarde une attribution"""
        attribution = Attribution(**{k: v for k, v in item.items() if k != 'page_html'})
        self.session.merge(attribution)
        self.session.commit()
        self.stats['inserted'] += 1
    
    def _save_achevement(self, item, spider):
        """Sauvegarde un achèvement"""
        achevement = Achevement(**{k: v for k, v in item.items() if k != 'page_html'})
        self.session.merge(achevement)
        self.session.commit()
        self.stats['inserted'] += 1


class MetricsPipeline:
    """Collecte des métriques pour Prometheus"""
    
    def process_item(self, item, spider):
        # Les métriques sont déjà collectées par les autres pipelines
        return item
