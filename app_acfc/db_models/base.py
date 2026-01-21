"""Modèles de données de base pour l'application ACFC."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from sqlalchemy.engine.url import URL
from app_acfc.config.config_models import Configuration
from app_acfc.db_models import (accounting, clients, users, orders, contacts, products, technical)  # type: ignore # pylint: disable=unused-import

# ====================================================================
# CONFIGURATION DE LA BASE DE DONNÉES
# ====================================================================

# Définition de la base déclarative pour les modèles
Base = declarative_base()

# Instance de configuration globale
conf: Configuration = Configuration()

# Construction de l'URL de connexion à la base de données
# Utilise le connecteur MySQL optimisé avec support UTF-8 complet
db_url = URL.create(
    drivername="mysql+mysqlconnector",  # Driver MySQL Connector/Python
    username=conf.db_user,              # Utilisateur depuis configuration
    password=conf.db_password,          # Mot de passe depuis configuration
    host=conf.db_host,                  # Serveur depuis configuration
    port=conf.db_port,                  # Port depuis configuration (défaut: 3306)
    database=conf.db_name,              # Base de données depuis configuration
    query={"charset": "utf8mb4"}        # Support Unicode complet (emojis, caractères spéciaux)
)

# Création de l'engine SQLAlchemy avec optimisations de performance
engine = create_engine(
    db_url,
    echo=False,                         # Désactive le logging SQL (à activer en debug)
    pool_size=10,                       # Taille du pool de connexions
    max_overflow=20,                    # Connexions supplémentaires autorisées
    pool_pre_ping=True,                 # Vérification de connexion avant utilisation
    pool_recycle=3600                   # Recyclage des connexions après 1h
)

# Factory de sessions pour l'accès aux données
SessionBdD = scoped_session(sessionmaker(
    autocommit=False,                   # Transactions manuelles pour meilleur contrôle
    autoflush=False,                    # Flush manuel pour optimiser les performances
    bind=engine                         # Liaison à l'engine configuré
))

Base.metadata.create_all(bind=engine, checkfirst=True)
