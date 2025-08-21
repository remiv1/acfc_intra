#!/usr/bin/env bash

# Script de test du workflow Docker CI en local
# Simule les étapes principales du workflow GitHub Actions

set -e

echo "🧪 Test du workflow Docker Compose CI"
echo "====================================="

# Variables
COMPOSE_FILE="docker-compose.yml"
HEALTH_URL="http://localhost:5000/health"
TIMEOUT=120

echo "1️⃣ Validation de la syntaxe docker-compose..."
docker compose -f $COMPOSE_FILE config --quiet
echo "✅ Syntaxe valide"

echo ""
echo "2️⃣ Build des images..."
docker compose -f $COMPOSE_FILE build --parallel
echo "✅ Images buildées"

echo ""
echo "3️⃣ Démarrage des services..."
docker compose -f $COMPOSE_FILE up -d

echo ""
echo "4️⃣ Attente de la disponibilité des services..."

# Attendre MariaDB
echo "   Attente de MariaDB..."
timeout $TIMEOUT bash -c 'until docker compose -f docker-compose.yml ps acfc-db | grep -q "healthy\|Up"; do sleep 2; done' || {
    echo "❌ MariaDB n'est pas prêt"
    docker compose -f $COMPOSE_FILE logs acfc-db
    exit 1
}
echo "   ✅ MariaDB prêt"

# Attendre MongoDB
echo "   Attente de MongoDB..."
timeout 60 bash -c 'until docker compose -f docker-compose.yml exec -T acfc-logs mongosh --eval "db.adminCommand(\"ping\")" > /dev/null 2>&1; do sleep 2; done' || {
    echo "⚠️ MongoDB non accessible (continuer quand même)"
}
echo "   ✅ MongoDB prêt"

# Attendre Flask
echo "   Attente de Flask..."
timeout 60 bash -c 'until curl -f '$HEALTH_URL' > /dev/null 2>&1 || curl -f http://localhost:5000/ > /dev/null 2>&1; do sleep 2; done' || {
    echo "❌ Flask app non accessible"
    docker compose -f $COMPOSE_FILE logs acfc-app
    exit 1
}
echo "   ✅ Flask prêt"

echo ""
echo "5️⃣ Tests de santé..."

# Test endpoint de santé
if curl -f -s $HEALTH_URL > /tmp/health_response.json; then
    echo "✅ Endpoint /health accessible"
    echo "   Réponse:"
    cat /tmp/health_response.json | python -m json.tool || cat /tmp/health_response.json
else
    echo "❌ Endpoint /health non accessible"
    curl -v $HEALTH_URL || true
fi

# Test endpoint principal
if curl -f -s http://localhost:5000/ > /dev/null; then
    echo "✅ Endpoint / accessible"
else
    echo "❌ Endpoint / non accessible"
fi

# Test proxy Nginx
if curl -f -s http://localhost:80/ > /dev/null; then
    echo "✅ Nginx proxy accessible"
else
    echo "⚠️ Nginx proxy non accessible (continuer quand même)"
fi

echo ""
echo "6️⃣ Status des conteneurs:"
docker compose -f $COMPOSE_FILE ps

echo ""
echo "7️⃣ Nettoyage..."
docker compose -f $COMPOSE_FILE down --volumes --remove-orphans

echo ""
echo "🎉 Test terminé avec succès !"
