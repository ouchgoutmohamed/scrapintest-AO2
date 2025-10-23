"""
Script de test pour vérifier l'extraction des consultations et des PV
Teste les spiders consultations_spider et pv_spider
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from scraper.selectors import URLs, ConsultationsSelectors, PVSelectors

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResults:
    """Classe pour stocker les résultats des tests"""
    def __init__(self):
        self.consultations = []
        self.pv_extraits = []
        self.errors = []
        self.start_time = datetime.now()
    
    def add_consultation(self, data):
        self.consultations.append(data)
    
    def add_pv(self, data):
        self.pv_extraits.append(data)
    
    def add_error(self, error):
        self.errors.append(error)
    
    def print_summary(self):
        """Affiche un résumé des résultats"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "="*80)
        print("📊 RÉSUMÉ DES TESTS D'EXTRACTION")
        print("="*80)
        print(f"⏱️  Durée totale: {duration:.2f} secondes")
        print(f"✅ Consultations extraites: {len(self.consultations)}")
        print(f"✅ PV extraits: {len(self.pv_extraits)}")
        print(f"❌ Erreurs: {len(self.errors)}")
        print("="*80)


async def test_consultations_extraction(browser, results):
    """
    Test d'extraction des consultations
    """
    logger.info("\n" + "="*80)
    logger.info("🔍 TEST 1: EXTRACTION DES CONSULTATIONS")
    logger.info("="*80)
    
    page = await browser.new_page()
    
    try:
        # User-Agent identifiable
        await page.set_extra_http_headers({
            'User-Agent': 'PMMP-DataCollector-Test/1.0'
        })
        
        # Navigation vers la page des consultations
        logger.info(f"🌐 Navigation vers: {URLs.CONSULTATIONS_EN_COURS}")
        await page.goto(URLs.CONSULTATIONS_EN_COURS, wait_until='networkidle', timeout=30000)
        
        # Attendre le chargement
        logger.info("⏳ Attente du chargement de la page...")
        await page.wait_for_timeout(3000)
        
        # Essayer de trouver et cliquer sur un bouton de recherche ou un lien pour afficher les résultats
        try:
            # Chercher un bouton de soumission
            submit_selectors = [
                'input[type="submit"]',
                'button[type="submit"]',
                'input[value*="Rechercher"]',
                'input[value*="Consulter"]',
                'button:has-text("Rechercher")',
                'button:has-text("Consulter")'
            ]
            
            button_found = False
            for selector in submit_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        logger.info(f"🔘 Clic sur le bouton: {selector}")
                        await page.locator(selector).first.click()
                        button_found = True
                        await page.wait_for_timeout(5000)  # Attendre le chargement des résultats
                        break
                except:
                    continue
            
            if not button_found:
                logger.info("ℹ️ Aucun bouton de soumission trouvé, la page contient peut-être déjà les résultats")
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors du clic: {e}")
        
        # Capture d'écran
        screenshot_path = 'logs/test_consultations.png'
        await page.screenshot(path=screenshot_path)
        logger.info(f"📸 Capture d'écran: {screenshot_path}")
        
        # Récupérer le HTML
        html_content = await page.content()
        
        # Sauvegarder le HTML
        html_path = 'logs/test_consultations.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"💾 HTML sauvegardé: {html_path}")
        
        # Parser avec BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Analyser la structure
        logger.info("\n📋 Analyse de la structure de la page...")
        
        # Chercher les tableaux
        tables = soup.find_all('table')
        logger.info(f"Nombre de tableaux trouvés: {len(tables)}")
        
        if not tables:
            logger.warning("⚠️ Aucun tableau trouvé!")
            
            # Recherche alternative
            all_links = soup.find_all('a', href=True)
            logger.info(f"Nombre total de liens: {len(all_links)}")
            
            consultation_links = [
                link for link in all_links 
                if 'consultation' in link.get('href', '').lower() or 
                   'details' in link.get('href', '').lower()
            ]
            logger.info(f"Liens de consultation potentiels: {len(consultation_links)}")
            
            # Afficher quelques exemples
            if consultation_links:
                logger.info("\n📌 Exemples de liens trouvés:")
                for i, link in enumerate(consultation_links[:5], 1):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)[:60]
                    logger.info(f"  {i}. {text}")
                    logger.info(f"     URL: {href}")
        else:
            # Analyser le premier tableau
            logger.info("\n🔍 Analyse du tableau principal:")
            first_table = tables[0]
            
            # Extraire les en-têtes
            headers = first_table.find_all('th')
            if headers:
                logger.info("📌 En-têtes du tableau:")
                for i, header in enumerate(headers, 1):
                    logger.info(f"  {i}. {header.get_text(strip=True)}")
            
            # Extraire les lignes de données
            rows = first_table.find_all('tr')[1:]  # Sauter l'en-tête
            logger.info(f"\n📊 Nombre de consultations trouvées: {len(rows)}")
            
            # Extraire les 5 premières consultations
            for idx, row in enumerate(rows[:5], 1):
                cells = row.find_all(['td', 'th'])
                
                if not cells:
                    continue
                
                consultation = {
                    'index': idx,
                    'ref_consultation': None,
                    'titre': None,
                    'organisme': None,
                    'type_marche': None,
                    'date_publication': None,
                    'date_limite': None,
                    'statut': None,
                    'url_detail': None,
                    'extraction_date': datetime.now().isoformat()
                }
                
                # Extraire les données
                logger.info(f"\n  📄 Consultation #{idx}:")
                
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    
                    # Mapper les colonnes (à ajuster selon la structure réelle)
                    if i == 0 and text:
                        consultation['ref_consultation'] = text
                        logger.info(f"    Référence: {text}")
                    elif i == 1 and text:
                        consultation['titre'] = text[:80]
                        logger.info(f"    Titre: {text[:80]}")
                    elif i == 2 and text:
                        consultation['organisme'] = text
                        logger.info(f"    Organisme: {text}")
                    elif i == 3 and text:
                        consultation['type_marche'] = text
                        logger.info(f"    Type: {text}")
                    elif i == 4 and text:
                        consultation['date_publication'] = text
                        logger.info(f"    Date publication: {text}")
                    elif i == 5 and text:
                        consultation['date_limite'] = text
                        logger.info(f"    Date limite: {text}")
                    
                    # Chercher un lien
                    link = cell.find('a', href=True)
                    if link:
                        href = link.get('href', '')
                        if href.startswith('/'):
                            full_url = URLs.BASE + href
                        elif not href.startswith('http'):
                            full_url = URLs.BASE + '/' + href
                        else:
                            full_url = href
                        consultation['url_detail'] = full_url
                        logger.info(f"    🔗 URL: {full_url}")
                
                results.add_consultation(consultation)
            
            logger.info(f"\n✅ {len(results.consultations)} consultations extraites avec succès")
    
    except Exception as e:
        error_msg = f"❌ Erreur lors de l'extraction des consultations: {str(e)}"
        logger.error(error_msg)
        results.add_error(error_msg)
    
    finally:
        await page.close()


async def test_pv_extraction(browser, results):
    """
    Test d'extraction des PV
    """
    logger.info("\n" + "="*80)
    logger.info("🔍 TEST 2: EXTRACTION DES PV (PROCÈS-VERBAUX)")
    logger.info("="*80)
    
    page = await browser.new_page()
    
    try:
        # User-Agent identifiable
        await page.set_extra_http_headers({
            'User-Agent': 'PMMP-DataCollector-Test/1.0'
        })
        
        # Navigation vers la page des PV
        logger.info(f"🌐 Navigation vers: {URLs.PV_EXTRAITS}")
        await page.goto(URLs.PV_EXTRAITS, wait_until='networkidle', timeout=30000)
        
        # Attendre le chargement
        logger.info("⏳ Attente du chargement...")
        await page.wait_for_timeout(3000)
        
        # Capture d'écran
        screenshot_path = 'logs/test_pv.png'
        await page.screenshot(path=screenshot_path)
        logger.info(f"📸 Capture d'écran: {screenshot_path}")
        
        # Récupérer le HTML
        html_content = await page.content()
        
        # Sauvegarder le HTML
        html_path = 'logs/test_pv.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"💾 HTML sauvegardé: {html_path}")
        
        # Parser avec BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Analyser la structure
        logger.info("\n📋 Analyse de la structure de la page...")
        
        # Chercher les tableaux
        tables = soup.find_all('table')
        logger.info(f"Nombre de tableaux trouvés: {len(tables)}")
        
        if not tables:
            logger.warning("⚠️ Aucun tableau trouvé!")
            
            # Recherche alternative
            all_links = soup.find_all('a', href=True)
            logger.info(f"Nombre total de liens: {len(all_links)}")
            
            pv_links = [
                link for link in all_links 
                if 'pv' in link.get('href', '').lower() or 
                   'proces-verbal' in link.get('href', '').lower()
            ]
            logger.info(f"Liens de PV potentiels: {len(pv_links)}")
            
            # Afficher quelques exemples
            if pv_links:
                logger.info("\n📌 Exemples de liens trouvés:")
                for i, link in enumerate(pv_links[:5], 1):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)[:60]
                    logger.info(f"  {i}. {text}")
                    logger.info(f"     URL: {href}")
        else:
            # Analyser le premier tableau
            logger.info("\n🔍 Analyse du tableau principal:")
            first_table = tables[0]
            
            # Extraire les en-têtes
            headers = first_table.find_all('th')
            if headers:
                logger.info("📌 En-têtes du tableau:")
                for i, header in enumerate(headers, 1):
                    logger.info(f"  {i}. {header.get_text(strip=True)}")
            
            # Extraire les lignes de données
            rows = first_table.find_all('tr')[1:]  # Sauter l'en-tête
            logger.info(f"\n📊 Nombre de PV trouvés: {len(rows)}")
            
            # Extraire les 5 premiers PV
            for idx, row in enumerate(rows[:5], 1):
                cells = row.find_all(['td', 'th'])
                
                if not cells:
                    continue
                
                pv = {
                    'index': idx,
                    'ref_consultation': None,
                    'organisme': None,
                    'type_pv': None,
                    'date_seance': None,
                    'date_publication': None,
                    'url_pv': None,
                    'extraction_date': datetime.now().isoformat()
                }
                
                # Extraire les données
                logger.info(f"\n  📄 PV #{idx}:")
                
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    
                    # Mapper les colonnes (à ajuster selon la structure réelle)
                    if i == 0 and text:
                        pv['ref_consultation'] = text
                        logger.info(f"    Référence: {text}")
                    elif i == 1 and text:
                        pv['organisme'] = text
                        logger.info(f"    Organisme: {text}")
                    elif i == 2 and text:
                        pv['type_pv'] = text
                        logger.info(f"    Type PV: {text}")
                    elif i == 3 and text:
                        pv['date_seance'] = text
                        logger.info(f"    Date séance: {text}")
                    elif i == 4 and text:
                        pv['date_publication'] = text
                        logger.info(f"    Date publication: {text}")
                    
                    # Chercher un lien
                    link = cell.find('a', href=True)
                    if link:
                        href = link.get('href', '')
                        if href.startswith('/'):
                            full_url = URLs.BASE + href
                        elif not href.startswith('http'):
                            full_url = URLs.BASE + '/' + href
                        else:
                            full_url = href
                        pv['url_pv'] = full_url
                        logger.info(f"    🔗 URL: {full_url}")
                
                results.add_pv(pv)
            
            logger.info(f"\n✅ {len(results.pv_extraits)} PV extraits avec succès")
    
    except Exception as e:
        error_msg = f"❌ Erreur lors de l'extraction des PV: {str(e)}"
        logger.error(error_msg)
        results.add_error(error_msg)
    
    finally:
        await page.close()


async def main():
    """Fonction principale"""
    logger.info("="*80)
    logger.info("🚀 DÉBUT DES TESTS D'EXTRACTION")
    logger.info("="*80)
    
    results = TestResults()
    
    # Créer le dossier logs s'il n'existe pas
    os.makedirs('logs', exist_ok=True)
    
    async with async_playwright() as p:
        # Lancer le navigateur
        logger.info("📱 Lancement du navigateur Chromium...")
        browser = await p.chromium.launch(
            headless=False,  # Mode visible pour voir ce qui se passe
            slow_mo=100  # Ralentir un peu pour mieux observer
        )
        
        try:
            # Test 1: Consultations
            await test_consultations_extraction(browser, results)
            
            # Pause entre les tests
            await asyncio.sleep(2)
            
            # Test 2: PV
            await test_pv_extraction(browser, results)
            
        finally:
            await browser.close()
            logger.info("\n🔒 Navigateur fermé")
    
    # Afficher le résumé
    results.print_summary()
    
    # Afficher les détails si disponibles
    if results.consultations:
        print("\n📋 CONSULTATIONS EXTRAITES:")
        for cons in results.consultations:
            print(f"  - Réf: {cons.get('ref_consultation', 'N/A')}")
            print(f"    Titre: {cons.get('titre', 'N/A')}")
            print(f"    Organisme: {cons.get('organisme', 'N/A')}")
            if cons.get('url_detail'):
                print(f"    🔗 URL: {cons['url_detail']}")
            print()
    
    if results.pv_extraits:
        print("\n📋 PV EXTRAITS:")
        for pv in results.pv_extraits:
            print(f"  - Réf: {pv.get('ref_consultation', 'N/A')}")
            print(f"    Organisme: {pv.get('organisme', 'N/A')}")
            print(f"    Type: {pv.get('type_pv', 'N/A')}")
            if pv.get('url_pv'):
                print(f"    🔗 URL: {pv['url_pv']}")
            print()
    
    if results.errors:
        print("\n❌ ERREURS RENCONTRÉES:")
        for error in results.errors:
            print(f"  - {error}")
    
    # Sauvegarder les résultats en JSON
    import json
    results_file = f'logs/test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'consultations': results.consultations,
            'pv_extraits': results.pv_extraits,
            'errors': results.errors,
            'summary': {
                'total_consultations': len(results.consultations),
                'total_pv': len(results.pv_extraits),
                'total_errors': len(results.errors),
                'test_date': results.start_time.isoformat()
            }
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n💾 Résultats sauvegardés: {results_file}")
    
    # Code de sortie
    return 0 if not results.errors else 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
