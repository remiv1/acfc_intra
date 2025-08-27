# ====================================================================
# DOCKERFILE - APPLICATION ACFC
# ====================================================================
# Configuration Docker pour l'application web ACFC (Accounting, CRM, Billing & Stock Management)
# 
# Architecture : Application Flask + Waitress WSGI Server
# Base : Python 3.12 sur Debian Bookworm (LTS, sécurisé)
# Port : 5000 (standard Flask, mappé par docker-compose)
# 
# Optimisations incluses :
# - Image officielle Python optimisée
# - Cache pip désactivé pour réduire la taille
# - Isolation des dépendances
# - Configuration multi-stage possible (future optimisation)
# 
# Maintenu par : ACFC Development Team
# Dernière mise à jour : Août 2025

# Utilisation de l'image Python officielle basée sur Debian Bookworm
# Avantages : Stabilité LTS, sécurité renforcée, support étendu des packages
FROM python:3.12-bookworm

# Définition du répertoire de travail dans le conteneur
# Isolation complète des fichiers de l'application
WORKDIR /app

# === PHASE 1: INSTALLATION DES DÉPENDANCES ===
# Copie du fichier de dépendances en premier pour optimiser le cache Docker
# Si requirements-app.txt ne change pas, cette couche sera réutilisée
COPY requirements-app.txt /app/requirements.txt
COPY logs /app/logs

# Configuration des métadonnées pour la traçabilité
LABEL maintainer="ACFC Development Team"
LABEL description="Application web ACFC - Gestion d'entreprise intégrée"
LABEL version="1.0"

# Installation des dépendances Python avec optimisations
# --no-cache-dir : Évite le stockage du cache pip (réduit la taille de l'image)
# --upgrade : Force la mise à jour vers les dernières versions compatibles
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# === PHASE 2: COPIE DU CODE APPLICATION ===
# Copie de tous les fichiers de l'application vers le conteneur
# Maintien de la structure app_acfc/ pour les imports Python
COPY app_acfc/ /app/app_acfc/

# Ajout du répertoire de travail au PYTHONPATH pour les imports
ENV PYTHONPATH=/app

# === PHASE 3: CONFIGURATION RÉSEAU ===
# Exposition du port 5000 pour l'application Flask/Waitress
# Ce port sera mappé par docker-compose vers l'extérieur
EXPOSE 5000

# === PHASE 4: COMMANDE DE DÉMARRAGE ===
# Lancement de l'application via le serveur WSGI Waitress (production-ready)
# Alternative plus robuste au serveur de développement Flask intégré
CMD ["python", "app_acfc/application.py"]