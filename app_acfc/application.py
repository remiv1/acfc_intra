'''
ACFC - Application de Gestion d'Entreprise
===========================================

Module principal de l'application ACFC (Accounting, Customer Relationship Management, 
Billing & Stock Management). Cette application web d'entreprise fournit une solution 
intégrée pour la gestion de :
- Comptabilité et facturation
- Gestion de la relation client (CRM)
- Gestion des stocks
- Catalogue produits
- Administration des utilisateurs

Architecture : Flask + SQLAlchemy + MariaDB + MongoDB (logs)
Serveur WSGI : Waitress (production-ready)
Authentification : Sessions sécurisées avec hachage Argon2

Auteur : ACFC Development Team
Version : 1.0
'''

from flask import Flask, Response, request, Blueprint, session, url_for, redirect, jsonify, g
from flask_session import Session
from waitress import serve
from typing import Any, Dict, Tuple, List, Optional
from werkzeug.exceptions import HTTPException
from datetime import datetime, date
from sqlalchemy import text, and_, or_
from sqlalchemy.orm import Session as SessionBdDType, joinedload
from sqlalchemy.sql.functions import func
from logs.logger import acfc_log, ERROR
from app_acfc.services import SecureSessionService, AuthenticationService
from app_acfc.modeles import (
    MyAccount, PrepareTemplates, Constants, User, Commande, Client, init_database, get_db_session,
    GeoMethods
    )
from app_acfc.contextes_bp.clients import clients_bp         # Module CRM - Gestion clients
from app_acfc.contextes_bp.catalogue import catalogue_bp     # Module Catalogue produits
from app_acfc.contextes_bp.commercial import commercial_bp   # Module Commercial - Devis, commandes
from app_acfc.contextes_bp.comptabilite import comptabilite_bp # Module Comptabilité - Facturation
from app_acfc.contextes_bp.stocks import stocks_bp          # Module Stocks - Inventaire
from app_acfc.contextes_bp.admin import admin_bp            # Module Administration - Utilisateurs
from app_acfc.contextes_bp.commandes import commandes_bp    # Module Commandes - Gestion des commandes

# Création de l'instance Flask principale avec configuration des dossiers statiques et templates
acfc = Flask(__name__,
             static_folder='statics',     # Ressources CSS, JS, images par module
             template_folder='templates') # Templates HTML Jinja2

# ====================================================================
# CONFIGURATION DES SERVICES YC DE LA SÉCURITÉ
# ====================================================================

# Initialisation du service de sessions sécurisées (chiffrement, cookies HTTPOnly)
SecureSessionService(acfc)

# Activation du gestionnaire de sessions Flask-Session (stockage filesystem)
Session(acfc)

# Regroupement des blueprints pour faciliter l'enregistrement en masse
acfc_blueprints: Tuple[Blueprint, ...] = (clients_bp, catalogue_bp, commercial_bp, comptabilite_bp, stocks_bp, admin_bp, commandes_bp)

# Messages d'erreur standardisés pour l'authentification
INVALID: str = 'Identifiants invalides.'
WRONG_ROAD: str = 'Méthode non autorisée ou droits insuffisants.'

# Création automatique des tables si elles n'existent pas (avec retry)
try:
    init_database()
except Exception as e:
    print(f"❌ Erreur critique lors de l'initialisation de la base : {e}")
    exit(1)

# ====================================================================
# MIDDLEWARES - GESTION DES REQUÊTES GLOBALES
# ====================================================================

@acfc.before_request
def before_request() -> Any:
    '''
    Middleware exécuté avant chaque requête.
    
    Vérifie l'état de la session utilisateur et redirige vers la page de connexion
    si aucune session active n'est détectée.
    
    Returns:
        str | None: Template de connexion si pas de session, None sinon
    '''
    # Si l'utilisateur est déjà connecté
    if 'user_id' in session:
        return None
    
    # Autoriser la page de login
    if request.endpoint == 'login':
        return None
    
    # Autoriser les statiques (app + blueprints)
    static_url = acfc.static_url_path or '/static'
    if request.path.startswith(static_url) or (request.endpoint and request.endpoint.endswith('.static')):
        return None

    # Si l'utilisateur n'est pas connecté, rediriger vers la page de login
    return redirect(url_for('login'))


@acfc.after_request
def after_request(response: Response) -> Response:
    """
    Middleware exécuté après chaque requête.
    
    Permet d'ajouter des headers personnalisés, du logging, ou de modifier la réponse
    avant qu'elle soit envoyée au client.
    
    Args:
        response (Response): Objet de réponse Flask
        
    Returns:
        Response: Réponse modifiée si nécessaire
    """
    return response


@acfc.teardown_appcontext
def teardown_appcontext(exception: Optional[BaseException]=None) -> None:
    """
    Middleware exécuté à la fin de chaque contexte d'application.
    
    Permet de libérer les ressources, de fermer les connexions, ou de gérer les erreurs.
    
    Args:
        exception (Exception | None): Exception levée pendant le traitement de la requête, si elle existe
    """
    db_session = g.pop('db_session', None)
    if db_session is not None:
        if exception is not None:
            db_session.rollback()
        db_session.close()
    
    if exception:
        acfc_log.log(level=ERROR, message=str(exception), specific_logger=Constants.log_files('warning'))

# ====================================================================
# FILTRES JINJA2 PERSONNALISÉS
# ====================================================================

@acfc.template_filter('strftime')
def format_datetime(value: datetime | date | None, fmt: str='%d/%m/%Y'):
    """
    Filtre Jinja2 pour formater les dates et datetime.
    
    Args:
        value: Date ou datetime à formater
        fmt: Format de sortie (défaut: '%d/%m/%Y')
    
    Returns:
        str: Date formatée ou chaîne vide si None
    """
    if isinstance(value, (datetime, date)):
        return value.strftime(fmt)
    return value


@acfc.template_filter('date_input')
def format_date_input(value: datetime | date | None):
    """Filtre spécifique pour les champs input[type=date] qui attendent le format ISO (YYYY-MM-DD)"""
    if isinstance(value, (datetime, date)):
        return value.strftime('%Y-%m-%d')
    return value

@acfc.template_filter('jinja_page_title')
def jinja_page_title(title_and_subtitle: Tuple[str, str]) -> str:
    """Filtre pour générer le titre de la page dans le format Jinja2."""
    return Constants.return_pages(title_and_subtitle[0], title_and_subtitle[1])

# ====================================================================
# FONCTIONS DE RECHERCHES - HORS ROUTES
# ====================================================================

def get_current_orders(id_client: int = 0) -> List[Commande]:
    """
    Récupère les commandes en cours pour un client donné.

    Args:
        id_client (int): ID du client, 0 pour tous les clients

    Returns:
        List[Commande]: Liste des commandes en cours
    """
    # Ouverture de la session
    db_session: SessionBdDType = get_db_session()

    # Récupération des commandes en cours sans notion de client
    if id_client == 0:
        commandes: List[Commande] = (
            db_session.query(Commande)
            .options(
                joinedload(Commande.client).joinedload(Client.part),  # Eager loading du client particulier
                joinedload(Commande.client).joinedload(Client.pro)    # Eager loading du client professionnel
            )
            .filter(or_(
                Commande.is_facture.is_(False),
                Commande.is_expedie.is_(False)
            ))
            .all()
        )

    # Récupération des commandes en cours pour un client spécifique
    else:
        commandes: List[Commande] = (
            db_session.query(Commande)
            .options(
                joinedload(Commande.client).joinedload(Client.part),  # Eager loading du client particulier
                joinedload(Commande.client).joinedload(Client.pro)    # Eager loading du client professionnel
            )
            .filter(and_(
                Commande.id_client == id_client,
                or_(
                    Commande.is_facture.is_(False),
                    Commande.is_expedie.is_(False)
                )
            ))
            .all()
        )

    return commandes

def get_commercial_indicators() -> Dict[str, Any] | None:
    """
    Récupère les indicateurs commerciaux:
        - Chiffre d'affaire mensuel
        - Chiffre d'affaire annuel
        - Panier moyen
        - Clients actifs
        - Commandes annuelles

    Returns:
        Dict[str, Any]: Dictionnaire des indicateurs commerciaux
    """
    # Ouverture de la session
    db_session: SessionBdDType = get_db_session()

    # Récupération des dates de référence
    today = date.today()
    first_day_of_month = today.replace(day=1)
    first_day_of_year = today.replace(month=1, day=1)

    # Récupération des indicateurs commerciaux et gestion des exceptions
    try:
        indicators: Dict[str, List[int | float | str]] | None = {
            # Chiffre d'affaire total facturé pour le mois en cours
            "ca_current_month": [
                round(db_session.query(func.sum(Commande.montant))
                .filter(
                    Commande.is_facture.is_(True),
                    Commande.date_commande >= first_day_of_month
                ).scalar() or 0.0, 2),
                'CA Mensuel'
            ],

            # Chiffre d'affaire total facturé pour l'année en cours
            "ca_current_year": [
                round(db_session.query(func.sum(Commande.montant))
                .filter(
                    Commande.is_facture.is_(True),
                    Commande.date_commande >= first_day_of_year
                ).scalar() or 0.0, 2),
                'CA Annuel'
            ],

            # Panier moyen annuel
            "average_basket": [
                round(db_session.query(func.avg(Commande.montant))
                .filter(
                    Commande.is_facture.is_(True),
                    Commande.date_commande >= first_day_of_year
                ).scalar() or 0.0, 2),
                'Panier Moyen'
            ],

            # Clients actifs
            "active_clients": [
                db_session.query(func.count(func.distinct(Commande.id_client)))
                .filter(
                    Commande.is_facture.is_(True),
                    Commande.date_commande >= first_day_of_year
                ).scalar() or 0,
                'Clients Actifs'
            ],

            # Nombre de commandes par an
            "orders_per_year": [
                db_session.query(func.count(Commande.id))
                .filter(
                    Commande.is_facture.is_(True),
                    Commande.date_commande >= first_day_of_year
                ).scalar() or 0,
                'Commandes Annuelles'
            ]
        }
    except Exception:
        indicators = None
    return indicators

# ====================================================================
# ROUTES PRINCIPALES DE L'APPLICATION
# ====================================================================

@acfc.route('/')
def index() -> Any:
    """
    Page d'accueil de l'application.
    
    Redirige automatiquement vers le module Clients après authentification.
    Point d'entrée principal de l'interface utilisateur.

    Possibilité par la suite de créer des dashboards personnalisés en fonction
    des habilitations utilisateur.
    
    Returns:
        str: Template HTML du module Clients
    """
    return redirect(url_for('dashboard'))

@acfc.route('/login', methods=['GET', 'POST'])
def login() -> Any:
    """
    Gestion de l'authentification utilisateur.
    
    Traite l'affichage du formulaire de connexion (GET) et la validation 
    des identifiants (POST). Utilise le hachage Argon2 pour vérifier les mots de passe
    et gère les tentatives d'authentification échouées.
    
    Returns:
        Any: Template de connexion, redirection vers l'accueil, ou page d'erreur
    """
    # === TRAITEMENT GET : Affichage du formulaire de connexion ===
    if request.method == 'GET': return PrepareTemplates.login()
    elif request.method != 'POST':
        message = Constants.messages('error_400', 'wrong_road') \
                  + f'\nMéthode {request.method} non autorisée.' \
                  + f'\nUtilisateur : {session.get("user_id", "inconnu")}'
        return PrepareTemplates.error_4xx(status_code=400, status_message=message, log=True)
    # === TRAITEMENT POST : Validation des identifiants ===
    else:
        user_to_authenticate = AuthenticationService(request)
        result_auth = user_to_authenticate.authenticate()
        # Schéma de vérification des identifiants
        try:
            # Si échec de l'authentification, retour au formulaire avec message d'erreur
            if not result_auth: return PrepareTemplates.login(message=INVALID)
            # Si succès, mais mot de passe à changer, redirection vers la page de changement
            
            return \
                PrepareTemplates.login(subcontext='change_password',
                                       message=Constants.messages('user', 'to_update'),
                                       username=user_to_authenticate.user_pseudo,
                                       log=True)  \
                if user_to_authenticate.is_chg_mdp \
                else redirect(url_for('dashboard'))
        except Exception as e:
            message = Constants.messages('error_500', 'default') + 'context : auth' \
                      + f' Utilisateur : {user_to_authenticate.user_pseudo if user_to_authenticate else "inconnu"}' + \
                        f' Détail : {str(e)}'
            raise 

@acfc.route('/logout')
def logout() -> Any:
    """
    Déconnexion de l'utilisateur.
    """
    session.clear()
    return redirect(url_for('login'))

@acfc.route('/health')
def health() -> Any:
    """
    Endpoint de santé pour les vérifications CI/CD et monitoring.
    
    Retourne l'état de l'application et de ses services dépendants.
    Utilisé par Docker Compose CI pour valider le bon fonctionnement.
    
    Returns:
        JSON: Statut de l'application et de ses dépendances
    """
    try:
        # Vérification de la base de données
        db_status = "ok"
        try:
            db_session = get_db_session()
            db_session.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        health_data: Dict[str, Any] = {
            "status": "healthy" if db_status == "ok" else "degraded",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db_status,
                "application": "ok"
            },
            "version": "1.0"
        }
        
        return jsonify(health_data), 200 if db_status == "ok" else 503
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500
    
@acfc.route('/dashboard')
def dashboard() -> Any:
    """
    Affichage du tableau de bord utilisateur.
    Point d'entrée principal après authentification. Affiche les commandes en cours.
        - Commandes en cours
        - Indicateurs commerciaux
    """
    current_orders = get_current_orders()
    commercial_indicators = get_commercial_indicators()
    return PrepareTemplates.default(objects=[current_orders, commercial_indicators])

@acfc.route('/user/<pseudo>', methods=['GET', 'POST'])
def my_account(pseudo: str) -> Any:
    """
    Affichage de la page "Mon Compte" pour l'utilisateur connecté.
    
    Returns:
        Any: Template de la page "Mon Compte"
    """
    db_session = get_db_session()

    # Vérification des autorisations
    MyAccount.check_user_permission(pseudo)

    # Recherche de l'utilisateur ou gestion de l'erreur 
    user = MyAccount.get_user_or_error(db_session, pseudo)

    #=== Gestion de la requête GET ===
    if request.method == 'GET':
        PrepareTemplates.users(objects=[user])
    
    #=== Gestion de la requête POST ===
    elif request.method == 'POST':
        try:
            # Récupération des données du formulaire
            _form_return = MyAccount.get_request_form(request=request, user=user)

            # Validation de l'email (format basique)
            MyAccount.valid_mail(mail=_form_return[2], user=user, db_session=db_session)

            # Mise à jour des données utilisateur et de la session
            user = MyAccount.update_user_settings(user=user, data_list=_form_return)

            # Sauvegarde en base de données
            db_session.commit()

            # Redirection vers la page de consultation avec message de succès
            message = "Vos informations ont été mises à jour avec succès."
            return PrepareTemplates.users(objects=[user], success_message=message)
        except Exception as e:
            # Si user n'a pas pu être récupéré, on crée un objet vide pour le template
            if ('user' not in locals()) or (not user):
                user = User()
                user.pseudo = pseudo  # Au moins le pseudo pour le template
            return PrepareTemplates.error_5xx(status_code=500, status_message=str(e),
                                              log=True, specific_log=Constants.log_files('user'))

    #=== Gestion de toutes les autres méthodes ===
    else: return PrepareTemplates.error_4xx(status_code=405,
                                            status_message=Constants.messages('error 400', 'wrong_road'),
                                            log=True)

@acfc.route('/user/<pseudo>/parameters', methods=['GET', 'POST'])
def user_parameters(pseudo: str) -> Any:
    """
    Affichage de la page "Paramètres" pour l'utilisateur connecté. (GET)
    Enregistrement des paramètres de l'utilisateur connecté. (POST)

    Returns:
        Any: Template de la page "Paramètres"
    """
    # === Gestion de la requête GET ===
    if request.method == 'GET':
        db_session = get_db_session()
        user = db_session.query(User).filter_by(pseudo=pseudo).first()
        if not user: return PrepareTemplates.error_4xx(status_code=404, status_message="Utilisateur introuvable", log=True)
        return PrepareTemplates.users(subcontext='parameters', objects=[user])
    elif request.method == 'POST':
        return redirect(url_for('my_account', pseudo=pseudo))
    else:
        return PrepareTemplates.error_4xx(status_code=405, status_message="Méthode non autorisée", log=True)

@acfc.route('/chg_pwd', methods=['POST'])
def chg_pwd() -> Any:
    """
    Changement de mot de passe utilisateur.
    """
    def _get_key_message(param: Dict[str, bool]) -> str:
        for key, value in param.items():
            if value is False:
                return key
        return ''

    # === Gestion de la méthode POST ===
    if request.method == 'POST':
        # Initialisation du service d'authentification
        user_to_chg_pwd = AuthenticationService(request)

        # Validation des données du formulaire
        chg_pwd_is_ok = user_to_chg_pwd.chg_pwd()

        # Si échec, retour au formulaire avec message d'erreur
        if not chg_pwd_is_ok:
            # Récupération de la clé du message d'erreur
            key_message = _get_key_message(user_to_chg_pwd.pwd_param)

            # Le message d'erreur est retourné dans le template
            return PrepareTemplates.login(subcontext='change_password',
                                          message=user_to_chg_pwd.pwd_param_messages[key_message],
                                          username=user_to_chg_pwd.user_pseudo)
        else:
            return redirect(url_for('login'))
    # === Gestion de toutes les autres méthodes ===
    return PrepareTemplates.error_4xx(status_code=405, log=True,
                                      status_message=Constants.messages('error_400', 'wrong_road'))

# ====================================================================
# GESTIONNAIRES D'ERREURS HTTP
# ====================================================================

@acfc.errorhandler(400)
@acfc.errorhandler(401)
@acfc.errorhandler(403)
@acfc.errorhandler(404)
def handle_4xx_errors(error: HTTPException) -> str:
    """
    Gestionnaire global des erreurs client (4xx).
    
    Traite les erreurs de type :
    - 400 Bad Request : Requête malformée
    - 401 Unauthorized : Authentification requise  
    - 403 Forbidden : Accès interdit
    - 404 Not Found : Ressource non trouvée
    
    Args:
        error (HTTPException): Exception HTTP capturée
        
    Returns:
        str: Template d'erreur personnalisé avec code et message
    """
    return PrepareTemplates.error_4xx(status_code=error.code or 400, log=True,
                                      status_message=error.description or Constants.messages('error_400', 'default'))

@acfc.errorhandler(500)
@acfc.errorhandler(502)
@acfc.errorhandler(503)
@acfc.errorhandler(504)
def handle_5xx_errors(error: HTTPException) -> str:
    """
    Gestionnaire global des erreurs serveur (5xx).
    
    Traite les erreurs de type :
    - 500 Internal Server Error : Erreur interne du serveur
    - 502 Bad Gateway : Erreur de passerelle
    - 503 Service Unavailable : Service indisponible
    - 504 Gateway Timeout : Timeout de passerelle
    
    Args:
        error (HTTPException): Exception HTTP capturée
        
    Returns:
        str: Template d'erreur personnalisé avec code et message
    """
    return PrepareTemplates.error_5xx(status_code=error.code or 500, log=True, specific_log=Constants.log_files('500'),
                                      status_message=error.description or Constants.messages('error_500', 'default'))

# ====================================================================
# Routes utilitaires diverses
# ====================================================================

@acfc.route('/api/indic-tel/<ilike_pays>', methods=['GET'])
def get_indic_tel(ilike_pays: str='') -> Any:
    """
    API REST pour récupérer les indicatifs téléphoniques par pays.
    
    Args:
        ilike_pays (str): Nom du pays (partiel, insensible à la casse)
        
    Returns:
        JSON: Liste des indicatifs téléphoniques
    """
    if request.method != 'GET':
        return PrepareTemplates.error_4xx(status_code=405,
                                          status_message=Constants.messages('error_400', 'wrong_road'),
                                          log=True)
    try:
        indicatifs = GeoMethods.get_indicatifs_tel(ilike_pays)
        indicatifs_list: List[Dict[str, str]] = [
            {
                'label': f'{ind.pays} ({ind.indicatif})',
                'value': ind.indicatif
            } for ind in indicatifs
        ]
        return jsonify(indicatifs_list), 200
    except Exception as e:
        return PrepareTemplates.error_5xx(status_code=500,
                                          status_message=f"Erreur lors de la récupération des indicatifs : {str(e)}",
                                          log=True, specific_log=Constants.log_files('500'))

# ====================================================================
# ENREGISTREMENT DES MODULES MÉTIERS
# ====================================================================
# Enregistrement automatique de tous les blueprints définis
for bp in acfc_blueprints:
    acfc.register_blueprint(bp)

# ====================================================================
# POINT D'ENTRÉE DE L'APPLICATION
# ====================================================================

def start_server():
    """
    Démarrage de l'application en mode production avec Waitress.
    
    Waitress est un serveur WSGI production-ready qui remplace le serveur 
    de développement Flask. Configuration :
    - Host: configurable via variable d'environnement (défaut: localhost)
    - Port: 5000 (port standard de l'application)
    
    Note: En production, l'application est généralement déployée derrière
    un reverse proxy (Nginx) pour la gestion SSL et la distribution de charge.
    """
    import os
    
    # Configuration sécurisée de l'host
    # En développement: localhost uniquement (plus sécurisé)
    # En production Docker: 0.0.0.0 pour permettre l'accès depuis le conteneur
    host = os.environ.get('FLASK_HOST', 'localhost')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    serve(acfc, host=host, port=port)


if __name__ == '__main__': start_server()
