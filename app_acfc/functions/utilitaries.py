"""Module utilitaire pour le démarrage du serveur de l'application ACFC."""

import os
from flask import Flask
from waitress import serve

# ====================================================================
# POINT D'ENTRÉE DE L'APPLICATION
# ====================================================================

def start_server(app: 'Flask'):
    """
    Démarrage de l'application en mode production avec Waitress.
    
    Waitress est un serveur WSGI production-ready. Configuration :
    - Host: configurable via variable d'environnement (défaut: localhost)
    - Port: 5000 (port standard de l'application)
    
    Note: En production, l'application est généralement déployée derrière
    un reverse proxy (Nginx) pour la gestion SSL et la distribution de charge.
    """
    # Configuration sécurisée de l'host
    # En développement: localhost uniquement (plus sécurisé)
    # En production Docker: 0.0.0.0 pour permettre l'accès depuis le conteneur
    host = os.environ.get('FLASK_HOST', 'localhost')
    port = int(os.environ.get('FLASK_PORT', 5000))

    serve(app, host=host, port=port)
