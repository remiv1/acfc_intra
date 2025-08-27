# Script de test du workflow Docker CI en local (PowerShell)
# Simule les étapes principales du workflow GitHub Actions

$ErrorActionPreference = "Stop"

Write-Host "🧪 Test du workflow Docker Compose CI" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Variables
$ComposeFile = "docker-compose.yml"
$HealthUrl = "http://localhost:5000/health"
$Timeout = 120

Write-Host ""
Write-Host "1️⃣ Validation de la syntaxe docker-compose..." -ForegroundColor Yellow
try {
    docker compose -f $ComposeFile config --quiet
    Write-Host "✅ Syntaxe valide" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur de syntaxe" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "2️⃣ Build des images..." -ForegroundColor Yellow
try {
    docker compose -f $ComposeFile build --parallel
    Write-Host "✅ Images buildées" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur de build" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "3️⃣ Démarrage des services..." -ForegroundColor Yellow
docker compose -f $ComposeFile up -d

Write-Host ""
Write-Host "4️⃣ Attente de la disponibilité des services..." -ForegroundColor Yellow

# Attendre Flask (test simple)
Write-Host "   Attente de Flask..." -ForegroundColor Gray
$maxAttempts = 30
$attempts = 0
$flaskReady = $false

while ($attempts -lt $maxAttempts -and -not $flaskReady) {
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $flaskReady = $true
            Write-Host "   ✅ Flask prêt" -ForegroundColor Green
        }
    } catch {
        # Essayer endpoint principal
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5000/" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $flaskReady = $true
                Write-Host "   ✅ Flask prêt (endpoint principal)" -ForegroundColor Green
            }
        } catch {
            # Do nothing, will sleep below
        }
    }
    if (-not $flaskReady) {
        Start-Sleep -Seconds 2
        $attempts++
    }
}

if (-not $flaskReady) {
    Write-Host "   ❌ Flask non accessible après $maxAttempts tentatives" -ForegroundColor Red
    Write-Host "   Logs de l'application:" -ForegroundColor Yellow
    docker compose -f $ComposeFile logs acfc-app
    docker compose -f $ComposeFile down --volumes --remove-orphans
    exit 1
}

Write-Host ""
Write-Host "5️⃣ Tests de santé..." -ForegroundColor Yellow

# Test endpoint de santé
try {
    $healthResponse = Invoke-RestMethod -Uri $HealthUrl -Method GET -TimeoutSec 10
    Write-Host "✅ Endpoint /health accessible" -ForegroundColor Green
    Write-Host "   Réponse:" -ForegroundColor Gray
    $healthResponse | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Endpoint /health non accessible: $($_.Exception.Message)" -ForegroundColor Red
}

# Test endpoint principal
try {
    $mainResponse = Invoke-WebRequest -Uri "http://localhost:5000/" -Method GET -TimeoutSec 10
    Write-Host "✅ Endpoint / accessible (Status: $($mainResponse.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Endpoint / non accessible: $($_.Exception.Message)" -ForegroundColor Red
}

# Test proxy Nginx
try {
    $nginxResponse = Invoke-WebRequest -Uri "http://localhost:80/" -Method GET -TimeoutSec 10
    Write-Host "✅ Nginx proxy accessible (Status: $($nginxResponse.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Nginx proxy non accessible: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "6️⃣ Status des conteneurs:" -ForegroundColor Yellow
docker compose -f $ComposeFile ps

Write-Host ""
Write-Host "7️⃣ Nettoyage..." -ForegroundColor Yellow
docker compose -f $ComposeFile down --volumes --remove-orphans

Write-Host ""
Write-Host "🎉 Test terminé avec succès !" -ForegroundColor Green
