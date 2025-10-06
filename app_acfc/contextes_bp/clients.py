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
from flask import (Blueprint, jsonify, request, redirect, url_for, Request,
                   session)
from sqlalchemy.orm import Session as SessionBdDType, joinedload, contains_eager
from sqlalchemy import or_, func
from werkzeug import Response as ResponseWerkzeug
from app_acfc.modeles import (
    get_db_session, Client, Part, Pro, Telephone, Mail, Commande,
    Facture, Adresse, PrepareTemplates, Constants)
from app_acfc.habilitations import validate_habilitation, CLIENTS, GESTIONNAIRE, ADMINISTRATEUR
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

@validate_habilitation([CLIENTS, GESTIONNAIRE], _and=False)
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

@validate_habilitation([GESTIONNAIRE, CLIENTS], _and=False)
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
    search_is_inactive = request.args.get('search-inactive', 'false').strip().lower() == 'true'
    search_inactive_phone = or_(Telephone.is_inactive == True, Telephone.is_inactive == False) if (
        search_is_inactive
        and ('1' in session['habilitations'] or '2' in session['habilitations'])
    ) else Telephone.is_inactive == False
    search_inactive_mail = or_(Mail.is_inactive == True, Mail.is_inactive == False) if (
        search_is_inactive
        and ('1' in session['habilitations'] or '2' in session['habilitations'])
    ) else Mail.is_inactive == False
    search_inactive_address = or_(Adresse.is_inactive == True, Adresse.is_inactive == False) if (
        search_is_inactive
        and ('1' in session['habilitations'] or '2' in session['habilitations'])
    ) else Adresse.is_inactive == False
    search_active_clients = or_(Client.is_active == True, Client.is_active == False) if (
        not search_is_inactive
        and ('1' in session['habilitations'] or '2' in session['habilitations'])
    ) else Client.is_active == True


    # Récupération de la session de base de données
    db_session: SessionBdDType = get_db_session()
    
    try:
        clients = []
        
        match search_type:
            case 'part':
                # Recherche dans les particuliers (prénom + nom)
                clients = (
                    db_session.query(Client)
                    .join(Client.part)
                    .filter(
                        search_active_clients,
                        or_(
                            Part.prenom.ilike(f'%{search_term}%'),
                            Part.nom.ilike(f'%{search_term}%'),
                            func.concat(Part.prenom, ' ', Part.nom).ilike(f'%{search_term}%')
                        )
                    )
                    .all()
                )
            case 'pro':
                # Recherche dans les professionnels (raison sociale)
                clients = (
                    db_session.query(Client)
                    .join(Client.pro)
                    .filter(
                        search_active_clients,
                        Pro.raison_sociale.ilike(f'%{search_term}%')
                    )
                    .all()
                )
            case 'mail':
                # Recherche par email
                clients = (
                    db_session.query(Client)
                    .join(Client.mails)
                    .filter(
                        search_active_clients,
                        Mail.mail.ilike(f'%{search_term}%'),
                        search_inactive_mail
                    )
                    .distinct()
                    .all()
                )
            case 'telephone':
                # Recherche par téléphone
                clients = (
                    db_session.query(Client)
                    .join(Client.tels)
                    .filter(
                        search_active_clients,
                        Telephone.telephone.ilike(f'%{search_term}%'),
                        search_inactive_phone
                    )
                    .distinct()
                    .all()
                )
            case _:
                # Recherche par adresse (adresse, code postal ou ville)
                clients = (
                    db_session.query(Client)
                    .join(Client.adresses)
                    .filter(
                        search_active_clients,
                        or_(
                            Adresse.adresse_l1.ilike(f'%{search_term}%'),
                            Adresse.adresse_l2.ilike(f'%{search_term}%'),
                            Adresse.code_postal.ilike(f'%{search_term}%'),
                            Adresse.ville.ilike(f'%{search_term}%'),
                            search_inactive_address
                        )
                    )
                    .distinct()
                    .all()
                )
        
        # Conversion en dictionnaire et retour
        return jsonify([client.to_dict() for client in clients[:20]])  # Limite à 20 résultats
        
    except Exception as e:
        return PrepareTemplates.error_5xx(status_code=500, status_message=str(e),
                                          log=True, specific_log=Constants.log_files('client') + str(e))


# ================================================================
# DONNÉES CLIENTS INDIVIDUELLES
# ================================================================

@clients_bp.route('/new', methods=['GET', 'POST'])
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
        new_client = Client(
            type_client=type_client,
            notes=notes,
            reduces=reduces,
            created_by=session.get('pseudo', 'N/A')
        )
        db_session.add(new_client)
        db_session.flush()  # Pour obtenir l'ID
        
        # Création du client particulier ou professionnel suivant type
        ClientMethods.create_or_modify_client(request, type_client, new_client, db_session)

        # Envoi du client en base de données
        db_session.commit()        
        
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=new_client.id,
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
    message = request.args.get('message', '')
    success_message = request.args.get('success_message', '')
    error_message = request.args.get('error_message', '')
    tab = request.args.get('tab', None)

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
        phones: List[Telephone] = sorted(
            client.tels,
            key=lambda p: (p.is_inactive, p.id)
        )
        mails: List[Mail] = sorted(
            client.mails,
            key=lambda m: (m.is_inactive, m.id)
        )
        addresses: List[Adresse] = sorted(
            client.adresses,
            key=lambda a: (a.is_inactive, a.id)
        )
        orders: List[Commande] = sorted(client.commandes, key=lambda x: x.id, reverse=True)
        bills: List[Facture] = client.factures
        nom_affichage = client.nom_affichage
        return PrepareTemplates.clients(sub_context='detail', client=client, part=part, pro=pro, phones=phones,
                                        mails=mails, addresses=addresses, orders=orders, bills=bills,
                                        nom_affichage=nom_affichage, log=True, tab=tab, message=message,
                                        success_message=success_message, error_message=error_message)
    else:
        return PrepareTemplates.error_4xx(status_code=404, log=True,
                                          status_message=Constants.messages('client', 'not_found'))

@clients_bp.route('/<int:id_client>/modify', methods=['GET'])
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
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                success_message=Constants.messages('client', 'update'),
                                id_client=client.id))
    except Exception as e:
        return PrepareTemplates.clients(sub_context='edit', client=client, log=True,
                                        id_client=client.id if client else id_client,
                                        nom_affichage=nom_affichage if nom_affichage else f"Client {id_client}",
                                        error_message=Constants.messages('error_500', 'default') + f" : {e}")

@clients_bp.route('/<int:id_client>/delete/', methods=['POST'])
@validate_habilitation(CLIENTS)
def delete_client(id_client: int) -> ResponseWerkzeug:
    """
    Suppression d'un client.
    
    Endpoint REST pour supprimer un client existant.
    La suppression est logique (is_active = False).
    
    Form Data:
        - id_client (int): ID du client à supprimer
    
    Returns:
        Redirect: Vers la page de recherche clients avec message de succès ou d'erreur
    """
    db_session = get_db_session()
    client = None

    try:
        # Récupération du client à supprimer
        client = db_session.query(Client).options(
            joinedload(Client.commandes),
            joinedload(Client.factures)
        ).get(id_client)
        if not client:
            return redirect(url_for(Constants.return_pages('clients', 'recherche'),
                        error_message=Constants.messages('client', 'not_found')))

        # Vérification de commandes ou factures de moins de 5 ans
        now = datetime.now()
        five_years_ago = now.replace(year=now.year - 5)
        recent_commande = any(
            c.date_commande and c.date_commande >= five_years_ago
            for c in client.commandes
        )
        recent_facture = any(
            f.date_facture and f.date_facture >= five_years_ago
            for f in client.factures
        )
        if recent_commande or recent_facture:
            return redirect(url_for(Constants.return_pages('clients', 'detail'),
                        id_client=id_client,
                        error_message=Constants.messages('client', 'delete_forbidden')))

        # Suppression logique
        client.is_active = False
        client.modified_by = session.get('pseudo', 'N/A')
        db_session.commit()

        return redirect(url_for(Constants.return_pages('clients', 'recherche'),
                                success_message=Constants.messages('client', 'delete')))
    
    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=id_client, log=True,
                                error_message=Constants.messages('error_500', 'default') + f" : {e}"))

@clients_bp.route('/<int:id_client>/add-phone/', methods=['POST'])
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
        if not client: return redirect(url_for(Constants.return_pages('clients', 'recherche')))

        # Validation du numéro de téléphone
        telephone = request.form.get('telephone', '').strip()
        if not telephone: return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                                  id_client=id_client, tab='phone',
                                                  error_message=Constants.messages('phone', 'missing')))

        # Récupération des autres données (type de téléphone, indicatif, détail, si principal)
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
            is_principal=is_principal,
            created_by=session.get('pseudo', 'N/A')
        )
        
        # Enregistrement en base de données
        db_session.add(new_telephone)
        db_session.commit()

        return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='phone',
                                id_client=id_client, success_message=Constants.messages('phone', 'valid')))

    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                 id_client=id_client, log=True, tab='phone',
                                 error_message=Constants.messages('error_500', 'default') + f" : {e}"))

@clients_bp.route('/<int:id_client>/modify-phone/<int:id_phone>/', methods=['POST'])
@validate_habilitation(CLIENTS)
def mod_phone(id_client: int, id_phone: int) -> ResponseWerkzeug:
    """
    Modification d'un numéro de téléphone existant pour un client.
    
    Endpoint REST pour modifier un numéro de téléphone existant d'un client.
    Supporte différents types : fixe_pro, mobile_pro, fixe_perso, mobile_perso, fax.
    
    Form Data:
        - id_client (int): ID du client
        - id_phone (int): ID du téléphone à modifier
        - telephone (str): Nouveau numéro de téléphone
        - type_telephone (str): Type de téléphone
        - indicatif (str, optional): Indicatif pays (ex: +33)
        - detail (str, optional): Précisions sur l'usage
        - is_principal (bool, optional): Téléphone principal
    
    Returns:
        Redirect: Vers la page de détails du client avec message de succès ou d'erreur
    """
    db_session = get_db_session()

    try:
        # Récupération et validation des données (client, téléphone, type, indicatif, détail, si principal)
        client = db_session.query(Client).get(id_client)
        phone = request.form.get('telephone', '').strip()
        type_phone = request.form.get('type_telephone', 'mobile_pro')
        indic = request.form.get('indicatif', '').strip()
        detail = request.form.get('detail', '').strip()
        is_principal = request.form.get('is_principal', 'false').lower() == 'true'

        # Récupération du téléphone à modifier
        phone_obj = db_session.query(Telephone).filter_by(id=id_phone, id_client=id_client, is_inactive=False).first()

        # Gestion de l'absence de retours (absence client, absence téléphone, absence numéro)
        # L'absence de client est peu probable, mais on la gère quand même
        if not client: return redirect(url_for(Constants.return_pages('clients', 'recherche')))
        # L'absence de téléphone est peu probable aussi (mauvais ID ou téléphone déjà supprimé)
        if not phone_obj: return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                         id_client=id_client, tab='phone',
                                         error_message=Constants.messages('phone', 'not_found')))
        # Le numéro de téléphone est obligatoire : retour avec message d'erreur
        if not phone: return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                                  id_client=id_client, tab='phone',
                                                  error_message=Constants.messages('phone', 'missing')))

        # Si c'est le téléphone principal, désactiver les autres
        if is_principal:
            db_session.query(Telephone).filter(
                Telephone.id_client == client.id,
                Telephone.id != id_phone,
                Telephone.is_principal == True
            ).update({'is_principal': False})
            db_session.commit()

        # Mise à jour du téléphone existant
        phone_obj.telephone = phone
        phone_obj.type_telephone = type_phone
        phone_obj.indicatif = indic if indic else '+33'
        phone_obj.detail = detail if detail else None
        phone_obj.is_principal = is_principal
        phone_obj.modified_by = session.get('pseudo', 'N/A')
        db_session.commit()

        # Redirection vers la page de détails du client sur l'onglet téléphone avec message de succès
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                 id_client=id_client, log=True, tab='phone',
                                 success_message=Constants.messages('phone', 'updated')))
    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                 id_client=id_client, log=True, tab='phone',
                                 error_message=Constants.messages('error_500', 'default') + f" : {e}"))

@clients_bp.route('/<int:id_client>/delete-phone/<int:id_phone>/', methods=['POST'])
@validate_habilitation(CLIENTS)
def del_phone(id_client: int, id_phone: int) -> ResponseWerkzeug:

    """
    Suppression d'un numéro de téléphone existant pour un client.
    Endpoint REST pour supprimer un numéro de téléphone d'un client.
    La suppression est logique (is_inactive = True).
    Form Data:
        - id_client (int): ID du client
        - id_phone (int): ID du téléphone à supprimer
    Returns:
        Redirect: Vers la page de détails du client avec message de succès ou d'erreur
    """
    db_session = get_db_session()
    client = None

    try:
        # Récupération et validation des données
        client = db_session.query(Client).get(id_client)
        phone_obj = db_session.query(Telephone).filter_by(id=id_phone, id_client=id_client).first()
        if not client: return redirect(url_for(Constants.return_pages('clients', 'recherche')))
        if not phone_obj: return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                         id_client=id_client, tab='phone',
                                         error_message=Constants.messages('phone', 'not_found')))

        # Suppression logique
        phone_obj.is_inactive = True
        phone_obj.modified_by = session.get('pseudo', 'N/A')
        phone_obj.is_principal = False  # Ne peut plus être principal
        phone_obj.modified_at = datetime.now()
        db_session.commit()
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                 id_client=id_client, log=True, tab='phone',
                                 success_message=Constants.messages('phone', 'deleted')))
    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                 id_client=id_client, log=True, tab='phone',
                                 error_message=Constants.messages('error_500', 'default') + f" : {e}"))

@clients_bp.route('/<int:id_client>/add-email/', methods=['POST'])
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
        if not client: return redirect(url_for(Constants.return_pages('clients', 'recherche')))

        # Validation de l'email
        email = request.form.get('mail', '').strip()
        if not email: return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                                  id_client=id_client, tab='mail',
                                                  error_message=Constants.messages('email', 'missing')))

        # Validation basique du format email
        if '@' not in email or '.' not in email.split('@')[-1]:
            return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                                  id_client=id_client, tab='mail',
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

        return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='mail',
                                id_client=id_client, success_message="Email ajouté avec succès"))

    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=id_client, log=True, tab='mail',
                                error_message=Constants.messages('error_500', 'default') + f" : {e}"))
    
@clients_bp.route('/<int:id_client>/modify-email/<int:id_mail>/', methods=['POST'])
@validate_habilitation(CLIENTS)
def mod_email(id_client: int, id_mail: int) -> ResponseWerkzeug:
    """
    Modification d'un email existant pour un client.
    
    Endpoint REST pour modifier une adresse email existante d'un client.
    Supporte différents types : professionnel, personnel, facturation, marketing.
    
    Form Data:
        - id_client (int): ID du client
        - id_mail (int): ID de l'email à modifier
        - mail (str): Nouvelle adresse email
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
        mail_obj = db_session.query(Mail).filter_by(id=id_mail, id_client=id_client).first()
        email = request.form.get('mail', '').strip()
        if not client: return redirect(url_for(Constants.return_pages('clients', 'recherche')))
        if not mail_obj: return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                         id_client=id_client, tab='mail',
                                         error_message=Constants.messages('email', 'not_found')))
        if not email: return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                                  id_client=id_client, tab='mail',
                                                  error_message=Constants.messages('email', 'missing')))

        # Validation basique du format email
        if '@' not in email or '.' not in email.split('@')[-1]:
            return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                                  id_client=id_client, tab='mail',
                                                  error_message=Constants.messages('email', 'invalid')))

        # Récupération des autres données
        type_mail = request.form.get('type_mail', 'professionnel')
        detail = request.form.get('detail', '').strip()
        is_principal = request.form.get('is_principal', 'false').lower() == 'true'

        # Si c'est l'email principal, désactiver les autres
        if is_principal: db_session.query(Mail).filter_by(
            id_client=client.id, is_principal=True
            ).update({'is_principal': False})

        # Mise à jour de l'email
        mail_obj.mail = email
        mail_obj.type_mail = type_mail
        mail_obj.detail = detail if detail else None
        mail_obj.is_principal = is_principal

        db_session.commit()
        return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='mail',
                                id_client=id_client, success_message=Constants.messages('email', 'valid')))

    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=id_client, log=True, tab='mail',
                                error_message=Constants.messages('error_500', 'default') + f" : {e}"))

@clients_bp.route('/<int:id_client>/delete-email/<int:id_mail>/', methods=['POST'])
@validate_habilitation(CLIENTS)
def del_email(id_client: int, id_mail: int) -> ResponseWerkzeug:
    """
    Suppression d'un email existant pour un client.
    
    Endpoint REST pour supprimer une adresse email d'un client.
    La suppression est logique (is_inactive = True).
    
    Form Data:
        - id_client (int): ID du client
        - id_mail (int): ID de l'email à supprimer
    
    Returns:
        Redirect: Vers la page de détails du client avec message de succès ou d'erreur
    """
    db_session = get_db_session()
    client = None

    try:
        # Récupération et validation des données
        client = db_session.query(Client).get(id_client)
        mail_obj = db_session.query(Mail).filter_by(id=id_mail, id_client=id_client).first()
        if not client: return redirect(url_for(Constants.return_pages('clients', 'recherche')))
        if not mail_obj: return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                         id_client=id_client, tab='mail',
                                         error_message=Constants.messages('email', 'not_found')))

        # Suppression logique
        mail_obj.is_inactive = True
        mail_obj.modified_by = session.get('pseudo', 'N/A')
        mail_obj.is_principal = False  # Ne peut plus être principal
        mail_obj.modified_at = datetime.now()
        db_session.commit()

        return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='mail',
                                id_client=id_client, success_message=Constants.messages('email', 'delete')))

    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=id_client, log=True, tab='mail',
                                error_message=Constants.messages('error_500', 'default') + f" : {e}"))

@clients_bp.route('/<int:id_client>/add-address/', methods=['POST'])
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
        - detail (str, optional): Précisions sur l'adresse
    
    Returns:
        Redirect: Vers la page de détails du client avec message de succès ou d'erreur
    """
    db_session = get_db_session()
    client = None

    try:
        # Récupération et validation des données
        client = db_session.query(Client).get(id_client)
        if not client:
            return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='add',
                                    id_client=id_client, error_message=Constants.messages('client', 'not_found')))

        # Validation des données d'adresse
        adresse_l1 = request.form.get('adresse_l1', '').strip()
        code_postal = request.form.get('code_postal', '').strip()
        ville = request.form.get('ville', '').strip()
        adresse_l2 = request.form.get('adresse_l2', '').strip()
        is_principal = request.form.get('is_principal', 'false').lower() == 'true'
        detail = request.form.get('detail', '').strip()
        if not adresse_l1 or not code_postal or not ville: return redirect(
            url_for(Constants.return_pages('clients', 'detail'), tab='add',
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
            detail=detail if detail else None,
            is_principal=is_principal,
            created_by=session.get('pseudo', 'N/A')
        )
        
        # Enregistrement en base de données
        db_session.add(new_adresse)
        db_session.commit()

        return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='add',
                                id_client=id_client, success_message=Constants.messages('address', 'valid')))

    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'), id_client=id_client, tab='add',
                                error_message=Constants.messages('error_500', 'default') + f" : {e}", log=True))

@clients_bp.route('/<int:id_client>/modify-address/<int:id_address>/', methods=['POST'])
@validate_habilitation(CLIENTS)
def mod_address(id_client: int, id_address: int) -> ResponseWerkzeug:
    """
    Modification d'une adresse existante pour un client.
    
    Endpoint REST pour modifier une adresse existante d'un client.
    Gère les adresses complètes avec code postal et ville.
    
    Form Data:
        - id_client (int): ID du client
        - id_address (int): ID de l'adresse à modifier
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
        address_obj = db_session.query(Adresse).filter_by(id=id_address, id_client=id_client).first()
        if not client:
            return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='add',
                                    id_client=id_client, error_message=Constants.messages('client', 'not_found')))
        if not address_obj:
            return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='add',
                                    id_client=id_client, error_message=Constants.messages('address', 'not_found')))

        # Validation des données d'adresse
        adresse_l1 = request.form.get('adresse_l1', '').strip()
        adresse_l2 = request.form.get('adresse_l2', '').strip()
        code_postal = request.form.get('code_postal', '').strip()
        ville = request.form.get('ville', '').strip()
        is_principal = request.form.get('is_principal', 'false').lower() == 'true'
        detail = request.form.get('detail', '').strip()
        if not adresse_l1 or not code_postal or not ville: return redirect(
            url_for(Constants.return_pages('clients', 'detail'), tab='add',
                    id_client=id_client, error_message=Constants.messages('address', 'missing')
                    )
            )

        # Si c'est l'adresse principale, désactiver les autres
        if is_principal: db_session.query(Adresse).filter_by(
            id_client=client.id, is_principal=True
            ).update({'is_principal': False})
        # Mise à jour de l'adresse
        address_obj.adresse_l1 = adresse_l1
        address_obj.adresse_l2 = adresse_l2 if adresse_l2 else None
        address_obj.code_postal = code_postal
        address_obj.ville = ville
        address_obj.is_principal = is_principal
        address_obj.detail = detail if detail else None
        address_obj.modified_by = session.get('pseudo', 'N/A')
        db_session.commit()
        return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='add',
                                id_client=id_client, success_message=Constants.messages('address', 'valid')))
    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=id_client, log=True, tab='add',
                                error_message=Constants.messages('error_500', 'default') + f" : {e}"))

@clients_bp.route('/<int:id_client>/delete-address/<int:id_address>/', methods=['POST'])
@validate_habilitation(CLIENTS)
def del_address(id_client: int, id_address: int) -> ResponseWerkzeug:
    """
    Suppression d'une adresse existante pour un client.
    
    Endpoint REST pour supprimer une adresse d'un client.
    La suppression est logique (is_inactive = True).
    
    Form Data:
        - id_client (int): ID du client
        - id_address (int): ID de l'adresse à supprimer
    
    Returns:
        Redirect: Vers la page de détails du client avec message de succès ou d'erreur
    """
    db_session = get_db_session()
    client = None

    try:
        # Récupération et validation des données
        client = db_session.query(Client).get(id_client)
        address_obj = db_session.query(Adresse).filter_by(id=id_address, id_client=id_client).first()
        if not client: return redirect(url_for(Constants.return_pages('clients', 'recherche')))
        if not address_obj: return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                         id_client=id_client, tab='add',
                                         error_message=Constants.messages('address', 'not_found')))

        # Suppression logique
        address_obj.is_inactive = True
        address_obj.modified_by = session.get('pseudo', 'N/A')
        db_session.commit()

        return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='add',
                                id_client=id_client, success_message=Constants.messages('address', 'delete')))

    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=id_client, log=True, tab='add',
                                error_message=Constants.messages('error_500', 'default') + f" : {e}"))
    
@clients_bp.route('/<int:id_client>/activate-address-<int:id_address>/', methods=['POST'])
@validate_habilitation([CLIENTS, ADMINISTRATEUR], _and=True)
@validate_habilitation([CLIENTS, GESTIONNAIRE], _and=True)
def activate_address(id_client: int, id_address: int) -> ResponseWerkzeug:
    """
    Réactivation d'une adresse inactive pour un client.
    
    Endpoint REST pour réactiver une adresse précédemment supprimée (logiquement) d'un client.
    
    Form Data:
        - id_client (int): ID du client
        - id_address (int): ID de l'adresse à réactiver
    
    Returns:
        Redirect: Vers la page de détails du client avec message de succès ou d'erreur
    """
    db_session = get_db_session()

    try:
        # Récupération et validation des données
        client = (db_session
            .query(Client).join(Client.adresses)
            .options(
                contains_eager(Client.adresses)
            ).filter(
                Client.id == id_client, Adresse.id == id_address
            ).first()
        )
        address_obj = client.adresses[0] if client and client.adresses else None
        if not address_obj: return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                         id_client=id_client, tab='add',
                                         error_message=Constants.messages('address', 'not_found')))

        # Réactivation logique
        address_obj.is_inactive = False
        address_obj.modified_by = session.get('pseudo', 'N/A')
        address_obj.modified_at = datetime.now()
        db_session.commit()

        return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='add',
                                id_client=id_client, success_message=Constants.messages('address', 'reactivated')))

    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=id_client, log=True, tab='add',
                                error_message=Constants.messages('error_500', 'default') + f" : {e}"))

@clients_bp.route('/<int:id_client>/activate-phone-<int:id_phone>/', methods=['POST'])
@validate_habilitation([CLIENTS, ADMINISTRATEUR], _and=True)
@validate_habilitation([CLIENTS, GESTIONNAIRE], _and=True)
def activate_phone(id_client: int, id_phone: int) -> ResponseWerkzeug:
    """
    Réactivation d'un numéro de téléphone inactif pour un client.
    
    Endpoint REST pour réactiver un numéro de téléphone précédemment supprimé (logiquement) d'un client.
    
    Form Data:
        - id_client (int): ID du client
        - id_phone (int): ID du téléphone à réactiver
    
    Returns:
        Redirect: Vers la page de détails du client avec message de succès ou d'erreur
    """
    db_session = get_db_session()

    try:
        # Récupération et validation des données
        client = (db_session
            .query(Client).join(Client.tels)
            .options(
                contains_eager(Client.tels)
            ).filter(
                Client.id == id_client, Telephone.id == id_phone
            ).first()
        )
        phone_obj = client.tels[0] if client and client.tels else None
        if not phone_obj: return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                         id_client=id_client, tab='phone',
                                         error_message=Constants.messages('phone', 'not_found')))

        # Réactivation logique
        phone_obj.is_inactive = False
        phone_obj.modified_by = session.get('pseudo', 'N/A')
        phone_obj.modified_at = datetime.now()
        db_session.commit()

        return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='phone',
                                id_client=id_client, success_message=Constants.messages('phone', 'reactivated')))

    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=id_client, log=True, tab='phone',
                                error_message=Constants.messages('error_500', 'default') + f" : {e}"))
    
@clients_bp.route('/<int:id_client>/activate-email-<int:id_mail>/', methods=['POST'])
@validate_habilitation([CLIENTS, ADMINISTRATEUR], _and=True)
@validate_habilitation([CLIENTS, GESTIONNAIRE], _and=True)
def activate_email(id_client: int, id_mail: int) -> ResponseWerkzeug:
    """
    Réactivation d'une adresse email inactive pour un client.
    
    Endpoint REST pour réactiver une adresse email précédemment supprimée (logiquement) d'un client.
    
    Form Data:
        - id_client (int): ID du client
        - id_mail (int): ID de l'email à réactiver
    
    Returns:
        Redirect: Vers la page de détails du client avec message de succès ou d'erreur
    """
    db_session = get_db_session()

    try:
        # Récupération et validation des données
        client = (db_session
            .query(Client).join(Client.mails)
            .options(
                contains_eager(Client.mails)
            ).filter(
                Client.id == id_client, Mail.id == id_mail
            ).first()
        )
        mail_obj = client.mails[0] if client and client.mails else None
        if not mail_obj: return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                         id_client=id_client, tab='mail',
                                         error_message=Constants.messages('email', 'not_found')))

        # Réactivation logique
        mail_obj.is_inactive = False
        mail_obj.modified_by = session.get('pseudo', 'N/A')
        mail_obj.modified_at = datetime.now()
        db_session.commit()

        return redirect(url_for(Constants.return_pages('clients', 'detail'), tab='mail',
                                id_client=id_client, success_message=Constants.messages('email', 'reactivated')))

    except Exception as e:
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=id_client, log=True, tab='mail',
                                error_message=Constants.messages('error_500', 'default') + f" : {e}"))