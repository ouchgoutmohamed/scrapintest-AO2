"""
Test d'extraction réel sur le site PMMP
Vérifie que les URLs détaillées sont bien capturées
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from scraper.selectors import URLs, ConsultationsSelectors

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_extract_consultations():
    """
    Test d'extraction de quelques consultations avec leurs URLs détaillées
    """
    logger.info("🚀 Début du test d'extraction...")
    
    results = []
    
    async with async_playwright() as p:
        # Lancer le navigateur
        logger.info("📱 Lancement du navigateur Chromium...")
        browser = await p.chromium.launch(headless=False)  # headless=False pour voir ce qui se passe
        page = await browser.new_page()
        
        # User-Agent identifiable
        await page.set_extra_http_headers({
            'User-Agent': 'PMMP-DataCollector/1.0-TEST (+mailto:contact@votredomaine.com)'
        })
        
        try:
            # Naviguer vers la page des consultations en cours
            logger.info(f"🌐 Navigation vers: {URLs.CONSULTATIONS_EN_COURS}")
            await page.goto(URLs.CONSULTATIONS_EN_COURS, wait_until='networkidle', timeout=30000)
            
            # Attendre que la page soit chargée
            logger.info("⏳ Attente du chargement de la page...")
            await page.wait_for_timeout(3000)
            
            # Prendre une capture d'écran pour debug
            await page.screenshot(path='logs/test_page_consultations.png')
            logger.info("📸 Capture d'écran sauvegardée: logs/test_page_consultations.png")
            
            # Récupérer le HTML
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Sauvegarder le HTML pour analyse
            with open('logs/test_page_consultations.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info("💾 HTML sauvegardé: logs/test_page_consultations.html")
            
            # Analyser la structure de la page
            logger.info("\n" + "="*60)
            logger.info("📊 ANALYSE DE LA STRUCTURE DE LA PAGE")
            logger.info("="*60)
            
            # Chercher les tableaux
            tables = soup.find_all('table')
            logger.info(f"Nombre de tableaux trouvés: {len(tables)}")
            
            if not tables:
                logger.warning("⚠️ Aucun tableau trouvé. La structure du site a peut-être changé.")
                logger.info("\nRecherche d'autres structures possibles...")
                
                # Rechercher des divs ou autres conteneurs
                divs_with_data = soup.find_all('div', class_=lambda x: x and ('result' in x.lower() or 'consultation' in x.lower()))
                logger.info(f"Divs avec 'result' ou 'consultation': {len(divs_with_data)}")
                
                # Rechercher tous les liens
                all_links = soup.find_all('a', href=True)
                logger.info(f"Total de liens trouvés: {len(all_links)}")
                
                # Filtrer les liens qui pourraient être des consultations
                consultation_links = [
                    link for link in all_links 
                    if 'consultation' in link.get('href', '').lower() or 
                       'details' in link.get('href', '').lower()
                ]
                logger.info(f"Liens potentiels de consultation: {len(consultation_links)}")
                
                if consultation_links:
                    logger.info("\n📋 Exemples de liens trouvés:")
                    for i, link in enumerate(consultation_links[:5], 1):
                        href = link.get('href', '')
                        text = link.get_text(strip=True)[:50]
                        logger.info(f"  {i}. {text}")
                        logger.info(f"     URL: {href}")
                
            else:
                # Analyser le premier tableau
                logger.info(f"\n🔍 Analyse du premier tableau:")
                first_table = tables[0]
                
                # Compter les lignes
                rows = first_table.find_all('tr')
                logger.info(f"  Nombre de lignes: {len(rows)}")
                
                if rows:
                    # Analyser l'en-tête
                    headers = rows[0].find_all(['th', 'td'])
                    if headers:
                        logger.info(f"\n  📌 En-têtes du tableau:")
                        for i, header in enumerate(headers, 1):
                            logger.info(f"    {i}. {header.get_text(strip=True)}")
                    
                    # Analyser quelques lignes de données
                    logger.info(f"\n  📋 Extraction des {min(5, len(rows)-1)} premières consultations:\n")
                    
                    for idx, row in enumerate(rows[1:6], 1):  # Sauter l'en-tête, prendre 5 lignes
                        cells = row.find_all(['td', 'th'])
                        
                        if not cells:
                            continue
                        
                        consultation_data = {
                            'index': idx,
                            'ref_consultation': None,
                            'titre': None,
                            'organisme': None,
                            'url_detail': None,
                        }
                        
                        # Extraire les données de chaque cellule
                        logger.info(f"  Consultation #{idx}:")
                        for i, cell in enumerate(cells, 1):
                            text = cell.get_text(strip=True)
                            if text:
                                logger.info(f"    Colonne {i}: {text[:80]}")
                            
                            # Chercher un lien dans la cellule
                            link = cell.find('a', href=True)
                            if link:
                                href = link.get('href', '')
                                full_url = URLs.BASE + href if href.startswith('/') else href
                                consultation_data['url_detail'] = full_url
                                logger.info(f"    🔗 Lien trouvé: {full_url}")
                        
                        # Essayer d'identifier les champs
                        if len(cells) >= 1:
                            consultation_data['ref_consultation'] = cells[0].get_text(strip=True)
                        if len(cells) >= 2:
                            consultation_data['titre'] = cells[1].get_text(strip=True)
                        if len(cells) >= 3:
                            consultation_data['organisme'] = cells[2].get_text(strip=True)
                        
                        results.append(consultation_data)
                        
                        logger.info(f"    ✅ Données extraites:")
                        logger.info(f"       Référence: {consultation_data['ref_consultation']}")
                        logger.info(f"       Titre: {consultation_data['titre'][:50] if consultation_data['titre'] else 'N/A'}...")
                        logger.info(f"       Organisme: {consultation_data['organisme']}")
                        logger.info(f"       URL détail: {consultation_data['url_detail'] or '❌ NON TROUVÉ'}")
                        logger.info("")
            
            # Résumé des résultats
            logger.info("\n" + "="*60)
            logger.info("📈 RÉSUMÉ DU TEST")
            logger.info("="*60)
            logger.info(f"Consultations extraites: {len(results)}")
            
            consultations_avec_url = sum(1 for r in results if r['url_detail'])
            logger.info(f"Avec URL détaillée: {consultations_avec_url}/{len(results)}")
            
            if results:
                logger.info("\n✅ Données collectées:")
                for i, res in enumerate(results, 1):
                    logger.info(f"\n  {i}. Réf: {res['ref_consultation']}")
                    logger.info(f"     Titre: {res['titre'][:60] if res['titre'] else 'N/A'}...")
                    logger.info(f"     URL: {res['url_detail'] or '❌ MANQUANT'}")
            
            # Vérifier si les URLs sont bien capturées
            if consultations_avec_url == 0 and len(results) > 0:
                logger.error("\n❌ PROBLÈME: Aucune URL détaillée n'a été trouvée!")
                logger.warning("Les sélecteurs dans scraper/selectors.py doivent être ajustés.")
                logger.info("\n💡 Suggestions:")
                logger.info("  1. Examiner logs/test_page_consultations.html")
                logger.info("  2. Identifier la structure HTML réelle des liens")
                logger.info("  3. Mettre à jour ConsultationsSelectors.DETAIL_LINK dans scraper/selectors.py")
            elif consultations_avec_url > 0:
                logger.info(f"\n✅ SUCCESS: {consultations_avec_url} URL(s) détaillée(s) capturée(s)!")
                logger.info("Le champ url_detail sera correctement rempli dans la base de données.")
            
        except Exception as e:
            logger.error(f"\n❌ Erreur lors de l'extraction: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        finally:
            await browser.close()
            logger.info("\n🏁 Test terminé")
    
    return results


async def test_detail_page():
    """
    Test de l'extraction d'une page de détail
    """
    logger.info("\n" + "="*60)
    logger.info("🔍 TEST D'UNE PAGE DE DÉTAIL")
    logger.info("="*60)
    
    # URL d'exemple (à remplacer par une URL réelle)
    # Cette URL est fictive, vous devrez la remplacer par une URL réelle du site
    test_url = URLs.DETAIL_CONSULTATION + "&refConsultation=TEST-2024-001&orgAcronyme=ONEE"
    
    logger.info(f"Note: Pour tester une page de détail, remplacer test_url par une URL réelle")
    logger.info(f"Exemple d'URL: {test_url}")


def main():
    """Point d'entrée principal"""
    print("\n" + "="*60)
    print("  PMMP SCRAPER - TEST D'EXTRACTION RÉEL")
    print("="*60)
    print("\nCe test va:")
    print("  1. Se connecter au site PMMP")
    print("  2. Extraire quelques consultations")
    print("  3. Vérifier que les URLs détaillées sont capturées")
    print("  4. Sauvegarder les résultats pour analyse")
    print("\nATTENTION: Ce test effectue de vraies requêtes au site PMMP")
    print("           Respectez les bonnes pratiques (délais, User-Agent)")
    print("\n" + "="*60 + "\n")
    
    # Créer le dossier logs s'il n'existe pas
    os.makedirs('logs', exist_ok=True)
    
    # Lancer le test
    try:
        results = asyncio.run(test_extract_consultations())
        
        # Sauvegarder les résultats en JSON
        import json
        with open('logs/test_extraction_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 Résultats sauvegardés: logs/test_extraction_results.json")
        
        return 0 if results else 1
    
    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrompu par l'utilisateur")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
