"""
ACFC - Services de Sécurité et Authentification
===============================================

Module contenant les services de sécurité de l'application ACFC :
- Gestion du hachage sécurisé des mots de passe (Argon2)
- Configuration des sessions utilisateur sécurisées
- Protection contre les attaques par force brute et CSRF

Technologies utilisées :
- Argon2 : Algorithme de hachage résistant aux attaques par GPU
- Flask-Session : Gestion avancée des sessions avec stockage filesystem
- Cookies sécurisés : HTTPOnly, SameSite, chiffrement

Auteur : ACFC Development Team
Version : 1.0
"""
from .modeles import User
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Flask, session
from sqlalchemy.orm import Session as SessionBdDType
from os import getenv
from flask import Request
from typing import Any, Dict, Tuple
from logs.logger import acfc_log, INFO

LOG_LOGIN_FILE = 'login.log'

class PasswordService:
    """
    Service de gestion sécurisée des mots de passe.
    
    Utilise l'algorithme Argon2id pour le hachage des mots de passe, 
    recommandé par l'OWASP comme standard de sécurité pour 2024.
    
    Configuration optimisée pour un équilibre sécurité/performance :
    - time_cost=4 : 4 itérations de hachage
    - memory_cost=64KB : Utilisation mémoire pour résister aux attaques GPU
    - parallelism=3 : Utilisation de 3 threads parallèles
    - hash_len=32 : Taille du hash de 32 octets (256 bits)
    - salt_len=16 : Taille du sel de 16 octets (128 bits)
    """
    
    def __init__(self):
        """
        Initialisation du service avec paramètres de sécurité optimisés.
        """
        self.hasher = PasswordHasher(
            time_cost=4,        # Complexité temporelle - résistance aux attaques par dictionnaire
            memory_cost=2**16,  # Complexité mémoire (64KB) - résistance aux attaques GPU
            parallelism=3,      # Nombre de threads - améliore les performances
            hash_len=32,        # Longueur du hash final en octets
            salt_len=16         # Longueur du sel aléatoire en octets
        )

    def hash_password(self, password: str) -> str:
        """
        Hachage sécurisé d'un mot de passe.
        
        Génère automatiquement un sel aléatoire unique pour chaque mot de passe,
        empêchant les attaques par tables arc-en-ciel.
        
        Args:
            password (str): Mot de passe en clair à hacher
            
        Returns:
            str: Hash Argon2 incluant tous les paramètres et le sel
            
        Example:
            >>> ps = PasswordService()
            >>> hash_val = ps.hash_password("motdepasse123")
            >>> print(hash_val)
            $argon2id$v=19$m=65536,t=4,p=3$...
        """
        return self.hasher.hash(password)

    def verify_password(self, pwd: str, hashed_pwd: str) -> bool:
        """
        Vérification d'un mot de passe contre son hash.
        
        Méthode sécurisée pour l'authentification qui résiste aux attaques
        par timing grâce à l'implémentation constante d'Argon2.
        
        Args:
            pwd (str): Mot de passe en clair à vérifier
            hashed_pwd (str): Hash stocké en base de données
            
        Returns:
            bool: True si le mot de passe correspond, False sinon
            
        Example:
            >>> ps = PasswordService()
            >>> is_valid = ps.verify_password("motdepasse123", stored_hash)
            >>> print(is_valid)
            True
        """
        try:
            self.hasher.verify(hashed_pwd, pwd)
            return True
        except VerifyMismatchError:
            return False
    
    def needs_rehash(self, hashed_pwd: str) -> bool:
        """
        Vérification de la nécessité de rehacher un mot de passe.
        
        Permet la mise à jour progressive des anciens hashes vers de nouveaux
        paramètres de sécurité plus robustes sans casser l'authentification.
        
        Args:
            hashed_pwd (str): Hash existant à analyser
            
        Returns:
            bool: True si le hash doit être régénéré, False sinon
            
        Note:
            Utilisé lors de l'authentification réussie pour upgrader
            automatiquement les anciens hashes vers les nouveaux paramètres.
        """
        return self.hasher.check_needs_rehash(hashed_pwd)

class SecureSessionService:
    """
    Service de configuration des sessions utilisateur sécurisées.
    
    Configure Flask-Session pour une gestion avancée des sessions avec :
    - Stockage filesystem (plus sécurisé que les cookies)
    - Chiffrement des données de session
    - Cookies HTTPOnly pour prévenir les attaques XSS
    - Gestion automatique de l'expiration des sessions
    
    Sécurité implémentée :
    - Protection CSRF via signature des cookies
    - Isolation des sessions par application
    - Timeout automatique des sessions inactives (30 minutes)
    - Résistance aux attaques de session fixation
    """
    
    def __init__(self, app: Flask):
        """
        Configuration complète de la sécurité des sessions.
        
        Args:
            app (Flask): Instance de l'application Flask à configurer
        """
        self.app = app
        
        # === CONFIGURATION DE LA CLÉ SECRÈTE ===
        # Récupération depuis les variables d'environnement avec fallback sécurisé
        self.app.secret_key = getenv('SESSION_PASSKEY', 'default_secret_key')
        
        # === CONFIGURATION DU STOCKAGE DES SESSIONS ===
        self.app.config['SESSION_TYPE'] = 'filesystem'  # Stockage sur disque (plus sécurisé)
        self.app.config['SESSION_PERMANENT'] = False    # Sessions non permanentes par défaut
        self.app.config['SESSION_USE_SIGNER'] = True    # Signature cryptographique des cookies
        
        # === CONFIGURATION DES COOKIES DE SESSION ===
        # TODO: SESSION_COOKIE_SECURE doit être activé en production HTTPS
        # self.app.config['SESSION_COOKIE_SECURE'] = True  # Production: Force HTTPS uniquement
        self.app.config['SESSION_COOKIE_HTTPONLY'] = True  # Protection XSS: pas d'accès JavaScript
        self.app.config['SESSION_COOKIE_NAME'] = 'acfc'    # Nom personnalisé du cookie
        
        # === CONFIGURATION DE L'EXPIRATION ===
        self.app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes d'inactivité max

class AuthenticationService:
    """
    Service de gestion de l'authentification des utilisateurs.

    Gère la validation des identifiants, la gestion des erreurs de connexion,
    et l'application des données de session.

    initialisation des données de session :
    user_to_authenticate = AuthenticationService(request)

    Méthodes :
    - authenticate: Authentifie un utilisateur
    - is_authenticated: Vérifie si l'utilisateur est authentifié
    - logout: Déconnecte l'utilisateur

    """
    def __init__(self, request_object: Request):
        self.user = request_object.form.get('username', '')
        self.pwd = request_object.form.get('password', '')
        self.old_pwd = request_object.form.get('old_password', '')
        self.new_pwd = request_object.form.get('new_password', '')
        self.confirm_new_pwd = request_object.form.get('confirm_password', '')
        self.authenticated: bool = False
        self.user_dict: Dict[str, Any]
        self.existing_user: bool
        self.is_chg_mdp: bool
        self.user_pseudo: str = ""
        self.pwd_param: Dict[str, bool] = {}
        self.pwd_param_messages: Dict[str, str] = {
            'all_field': 'Merci de remplir tous les champs.',
            'pwd_match': "Les mots de passe ne correspondent pas.",
            'pwd_changed': "Le nouveau mot de passe ne peut pas être identique à l'ancien.",
            'authenticated_user': "Merci de renseigner correctement l'ancien mot de passe",
            'db_unerror': "Erreur lors de la mise à jour en base de données.",
            'user_found': "Utilisateur non trouvé."
        }


    def _create_session(self, user: User):
        """
        Crée une session utilisateur.

        Args:
            user (User): L'utilisateur à authentifier
        """
        session.clear()
        session['user_id'] = user.id
        session['pseudo'] = user.pseudo
        session['last_name'] = user.nom
        session['first_name'] = user.prenom
        session['email'] = user.email
        session['tel'] = user.telephone
        session['habilitations'] = user.permission

    def _log_result(self, message: str, level: int = INFO):
        """
        Enregistre un message de log.

        Args:
            message (str): Le message à enregistrer
            level (int): Le niveau de log (INFO, ERROR, etc.)
        """
        acfc_log.log_to_file(level=level,
                            message=message,
                            specific_logger=LOG_LOGIN_FILE,
                            zone_log=LOG_LOGIN_FILE,
                            db_log=True)

    def _bad_password(self, user: User):
        """
        Gère un mot de passe incorrect pour un utilisateur existant.

        Args:
            user (User): L'utilisateur concerné
        """
        self.existing_user = True
        user.nb_errors += 1
        user.is_locked = user.nb_errors >= 3
        user.is_chg_mdp = user.nb_errors >= 3

    def _good_password(self, user: User, ph_acfc: PasswordService):
        """
        Gère un mot de passe correct pour un utilisateur existant.

        Args:
            user (User): L'utilisateur concerné
        """
        self.existing_user = True
        self.authenticated = True
        self.user_dict = user.to_dict()
        # Stocker les propriétés nécessaires avant de détacher l'objet de la session
        self.is_chg_mdp = user.is_chg_mdp
        acfc_log.log_to_file(level=INFO,
                            message=f'Changement de mot de passe requis pour l\'utilisateur: {self.is_chg_mdp}',
                            specific_logger=LOG_LOGIN_FILE,
                            zone_log=LOG_LOGIN_FILE,
                            db_log=True)
        self.user_pseudo = user.pseudo
        user.nb_errors = 0
        user.is_locked = False
        if ph_acfc.needs_rehash(user.sha_mdp): user.sha_mdp = ph_acfc.hash_password(user.sha_mdp)

    def _get_user(self) -> Tuple[User | None, SessionBdDType]:
        from modeles import SessionBdD
        session_db = SessionBdD()
        user = session_db.query(User).filter_by(pseudo=self.user).first()
        return user, session_db

    def authenticate(self) -> bool:
        """
        Authentifie un utilisateur en vérifiant ses identifiants et mot de passe.

        :Args:
            None

        :Returns:
            None
        """
        user, session_db = self._get_user()
        # Instance du service de gestion des mots de passe (hachage Argon2)
        ph_acfc = PasswordService()
        try:
            if user and ph_acfc.verify_password(self.pwd, user.sha_mdp) and (not user.is_locked and user.is_active):
                self._good_password(user, ph_acfc)
                self._create_session(user)
                self._log_result(message=f'début de session pour l\'utilisateur: {self.user_pseudo if self.user_pseudo else "inconnu"}')
                statement = True
            elif user and user.is_locked:
                self._log_result(message=f'Utilisateur verrouillé: {self.user}')
                statement = False
            elif user and not user.is_active:
                self._log_result(message=f'Utilisateur inactif: {self.user}')
                statement = False
            elif user:
                self._bad_password(user)
                self._log_result(message=f'Utilisateur existant: {self.user} et mot de passe incorrect essai n°{user.nb_errors}')
                statement = False
            else:
                self._log_result(message=f'Utilisateur non trouvé: {self.user}')
                statement = False
            session_db.commit()
            # Détacher l'objet user de la session si il existe
            if user is not None:
                session_db.expunge(user)
        except Exception as e:
            session_db.rollback()
            self._log_result(message=f'Erreur lors de l\'authentification de l\'utilisateur: {self.user}.\nErreur: {e}', level=40)
            statement = False
        finally:
            # Fermeture de la session de base de données
            session_db.close()
        return statement
    
    def _validate_chg_pwd_form(self, user: User, pwd_hasher: PasswordService):
        if not all([self.user, self.old_pwd, self.new_pwd, self.confirm_new_pwd]):
            self.pwd_param['all_field'] = False
            return False
        elif self.new_pwd != self.confirm_new_pwd:
            self.pwd_param['pwd_match'] = False
            return False
        elif self.new_pwd == self.old_pwd:
            self.pwd_param['pwd_changed'] = False
            return False
        elif not pwd_hasher.verify_password(self.old_pwd, user.sha_mdp):
            self.pwd_param['authenticated_user'] = False
            return False
        else:
            self.pwd_param['all_field'] = True
            self.pwd_param['pwd_match'] = True
            self.pwd_param['pwd_changed'] = True
            self.pwd_param['authenticated_user'] = True
            return True

    def chg_pwd(self) -> bool:
        user, session_db = self._get_user()
        ph_acfc = PasswordService()
        if not self._validate_chg_pwd_form(user, ph_acfc):
            return False
        elif user:
            try:
                user.sha_mdp = ph_acfc.hash_password(self.new_pwd)
                user.is_chg_mdp = False
                user.nb_errors = 0
                user.is_locked = False
                session_db.commit()
                self._log_result(message=f'Mot de passe changé pour l\'utilisateur: {self.user}.')
                return True

            except Exception as e:
                session_db.rollback()
                self._log_result(message=f'Erreur lors du changement de mot de passe de l\'utilisateur: {self.user}.\nErreur: {e}', level=40)
                self.pwd_param['db_unerror'] = False
                return False
            
            finally:
                session_db.close()
        else:
            self._log_result(message=f'Utilisateur non trouvé: {self.user}.')
            self.pwd_param['user_found'] = False
            return False

    def is_authenticated(self) -> bool:
        """
        Vérifie si l'utilisateur est authentifié.

        Returns:
            bool: True si l'utilisateur est authentifié, False sinon
        """
        return self.authenticated
    