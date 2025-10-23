"""
Script de test du scraper
Teste l'extraction d'une page sans sauvegarder en DB
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import logging

logging.basicConfig(level=logging.INFO)


def test_consultations_spider():
    """Test du spider consultations"""
    print("🧪 Test du spider consultations...")
    
    settings = get_project_settings()
    # Désactiver le pipeline DB pour le test
    settings['ITEM_PIPELINES'] = {
        'scraper.pipelines.ValidationPipeline': 100,
        'scraper.pipelines.CleaningPipeline': 200,
    }
    
    process = CrawlerProcess(settings)
    process.crawl('consultations_spider', statut='en_cours')
    process.start()


def test_pv_spider():
    """Test du spider PV"""
    print("🧪 Test du spider PV...")
    
    settings = get_project_settings()
    settings['ITEM_PIPELINES'] = {
        'scraper.pipelines.ValidationPipeline': 100,
        'scraper.pipelines.CleaningPipeline': 200,
    }
    
    process = CrawlerProcess(settings)
    process.crawl('pv_spider')
    process.start()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'pv':
        test_pv_spider()
    else:
        test_consultations_spider()
