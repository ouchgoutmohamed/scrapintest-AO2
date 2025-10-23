"""
Script de vérification de l'installation
Vérifie que tous les composants sont correctement configurés
"""
import sys
import os
from pathlib import Path

# Couleurs pour le terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def check_item(name, check_func, fix_suggestion=None):
    """Vérifie un élément et affiche le résultat"""
    print(f"  Vérification: {name}...", end=" ")
    try:
        result = check_func()
        if result:
            print(f"{Colors.GREEN}✓{Colors.END}")
            return True
        else:
            print(f"{Colors.RED}✗{Colors.END}")
            if fix_suggestion:
                print(f"    {Colors.YELLOW}→ {fix_suggestion}{Colors.END}")
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ Erreur: {e}{Colors.END}")
        if fix_suggestion:
            print(f"    {Colors.YELLOW}→ {fix_suggestion}{Colors.END}")
        return False

def main():
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  PMMP Scraper - Vérification de l'installation{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")
    
    all_checks = []
    
    # 1. Vérifier Python
    print(f"{Colors.BOLD}[1] Python{Colors.END}")
    all_checks.append(check_item(
        "Version Python >= 3.9",
        lambda: sys.version_info >= (3, 9),
        "Installer Python 3.9 ou supérieur"
    ))
    
    # 2. Vérifier les modules Python
    print(f"\n{Colors.BOLD}[2] Modules Python{Colors.END}")
    
    modules = [
        ('scrapy', 'pip install scrapy'),
        ('playwright', 'pip install playwright'),
        ('sqlalchemy', 'pip install sqlalchemy'),
        ('fastapi', 'pip install fastapi'),
        ('pydantic', 'pip install pydantic'),
        ('psycopg2', 'pip install psycopg2-binary'),
    ]
    
    for module, install_cmd in modules:
        all_checks.append(check_item(
            f"Module {module}",
            lambda m=module: __import__(m),
            install_cmd
        ))
    
    # 3. Vérifier la structure des dossiers
    print(f"\n{Colors.BOLD}[3] Structure du projet{Colors.END}")
    
    required_dirs = [
        'scraper/spiders',
        'database',
        'api',
        'airflow/dags',
        'monitoring',
        'scripts',
        'tests',
        'data/archives',
        'data/exports',
        'logs',
    ]
    
    for dir_path in required_dirs:
        all_checks.append(check_item(
            f"Dossier {dir_path}",
            lambda p=dir_path: Path(p).exists(),
            f"Créer le dossier: mkdir -p {dir_path}"
        ))
    
    # 4. Vérifier les fichiers principaux
    print(f"\n{Colors.BOLD}[4] Fichiers de configuration{Colors.END}")
    
    required_files = [
        'requirements.txt',
        'scrapy.cfg',
        'docker-compose.yml',
        'Dockerfile',
        '.env.example',
        'README.md',
    ]
    
    for file_path in required_files:
        all_checks.append(check_item(
            f"Fichier {file_path}",
            lambda p=file_path: Path(p).exists(),
            f"Le fichier {file_path} est manquant"
        ))
    
    # 5. Vérifier le fichier .env
    print(f"\n{Colors.BOLD}[5] Configuration{Colors.END}")
    
    env_exists = Path('.env').exists()
    all_checks.append(check_item(
        "Fichier .env",
        lambda: env_exists,
        "Copier .env.example vers .env et configurer"
    ))
    
    # 6. Vérifier Playwright
    print(f"\n{Colors.BOLD}[6] Playwright{Colors.END}")
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser_installed = True
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
            except:
                browser_installed = False
        
        all_checks.append(check_item(
            "Navigateur Chromium installé",
            lambda: browser_installed,
            "Exécuter: playwright install chromium"
        ))
    except:
        print(f"  {Colors.YELLOW}Impossible de vérifier Playwright{Colors.END}")
    
    # 7. Vérifier la connexion à PostgreSQL
    print(f"\n{Colors.BOLD}[7] Base de données{Colors.END}")
    
    if env_exists:
        from dotenv import load_dotenv
        load_dotenv()
        
        try:
            from database.connection import check_connection
            db_ok = check_connection()
            all_checks.append(check_item(
                "Connexion PostgreSQL",
                lambda: db_ok,
                "Vérifier DATABASE_URL dans .env et que PostgreSQL est démarré"
            ))
        except Exception as e:
            print(f"  {Colors.YELLOW}Impossible de tester la connexion DB: {e}{Colors.END}")
    else:
        print(f"  {Colors.YELLOW}Fichier .env manquant, vérification DB ignorée{Colors.END}")
    
    # Résumé
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    total = len(all_checks)
    passed = sum(all_checks)
    failed = total - passed
    
    print(f"{Colors.BOLD}Résumé:{Colors.END}")
    print(f"  Total: {total} vérifications")
    print(f"  {Colors.GREEN}Réussies: {passed}{Colors.END}")
    print(f"  {Colors.RED}Échouées: {failed}{Colors.END}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Installation complète et fonctionnelle!{Colors.END}")
        print(f"\n{Colors.CYAN}Prochaines étapes:{Colors.END}")
        print(f"  1. Configurer .env avec vos paramètres")
        print(f"  2. python scripts/init_database.py")
        print(f"  3. python scripts/test_scraper.py")
        print(f"  4. uvicorn api.main:app --reload")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠ Certaines vérifications ont échoué.{Colors.END}")
        print(f"  Consultez les suggestions ci-dessus pour corriger les problèmes.")
        return 1
    
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

if __name__ == "__main__":
    sys.exit(main())
