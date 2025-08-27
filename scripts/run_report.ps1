# Script PowerShell pour générer un rapport de suivi
param(
    [int]$Days = 7,
    [string]$Output = "",
    [string]$Repo = ".",
    [switch]$Help
)

# Fonction pour afficher l'aide
function Show-Help {
    Write-Host "🚀 Générateur de Rapport de Suivi - ACFC" -ForegroundColor Blue
    Write-Host "=================================================="
    Write-Host ""
    Write-Host "Usage: .\scripts\run_report.ps1 [PARAMETRES]"
    Write-Host ""
    Write-Host "Paramètres:"
    Write-Host "  -Days JOURS      Nombre de jours à analyser (défaut: 7)" -ForegroundColor Yellow
    Write-Host "  -Output FICHIER  Fichier de sortie (défaut: auto-généré)" -ForegroundColor Yellow
    Write-Host "  -Repo CHEMIN     Chemin vers le dépôt Git (défaut: .)" -ForegroundColor Yellow
    Write-Host "  -Help            Affiche cette aide" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Exemples:"
    Write-Host "  .\scripts\run_report.ps1                                    # Rapport des 7 derniers jours"
    Write-Host "  .\scripts\run_report.ps1 -Days 30                         # Rapport des 30 derniers jours"
    Write-Host "  .\scripts\run_report.ps1 -Days 7 -Output 'mon_rapport.md'"
    exit 0
}

if ($Help) {
    Show-Help
}

Write-Host "🚀 Générateur de Rapport de Suivi - ACFC" -ForegroundColor Blue
Write-Host "=================================================="

# Vérifications préalables
Write-Host "🔍 Vérifications préalables..." -ForegroundColor Yellow

# Vérifier si on est dans un dépôt Git
try {
    git rev-parse --git-dir 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Pas un dépôt Git"
    }
} catch {
    Write-Host "❌ Erreur: Ce n'est pas un dépôt Git" -ForegroundColor Red
    exit 1
}

# Vérifier si Python est disponible
try {
    python --version 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Python non disponible"
    }
} catch {
    Write-Host "❌ Erreur: Python n'est pas installé ou pas dans le PATH" -ForegroundColor Red
    exit 1
}

# Vérifier si le script existe
if (-not (Test-Path "scripts\generate_progress_report.py")) {
    Write-Host "❌ Erreur: Script scripts\generate_progress_report.py introuvable" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Vérifications réussies" -ForegroundColor Green

# Affichage des paramètres
Write-Host ""
Write-Host "📊 Paramètres de génération:" -ForegroundColor Blue
Write-Host "  📅 Période: $Days derniers jours"
Write-Host "  📁 Dépôt: $Repo"
if ($Output) {
    Write-Host "  📄 Sortie: $Output"
} else {
    Write-Host "  📄 Sortie: Auto-générée"
}

# Génération du rapport
Write-Host ""
Write-Host "🔄 Génération du rapport en cours..." -ForegroundColor Yellow

# Construction de la commande
$cmd = @("scripts\generate_progress_report.py", "--days", $Days.ToString(), "--repo", $Repo)
if ($Output) {
    $cmd += @("--output", $Output)
}

# Exécution
try {
    python @cmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Rapport généré avec succès!" -ForegroundColor Green
        
        # Détermination du fichier de sortie
        if ($Output) {
            $generatedFile = $Output
        } else {
            $date = Get-Date -Format "yyyyMMdd"
            $generatedFile = "suivi_realisation_auto_$date.md"
        }
        
        # Vérification et affichage des informations du fichier
        if (Test-Path $generatedFile) {
            Write-Host "📄 Fichier créé: $generatedFile" -ForegroundColor Blue
            
            # Statistiques du fichier
            $fileInfo = Get-Item $generatedFile
            $lines = (Get-Content $generatedFile).Count
            $sizeKB = [math]::Round($fileInfo.Length / 1KB, 2)
            
            Write-Host "📏 Taille: $lines lignes, $sizeKB KB" -ForegroundColor Blue
            
            # Suggestions
            Write-Host ""
            Write-Host "💡 Suggestions:" -ForegroundColor Yellow
            Write-Host "  • Ouvrir le fichier: code '$generatedFile'"
            Write-Host "  • Voir un aperçu: Get-Content '$generatedFile' | Select-Object -First 20"
            Write-Host "  • Ajouter au Git: git add '$generatedFile'"
        } else {
            Write-Host "❌ Fichier de sortie non trouvé" -ForegroundColor Red
            exit 1
        }
    } else {
        throw "Échec de l'exécution du script Python"
    }
} catch {
    Write-Host "❌ Échec de la génération du rapport: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 Processus terminé avec succès!" -ForegroundColor Green
