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

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from sqlalchemy.orm import Session as SessionBdDType
from sqlalchemy import or_
from app_acfc.modeles import SessionBdD, Client, Part, Pro, Telephone, Mail, Commande, Facture, Adresse
from typing import List, Dict
from app_acfc.habilitations import validate_habilitation, CLIENTS
from logs.logger import acfc_log, ERROR, WARNING, INFO, DEBUG
from datetime import datetime
import logging

# ================================================================
# CONSTANTES
# ================================================================

# Messages d'erreur constants
ERROR_CLIENT_NOT_FOUND = "Client not found"
ERROR_ACCESS_DENIED = "Accès refusé"

# Messages constants pour les titres
TITLE_NEW_CLIENT = "ACFC - Nouveau client"
TITLE_EDIT_CLIENT = "ACFC - Modifier client"
BASE = 'base.html'

# Configuration page de création/modification de client
CLIENT_FORM: Dict[str, str] = {
    'title': TITLE_NEW_CLIENT,
    'context': 'clients',
    'page': BASE
}

# Configuration page de gestion des clients
CLIENT_PARAM_PAGE: Dict[str, str] = {
    'title': 'ACFC - Gestion Clients',
    'context': 'clients',
    'page': BASE
}

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

@clients_bp.route('/all_clients', methods=['GET'])
@validate_habilitation(CLIENTS)
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

@clients_bp.route('/list')
@validate_habilitation(CLIENTS)
def client_list():
    """
    Page de liste des clients - redirection vers la page principale.
    """
    return jsonify({
        "clients": "clients",
        "total": len("clients"),
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

@clients_bp.route('/<int:id_client>', methods=['GET'])
@validate_habilitation(CLIENTS)
def get_client(id_client: int):
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
    client: Client | None = db_session.query(Client).get(id_client)
    acfc_log.log_to_file(DEBUG, f'{client}')

    # Récupération du contexte du client et retour
    if client:
        part = client.part
        pro = client.pro
        phones: List[Telephone] = client.tels
        mails: List[Mail] = client.mails
        addresses: List[Adresse] = client.adresses
        orders: List[Commande] = client.commandes
        bills: List[Facture] = client.factures
        nom_affichage = client.nom_affichage
        db_session.close()
        return render_template(CLIENT_PARAM_PAGE['page'],
                               title=CLIENT_PARAM_PAGE['title'],
                               context=CLIENT_PARAM_PAGE['context'],
                               objects=[client, part, pro, addresses, phones, mails, orders, bills, nom_affichage])
    else:
        db_session.close()
        return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404
    
@clients_bp.route('/<id_client>/commandes/en-cours')
@validate_habilitation(CLIENTS)
def get_commandes_en_cours(id_client: int):
    """
    Route de récupération des commandes en cours
    """
    db_session: SessionBdDType = SessionBdD()
    commandes: List[Commande] = (
        db_session.query(Commande)
        .filter(Commande.id_client == id_client, Commande.status == "en_cours")
        .all()
    )
    db_session.close()
    return jsonify([c.to_dict() for c in commandes])

@clients_bp.route('/nouveau')
@validate_habilitation(CLIENTS)
def new_client():
    """
    Route d'affichage du formulaire de création d'un nouveau client.
    """
    client = Client()
    return render_template(CLIENT_FORM['page'],
                           title=CLIENT_FORM['title'],
                           context=CLIENT_FORM['context'],
                           sub_context='create',
                           client=client)

@clients_bp.route('/<int:id_client>/modifier')
@validate_habilitation(CLIENTS)
def edit_client(id_client: int):
    """
    Route d'affichage du formulaire de modification d'un client existant.
    """
    db_session: SessionBdDType = SessionBdD()
    client: Client | None = db_session.query(Client).get(id_client)
    
    if client:
        db_session.close()
        return render_template(CLIENT_FORM['page'],
                               title=f"ACFC - Modifier {client.nom_affichage}",
                               context=CLIENT_FORM['context'],
                               sub_context='edit',
                               client=client)
    else:
        db_session.close()
        return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404

@clients_bp.route('/create', methods=['GET', 'POST'])
@validate_habilitation(CLIENTS)
def create_client():
    """
    Création d'un nouveau client (particulier ou professionnel).
    
    GET : Affiche le formulaire de création
    POST : Traite les données et crée le client
    """
    if request.method == 'GET':
        return render_template(CLIENT_FORM['page'],
                               title=TITLE_NEW_CLIENT,
                               context=CLIENT_FORM['context'],
                               sub_context='create')
    
    # Traitement POST
    db_session = SessionBdD()
    try:
        # Validation des données requises
        type_client_str = request.form.get('type_client')
        if not type_client_str:
            raise ValueError("Le type de client est obligatoire")
        
        type_client = int(type_client_str)
        notes = request.form.get('notes', '')
        
        # Création du client de base
        nouveau_client = Client(
            type_client=type_client,
            notes=notes
        )
        db_session.add(nouveau_client)
        db_session.flush()  # Pour obtenir l'ID
        
        # Création des informations spécifiques selon le type
        if type_client == 1:  # Particulier
            date_naissance_str = request.form.get('date_naissance', None)
            prenom = request.form.get('prenom')
            nom = request.form.get('nom')
            lieu_naissance = request.form.get('lieu_naissance')
            
            if not all([prenom, nom]):
                raise ValueError("Tous les champs particulier sont obligatoires")
            
            part = Part(
                id_client=nouveau_client.id,
                prenom=prenom,
                nom=nom,
                date_naissance=datetime.strptime(date_naissance_str, '%Y-%m-%d').date() if date_naissance_str else None,
                lieu_naissance=lieu_naissance if lieu_naissance else None
            )
            db_session.add(part)
            
        elif type_client == 2:  # Professionnel
            raison_sociale = request.form.get('raison_sociale')
            if raison_sociale: raison_sociale = raison_sociale.strip()
            type_pro_str = request.form.get('type_pro')
            
            if not all([raison_sociale, type_pro_str]):
                raise ValueError("La raison sociale et le type sont obligatoires pour un professionnel")
            
            # Vérification de type explicite pour type_pro_str
            if not isinstance(type_pro_str, str):
                raise ValueError("Type de professionnel invalide")
            
            siren = request.form.get('siren', '')
            rna = request.form.get('rna', '')
            
            pro = Pro(
                id_client=nouveau_client.id,
                raison_sociale=raison_sociale,
                type_pro=int(type_pro_str),
                siren=siren if siren else None,
                rna=rna if rna else None
            )
            db_session.add(pro)
        
        db_session.commit()
        acfc_log.log_to_file(logging.INFO, f"Nouveau client créé : ID {nouveau_client.id}", db_log=True, zone_log="clients")
        
        return redirect(url_for('clients.get_client', id_client=nouveau_client.id, success_message='Prospect créé avec succès.'))
        
    except ValueError as e:
        if 'db_session' in locals():
            db_session.rollback()
        return render_template(CLIENT_FORM['page'],
                               title=TITLE_NEW_CLIENT,
                               context=CLIENT_FORM['context'],
                               sub_context='create',
                               error_message=str(e))
    except Exception as e:
        if 'db_session' in locals():
            db_session.rollback()
        acfc_log.log_to_file(logging.ERROR, f"Erreur lors de la création du client : {str(e)}", db_log=True, zone_log="clients")
        return render_template(CLIENT_FORM['page'],
                               title=TITLE_NEW_CLIENT,
                               context=CLIENT_FORM['context'],
                               sub_context='create',
                               error_message=f"Une erreur est survenue lors de la création du client: {e}")
    finally:
        if 'db_session' in locals():
            db_session.close()

@clients_bp.route('/<int:id_client>/edit', methods=['GET'])
@validate_habilitation(CLIENTS)
def edit_client_form(id_client: int):
    """
    Affiche le formulaire d'édition d'un client.
    """
    db_session = SessionBdD()
    try:
        client = db_session.query(Client).get(id_client)
        
        if not client:
            return render_template("errors/404.html",
                                   title="ACFC - Client introuvable",
                                   sub_context="error",
                                   error_message=ERROR_CLIENT_NOT_FOUND)
        
        title = f"ACFC - Modifier {getattr(client, 'nom_affichage', f'Client {id_client}')}"
        
        return render_template(CLIENT_FORM['page'],
                               title=title,
                               context=CLIENT_FORM['context'],
                               sub_context='edit',
                               client=client)
    finally:
        db_session.close()

@clients_bp.route('/<int:id_client>/update', methods=['POST'])
@validate_habilitation(CLIENTS)
def update_client(id_client: int):
    """
    Mise à jour des informations d'un client existant.
    """
    db_session = SessionBdD()
    client = None
    
    try:
        client = db_session.query(Client).get(id_client)
        
        if not client:
            return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404
        
        # Mise à jour des données de base
        notes = request.form.get('notes', '')
        client.notes = notes
        
        # Mise à jour des données spécifiques selon le type
        if client.type_client == 1 and client.part:  # Particulier
            prenom = request.form.get('prenom')
            nom = request.form.get('nom')
            lieu_naissance = request.form.get('lieu_naissance')
            date_naissance_str = request.form.get('date_naissance')
            
            if prenom:
                client.part.prenom = prenom
            if nom:
                client.part.nom = nom
            if lieu_naissance:
                client.part.lieu_naissance = lieu_naissance
            if date_naissance_str:
                client.part.date_naissance = datetime.strptime(date_naissance_str, '%Y-%m-%d').date()
        
        elif client.type_client == 2 and client.pro:  # Professionnel
            raison_sociale = request.form.get('raison_sociale')
            type_pro_str = request.form.get('type_pro')
            siren = request.form.get('siren', '')
            rna = request.form.get('rna', '')
            
            if raison_sociale:
                client.pro.raison_sociale = raison_sociale
            if type_pro_str:
                client.pro.type_pro = int(type_pro_str)
            client.pro.siren = siren if siren else None
            client.pro.rna = rna if rna else None
        
        db_session.commit()
        acfc_log.log_to_file(logging.INFO, f"Client modifié : ID {client.id}")
        
        # Redirection vers la page de détails du client
        return redirect(url_for('clients.get_client', id_client=client.id))
        
    except Exception as e:
        if 'db_session' in locals():
            db_session.rollback()
        acfc_log.log_to_file(logging.ERROR, f"Erreur lors de la modification du client {id_client} : {str(e)}")
        
        # Gestion de l'affichage en cas d'erreur
        title = TITLE_EDIT_CLIENT
        if client:
            title = f"ACFC - Modifier {getattr(client, 'nom_affichage', f'Client {id_client}')}"
            
        return render_template(CLIENT_FORM['page'],
                               title=title,
                               context=CLIENT_FORM['context'],
                               sub_context='edit',
                               client=client,
                               error_message=f"Erreur lors de la modification : {str(e)}")
    finally:
        if 'db_session' in locals():
            db_session.close()

@clients_bp.route('/add_phone/', methods=['POST'])
def clients_add_phone():
    """
    Ajout d'un numéro de téléphone pour un client.
    """
    db_session = SessionBdD()
    client = None

    try:
        client_id = request.form.get('client_id')
        client = db_session.query(Client).get(client_id)

        if not client:
            return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404

        # Récupération et validation du numéro de téléphone
        phone_number = request.form.get('phone_number')
        if not phone_number:
            return jsonify({"error": "Numéro de téléphone manquant"}), 400

        # Ajout du numéro de téléphone
        new_phone = Phone(client_id=client.id, numero=phone_number)
        db_session.add(new_phone)
        db_session.commit()

        return jsonify({"message": "Numéro de téléphone ajouté avec succès"}), 201

    except Exception as e:
        if 'db_session' in locals():
            db_session.rollback()
        acfc_log.log_to_file(logging.ERROR, f"Erreur lors de l'ajout du téléphone pour le client {client_id} : {str(e)}")
        return jsonify({"error": "Erreur lors de l'ajout du téléphone"}), 500
    finally:
        if 'db_session' in locals():
            db_session.close()

@clients_bp.route('/add_email/', methods=['POST'])
def clients_add_email():
    """
    Ajout d'un email pour un client.
    """
    db_session = SessionBdD()
    client = None

    try:
        client_id = request.form.get('client_id')
        client = db_session.query(Client).get(client_id)

        if not client:
            return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404

        # Récupération et validation de l'email
        email = request.form.get('email')
        if not email:
            return jsonify({"error": "Email manquant"}), 400

        # Ajout de l'email
        new_email = Email(client_id=client.id, email=email)
        db_session.add(new_email)
        db_session.commit()

        return jsonify({"message": "Email ajouté avec succès"}), 201

    except Exception as e:
        if 'db_session' in locals():
            db_session.rollback()
        acfc_log.log_to_file(logging.ERROR, f"Erreur lors de l'ajout de l'email pour le client {client_id} : {str(e)}")
        return jsonify({"error": "Erreur lors de l'ajout de l'email"}), 500
    finally:
        if 'db_session' in locals():
            db_session.close()

@clients_bp.route('/add_address/', methods=['POST'])
def clients_add_address():
    """
    Ajout d'une adresse pour un client.
    """
    db_session = SessionBdD()
    client = None

    try:
        client_id = request.form.get('client_id')
        client = db_session.query(Client).get(client_id)

        if not client:
            return jsonify({"error": ERROR_CLIENT_NOT_FOUND}), 404

        # Récupération et validation de l'adresse
        adresse = request.form.get('adresse')
        if not adresse:
            return jsonify({"error": "Adresse manquante"}), 400

        # Ajout de l'adresse
        new_address = Address(client_id=client.id, adresse=adresse)
        db_session.add(new_address)
        db_session.commit()

        return jsonify({"message": "Adresse ajoutée avec succès"}), 201

    except Exception as e:
        if 'db_session' in locals():
            db_session.rollback()
        acfc_log.log_to_file(logging.ERROR, f"Erreur lors de l'ajout de l'adresse pour le client {client_id} : {str(e)}")
        return jsonify({"error": "Erreur lors de l'ajout de l'adresse"}), 500
    finally:
        if 'db_session' in locals():
            db_session.close()


