# Copie tous les .env*.exemple du dossier courant vers le dossier parent en .env-*

Get-ChildItem -Filter ".env*.exemple" | ForEach-Object {
    $newname = $_.Name -replace '\.env\.?([^.]+)?\.exemple$', '.env-$1'
    $newname = $newname -replace '\.env-\.exemple$', '.env'
    Copy-Item $_.FullName ("../" + $newname)
    Write-Host "Copié $($_.Name) -> ../$newname"
}
