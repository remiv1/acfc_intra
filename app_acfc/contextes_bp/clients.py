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
from flask import Blueprint, jsonify, request, redirect, url_for, Request, session
from sqlalchemy.orm import Session as SessionBdDType, joinedload
from sqlalchemy import or_, func
from werkzeug import Response as ResponseWerkzeug
from app_acfc.modeles import (
    get_db_session, Client, Part, Pro, Telephone, Mail, Commande,
    Facture, Adresse, PrepareTemplates, Constants)
from app_acfc.habilitations import validate_habilitation, CLIENTS, GESTIONNAIRE
from datetime import datetime
from typing import List

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
# FONCTIONS ET CLASSES HORS ROUTES
# ================================================================

class ClientMethods:
    """
    Classe utilitaire pour les méthodes liées aux clients.

    Methodes statiques pour :
        - Récupération du taux de réduction
        - Création/modification de clients particuliers ou professionnels
    """
    
    @staticmethod
    def get_reduces(request: Request) -> float:
        """
        Récupère le taux de réduction depuis la requête.

        Args:
            request (Request): Objet de requête Flask

        Returns:
            float: Taux de réduction (0.10 par défaut si non spécifié)
        """
        reduces_str = request.form.get('reduces', '0.10')
        try:
            return float(reduces_str) / 100  # Conversion pourcentage vers décimal
        except (ValueError, TypeError):
            return 10.0  # Valeur par défaut : 10%

    @staticmethod
    def create_or_modify_client(request: Request, type_client: int, client: Client,
                                db_session: SessionBdDType, type_test: str = 'create') -> None:
        '''
        Teste la création d'un client particulier ou professionnel.
        Création du client suivant le type.
        '''
        if type_client == 1:  # Particulier
            ClientMethods.create_or_modify_part(request, client, db_session, type_test)

        elif type_client == 2:  # Professionnel
            ClientMethods.create_or_modify_pro(request, client, db_session, type_test)

    @staticmethod
    def create_or_modify_part(request: Request, client: Client, db_session: SessionBdDType,
                              type_test: str = 'create') -> None:
        """
        Crée ou modifie un client particulier.

        Args:
            request (Request): Objet de requête Flask
            client (Client): Objet client à modifier ou à créer
            db_session (SessionBdDType): Session de base de données
            type_test (str): Type de test ('create' ou 'update')
        """
        # Récupération des données spécifiques au particulier depuis le formulaire
        prenom = request.form.get('prenom', '')
        nom = request.form.get('nom', '')
        date_naissance_str = request.form.get('date_naissance', None)
        lieu_naissance = request.form.get('lieu_naissance', '')

        # Création ou récupération du client particulier
        part = Part(id_client=client.id) if type_test == 'create' else client.part
        part.prenom = prenom
        part.nom = nom
        part.date_naissance = datetime.strptime(date_naissance_str, '%Y-%m-%d').date() if date_naissance_str else None
        part.lieu_naissance = lieu_naissance if lieu_naissance else None

        db_session.add(part) if type_test == 'create' else db_session.merge(part)

    @staticmethod
    def create_or_modify_pro(request: Request, client: Client,
                             db_session: SessionBdDType, type_test: str = 'create') -> None:
        """
        Crée ou modifie un client professionnel.

        Args:
            request (Request): Objet de requête Flask
            client (Client): Objet client à modifier ou à créer
            db_session (SessionBdDType): Session de base de données
            type_test (str): Type de test ('create' ou 'update')
        """
        # Récupération des données spécifiques au professionnel depuis le formulaire
        raison_sociale = request.form.get('raison_sociale', '')
        type_pro_str = request.form.get('type_pro', '')
        siren = request.form.get('siren', '')
        rna = request.form.get('rna', '')

        # Création ou récupération du client professionnel
        pro = Pro(id_client=client.id) if type_test == 'create' else client.pro
        pro.raison_sociale = raison_sociale
        pro.type_pro = int(type_pro_str)
        pro.siren = siren if siren else None
        pro.rna = rna if rna else None

        db_session.add(pro) if type_test == 'create' else db_session.merge(pro)


# ================================================================
# ROUTES - INTERFACE DE RECHERCHE CLIENTS
# ================================================================

@validate_habilitation(CLIENTS)
@validate_habilitation(GESTIONNAIRE)
@clients_bp.route('/rechercher', methods=['GET'])
def clients_list() -> str:
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
    return PrepareTemplates.clients(sub_context='research')

# ================================================================
# API REST - DONNÉES CLIENTS GLOBALES
# ================================================================

@validate_habilitation(GESTIONNAIRE)
@validate_habilitation(CLIENTS)
@clients_bp.route('/recherche_avancee', methods=['GET'])
def recherche_avancee() -> ResponseWerkzeug | str:
    """
    API REST : Recherche avancée de clients.
    
    Effectue une recherche dans différents champs selon le type spécifié.
    Supporte la recherche dans : nom, email, téléphone, adresse.
    
    Query Parameters:
        - q (str): Terme de recherche (minimum 3 caractères)
        - type (str): Type de recherche ('part', 'pro', 'mail', 'telephone', 'adresse')
        
    Returns:
        JSON: Liste des clients correspondants avec nom_affichage, code_postal, ville, type
    """
    # Récupération des paramètres
    search_term = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'part').strip()
    
    # Validation longueur minimum
    if len(search_term) < 3:
        return jsonify([])
    
    db_session: SessionBdDType = get_db_session()
    
    try:
        clients = []
        
        if search_type == 'part':
            # Recherche dans les particuliers (prénom + nom)
            clients = (
                db_session.query(Client)
                .join(Client.part)
                .filter(
                    Client.is_active == True,
                    or_(
                        Part.prenom.ilike(f'%{search_term}%'),
                        Part.nom.ilike(f'%{search_term}%'),
                        func.concat(Part.prenom, ' ', Part.nom).ilike(f'%{search_term}%')
                    )
                )
                .all()
            )
            
        elif search_type == 'pro':
            # Recherche dans les professionnels (raison sociale)
            clients = (
                db_session.query(Client)
                .join(Client.pro)
                .filter(
                    Client.is_active == True,
                    Pro.raison_sociale.ilike(f'%{search_term}%')
                )
                .all()
            )
            
        elif search_type == 'mail':
            # Recherche par email
            clients = (
                db_session.query(Client)
                .join(Client.mails)
                .filter(
                    Client.is_active == True,
                    Mail.mail.ilike(f'%{search_term}%')
                )
                .distinct()
                .all()
            )
            
        elif search_type == 'telephone':
            # Recherche par téléphone
            clients = (
                db_session.query(Client)
                .join(Client.tels)
                .filter(
                    Client.is_active == True,
                    Telephone.telephone.ilike(f'%{search_term}%')
                )
                .distinct()
                .all()
            )
            
        elif search_type == 'adresse':
            # Recherche par adresse (adresse, code postal ou ville)
            clients = (
                db_session.query(Client)
                .join(Client.adresses)
                .filter(
                    Client.is_active == True,
                    Adresse.is_active == True,
                    or_(
                        Adresse.adresse_l1.ilike(f'%{search_term}%'),
                        Adresse.adresse_l2.ilike(f'%{search_term}%'),
                        Adresse.code_postal.ilike(f'%{search_term}%'),
                        Adresse.ville.ilike(f'%{search_term}%')
                    )
                )
                .distinct()
                .all()
            )
        
        # Conversion en dictionnaire et retour
        return jsonify([client.to_dict() for client in clients[:20]])  # Limite à 20 résultats
        
    except Exception as e:
        return PrepareTemplates.error_5xx(status_code=500, status_message=str(e),
                                          log=True, specific_log=Constants.log_files('client'))


# ================================================================
# DONNÉES CLIENTS INDIVIDUELLES
# ================================================================

@clients_bp.route('/nouveau', methods=['GET', 'POST'])
@validate_habilitation(CLIENTS)
def create_client() -> str | ResponseWerkzeug:
    """
    Création d'un nouveau client (particulier ou professionnel).
    
    GET : Affiche le formulaire de création
    POST : Traite les données et crée le client
    """
    # === L'utilisateur demande le formulaire ===
    if request.method == 'GET':
        return PrepareTemplates.clients(sub_context='create')
    
    # === L'utilisateur soumet le formulaire ===
    db_session = get_db_session()
    try:
        # Validation des données requises
        type_client = int(request.form.get('type_client', -1)) or -1
        if type_client == -1: raise ValueError("Le type de client est obligatoire")
        notes = request.form.get('notes', '')
        reduces = ClientMethods.get_reduces(request)
        
        # Création du client de base
        nouveau_client = Client(
            type_client=type_client,
            notes=notes,
            reduces=reduces,
            created_by=session.get('pseudo', 'N/A')
        )
        db_session.add(nouveau_client)
        db_session.flush()  # Pour obtenir l'ID
        
        # Création du client particulier ou professionnel suivant type
        ClientMethods.create_or_modify_client(request, type_client, nouveau_client, db_session)

        # Envoi du client en base de données
        db_session.commit()        
        
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=nouveau_client.id,
                                success_message=Constants.messages('client', 'create')))
    except Exception as e:
        return PrepareTemplates.error_5xx(status_code=500, status_message=str(e),
                                          log=True, specific_log=Constants.log_files('client'))

@clients_bp.route('/<int:id_client>', methods=['GET'])
@validate_habilitation(CLIENTS)
def get_client(id_client: int) -> str:
    """
    Route de récupération d'un client et de tout son contexte par son ID.
    Contexte du client :
        - Téléphones
        - Mails
        - Adresses
        - Commandes
        - Factures
    Pour le moment, retour sous forme de dictionnaire, mais par la suite, intégration dans une page.
    """
    # Ouverture d'une session vers la base de données
    db_session: SessionBdDType = get_db_session()

    # Recherche du client par ID avec eager loading
    client: Client | None = db_session.query(Client).options(
        joinedload(Client.part),
        joinedload(Client.pro),
        joinedload(Client.tels),
        joinedload(Client.mails),
        joinedload(Client.adresses),
        joinedload(Client.commandes),
        joinedload(Client.factures)
    ).get(id_client)

    # Récupération du contexte du client et retour
    if client:
        part = client.part
        pro = client.pro
        phones: List[Telephone] = client.tels
        mails: List[Mail] = client.mails
        addresses: List[Adresse] = client.adresses
        orders: List[Commande] = sorted(client.commandes, key=lambda x: x.id, reverse=True)
        bills: List[Facture] = client.factures
        nom_affichage = client.nom_affichage
        return PrepareTemplates.clients(sub_context='detail', client=client, part=part, pro=pro, phones=phones,
                                        mails=mails, addresses=addresses, orders=orders, bills=bills,
                                        id_client=client.id, nom_affichage=nom_affichage, log=True)
    else:
        return PrepareTemplates.error_4xx(status_code=404, log=True,
                                          status_message=Constants.messages('client', 'not_found'))

@clients_bp.route('/<int:id_client>/modifier', methods=['GET'])
@validate_habilitation(CLIENTS)
def edit_client(id_client: int) -> str:
    """
    Route d'affichage du formulaire de modification d'un client existant.
    Récupère les informations actuelles du client et les affiche dans un formulaire.
    Args:
        id_client (int): ID du client à modifier
    Returns:
        str: Template HTML du formulaire de modification avec les données pré-remplies
    """
    db_session: SessionBdDType = get_db_session()
    client: Client | None = db_session.query(Client).options(
        joinedload(Client.part),
        joinedload(Client.pro)
    ).get(id_client)
    
    if client:
        # Récupération du nom d'affichage avant de fermer la session
        nom_affichage = client.nom_affichage
        id_client = client.id
        return PrepareTemplates.clients(sub_context='edit', client=client,
                                        id_client=id_client,
                                        nom_affichage=nom_affichage)
    else:
        return PrepareTemplates.error_4xx(status_code=404, log=True,
                                          status_message=Constants.messages('client', 'not_found'))

@validate_habilitation(CLIENTS)
@clients_bp.route('/<int:id_client>/update', methods=['POST'])
def update_client(id_client: int) -> ResponseWerkzeug | str:
    """
    Mise à jour des informations d'un client existant.
    Endpoint REST pour modifier les informations d'un client.
    Accepte les données via un formulaire POST.
    Form Data:
        - id_client (int): ID du client à modifier
        - type_client (int): Type de client (1=particulier, 2=professionnel)
        - notes (str): Notes internes
        - reduces (float): Taux de réduction en pourcentage (ex: 10 pour 10%)
        - Données spécifiques au type de client (particulier ou professionnel)
    Returns:
        Redirect: Vers la page de détails du client avec message de succès ou d'erreur
    """
    db_session = get_db_session()
    client = None
    nom_affichage = None
    
    try:
        # Récupération du client à modifier
        client = db_session.query(Client).options(
            joinedload(Client.part),
            joinedload(Client.pro)
        ).get(id_client)
        
        # Gestion de l'absence de retours
        if not client:
            return redirect(url_for(Constants.return_pages('clients', 'recherche')))
        
        # Récupération du nom d'affichage au début pour éviter les problèmes de session
        nom_affichage = client.nom_affichage
        
        # Mise à jour des données de base
        notes = request.form.get('notes', '')
        client.notes = notes
        reduces = request.form.get('reduces', '10')
        client.reduces = float(reduces) / 100
        type_client = client.type_client
        client.modified_by = session.get('pseudo', 'N/A')

        # Création du client part ou pro suivant le context
        ClientMethods.create_or_modify_client(request=request, type_client=type_client,
                                              client=client, db_session=db_session,
                                              type_test='update')

        # Intégration dans la base de données
        db_session.commit()
        
        # Redirection vers la page de détails du client avec message de succès
        return PrepareTemplates.clients(success_message=Constants.messages('client', 'update'), id_client=client.id)
    except Exception as e:
        return PrepareTemplates.clients(sub_context='edit', client=client, log=True,
                                        id_client=client.id if client else id_client,
                                        nom_affichage=nom_affichage if nom_affichage else f"Client {id_client}",
                                        error_message=Constants.messages('error_500', 'default') + f" : {e}")

@clients_bp.route('<int:id_client>/add_phone/', methods=['POST'])
@validate_habilitation(CLIENTS)
def add_phone(id_client: int) -> ResponseWerkzeug:
    """
    Ajout d'un numéro de téléphone pour un client.
    
    Endpoint REST pour ajouter un nouveau numéro de téléphone à un client existant.
    Supporte différents types : fixe_pro, mobile_pro, fixe_perso, mobile_perso, fax.
    
    Form Data:
        - id_client (int): ID du client
        - telephone (str): Numéro de téléphone
        - type_telephone (str): Type de téléphone
        - indicatif (str, optional): Indicatif pays (ex: +33)
        - detail (str, optional): Précisions sur l'usage
        - is_principal (bool, optional): Téléphone principal
    
    Returns:
        Redirect: Vers la page de détails du client avec message de succès ou d'erreur
    """
    db_session = get_db_session()
    client = None

    try:
        # Récupération et validation des données
        client = db_session.query(Client).get(id_client)
        if not client: return redirect(url_for(Constants.return_pages('clients', 'client-search')))

        # Validation du numéro de téléphone
        telephone = request.form.get('telephone', '').strip()
        if not telephone: return redirect(url_for(Constants.return_pages('clients', 'client-detail'),
                                                  id_client=id_client,
                                                  error_message=Constants.messages('phone', 'missing')))

        # Récupération des autres données
        type_telephone = request.form.get('type_telephone', 'mobile_pro')
        indicatif = request.form.get('indicatif', '').strip()
        detail = request.form.get('detail', '').strip()
        is_principal = request.form.get('is_principal', 'false').lower() == 'true'

        # Si c'est le téléphone principal, désactiver les autres
        if is_principal: db_session.query(Telephone).filter_by(
            id_client=client.id, is_principal=True
            ).update({'is_principal': False})

        # Création du nouveau téléphone
        new_telephone = Telephone(
            id_client=client.id,
            telephone=telephone,
            type_telephone=type_telephone,
            indicatif=indicatif if indicatif else None,
            detail=detail if detail else None,
            is_principal=is_principal
        )
        
        # Enregistrement en base de données
        db_session.add(new_telephone)
        db_session.commit()

        return redirect(url_for(Constants.return_pages('clients', 'client-detail'),
                                id_client=id_client, success_message=Constants.messages('phone', 'valid')))

    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'client-detail'),
                                 id_client=id_client, log=True,
                                 error_message=Constants.messages('error_500', 'default') + f" : {e}"))

# TODO: Faire une méthode modifier/supprimer pour les téléphones, emails et adresses

@clients_bp.route('/<int:id_client>/add_email/', methods=['POST'])
@validate_habilitation(CLIENTS)
def add_email(id_client: int) -> ResponseWerkzeug:
    """
    Ajout d'un email pour un client.
    
    Endpoint REST pour ajouter une nouvelle adresse email à un client existant.
    Supporte différents types : professionnel, personnel, facturation, marketing.
    
    Form Data:
        - id_client (int): ID du client
        - mail (str): Adresse email
        - type_mail (str): Type d'email
        - detail (str, optional): Précisions sur l'usage
        - is_principal (bool, optional): Email principal
    
    Returns:
        Page redirection avec message de succès ou d'erreur
    """
    db_session = get_db_session()
    client = None

    try:
        # Récupération et validation des données
        client = db_session.query(Client).get(id_client)
        if not client: return redirect(url_for(Constants.return_pages('clients', 'client-search')))

        # Validation de l'email
        email = request.form.get('mail', '').strip()
        if not email: return redirect(url_for(Constants.return_pages('clients', 'client-detail'),
                                                  id_client=id_client,
                                                  error_message=Constants.messages('email', 'missing')))

        # Validation basique du format email
        if '@' not in email or '.' not in email.split('@')[-1]:
            return redirect(url_for(Constants.return_pages('clients', 'client-detail'),
                                                  id_client=id_client,
                                                  error_message=Constants.messages('email', 'invalid')))

        # Récupération des autres données
        type_mail = request.form.get('type_mail', 'professionnel')
        detail = request.form.get('detail', '').strip()
        is_principal = request.form.get('is_principal', 'false').lower() == 'true'

        # Si c'est l'email principal, désactiver les autres
        if is_principal: db_session.query(Mail).filter_by(
            id_client=client.id, is_principal=True
            ).update({'is_principal': False})

        # Création du nouvel email
        new_mail = Mail(
            id_client=client.id,
            mail=email,
            type_mail=type_mail,
            detail=detail if detail else None,
            is_principal=is_principal,
            created_by=session.get('pseudo', 'N/A')
        )
        
        # Enregistrement en base de données
        db_session.add(new_mail)
        db_session.commit()

        return redirect(url_for(Constants.return_pages('clients', 'client-detail'),
                                id_client=id_client, success_message="Email ajouté avec succès"))

    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'client-detail'),
                                id_client=id_client, log=True,
                                error_message=Constants.messages('error_500', 'default') + f" : {e}"))

@clients_bp.route('/<int:id_client>/add_address/', methods=['POST'])
@validate_habilitation(CLIENTS)
def add_address(id_client: int) -> ResponseWerkzeug:
    """
    Ajout d'une adresse pour un client.
    
    Endpoint REST pour ajouter une nouvelle adresse à un client existant.
    Gère les adresses complètes avec code postal et ville.
    
    Form Data:
        - id_client (int): ID du client
        - adresse_l1 (str): Première ligne d'adresse
        - adresse_l2 (str, optional): Deuxième ligne d'adresse
        - code_postal (str): Code postal
        - ville (str): Ville
        - is_principal (bool, optional): Si c'est l'adresse principale
    
    Returns:
        Redirect: Vers la page de détails du client avec message de succès ou d'erreur
    """
    db_session = get_db_session()
    client = None

    try:
        # Récupération et validation des données
        client = db_session.query(Client).get(id_client)
        if not client:
            return redirect(url_for(Constants.return_pages('clients', 'client-detail'),
                                    id_client=id_client, error_message=Constants.messages('client', 'not_found')))

        # Validation des données d'adresse
        adresse_l1 = request.form.get('adresse_l1', '').strip()
        code_postal = request.form.get('code_postal', '').strip()
        ville = request.form.get('ville', '').strip()
        adresse_l2 = request.form.get('adresse_l2', '').strip()
        is_principal = request.form.get('is_principal', 'false').lower() == 'true'
        if not adresse_l1 or not code_postal or not ville: return redirect(
            url_for(Constants.return_pages('clients', 'client-detail'),
                    id_client=id_client, error_message=Constants.messages('address', 'missing')
                    )
            )

        # Si c'est l'adresse principale, désactiver les autres
        if is_principal: db_session.query(Adresse).filter_by(
            id_client=client.id, is_principal=True
            ).update({'is_principal': False})

        # Création de la nouvelle adresse
        new_adresse = Adresse(
            id_client=client.id,
            adresse_l1=adresse_l1,
            adresse_l2=adresse_l2 if adresse_l2 else None,
            code_postal=code_postal,
            ville=ville,
            is_principal=is_principal,
            created_by=session.get('pseudo', 'N/A')
        )
        
        # Enregistrement en base de données
        db_session.add(new_adresse)
        db_session.commit()

        return redirect(url_for(Constants.return_pages('clients', 'client-detail'),
                                id_client=id_client, success_message=Constants.messages('address', 'valid')))

    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'client-detail'), id_client=id_client,
                                error_message=Constants.messages('error_500', 'default') + f" : {e}", log=True))
