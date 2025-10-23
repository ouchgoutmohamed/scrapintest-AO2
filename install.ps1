# Script PowerShell d'installation et de vérification du projet PMMP

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PMMP Scraper - Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Fonction de vérification
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Vérifier Python
Write-Host "[1/8] Vérification de Python..." -ForegroundColor Yellow
if (Test-Command python) {
    $pythonVersion = python --version
    Write-Host "  ✓ Python trouvé: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python n'est pas installé!" -ForegroundColor Red
    Write-Host "    Téléchargez Python depuis https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Vérifier pip
Write-Host "[2/8] Vérification de pip..." -ForegroundColor Yellow
if (Test-Command pip) {
    Write-Host "  ✓ pip trouvé" -ForegroundColor Green
} else {
    Write-Host "  ✗ pip n'est pas installé!" -ForegroundColor Red
    exit 1
}

# Créer l'environnement virtuel
Write-Host "[3/8] Création de l'environnement virtuel..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  ! L'environnement virtuel existe déjà" -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "  ✓ Environnement virtuel créé" -ForegroundColor Green
}

# Activer l'environnement virtuel
Write-Host "[4/8] Activation de l'environnement virtuel..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "  ✓ Environnement activé" -ForegroundColor Green

# Installer les dépendances
Write-Host "[5/8] Installation des dépendances Python..." -ForegroundColor Yellow
pip install --upgrade pip -q
pip install -r requirements.txt -q
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Dépendances installées" -ForegroundColor Green
} else {
    Write-Host "  ✗ Erreur lors de l'installation des dépendances" -ForegroundColor Red
    exit 1
}

# Installer Playwright
Write-Host "[6/8] Installation de Playwright..." -ForegroundColor Yellow
playwright install chromium
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Playwright installé" -ForegroundColor Green
} else {
    Write-Host "  ✗ Erreur lors de l'installation de Playwright" -ForegroundColor Red
}

# Créer le fichier .env
Write-Host "[7/8] Configuration de l'environnement..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  ! Le fichier .env existe déjà" -ForegroundColor Yellow
} else {
    Copy-Item .env.example .env
    Write-Host "  ✓ Fichier .env créé (à configurer)" -ForegroundColor Green
}

# Vérifier PostgreSQL (optionnel)
Write-Host "[8/8] Vérification de PostgreSQL..." -ForegroundColor Yellow
if (Test-Command psql) {
    Write-Host "  ✓ PostgreSQL trouvé" -ForegroundColor Green
} else {
    Write-Host "  ! PostgreSQL non détecté (optionnel pour Docker)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation terminée!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Prochaines étapes:" -ForegroundColor Cyan
Write-Host "  1. Configurer .env avec vos paramètres PostgreSQL" -ForegroundColor White
Write-Host "  2. Initialiser la base de données:" -ForegroundColor White
Write-Host "     python scripts\init_database.py" -ForegroundColor Gray
Write-Host "  3. Tester le scraper:" -ForegroundColor White
Write-Host "     python scripts\test_scraper.py" -ForegroundColor Gray
Write-Host "  4. Lancer l'API:" -ForegroundColor White
Write-Host "     uvicorn api.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "Alternative Docker:" -ForegroundColor Cyan
Write-Host "  docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "Documentation: README.md | QUICKSTART.md" -ForegroundColor Yellow
Write-Host ""
