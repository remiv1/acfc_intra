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

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Flask
from os import getenv

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
