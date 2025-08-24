"""
ACFC - Module CRM - Gestion des Clients
=======================================

Blueprint Flask pour la gestion de la relation client (Customer Relationship Management).
Ce module centralise toutes les fonctionnalités liées aux clients :

Fonctionnalités principales :
- Recherche et filtrage avancé des clients
- Consultation des fiches clients détaillées
- Gestion des contacts (emails, téléphones, adresses)
- Historique des interactions et commandes
- Segmentation et classification client

Architecture REST :
- Routes GET pour consultation des données
- Routes POST pour création/modification
- API JSON pour intégration avec le frontend JavaScript
- Templates HTML pour interface utilisateur

Sécurité :
- Vérification des sessions utilisateur
- Contrôle d'accès basé sur les rôles
- Validation des données d'entrée
- Protection CSRF

Auteur : Rémi Verschuur - Module CRM
Version : 1.0
"""

from flask import Blueprint, render_template, jsonify
from sqlalchemy.orm import Session as SessionBdDType
from sqlalchemy import or_
#=================================================================
# Dans un contexte conteneur, app_acfc s'appelle simplement app
# ainsi on appellera les fonctions différemment suivant le contexte
#=================================================================
#try:
from app_acfc.modeles import SessionBdD, Client, Part, Pro
#except ImportError:
#    from app.modeles import SessionBdD
from typing import Dict, List, Any

# ================================================================
# CONFIGURATION DU BLUEPRINT CRM CLIENTS
# ================================================================

clients_bp = Blueprint(
    'clients',                              # Nom interne du blueprint
    __name__,                               # Module de référence
    url_prefix='/clients',                  # Préfixe pour toutes les routes (/clients/...)
    static_folder='statics/clients'         # Dossier statique spécialisé (CSS, JS, images)
)

# ================================================================
# ROUTES - INTERFACE DE RECHERCHE CLIENTS
# ================================================================

@clients_bp.route('/rechercher', methods=['GET'])
def clients_list():
    """
    Interface de recherche et filtrage des clients.
    
    Affiche la page de recherche avancée permettant de filtrer les clients
    selon différents critères : nom, type, statut, date de création, etc.
    
    Returns:
        str: Template HTML de la page de recherche clients
        
    Features:
        - Filtres multiples (nom, type, statut, période)
        - Pagination des résultats
        - Export des résultats (CSV, Excel)
        - Tri par colonnes
        - Recherche textuelle libre
    """
    return render_template('base.html', 
                         context='clients',           # Context CSS/JS pour styling
                         sub_context='research')      # Sous-context pour recherche

# ================================================================
# API REST - DONNÉES CLIENTS
# ================================================================

@clients_bp.route('/clients', methods=['GET'])
def get_clients():
    """
    API REST : Récupération de la liste des clients.
    
    Endpoint JSON pour alimenter les interfaces dynamiques (DataTables, AutoComplete, etc.).
    Supporte les paramètres de pagination, tri et filtrage via query string.
    
    Query Parameters:
        - page (int): Numéro de page (défaut: 1)
        - limit (int): Nombre d'éléments par page (défaut: 50)
        - search (str): Terme de recherche libre
        - type (int): Filtrage par type client (1=Particulier, 2=Professionnel)
        - status (bool): Filtrage par statut actif/inactif
        
    Returns:
        JSON: Liste des clients avec métadonnées de pagination
        
    Format de réponse:
        {
            "clients": [...],
            "total": 150,
            "page": 1,
            "pages": 3,
            "per_page": 50
        }
        
    Note: 
        Actuellement retourne des données de test. À connecter avec la base
        de données via les modèles SQLAlchemy (Client, Part, Pro).
    """
    # TODO: Remplacer par une vraie requête base de données
    # Exemple d'implémentation future :
    # db_session = SessionBdD()
    # clients = db_session.query(Client).filter(Client.is_active == True).all()
    
    # Données de test pour développement frontend
    clients: List[Dict[str, Any]] = [
        {
            "id": 1, 
            "global_name": "ACME Corporation", 
            "type": "Professionnel",
            "email": "contact@acme.com",
            "phone": "+33 1 23 45 67 89",
            "status": "Actif",
            "created_at": "2024-01-15"
        },
        {
            "id": 2, 
            "global_name": "Martin Dupont", 
            "type": "Particulier",
            "email": "martin.dupont@email.com",
            "phone": "+33 6 12 34 56 78",
            "status": "Actif",
            "created_at": "2024-02-20"
        },
        {
            "id": 3, 
            "global_name": "Tech Solutions SARL", 
            "type": "Professionnel",
            "email": "info@techsolutions.fr",
            "phone": "+33 4 56 78 90 12",
            "status": "Inactif",
            "created_at": "2024-03-10"
        },
    ]
    
    return jsonify({
        "clients": clients,
        "total": len(clients),
        "page": 1,
        "pages": 1,
        "per_page": 50
    })

# ================================================================
# ROUTES DE DÉVELOPPEMENT
# ================================================================

@clients_bp.route('/research/<client_string>')
def hello_clients(client_string: str):
    """
    Route de recherche de client par nom.
    La recherche s'effectue sur le nom complet du client, particulier ou professionnel.
    """
    db_session: SessionBdDType = SessionBdD()
    clients: List[Client] = (
    db_session.query(Client)
    .outerjoin(Client.part)
    .outerjoin(Client.pro)
    .filter(
        or_(
            Part.nom.ilike(f"%{client_string}%"),
            Pro.raison_sociale.ilike(f"%{client_string}%")
        )
    )
    .all()
)
    return jsonify([c.to_dict() for c in clients])
