#!/bin/bash
set -e

# Lancer le worker RQ en arrière-plan
echo "🚀 Lancement du worker RQ..."
rq worker --url redis://$REDIS_HOST:$REDIS_PORT &

# Lancer l'API (FastAPI ici)
echo "🌐 Lancement de l'API Mail..."
exec uvicorn mail_api:app --host 0.0.0.0 --port 8000
