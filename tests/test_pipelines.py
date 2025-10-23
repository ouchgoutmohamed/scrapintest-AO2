"""
Tests unitaires pour les pipelines
"""
import pytest
from scraper.pipelines import ValidationPipeline, CleaningPipeline
from scraper.items import ConsultationItem
from scrapy.exceptions import DropItem


def test_validation_pipeline_valid_item():
    """Test qu'un item valide passe la validation"""
    pipeline = ValidationPipeline()
    item = ConsultationItem()
    item['ref_consultation'] = 'TEST-001'
    item['titre'] = 'Test consultation'
    item['organisme_acronyme'] = 'TEST'
    
    result = pipeline.process_item(item, None)
    assert result == item


def test_validation_pipeline_missing_field():
    """Test qu'un item invalide est rejeté"""
    pipeline = ValidationPipeline()
    item = ConsultationItem()
    item['ref_consultation'] = 'TEST-001'
    # Manque 'titre' et 'organisme_acronyme'
    
    with pytest.raises(DropItem):
        pipeline.process_item(item, None)


def test_cleaning_pipeline():
    """Test le nettoyage des données"""
    pipeline = CleaningPipeline()
    item = ConsultationItem()
    item['ref_consultation'] = 'TEST-001'
    item['titre'] = '  Test   avec   espaces  '
    item['montant_estime'] = '1 234 567,89'
    
    result = pipeline.process_item(item, None)
    
    assert result['titre'] == 'Test avec espaces'
    # Le montant devrait être converti en float
    # assert isinstance(result['montant_estime'], float)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
