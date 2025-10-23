"""
Test rapide d'extraction avec vérification des URLs détaillées
Ce script teste le spider sans sauvegarder en base de données
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Créer un SelectorEventLoop pour Windows (Playwright nécessite asyncio)
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from twisted.internet import asyncioreactor
asyncioreactor.install(loop)

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy import signals
from pprint import pprint
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)

# Statistiques collectées
stats_collector = {
    'items_with_url': 0,
    'items_without_url': 0,
    'total_items': 0,
    'sample_items': []
}


class ItemCollector:
    """Collecteur d'items pour analyse"""
    
    def __init__(self):
        self.items = []
    
    def item_scraped(self, item, response, spider):
        """Appelé quand un item est extrait"""
        self.items.append(dict(item))
        
        # Vérifier la présence de l'URL
        url_detail = item.get('url_detail', '')
        
        stats_collector['total_items'] += 1
        
        if url_detail and url_detail.strip():
            stats_collector['items_with_url'] += 1
            print(f"\n✓ Item extrait avec URL:")
            print(f"  Ref: {item.get('ref_consultation', 'N/A')}")
            print(f"  Titre: {item.get('titre', 'N/A')[:60]}...")
            print(f"  URL: {url_detail}")
        else:
            stats_collector['items_without_url'] += 1
            print(f"\n✗ Item SANS URL:")
            print(f"  Ref: {item.get('ref_consultation', 'N/A')}")
            print(f"  Titre: {item.get('titre', 'N/A')[:60]}...")
        
        # Garder quelques exemples
        if len(stats_collector['sample_items']) < 5:
            stats_collector['sample_items'].append({
                'ref': item.get('ref_consultation'),
                'titre': item.get('titre', '')[:80],
                'organisme': item.get('organisme_acronyme'),
                'url_detail': url_detail,
                'has_url': bool(url_detail and url_detail.strip())
            })


def run_test():
    """Lance le test d'extraction"""
    
    print("\n" + "="*70)
    print("  TEST D'EXTRACTION - VÉRIFICATION DES URLs DÉTAILLÉES")
    print("="*70)
    print("\nCe test va:")
    print("  1. Extraire quelques consultations du site PMMP")
    print("  2. Vérifier que le champ url_detail est bien rempli")
    print("  3. Afficher les résultats sans sauvegarder en DB")
    print("\nLe test s'arrête après avoir extrait quelques items...")
    print("="*70 + "\n")
    
    # Configuration Scrapy
    settings = get_project_settings()
    
    # Désactiver les pipelines DB pour le test
    settings['ITEM_PIPELINES'] = {
        'scraper.pipelines.ValidationPipeline': 100,
        'scraper.pipelines.CleaningPipeline': 200,
        # Pas de DB ni d'archivage pour le test
    }
    
    # Limiter le nombre de pages
    settings['CLOSESPIDER_ITEMCOUNT'] = 10  # Arrêter après 10 items
    settings['CONCURRENT_REQUESTS'] = 1
    settings['DOWNLOAD_DELAY'] = 2
    
    # Créer le processus
    process = CrawlerProcess(settings)
    
    # Créer le collecteur
    collector = ItemCollector()
    
    # Connecter le signal
    from scrapy.crawler import CrawlerRunner
    crawler = process.create_crawler('consultations_spider')
    crawler.signals.connect(collector.item_scraped, signal=signals.item_scraped)
    
    # Lancer le spider
    try:
        process.crawl('consultations_spider', statut='en_cours')
        process.start()
    except KeyboardInterrupt:
        print("\n⚠️ Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    # Afficher les résultats
    print("\n" + "="*70)
    print("  RÉSULTATS DU TEST")
    print("="*70)
    
    total = stats_collector['total_items']
    with_url = stats_collector['items_with_url']
    without_url = stats_collector['items_without_url']
    
    print(f"\n📊 Statistiques:")
    print(f"  Total d'items extraits: {total}")
    print(f"  Avec URL détaillée: {with_url} ({with_url/total*100 if total > 0 else 0:.1f}%)")
    print(f"  Sans URL détaillée: {without_url} ({without_url/total*100 if total > 0 else 0:.1f}%)")
    
    if stats_collector['sample_items']:
        print(f"\n📋 Exemples d'items extraits:")
        for i, item in enumerate(stats_collector['sample_items'], 1):
            status = "✓" if item['has_url'] else "✗"
            print(f"\n  {i}. {status} {item['ref']}")
            print(f"     Titre: {item['titre']}")
            print(f"     Organisme: {item['organisme']}")
            print(f"     URL: {item['url_detail'] or '❌ MANQUANT'}")
    
    # Verdict
    print("\n" + "="*70)
    if total > 0:
        if with_url == total:
            print("✅ EXCELLENT: Toutes les consultations ont une URL détaillée!")
            print("   Le champ url_detail sera correctement rempli dans la base.")
        elif with_url > total * 0.8:
            print("✓ BON: La majorité des consultations ont une URL détaillée.")
            print(f"  Mais {without_url} items n'ont pas d'URL. Vérifiez les logs.")
        else:
            print("⚠️ ATTENTION: Beaucoup d'items sans URL détaillée!")
            print("   Les sélecteurs dans scraper/selectors.py doivent être ajustés.")
            print("\n💡 Action recommandée:")
            print("   1. Exécuter: python scripts/test_extraction_real.py")
            print("   2. Examiner le fichier HTML généré")
            print("   3. Ajuster ConsultationsSelectors.DETAIL_LINK")
    else:
        print("❌ ÉCHEC: Aucun item n'a été extrait!")
        print("   Vérifiez la connexion au site et les sélecteurs.")
    
    print("="*70 + "\n")
    
    return 0 if with_url > 0 else 1


if __name__ == "__main__":
    sys.exit(run_test())
