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
from app_acfc.modeles import SessionBdD, Client, Part, Pro, Telephone, Mail, Commande, Facture
from typing import List
from app_acfc.habilitations import validate_habilitation, CLIENTS

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
@validate_habilitation(CLIENTS)
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
                         context='clients',           # Context CSS/JS pour styling et page contextuelle
                         sub_context='research')      # Sous-context personnalisation du contexte

# ================================================================
# API REST - DONNÉES CLIENTS GLOBALES
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
    # Ouverture d'une session vers la base de données
    db_session: SessionBdDType = SessionBdD()

    # Recherche de la liste de clients
    clients: List[Client] = (
        db_session.query(Client)
        .filter(Client.is_active == True)
        .all()
    )

    # Création d'un dictionnaire pour le retour
    clients = [c.to_dict() for c in clients]

    # Fermeture de la session et retour de la route
    db_session.close()
    # TODO: Créer une page de retour de la liste
    return jsonify({
        "clients": clients,
        "total": len(clients),
        "page": 1,
        "pages": 1,
        "per_page": 50
    })

# ================================================================
# DONNÉES CLIENTS INDIVIDUELLES
# ================================================================

@clients_bp.route('/research/<client_string>')
@validate_habilitation(CLIENTS)
def get_clients_by_name(client_string: str):
    """
    Route de recherche de client par nom.
    La recherche s'effectue sur le nom complet du client, particulier ou professionnel.
    """
    db_session: SessionBdDType = SessionBdD()
    # Recherche de clients par nom (particuliers et professionnels)
    clients: List[Client] = (
        db_session.query(Client)
        .outerjoin(Client.part)    # Utilise le relationship
        .outerjoin(Client.pro)     # Utilise le relationship
        .filter(
            or_(
                Part.nom.ilike(f'%{client_string}%'),
                Part.prenom.ilike(f'%{client_string}%'),
                Pro.raison_sociale.ilike(f'%{client_string}%')
            )
        )
        .all()
    )
    
    db_session.close()
    return jsonify([c.to_dict() for c in clients])

@clients_bp.route('/client/<int:client_id>', methods=['GET'])
@validate_habilitation(CLIENTS)
def get_client(client_id: int):
    """
    Route de récupération d'un client et de tout son contexte par son ID.
    Contexte du client :
        - Téléphones
        - Mails
        - Commandes
        - Factures
    Pour le moment, retour sous forme de dictionnaire, mais par la suite, intégration dans une page.
    """
    # Ouverture d'une session vers la base de données
    db_session: SessionBdDType = SessionBdD()

    # Recherche du client par ID
    client: Client | None = db_session.query(Client).get(id==client_id)

    # Récupération du contexte du client et retour
    if client:
        phones: List[Telephone] = db_session.query(Telephone).filter(Telephone.client_id == client_id).all()
        mails: List[Mail] = db_session.query(Mail).filter(Mail.client_id == client_id).all()
        orders: List[Commande] = db_session.query(Commande).filter(Commande.client_id == client_id).all()
        bills: List[Facture] = db_session.query(Facture).filter(Facture.client_id == client_id).all()
        db_session.close()
        return jsonify({
            "client": client.to_dict(),
            "phones": [p.to_dict() for p in phones],
            "mails": [m.to_dict() for m in mails],
            "orders": [o.to_dict() for o in orders],
            "bills": [b.to_dict() for b in bills]
        })
    else:
        db_session.close()
        return jsonify({"error": "Client not found"}), 404