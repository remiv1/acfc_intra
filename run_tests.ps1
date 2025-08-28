# Script PowerShell de lancement des tests ACFC
# ==============================================

param(
    [string]$Action = "",
    [switch]$Help
)

# Couleurs pour l'affichage
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    White = "White"
}

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

function Show-Header {
    Write-Host "🚀 Lancement des Tests ACFC" -ForegroundColor $Colors.Blue
    Write-Host "=============================" -ForegroundColor $Colors.Blue
    Write-Host ""
}

function Test-Environment {
    Write-Status "Vérification de l'environnement..."
    
    # Vérifier Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Status "Python trouvé: $pythonVersion"
    }
    catch {
        Write-Error "Python n'est pas installé ou non trouvé dans PATH"
        exit 1
    }
    
    # Vérifier pytest
    try {
        python -c "import pytest" 2>$null
        Write-Status "pytest est disponible"
    }
    catch {
        Write-Error "pytest n'est pas installé. Installation..."
        pip install pytest pytest-cov pytest-html
    }
    
    # Installer les dépendances
    if (Test-Path "requirements-test.txt") {
        Write-Status "Installation des dépendances de test..."
        pip install -r requirements-test.txt
    }
    
    if (Test-Path "requirements-app.txt") {
        Write-Status "Installation des dépendances application..."
        pip install -r requirements-app.txt
    }
}

function Invoke-UnitTests {
    Write-Status "Exécution des tests unitaires..."
    $result = pytest tests/unit/ -v --tb=short -m unit
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Tests unitaires réussis"
        return $true
    } else {
        Write-Error "Échec des tests unitaires"
        return $false
    }
}

function Invoke-IntegrationTests {
    Write-Status "Exécution des tests d'intégration..."
    $result = pytest tests/integration/ -v --tb=short -m integration
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Tests d'intégration réussis"
        return $true
    } else {
        Write-Error "Échec des tests d'intégration"
        return $false
    }
}

function Invoke-E2ETests {
    Write-Status "Exécution des tests end-to-end..."
    $result = pytest tests/e2e/ -v --tb=short -m e2e
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Tests end-to-end réussis"
        return $true
    } else {
        Write-Error "Échec des tests end-to-end"
        return $false
    }
}

function Invoke-DemoTests {
    Write-Status "Exécution des tests de démonstration..."
    $result = pytest tests/demo/ -v -s --tb=short -m demo
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Tests de démonstration réussis"
        return $true
    } else {
        Write-Error "Échec des tests de démonstration"
        return $false
    }
}

function Invoke-CoverageTests {
    Write-Status "Exécution des tests avec couverture..."
    $result = pytest --cov=app_acfc --cov=api_acfc --cov-report=html --cov-report=xml --cov-report=term
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Tests de couverture réussis"
        Write-Status "Rapport HTML généré dans htmlcov/"
        return $true
    } else {
        Write-Error "Échec des tests de couverture"
        return $false
    }
}

function Invoke-QRCodeTests {
    Write-Status "Exécution des tests QR Code..."
    $result = pytest -m qrcode -v --tb=short
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Tests QR Code réussis"
        return $true
    } else {
        Write-Error "Échec des tests QR Code"
        return $false
    }
}

function Invoke-PrintingTests {
    Write-Status "Exécution des tests d'impression..."
    $result = pytest -m printing -v --tb=short
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Tests d'impression réussis"
        return $true
    } else {
        Write-Error "Échec des tests d'impression"
        return $false
    }
}

function Invoke-AllTests {
    Write-Status "Exécution de tous les tests..."
    $failed = 0
    
    if (-not (Invoke-UnitTests)) { $failed++ }
    if (-not (Invoke-IntegrationTests)) { $failed++ }
    if (-not (Invoke-E2ETests)) { $failed++ }
    
    if ($failed -eq 0) {
        Write-Success "Tous les tests ont réussi!"
        return $true
    } else {
        Write-Error "$failed suite(s) de tests ont échoué"
        return $false
    }
}

function Show-Menu {
    Write-Host ""
    Write-Host "Choisissez une option:" -ForegroundColor $Colors.White
    Write-Host "1) Tests unitaires uniquement"
    Write-Host "2) Tests d'intégration uniquement"
    Write-Host "3) Tests end-to-end uniquement"
    Write-Host "4) Tests de démonstration"
    Write-Host "5) Tests QR Code spécifiques"
    Write-Host "6) Tests d'impression spécifiques"
    Write-Host "7) Tests avec couverture de code"
    Write-Host "8) Tous les tests"
    Write-Host "9) Tests rapides (unitaires + QR Code)"
    Write-Host "0) Quitter"
    Write-Host ""
}

function Show-Help {
    Write-Host "Usage: ./run_tests.ps1 [option]" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "Options disponibles:" -ForegroundColor $Colors.White
    Write-Host "  unit          Tests unitaires"
    Write-Host "  integration   Tests d'intégration"
    Write-Host "  e2e           Tests end-to-end"
    Write-Host "  demo          Tests de démonstration"
    Write-Host "  qrcode        Tests QR Code"
    Write-Host "  printing      Tests d'impression"
    Write-Host "  coverage      Tests avec couverture"
    Write-Host "  all           Tous les tests"
    Write-Host "  quick         Tests rapides"
    Write-Host "  help          Afficher cette aide"
    Write-Host ""
}

# Main script
Show-Header

if ($Help) {
    Show-Help
    exit 0
}

Test-Environment

# Gestion des arguments
switch ($Action.ToLower()) {
    "unit" {
        Invoke-UnitTests
        exit $(if ($?) { 0 } else { 1 })
    }
    "integration" {
        Invoke-IntegrationTests
        exit $(if ($?) { 0 } else { 1 })
    }
    "e2e" {
        Invoke-E2ETests
        exit $(if ($?) { 0 } else { 1 })
    }
    "demo" {
        Invoke-DemoTests
        exit $(if ($?) { 0 } else { 1 })
    }
    "qrcode" {
        Invoke-QRCodeTests
        exit $(if ($?) { 0 } else { 1 })
    }
    "printing" {
        Invoke-PrintingTests
        exit $(if ($?) { 0 } else { 1 })
    }
    "coverage" {
        Invoke-CoverageTests
        exit $(if ($?) { 0 } else { 1 })
    }
    "all" {
        Invoke-AllTests
        exit $(if ($?) { 0 } else { 1 })
    }
    "quick" {
        Write-Status "Tests rapides (unitaires + QR Code)..."
        $unit = Invoke-UnitTests
        $qr = Invoke-QRCodeTests
        exit $(if ($unit -and $qr) { 0 } else { 1 })
    }
    "help" {
        Show-Help
        exit 0
    }
    "" {
        # Mode interactif
    }
    default {
        Write-Error "Option inconnue: $Action"
        Write-Host "Utilisez './run_tests.ps1 help' pour voir les options disponibles"
        exit 1
    }
}

# Mode interactif
while ($true) {
    Show-Menu
    $choice = Read-Host "Votre choix"
    
    switch ($choice) {
        "1" {
            Invoke-UnitTests
        }
        "2" {
            Invoke-IntegrationTests
        }
        "3" {
            Invoke-E2ETests
        }
        "4" {
            Invoke-DemoTests
        }
        "5" {
            Invoke-QRCodeTests
        }
        "6" {
            Invoke-PrintingTests
        }
        "7" {
            Invoke-CoverageTests
        }
        "8" {
            Invoke-AllTests
        }
        "9" {
            Write-Status "Tests rapides (unitaires + QR Code)..."
            $unit = Invoke-UnitTests
            $qr = Invoke-QRCodeTests
        }
        "0" {
            Write-Status "Au revoir!"
            exit 0
        }
        default {
            Write-Warning "Option invalide. Veuillez choisir entre 0 et 9."
        }
    }
    
    Write-Host ""
    Read-Host "Appuyez sur Entrée pour continuer"
}
