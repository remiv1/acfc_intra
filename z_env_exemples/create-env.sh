#!/bin/bash
# Copie tous les .env*.exemple du dossier courant vers le dossier parent en .env-*

for file in .env*.exemple; do
  if [[ -f "$file" ]]; then
    newname=$(echo "$file" | sed -E 's/\.env\.?([^.]+)?\.exemple$/.env-\1/')
    newname=$(echo "$newname" | sed 's/\.env-\.exemple$/.env/')
    cp "$file" "../$newname"
    echo "Copié $file -> ../$newname"
  fi
done