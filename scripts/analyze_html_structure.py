"""
Analyseur de structure HTML pour identifier les sélecteurs corrects
Permet d'analyser une page sauvegardée pour trouver les bons sélecteurs
"""
import sys
from bs4 import BeautifulSoup
from pathlib import Path


def analyze_html_file(filepath):
    """Analyse un fichier HTML pour identifier la structure"""
    
    print("\n" + "="*70)
    print(f"  ANALYSE DE: {filepath}")
    print("="*70 + "\n")
    
    if not Path(filepath).exists():
        print(f"❌ Fichier non trouvé: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Analyser les tableaux
    print("📊 [1] TABLEAUX TROUVÉS")
    print("-" * 70)
    tables = soup.find_all('table')
    print(f"Nombre de tableaux: {len(tables)}\n")
    
    for i, table in enumerate(tables, 1):
        print(f"Tableau #{i}:")
        
        # Classes du tableau
        classes = table.get('class', [])
        print(f"  Classes: {', '.join(classes) if classes else 'Aucune'}")
        
        # ID
        table_id = table.get('id', '')
        print(f"  ID: {table_id if table_id else 'Aucun'}")
        
        # Nombre de lignes
        rows = table.find_all('tr')
        print(f"  Lignes: {len(rows)}")
        
        # En-têtes
        headers = table.find_all('th')
        if headers:
            print(f"  En-têtes: {[h.get_text(strip=True) for h in headers[:5]]}")
        
        # Première ligne de données
        if len(rows) > 1:
            first_data_row = rows[1]
            cells = first_data_row.find_all(['td', 'th'])
            print(f"  Colonnes de données: {len(cells)}")
            
            # Afficher le contenu de chaque cellule
            print("  Exemple de données:")
            for j, cell in enumerate(cells[:5], 1):
                text = cell.get_text(strip=True)[:50]
                has_link = cell.find('a', href=True) is not None
                print(f"    Col {j}: {text}{'  [LIEN]' if has_link else ''}")
        
        print()
    
    # 2. Analyser tous les liens
    print("\n🔗 [2] LIENS (URLs)")
    print("-" * 70)
    all_links = soup.find_all('a', href=True)
    print(f"Total de liens: {len(all_links)}\n")
    
    # Filtrer les liens de consultation/détail
    detail_links = [
        link for link in all_links
        if any(keyword in link.get('href', '').lower() 
               for keyword in ['detail', 'consultation', 'pp', 'annonce'])
    ]
    
    print(f"Liens potentiels de consultation: {len(detail_links)}")
    
    if detail_links:
        print("\nExemples de liens de consultation:")
        for i, link in enumerate(detail_links[:10], 1):
            href = link.get('href', '')
            text = link.get_text(strip=True)[:60]
            classes = ' '.join(link.get('class', []))
            print(f"\n  {i}. Texte: {text}")
            print(f"     URL: {href}")
            print(f"     Classes: {classes if classes else 'Aucune'}")
    
    # 3. Patterns des URLs
    print("\n\n📋 [3] PATTERNS DES URLs")
    print("-" * 70)
    
    unique_patterns = set()
    for link in detail_links[:20]:
        href = link.get('href', '')
        # Extraire le pattern (partie avant les paramètres)
        base_url = href.split('?')[0] if '?' in href else href
        unique_patterns.add(base_url)
    
    print("Patterns d'URLs trouvés:")
    for pattern in sorted(unique_patterns):
        print(f"  - {pattern}")
    
    # 4. Proposer des sélecteurs CSS
    print("\n\n💡 [4] SÉLECTEURS CSS RECOMMANDÉS")
    print("-" * 70)
    
    if tables:
        table = tables[0]
        table_classes = ' '.join(table.get('class', []))
        table_id = table.get('id', '')
        
        print("\nPour le tableau principal:")
        if table_id:
            print(f"  TABLE = 'table#{table_id}'")
        elif table_classes:
            print(f"  TABLE = 'table.{table_classes.split()[0]}'")
        else:
            print(f"  TABLE = 'table'  # (pas de classe/id spécifique)")
        
        print(f"  ROWS = 'tbody tr' ou 'tr'")
    
    if detail_links:
        link = detail_links[0]
        link_classes = ' '.join(link.get('class', []))
        
        print("\nPour les liens de détail:")
        if link_classes:
            print(f"  DETAIL_LINK = 'a.{link_classes.split()[0]}'")
        
        # Analyser l'href pour pattern
        href = link.get('href', '')
        if 'detail' in href.lower():
            print(f"  DETAIL_LINK = 'a[href*=\"detail\"]'")
        elif 'consultation' in href.lower():
            print(f"  DETAIL_LINK = 'a[href*=\"consultation\"]'")
        
        print(f"  # Ou simplement: DETAIL_LINK = 'a::attr(href)'")
    
    # 5. Exemple de code Python
    print("\n\n🐍 [5] CODE PYTHON RECOMMANDÉ")
    print("-" * 70)
    print("""
# Dans parse_consultation_row():
detail_url = row.css('a::attr(href)').get()  # Récupère le premier lien
if not detail_url:
    # Essayer d'autres sélecteurs
    detail_url = row.css('a[href*="detail"]::attr(href)').get()
    
if detail_url:
    item['url_detail'] = response.urljoin(detail_url)
else:
    self.logger.warning(f"Aucun lien trouvé pour {item['ref_consultation']}")
    """)
    
    print("\n" + "="*70 + "\n")


def main():
    """Point d'entrée"""
    
    # Fichier par défaut
    default_file = 'logs/test_page_consultations.html'
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = default_file
        print(f"\nUtilisation: python {sys.argv[0]} <fichier.html>")
        print(f"Par défaut: {default_file}\n")
    
    analyze_html_file(filepath)
    
    print("\n💡 Prochaines étapes:")
    print("  1. Identifier le bon sélecteur pour DETAIL_LINK")
    print("  2. Mettre à jour scraper/selectors.py")
    print("  3. Relancer: python scripts/test_url_extraction.py")


if __name__ == "__main__":
    main()
