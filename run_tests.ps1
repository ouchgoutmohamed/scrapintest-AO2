# Script PowerShell - Menu de Test Rapide

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PMMP SCRAPER - TESTS D'EXTRACTION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Que souhaitez-vous faire ?" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Test rapide d'extraction (recommandé)" -ForegroundColor White
Write-Host "     → Vérifie que les URLs détaillées sont capturées" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Test avec analyse HTML du site" -ForegroundColor White
Write-Host "     → Extrait et analyse la structure réelle" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Analyser un fichier HTML existant" -ForegroundColor White
Write-Host "     → Pour trouver les bons sélecteurs CSS" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Vérifier l'installation complète" -ForegroundColor White
Write-Host "     → Check tous les composants" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Initialiser la base de données" -ForegroundColor White
Write-Host "     → Créer les tables PostgreSQL" -ForegroundColor Gray
Write-Host ""
Write-Host "  6. Lancer l'API REST" -ForegroundColor White
Write-Host "     → Démarrer l'API sur http://localhost:8000" -ForegroundColor Gray
Write-Host ""
Write-Host "  7. Export des données" -ForegroundColor White
Write-Host "     → Exporter vers CSV/JSON" -ForegroundColor Gray
Write-Host ""
Write-Host "  0. Quitter" -ForegroundColor Red
Write-Host ""

$choice = Read-Host "Votre choix"

switch ($choice) {
    "1" {
        Write-Host "`n🧪 Lancement du test rapide..." -ForegroundColor Green
        python scripts\test_url_extraction.py
    }
    "2" {
        Write-Host "`n🌐 Test avec extraction réelle du site..." -ForegroundColor Green
        python scripts\test_extraction_real.py
    }
    "3" {
        $htmlFile = Read-Host "`nChemin du fichier HTML (ou Enter pour logs\test_page_consultations.html)"
        if ([string]::IsNullOrWhiteSpace($htmlFile)) {
            $htmlFile = "logs\test_page_consultations.html"
        }
        Write-Host "`n🔍 Analyse du fichier HTML..." -ForegroundColor Green
        python scripts\analyze_html_structure.py $htmlFile
    }
    "4" {
        Write-Host "`n✓ Vérification de l'installation..." -ForegroundColor Green
        python scripts\check_installation.py
    }
    "5" {
        Write-Host "`n💾 Initialisation de la base de données..." -ForegroundColor Green
        python scripts\init_database.py
    }
    "6" {
        Write-Host "`n🚀 Lancement de l'API REST..." -ForegroundColor Green
        Write-Host "   Accès: http://localhost:8000/docs`n" -ForegroundColor Cyan
        Set-Location api
        uvicorn main:app --reload
        Set-Location ..
    }
    "7" {
        Write-Host "`n📊 Export des données..." -ForegroundColor Green
        python scripts\export_data.py
    }
    "0" {
        Write-Host "`nAu revoir! 👋`n" -ForegroundColor Cyan
        exit
    }
    default {
        Write-Host "`n❌ Choix invalide`n" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Terminé!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Proposer de refaire un test
$again = Read-Host "Lancer un autre test ? (O/N)"
if ($again -eq "O" -or $again -eq "o") {
    & $PSCommandPath
}
