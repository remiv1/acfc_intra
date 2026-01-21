"""
Module de configuration des modèles de l'application ACFC.
"""
import time
from os import getenv
from typing import List
from dotenv import load_dotenv
from sqlalchemy.orm.session import Session as SessionBdD
from sqlalchemy.orm import Session as SessionBdDType
from sqlalchemy.exc import OperationalError, DatabaseError
from flask import g
from app_acfc.db_models.technical import IndicatifsTel, Villes

# ====================================================================
# CLASSE DE CONFIGURATION DE L'APPLICATION
# ====================================================================

class Configuration:
    """
    Classe de configuration centralisée de l'application.
    
    Gère le chargement et la validation de toutes les variables d'environnement
    nécessaires au fonctionnement de l'application, avec des valeurs par défaut
    sécurisées pour l'environnement de développement.
    
    Attributes:
        db_port (int): Port de connexion à la base de données (défaut: 3306)
        db_name (str): Nom de la base de données
        db_user (str): Utilisateur de la base de données
        db_password (str): Mot de passe de la base de données
        db_host (str): Adresse du serveur de base de données
        api_key_l (str): Clé d'API pour services externes
        api_secret_l (str): Secret d'API pour services externes
    """
    def __init__(self) -> None:
        """
        Initialisation de la configuration avec chargement des variables d'environnement.
        
        Raises:
            ValueError: En cas de configuration incomplète ou invalide
        """
        # Essayer de charger le .env si disponible (développement local)
        # En production/Docker, les variables sont directement dans l'environnement
        try:
            load_dotenv()
        except FileNotFoundError:
            # Pas de fichier .env, on utilise les variables d'environnement directement
            pass
        # === CONFIGURATION DU PORT DE BASE DE DONNÉES ===
        db_port_env: str | None = getenv("MYSQL_PORT")
        if db_port_env is not None:
            try:
                self.db_port: int = int(db_port_env)
            except ValueError:
                # Fallback sur le port MySQL standard en cas de valeur invalide
                self.db_port: int = 3306
        else:
            self.db_port: int = 3306
        # === VALIDATION ET CHARGEMENT DES VARIABLES CRITIQUES ===
        if verify_env():
            self.db_name: str = getenv("MYSQL_DATABASE", "acfc_db")
            self.db_user: str = getenv("MYSQL_USER", "acfc_user")
            self.db_password: str = getenv("MYSQL_PASSWORD", "secure_password")
            self.db_host: str = getenv("MYSQL_HOST", "localhost")
            self.api_key_l: str = getenv("API_URL", "default_api_key")
            self.api_secret_l: str = getenv("API_SECRET", "default_api_secret")
        else:
            # Configuration de fallback en cas d'échec de vérification
            self.api_key_l: str = "default_api_key"
        # === VALIDATION FINALE DE LA CONFIGURATION ===
        if not all([self.db_user, self.db_password, self.db_host, self.db_name]):
            raise ValueError(
                "Configuration incomplète : Une ou plusieurs variables d'environnement de bdd "
                "(MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE) ne sont pas définies."
            )

# ====================================================================
# CLASSES ET FONCTIONS UTILITAIRES
# ====================================================================

class GeoMethods:
    """
    Classe utilitaire pour les méthodes liées aux données géographiques :
        - Codes postaux et villes
        - Indicatifs téléphoniques
        - Autres éventuelles API géographiques
    """

    @staticmethod
    def get_indicatifs_tel() -> List[IndicatifsTel]:
        """
        Récupère la liste des indicatifs téléphoniques depuis l'objet SQLAlchemy.
        Args:
            pays (str): données textuelles du pays (ex: 'franc')
        Returns:
            List[Dict]: Liste des indicatifs téléphoniques
        """
        db_session: SessionBdDType = get_db_session()
        return db_session.query(IndicatifsTel) \
                            .order_by(IndicatifsTel.id.asc()) \
                            .all()

    @staticmethod
    def get_codes_postaux_villes(code_postal: str) -> List[Villes]:
        """
        Récupère la liste des villes et codes postaux depuis l'objet SQLAlchemy.
        Args:
            code_postal (str): données textuelles du code postal (ex: '39270')
        Returns:
            List[Villes]: Liste des villes et codes postaux
        """
        db_session: SessionBdDType = get_db_session()
        return db_session.query(Villes).filter(
            Villes.code_postal.ilike(f'{code_postal}'
            )).all()


def verify_env() -> bool:
    """
    Vérification et chargement des variables d'environnement critiques.
    
    Valide la présence des variables de configuration de base de données
    avant l'initialisation de l'application. Empêche le démarrage avec
    une configuration incomplète.
    
    Returns:
        bool: True si toutes les variables requises sont présentes
        
    Raises:
        ValueError: Si des variables critiques sont manquantes
        
    Variables requises :
        - MYSQL_USER : Nom d'utilisateur de la base de données
        - MYSQL_PASSWORD : Mot de passe de la base de données
        - MYSQL_HOST : Adresse du serveur de base de données
        - MYSQL_DATABASE : Nom de la base de données
    """
    # Essayer de charger le .env si disponible (développement local)
    # En production/Docker, les variables sont directement dans l'environnement
    try:
        load_dotenv()
    except FileNotFoundError:
        # Pas de fichier .env, on utilise les variables d'environnement directement
        pass

    db_user: str | None = getenv("MYSQL_USER")
    db_password: str | None = getenv("MYSQL_PASSWORD")
    db_host: str | None = getenv("MYSQL_HOST")
    db_name: str | None = getenv("MYSQL_DATABASE")

    if db_user is None or db_password is None or db_host is None or db_name is None:
        raise ValueError(
            "Les var d'env. MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST et MYSQL_DATABASE "
            "doivent être définies (fichier .env ou variables d'environnement système)"
        )
    return True

def get_db_session() -> SessionBdDType:
    """
    Récupère la session de base de données pour la requête en cours.
    Utilise une session scoped pour garantir l'isolation entre les requêtes.
    
    Returns:
        SessionBdDType: Session SQLAlchemy pour la base de données
    """
    if 'db_session' not in g:
        g.db_session = SessionBdD()
    return g.db_session

# ====================================================================
# INITIALISATION BASE DE DONNÉES AVEC RETRY
# ====================================================================

def init_database(max_retries: int = 30, retry_delay: int = 2) -> None:
    """
    Initialise la base de données avec mécanisme de retry.
    
    Args:
        max_retries (int): Nombre maximum de tentatives
        retry_delay (int): Délai entre les tentatives en secondes
    
    Raises:
        ConnectionError: Si impossible de se connecter après toutes les tentatives
    """
    from app_acfc.db_models.base import engine, Base #pylint: disable=import-outside-toplevel
    from sqlalchemy import text #pylint: disable=import-outside-toplevel

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Tentative {attempt}/{max_retries} de connexion à la bdd...")

            # Test de connexion
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            # Si connexion OK, création des tables
            Base.metadata.create_all(engine)
            print("✅ Base de données initialisée avec succès !")
            return

        except (OperationalError, DatabaseError) as e:
            if attempt == max_retries:
                print(f"❌ Échec final après {max_retries} tentatives")
                raise ConnectionError(
                    f"Impossible de se connecter à la bdd après {max_retries} tentatives. "
                    f"Dernière erreur: {e}"
                ) from e

            print(f"⚠️  Tentative {attempt} échouée: {e}")
            print(f"🕒 Nouvelle tentative dans {retry_delay}s...")
            time.sleep(retry_delay)
