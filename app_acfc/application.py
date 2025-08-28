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

from flask import Flask, Response, render_template, request, Request, Blueprint, session, url_for, redirect, jsonify
from flask_session import Session
from waitress import serve
from typing import Any, Dict, Tuple, List
from werkzeug.exceptions import HTTPException, Forbidden, Unauthorized
from services import PasswordService, SecureSessionService
from modeles import SessionBdD, User, Commande, Client, init_database
from datetime import datetime, date
from sqlalchemy import text, and_, or_
from sqlalchemy.orm import Session as SessionBdDType, joinedload
from sqlalchemy.sql.functions import func
from logs.logger import acfc_log, INFO, WARNING, ERROR
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

# ====================================================================
# CONSTANTES DE CONFIGURATION DES PAGES
# ====================================================================
BASE: str = 'base.html'  # Template de base pour toutes les pages

# Regroupement des blueprints pour faciliter l'enregistrement en masse
acfc_blueprints: Tuple[Blueprint, ...] = (clients_bp, catalogue_bp, commercial_bp, comptabilite_bp, stocks_bp, admin_bp, commandes_bp)

# Dictionnaires de configuration pour standardiser le rendu des pages
# Structure : title (titre affiché), context (identifiant CSS/JS), page (template base)
# Configuration page de connexion
LOGIN: Dict[str, str] = {
    'title': 'ACFC - Authentification',  # Titre affiché dans l'onglet navigateur
    'context': 'login',                  # Contexte pour CSS/JS spécifiques
    'page': BASE                         # Template HTML à utiliser
}
LOG_LOGIN_FILE = 'login.log'

# Configuration module Clients (CRM)
CLIENT: Dict[str, str] = {
    'title': 'ACFC - Gestion Clients',
    'context': 'clients',
    'page': BASE
}

LOG_CLIENT_FILE = 'clients.log'

# Configuration administration utilisateurs
USERS: Dict[str, str] = {
    'title': 'ACFC - Administration Utilisateurs',
    'context': 'user',
    'page': BASE
}
LOG_USERS_FILE = 'users.log'

# Configuration changement de mot de passe
CHG_PWD: Dict[str, str] = {
    'title': 'ACFC - Changement de Mot de Passe',
    'context': 'change_password',
    'page': BASE
}
LOG_SECURITY_FILE = 'security.log'

# Configuration changement de mot de passe
USER: Dict[str, str] = {
    'title': 'ACFC - Mon Compte',
    'context': 'user_account',
    'page': BASE
}

# Configuration de la page par défaut
DEFAULT: Dict[str, str] = {
    'title': 'ACFC - Accueil',
    'context': 'default',
    'page': BASE
}

# Configuration erreur 400
ERROR400: Dict[str, str] = {
    'title': 'ACFC - Erreur chez vous',
    'context': '400',
    'page': BASE
}

# Configuration erreur 500
ERROR500: Dict[str, str] = {
    'title': 'ACFC - Erreur chez nous',
    'context': '500',
    'page': BASE
}
LOG_500_FILE = '500.log'

# Configuration commerciale
LOG_COMMERCIAL_FILE = 'commercial.log'

# Messages d'erreur standardisés pour l'authentification
INVALID: str = 'Identifiants invalides.'
WRONG_ROAD: str = 'Méthode non autorisée ou droits insuffisants.'

# Instance du service de gestion des mots de passe (hachage Argon2)
ph_acfc = PasswordService()

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
    print("After request")  # Log basique - à remplacer par un logger professionnel
    return response

@acfc.template_filter('strftime')
def format_datetime(value: datetime | date | None, format: str='%d/%m/%Y'):
    if isinstance(value, (datetime, date)):
        return value.strftime(format)
    return value

@acfc.template_filter('date_input')
def format_date_input(value: datetime | date | None):
    """Filtre spécifique pour les champs input[type=date] qui attendent le format ISO (YYYY-MM-DD)"""
    if isinstance(value, (datetime, date)):
        return value.strftime('%Y-%m-%d')
    return value

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
    db_session_orders: SessionBdDType = SessionBdD()

    # Récupération des commandes en cours sans notion de client
    if id_client == 0:
        commandes: List[Commande] = (
            db_session_orders.query(Commande)
            .options(
                joinedload(Commande.client).joinedload(Client.part),  # Eager loading du client particulier
                joinedload(Commande.client).joinedload(Client.pro)    # Eager loading du client professionnel
            )
            .filter(or_(
                Commande.is_facture == False,
                Commande.is_expedie == False
            ))
            .all()
        )

    # Récupération des commandes en cours pour un client spécifique
    else:
        commandes: List[Commande] = (
            db_session_orders.query(Commande)
            .options(
                joinedload(Commande.client).joinedload(Client.part),  # Eager loading du client particulier
                joinedload(Commande.client).joinedload(Client.pro)    # Eager loading du client professionnel
            )
            .filter(and_(
                Commande.id_client == id_client,
                or_(
                    Commande.is_facture == False,
                    Commande.is_expedie == False
                )
            ))
            .all()
        )

    # Fermeture de la session
    db_session_orders.close()

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
    db_session_commercial: SessionBdDType = SessionBdD()

    # Récupération des dates de référence
    today = date.today()
    first_day_of_month = today.replace(day=1)
    first_day_of_year = today.replace(month=1, day=1)

    # Récupération des indicateurs commerciaux et gestion des exceptions
    try:
        indicators: Dict[str, List[Any]] | None = {
            # Chiffre d'affaire total facturé pour le mois en cours
            "ca_current_month": [
                db_session_commercial.query(func.sum(Commande.montant))
                .filter(
                    Commande.is_facture == True,
                    Commande.date_commande >= first_day_of_month
                ).scalar() or 0,
                'CA Mensuel'
            ],

            # Chiffre d'affaire total facturé pour l'année en cours
            "ca_current_year": [
                db_session_commercial.query(func.sum(Commande.montant))
                .filter(
                    Commande.is_facture == True,
                    Commande.date_commande >= first_day_of_year
                ).scalar() or 0,
                'CA Annuel'
            ],

            # Panier moyen annuel
            "average_basket": [
                db_session_commercial.query(func.avg(Commande.montant))
                .filter(
                    Commande.is_facture == True,
                    Commande.date_commande >= first_day_of_year
                ).scalar() or 0,
                'Panier Moyen'
            ],

            # Clients actifs
            "active_clients": [
                db_session_commercial.query(func.count(func.distinct(Commande.id_client)))
                .filter(
                    Commande.is_facture == True,
                    Commande.date_commande >= first_day_of_year
                ).scalar() or 0,
                'Clients Actifs'
            ],

            # Nombre de commandes par an
            "orders_per_year": [
                db_session_commercial.query(func.count(Commande.id))
                .filter(
                    Commande.is_facture == True,
                    Commande.date_commande >= first_day_of_year
                ).scalar() or 0,
                'Commandes Annuelles'
            ]
        }
    except Exception as e:
        acfc_log.log_to_file(level=ERROR, message=str(e), specific_logger=LOG_COMMERCIAL_FILE, zone_log='commercial', db_log=False)
        indicators = None
    finally:
        # Rollback et fermeture de la session
        db_session_commercial.rollback()
        db_session_commercial.close()
    return indicators

# ====================================================================
# ROUTES PRINCIPALES DE L'APPLICATION
# ====================================================================

@acfc.route('/')
def index() -> str:
    """
    Page d'accueil de l'application.
    
    Redirige automatiquement vers le module Clients après authentification.
    Point d'entrée principal de l'interface utilisateur.
    
    Returns:
        str: Template HTML du module Clients
    """
    return render_template(CLIENT['page'], title=CLIENT['title'], context=CLIENT['context'])

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

    def _get_credentials() -> Tuple[str, str]:
        """Extraction sécurisée des identifiants depuis le formulaire."""
        return request.form.get('username', ''), request.form.get('password', '')

    def _apply_successful_login(user: User) -> None:
        """
        Application des données de session après authentification réussie.
        
        Args:
            user (User): Objet utilisateur authentifié
        """
        session.clear()
        session['user_id'] = user.id
        session['pseudo'] = user.pseudo
        session['last_name'] = user.nom
        session['first_name'] = user.prenom
        session['email'] = user.email
        session['habilitations'] = user.permission
        user.nb_errors = 0  # Remise à zéro du compteur d'erreurs

    # === TRAITEMENT GET : Affichage du formulaire de connexion ===
    if request.method == 'GET':
        return render_template(LOGIN['page'], title=LOGIN['title'], context=LOGIN['context'])
    elif request.method != 'POST':
        acfc_log.log_to_file(level=WARNING,
                             message=f'{request.method} sur route Login par utilisateur {session.get("user_id", "inconnu")}',
                             specific_logger=LOG_LOGIN_FILE, zone_log=LOG_LOGIN_FILE, db_log=True)
        return render_template(ERROR400['page'], title=ERROR400['title'], context=ERROR400['context'], message=WRONG_ROAD)

    # === TRAITEMENT POST : Validation des identifiants ===
    username, password = _get_credentials()
    db_session = SessionBdD()
    user = db_session.query(User).filter_by(pseudo=username).first()
    acfc_log.log_to_file(level=INFO,
                         message=f'début de session pour l\'utilisateur: {user is not None}',
                         specific_logger=LOG_LOGIN_FILE, zone_log=LOG_LOGIN_FILE, db_log=True)

    # Vérification de l'existence de l'utilisateur
    if not user:
        acfc_log.log_to_file(level=WARNING,
                             message=f'Utilisateur non trouvé: {username}',
                             specific_logger=LOG_LOGIN_FILE, zone_log=LOG_LOGIN_FILE, db_log=True)
        return render_template(LOGIN['page'], title=LOGIN['title'], context=LOGIN['context'], message=INVALID)

    # Vérification du mot de passe avec Argon2... si mot de passe faux
    if not ph_acfc.verify_password(password, user.sha_mdp):
        user.nb_errors += 1  # Incrémentation du compteur d'erreurs (sécurité)
        try:
            db_session.commit()
            acfc_log.log_to_file(level=WARNING,
                                 message=f'Tentative de connexion, mot de passe invalide pour l\'utilisateur: {username}. Reste {3 - user.nb_errors} tentatives.',
                                 specific_logger=LOG_LOGIN_FILE, zone_log=LOG_LOGIN_FILE, db_log=True)
            return render_template(LOGIN['page'], title=LOGIN['title'], context=LOGIN['context'], message=INVALID)
        except Exception as e:
            acfc_log.log_to_file(level=ERROR,
                                 message=f'Erreur {e} lors de la validation du mot de passe pour l\'utilisateur: {username}',
                                 specific_logger=LOG_LOGIN_FILE, zone_log=LOG_LOGIN_FILE, db_log=True)
            db_session.rollback()
            return render_template(LOGIN['page'], title=LOGIN['title'], context=LOGIN['context'], message=str(e))

    # === AUTHENTIFICATION RÉUSSIE ===
    _apply_successful_login(user)
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        acfc_log.log_to_file(level=ERROR,
                             message=f'Erreur lors de la connexion pour l\'utilisateur: {username}, {e}.',
                             specific_logger=LOG_LOGIN_FILE, zone_log=LOG_LOGIN_FILE, db_log=True)
        return render_template(LOGIN['page'], title=LOGIN['title'], context='500', message=str(e))
    
    # Vérification de la nécessité de re-hashage de mot de passe
    if ph_acfc.needs_rehash(user.sha_mdp):
        user.sha_mdp = ph_acfc.hash_password(password)
        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            return render_template(LOGIN['page'], title=LOGIN['title'], context='500', message=str(e))

    # Fonctionnalité de sécurité pour forcer le renouvellement des mots de passe
    if user.is_chg_mdp:
        return render_template(LOGIN['page'], title=LOGIN['title'], context='change_password', 
                             message="Veuillez changer votre mot de passe.", username=user.pseudo)

    # Redirection vers la page d'accueil (module Clients)
    return redirect(url_for('dashboard'))

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
            db_session = SessionBdD()
            db_session.execute(text("SELECT 1"))
            db_session.close()
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
    return render_template(DEFAULT['page'], title=DEFAULT['title'], context=DEFAULT['context'], objects=[current_orders, commercial_indicators])

# ====================================================================
# GESTIONNAIRES UTILISATEURS/UTILISATEUR
# ====================================================================

@acfc.route('/users', methods=['GET', 'POST'])
def users() -> Any:
    """
    Gestion des utilisateurs de l'application.
    
    Route d'administration permettant la création, modification et consultation
    des comptes utilisateurs. Réservée aux administrateurs.
    
    Methods:
        GET: Affichage de la liste des utilisateurs existants
        POST: Création ou modification d'un utilisateur
    
    Returns:
        Any: Template de gestion des utilisateurs ou message d'erreur
        
    TODO: 
        Fonctionnalité en développement - nécessite l'implémentation complète 
        de la logique de gestion des utilisateurs et des contrôles d'autorisation.
    """
    # Traitement de la création/modification d'utilisateur
    if request.method == 'POST':
        # TODO: Logique de création d'utilisateur à implémenter
        # Devra inclure: validation des données, hashage du mot de passe,
        # vérification des autorisations, sauvegarde en base
        pass
    
    # Traitement de l'affichage de la liste des utilisateurs
    elif request.method == 'GET':
        # TODO: Récupération et affichage de la liste des utilisateurs
        # Devra inclure: pagination, filtrage, contrôle des autorisations
        return render_template(BASE, title='ACFC - Gestion Utilisateurs', context='users')
    else:
        return render_template(ERROR400['page'], title=ERROR400['title'], context=ERROR400['context'], message=WRONG_ROAD)

class MyAccount:
    """
    Classe de gestion du compte utilisateur.
    """
    @staticmethod
    def get_user_or_error(db_session: SessionBdDType, pseudo: str) -> Any:
        user: User = db_session.query(User).filter_by(pseudo=pseudo).first()
        if not user:
            return render_template(ERROR400['page'], title=ERROR400['title'], context=ERROR400['context'])
        return user

    @staticmethod
    def check_user_permission(pseudo: str) -> Any:
        if session.get('pseudo') != pseudo:
            raise Forbidden("Vous n'êtes pas autorisé à accéder à ce compte.")

    @staticmethod
    def get_request_form(request: Request):
        new_prenom = request.form.get('prenom', '').strip()
        new_nom = request.form.get('nom', '').strip()
        new_email = request.form.get('email', '').strip()
        new_telephone = request.form.get('telephone', '').strip()
        return [new_prenom, new_nom, new_email, new_telephone]

    @staticmethod
    def valid_mail(mail: str, user:User, db_session: SessionBdDType) -> Any:
        """
        Validation de l'adresse email. Retour de la page de paramètre avec un message si invalide.
        Validation que l'email n'est pas déjà utilisé par un autre compte.
        """
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, mail): return render_template(USER['page'], title=USER['title'],
                                                                        context=USER['context'],
                                                                        subcontext='parameters',
                                                                        objects=[user], 
                                                                        message="Le format de l'adresse email n'est pas valide.")
        elif mail != user.email:
            existing_user = db_session.query(User).filter_by(email=mail).first()
            if existing_user: return render_template(USER['page'], title=USER['title'], context=USER['context'],
                                                        subcontext='parameters', objects=[user],
                                                        message="Cette adresse email est déjà utilisée par un autre compte.")
        return re.match(email_pattern, mail) is not None

@acfc.route('/user/<pseudo>', methods=['GET', 'POST'])
def my_account(pseudo: str) -> Any:
    """
    Affichage de la page "Mon Compte" pour l'utilisateur connecté.
    
    Returns:
        Any: Template de la page "Mon Compte"
    """
    db_session = SessionBdD()

    # Vérification des autorisations
    MyAccount.check_user_permission(pseudo)

    # Recherche de l'utilisateur ou gestion de l'erreur 
    user = MyAccount.get_user_or_error(db_session, pseudo)

    #=== Gestion de la requête GET ===
    if request.method == 'GET':
        return render_template(USER['page'], title=USER['title'], context=USER['context'], objects=[user])
    
    #=== Gestion de la requête POST ===
    elif request.method == 'POST':
        try:
            # Récupération des données du formulaire
            _form_return = MyAccount.get_request_form(request)

            # Validation des données obligatoires
            if '' in _form_return: return render_template(USER['page'], title=USER['title'],
                                                                                                context=USER['context'], subcontext='parameters',
                                                                                                objects=[user], message="Tous les champs sont obligatoires.")

            # Validation de l'email (format basique)
            MyAccount.valid_mail(_form_return[2], user, db_session)

            # Mise à jour des données utilisateur
            user.prenom = _form_return[0]
            user.nom = _form_return[1]
            user.email = _form_return[2]
            user.telephone = _form_return[3]

            # Mise à jour de la session si les données affichées changent
            session['first_name'] = _form_return[0]
            session['last_name'] = _form_return[1]
            session['email'] = _form_return[2]
            session['telephone'] = _form_return[3]

            # Sauvegarde en base de données
            db_session.commit()

            # Redirection vers la page de consultation avec message de succès
            return render_template(USER['page'], title=USER['title'], context=USER['context'], 
                                 objects=[user], success_message="Vos informations ont été mises à jour avec succès.")
        except Exception as e:
            db_session.rollback()
            # Si user n'a pas pu être récupéré, on crée un objet vide pour le template
            if ('user' not in locals()) or (not user):
                user = User()
                user.pseudo = pseudo  # Au moins le pseudo pour le template
            return render_template(USER['page'], title=USER['title'], context=USER['context'], 
                                 subcontext='parameters', objects=[user], 
                                 message=f"Erreur lors de la mise à jour : {str(e)}")
        finally:
            db_session.close()
    
    #=== Gestion de toutes les autres méthodes ===
    else: raise Unauthorized("Méthode non autorisée.")

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
        db_session = SessionBdD()
        user = db_session.query(User).filter_by(pseudo=pseudo).first()
        if not user: return render_template(ERROR400['page'], title=ERROR400['title'], context=ERROR400['context'])
        return render_template(USER['page'], title=USER['title'], context=USER['context'], subcontext='parameters', objects=[user])
    elif request.method == 'POST':
        # Redirection vers my_account qui gère la logique POST
        # car le formulaire pointe vers my_account, pas vers user_parameters
        return redirect(url_for('my_account', pseudo=pseudo))
    else:
        return render_template(ERROR400['page'], title=ERROR400['title'], context=ERROR400['context'])
    
@acfc.route('/chg_pwd', methods=['POST'])
def chg_pwd() -> Any:
    """
    Changement de mot de passe utilisateur.
    """
    if request.method == 'POST':
        # Récupération des données du formulaire
        username = request.form.get('username', '')
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation des données
        if not all([username, old_password, new_password, confirm_password]):
            return render_template(CHG_PWD['page'], title=CHG_PWD['title'], context=CHG_PWD['context'],
                                   message='Merci de remplir tous les champs.', username=username)

        if new_password != confirm_password:
            return render_template(CHG_PWD['page'], title=CHG_PWD['title'], context=CHG_PWD['context'],
                                   message="Les mots de passe ne correspondent pas.", username=username)

        if new_password == old_password:
            return render_template(CHG_PWD['page'], title=CHG_PWD['title'], context=CHG_PWD['context'],
                                   message="Le nouveau mot de passe ne peut pas être identique à l'ancien.", username=username)

        # Vérification de l'ancien mot de passe
        db_session = SessionBdD()
        user = db_session.query(User).filter_by(pseudo=username).first()
        if not user or not ph_acfc.verify_password(old_password, user.sha_mdp):
            return render_template(CHG_PWD['page'], title=CHG_PWD['title'], context=CHG_PWD['context'],
                                   message='Ancien mot de passe incorrect.', username=username)

        # Hashage du nouveau mot de passe
        user.sha_mdp = ph_acfc.hash_password(new_password)

        # retrait de la nécessité de changer le mot de passe
        user.is_chg_mdp = False
        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            return render_template(CHG_PWD['page'], title=CHG_PWD['title'], context='500', message=str(e))

        return redirect(url_for('login'))

    return render_template(ERROR400['page'], title=ERROR400['title'], context=ERROR400['context'], message=INVALID)

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
    match error.code:
        case 400:
            message_error = f'Votre requête est mal formée.\n{error.name}'
        case 401:
            message_error = f'Authentification requise.\n{error.name}'
        case 403:
            message_error = f'Accès interdit.\n{error.name}'
        case 404:
            message_error = f'Ressource non trouvée.\n{error.name}'
        case _:
            message_error = f'Erreur inconnue, {error.name}'

    return render_template(ERROR400['page'], title=ERROR400['title'], context=ERROR400['context'], 
                         status_code=error.code, status_message=message_error)

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
    match error.code:
        case 500:
            message_error = f'Erreur interne du serveur.\n{error.name}'
        case 502:
            message_error = f'Erreur de passerelle.\n{error.name}'
        case 503:
            message_error = f'Service indisponible.\n{error.name}'
        case 504:
            message_error = f'Timeout de passerelle.\n{error.name}'
        case _:
            message_error = f'Erreur inconnue, {error.name}'

    return render_template(BASE, title='ACFC - Erreur Serveur', context='500', 
                         status_code=error.code, status_message=message_error)

# ====================================================================
# ENREGISTREMENT DES MODULES MÉTIERS
# ====================================================================
# Enregistrement automatique de tous les blueprints définis
for bp in acfc_blueprints:
    acfc.register_blueprint(bp)

# ====================================================================
# POINT D'ENTRÉE DE L'APPLICATION
# ====================================================================

if __name__ == '__main__':
    """
    Démarrage de l'application en mode production avec Waitress.
    
    Waitress est un serveur WSGI production-ready qui remplace le serveur 
    de développement Flask. Configuration :
    - Host: 0.0.0.0 (écoute sur toutes les interfaces)
    - Port: 5000 (port standard de l'application)
    
    Note: En production, l'application est généralement déployée derrière
    un reverse proxy (Nginx) pour la gestion SSL et la distribution de charge.
    """
    serve(acfc, host="0.0.0.0", port=5000)
