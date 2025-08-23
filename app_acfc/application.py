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

from flask import Flask, Response, render_template, request, Blueprint, session, url_for, redirect, jsonify
from flask_session import Session
from waitress import serve
from typing import Any, Dict, Tuple
from werkzeug.exceptions import HTTPException, Forbidden, Unauthorized
from services import PasswordService, SecureSessionService
from modeles import SessionBdD, User
from datetime import datetime
from sqlalchemy import text
#TODO: modifier les systèmes de logs
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Écrit dans stdout
    ]
)

logging.debug("Ceci est un message de débogage")
logging.info("Ceci est un message d'information")
logging.error("Ceci est un message d'erreur")

# Création de l'instance Flask principale avec configuration des dossiers statiques et templates
acfc = Flask(__name__,
             static_folder='statics',     # Ressources CSS, JS, images par module
             template_folder='templates') # Templates HTML Jinja2

# ====================================================================
# IMPORTS ET ENREGISTREMENT DES BLUEPRINTS (MODULES MÉTIERS)
# ====================================================================

# Importer et enregistrer les blueprints des différents modules métiers
# Gestion de l'import avec fallback pour compatibilité développement/production
try:
    # Import absolu privilégié quand le package est installé ou exécuté comme module
    from app_acfc.contextes_bp.clients import clients_bp         # Module CRM - Gestion clients
    from app_acfc.contextes_bp.catalogue import catalogue_bp     # Module Catalogue produits
    from app_acfc.contextes_bp.commercial import commercial_bp   # Module Commercial - Devis, commandes
    from app_acfc.contextes_bp.comptabilite import comptabilite_bp # Module Comptabilité - Facturation
    from app_acfc.contextes_bp.stocks import stocks_bp          # Module Stocks - Inventaire
    from app_acfc.contextes_bp.admin import admin_bp            # Module Administration - Utilisateurs
except Exception:
    # Fallback vers les imports locaux en cas d'exécution directe des fichiers
    from contextes_bp.clients import clients_bp
    from contextes_bp.catalogue import catalogue_bp
    from contextes_bp.commercial import commercial_bp
    from contextes_bp.comptabilite import comptabilite_bp
    from contextes_bp.stocks import stocks_bp
    from contextes_bp.admin import admin_bp

# Regroupement des blueprints pour faciliter l'enregistrement en masse
acfc_blueprints: Tuple[Blueprint, ...] = (clients_bp, catalogue_bp, commercial_bp, comptabilite_bp, stocks_bp, admin_bp)

# ====================================================================
# CONFIGURATION DES SERVICES DE SÉCURITÉ
# ====================================================================

# Initialisation du service de sessions sécurisées (chiffrement, cookies HTTPOnly)
SecureSessionService(acfc)
# Activation du gestionnaire de sessions Flask-Session (stockage filesystem)
Session(acfc)

# ====================================================================
# CONSTANTES DE CONFIGURATION DES PAGES
# ====================================================================
# Dictionnaires de configuration pour standardiser le rendu des pages
# Structure : title (titre affiché), context (identifiant CSS/JS), page (template base)

BASE: str = 'base.html'  # Template de base pour toutes les pages

# Configuration page de connexion
LOGIN: Dict[str, str] = {
    'title': 'ACFC - Authentification',  # Titre affiché dans l'onglet navigateur
    'context': 'login',                  # Contexte pour CSS/JS spécifiques
    'page': BASE                         # Template HTML à utiliser
}

# Configuration module Clients (CRM)
CLIENT: Dict[str, str] = {
    'title': 'ACFC - Gestion Clients',
    'context': 'clients',
    'page': BASE
}

# Configuration administration utilisateurs
USERS: Dict[str, str] = {
    'title': 'ACFC - Administration Utilisateurs',
    'context': 'user',
    'page': BASE
}

# Configuration changement de mot de passe
CHG_PWD: Dict[str, str] = {
    'title': 'ACFC - Changement de Mot de Passe',
    'context': 'change_password',
    'page': BASE
}

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

# Messages d'erreur standardisés pour l'authentification
INVALID: str = 'Identifiants invalides.'
WRONG_ROAD: str = 'Méthode non autorisée ou droits insuffisants.'

# Instance du service de gestion des mots de passe (hachage Argon2)
ph_acfc = PasswordService()

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
        user.nb_errors = 0  # Remise à zéro du compteur d'erreurs

    # === TRAITEMENT GET : Affichage du formulaire de connexion ===
    if request.method == 'GET':
        logging.info("GET request for login")
        return render_template(LOGIN['page'], title=LOGIN['title'], context=LOGIN['context'])
    elif request.method != 'POST':
        logging.warning("Invalid request method")
        return render_template(BASE, title=LOGIN['title'], context='400', message=WRONG_ROAD)

    # === TRAITEMENT POST : Validation des identifiants ===
    username, password = _get_credentials()
    logging.debug(f"Attempting login for user: {username}")
    db_session = SessionBdD()
    user = db_session.query(User).filter_by(pseudo=username).first()
    logging.debug(f"User found: {user is not None}")

    # Vérification de l'existence de l'utilisateur
    if not user:
        logging.warning("User not found")
        return render_template(LOGIN['page'], title=LOGIN['title'], context=LOGIN['context'], message=INVALID)

    # Vérification du mot de passe avec Argon2... si mot de passe faux
    if not ph_acfc.verify_password(password, user.sha_mdp):
        user.nb_errors += 1  # Incrémentation du compteur d'erreurs (sécurité)
        try:
            db_session.commit()
            return render_template(LOGIN['page'], title=LOGIN['title'], context=LOGIN['context'], message=INVALID)
        except Exception as e:
            db_session.rollback()
            return render_template(LOGIN['page'], title=LOGIN['title'], context=LOGIN['context'], message=str(e))

    # === AUTHENTIFICATION RÉUSSIE ===
    _apply_successful_login(user)
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
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
    return render_template(DEFAULT['page'], title=DEFAULT['title'], context=DEFAULT['context'])

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

    return render_template(CHG_PWD['page'], title=CHG_PWD['title'], context='400', message=INVALID)

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
        return render_template(BASE, title='ACFC - Erreur', context='400')

@acfc.route('/user/<pseudo>', methods=['GET', 'POST'])
def my_account(pseudo: str) -> Any:
    """
    Affichage de la page "Mon Compte" pour l'utilisateur connecté.
    
    Returns:
        Any: Template de la page "Mon Compte"
    """
    
    #=== Gestion de la requête GET ===
    if request.method == 'GET':
        db_session = SessionBdD()
        # Vérification de l'utilisateur connecté == au compte recherché
        if session.get('pseudo') != pseudo: raise Forbidden("Vous n'êtes pas autorisé à accéder à ce compte.")

        # Recherche de l'utilisateur en base de données
        user = db_session.query(User).filter_by(pseudo=pseudo).first()

        # Retour si l'utilisateur n'est pas trouvé (route appelée hors lien)
        if not user: return render_template(BASE, title='ACFC - Erreur', context='400')

        return render_template(USER['page'], title=USER['title'], context=USER['context'], objects=[user])
    
    #=== Gestion de la requête POST ===
    elif request.method == 'POST':
        db_session = SessionBdD()
        try:
            # Vérification de l'utilisateur connecté == au compte recherché
            if session.get('pseudo') != pseudo:
                raise Forbidden("Vous n'êtes pas autorisé à modifier ce compte.")

            # Recherche de l'utilisateur en base de données
            user = db_session.query(User).filter_by(pseudo=pseudo).first()
            if not user:
                return render_template(BASE, title='ACFC - Erreur', context='400', 
                                     message="Utilisateur non trouvé.")

            # Récupération des données du formulaire
            new_prenom = request.form.get('prenom', '').strip()
            new_nom = request.form.get('nom', '').strip()
            new_email = request.form.get('email', '').strip()
            new_telephone = request.form.get('telephone', '').strip()

            # Validation des données obligatoires
            if not all([new_prenom, new_nom, new_email, new_telephone]):
                return render_template(USER['page'], title=USER['title'], context=USER['context'], 
                                     subcontext='parameters', objects=[user], 
                                     message="Tous les champs sont obligatoires.")

            # Validation de l'email (format basique)
            import re
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_pattern, new_email):
                return render_template(USER['page'], title=USER['title'], context=USER['context'], 
                                     subcontext='parameters', objects=[user], 
                                     message="Le format de l'adresse email n'est pas valide.")

            # Vérification de l'unicité de l'email (si modifié)
            if new_email != user.email:
                existing_user = db_session.query(User).filter_by(email=new_email).first()
                if existing_user:
                    return render_template(USER['page'], title=USER['title'], context=USER['context'], 
                                         subcontext='parameters', objects=[user], 
                                         message="Cette adresse email est déjà utilisée par un autre compte.")

            # Mise à jour des données utilisateur
            user.prenom = new_prenom
            user.nom = new_nom
            user.email = new_email
            user.telephone = new_telephone

            # Mise à jour de la session si les données affichées changent
            session['first_name'] = new_prenom
            session['last_name'] = new_nom
            session['email'] = new_email

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
        if not user: return render_template(BASE, title='ACFC - Erreur', context='400')
        return render_template(USER['page'], title=USER['title'], context=USER['context'], subcontext='parameters', objects=[user])
    elif request.method == 'POST':
        # Redirection vers my_account qui gère la logique POST
        # car le formulaire pointe vers my_account, pas vers user_parameters
        return redirect(url_for('my_account', pseudo=pseudo))
    else:
        return render_template(BASE, title='ACFC - Erreur', context='400')

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

    return render_template(BASE, title='ACFC - Erreur Client', context='400', 
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
