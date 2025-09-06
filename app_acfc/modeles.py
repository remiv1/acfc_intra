from sqlalchemy import (
    Integer, String, Date, DateTime, Boolean, Text, Numeric, event, Computed,
    LargeBinary, ForeignKey, text)
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session as SessionBdDType, scoped_session, sessionmaker, Mapper, relationship, mapped_column
from sqlalchemy.orm.session import Session as SessionBdDType
from typing import Any, Dict, List, Optional
from sqlalchemy.engine import Connection
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from flask import Request, g, render_template, session
from dotenv import load_dotenv
from os import getenv
from werkzeug.exceptions import Forbidden
from logs.logger import acfc_log, INFO, ERROR
from datetime import datetime

"""
ACFC - Modèles de Données et Configuration Base de Données
=========================================================

Module définissant l'architecture des données de l'application ACFC.
Contient les modèles SQLAlchemy pour tous les modules métiers :

Modules couverts :
- Gestion des utilisateurs et authentification
- CRM (Client Relationship Management)  
- Gestion des contacts (emails, téléphones, adresses)
- Comptabilité et plan comptable
- Gestion des commandes et facturation
- Catalogue produits et stocks

Technologies :
- SQLAlchemy ORM : Mapping objet-relationnel
- MariaDB/MySQL : Base de données relationnelle
- Connecteur MySQL : Driver de connexion optimisé
- Variables d'environnement : Configuration sécurisée

Architecture :
- Modèle en couches avec séparation des responsabilités
- Relations cohérentes entre entités métiers
- Contraintes d'intégrité référentielle
- Optimisations de performance (index, types de données)

Auteur : ACFC Development Team
Version : 1.0
"""

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
        - DB_USER : Nom d'utilisateur de la base de données
        - DB_PASSWORD : Mot de passe de la base de données  
        - DB_HOST : Adresse du serveur de base de données
        - DB_NAME : Nom de la base de données
    """
    # Essayer de charger le .env si disponible (développement local)
    # En production/Docker, les variables sont directement dans l'environnement
    try:
        load_dotenv()
    except FileNotFoundError:
        # Pas de fichier .env, on utilise les variables d'environnement directement
        pass
    
    db_user: str | None = getenv("DB_USER")
    db_password: str | None = getenv("DB_PASSWORD")
    db_host: str | None = getenv("DB_HOST")
    db_name: str | None = getenv("DB_NAME")
    
    if db_user is None or db_password is None or db_host is None or db_name is None:
        raise ValueError(
            "Les variables d'environnement DB_USER, DB_PASSWORD, DB_HOST et DB_NAME "
            "doivent être définies (fichier .env ou variables d'environnement système)"
        )
    return True


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
        db_port_env: str | None = getenv("DB_PORT")
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
            self.db_name: str = getenv("DB_NAME", "acfc_db")
            self.db_user: str = getenv("DB_USER", "acfc_user") 
            self.db_password: str = getenv("DB_PASSWORD", "secure_password")
            self.db_host: str = getenv("DB_HOST", "localhost")
            self.api_key_l: str = getenv("API_URL", "default_api_key")
            self.api_secret_l: str = getenv("API_SECRET", "default_api_secret")
        else:
            # Configuration de fallback en cas d'échec de vérification
            self.api_key_l: str = "default_api_key"
            
        # === VALIDATION FINALE DE LA CONFIGURATION ===
        if not all([self.db_user, self.db_password, self.db_host, self.db_name]):
            raise ValueError(
                "Configuration incomplète : Une ou plusieurs variables d'environnement "
                "de base de données (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME) ne sont pas définies."
            )

# ====================================================================
# CONFIGURATION DE LA BASE DE DONNÉES
# ====================================================================

# Instance de configuration globale
conf: Configuration = Configuration()

# Classe de base pour tous les modèles SQLAlchemy
Base = declarative_base()

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
# CONSTANTES DE CLÉS PRIMAIRES POUR RÉFÉRENCES ÉTRANGÈRES
# ====================================================================
# Centralisation des références pour maintenir la cohérence du schéma

PK_CLIENTS = '01_clients.id'           # Référence vers la table clients
PK_ADRESSE = '04_adresse.id'           # Référence vers la table adresses
PK_COMMANDE = '11_commandes.id'        # Référence vers la table commandes
PK_OPERATION = '31_operations.id'      # Référence vers la table opérations comptables
PK_COMPTE = '30_pcg.compte'            # Référence vers le plan comptable général

# ====================================================================
# AUTRES CONSTANTES
# ====================================================================
# Centralisation des références pour maintenir la cohérence du schéma

UNIQUE_ID = 'Identifiant unique'

# ====================================================================
# MODÈLES DE DONNÉES - MODULE UTILISATEURS ET AUTHENTIFICATION
# ====================================================================

class User(Base):
    """
    Modèle représentant un utilisateur du système ACFC.
    
    Gère l'authentification, les autorisations et la sécurité des comptes utilisateurs.
    Inclut des mécanismes de protection contre les attaques par force brute et la
    gestion du cycle de vie des comptes (création, activation, désactivation).
    
    Attributs de sécurité :
        - sha_mdp : Mot de passe haché avec Argon2
        - nb_errors : Compteur d'erreurs d'authentification (protection force brute)
        - is_locked : Verrouillage du compte après trop d'échecs
        - is_chg_mdp : Force le changement de mot de passe à la prochaine connexion
    
    Cycle de vie :
        - created_at : Date de création du compte
        - debut/fin : Période de validité du compte
        - is_active : Statut d'activation du compte
    """
    __tablename__ = "99_users"

    # === IDENTIFIANTS ET INFORMATIONS PERSONNELLES ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True, comment=UNIQUE_ID)
    prenom = mapped_column(String(100), nullable=False, comment="Prénom de l'utilisateur")
    nom = mapped_column(String(100), nullable=False, comment="Nom de famille de l'utilisateur")
    pseudo = mapped_column(String(100), nullable=False, unique=True, comment="Nom d'utilisateur pour connexion")
    email = mapped_column(String(100), nullable=False, unique=True, comment="Adresse email professionnelle")
    telephone = mapped_column(String(20), nullable=False, comment="Numéro de téléphone professionnel")
    
    # === SÉCURITÉ ET AUTHENTIFICATION ===
    sha_mdp = mapped_column(String(255), nullable=False, comment="Mot de passe haché avec Argon2")
    is_chg_mdp = mapped_column(Boolean, default=False, nullable=False, 
                              comment="Force le changement de mot de passe à la prochaine connexion")
    date_chg_mdp = mapped_column(Date, default=func.now(), nullable=False, 
                                 comment="Date du dernier changement de mot de passe")
    nb_errors = mapped_column(Integer, default=0, nullable=False, 
                             comment="Nombre d'erreurs d'authentification consécutives")
    is_locked = mapped_column(Boolean, default=False, nullable=False, 
                             comment="Compte verrouillé après trop d'échecs d'authentification")
    permission = mapped_column(String(10), nullable=False, comment="Habilitations de l'utilisateur")

    # === CYCLE DE VIE ET ACTIVATION ===
    created_at = mapped_column(Date, default=func.now(), nullable=False, comment="Date de création du compte")
    is_active = mapped_column(Boolean, default=True, nullable=False, comment="Compte actif/inactif")
    debut = mapped_column(Date, nullable=False, default=func.now(), comment="Date de début de validité")
    fin = mapped_column(Date, nullable=True, comment="Date de fin de validité (optionnelle)")
    
    def to_dict(self):
        """
        Retourne un dictionnaire représentant l'utilisateur
        """
        user_dict: Dict[str, Any] = {
            'id': self.id,
            'prenom': self.prenom,
            'nom': self.nom,
            'pseudo': self.pseudo,
            'email': self.email,
            'telephone': self.telephone,
            'is_active': self.is_active,
            'is_locked': self.is_locked,
            'permission': self.permission,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'debut': self.debut.isoformat() if self.debut else None,
            'fin': self.fin.isoformat() if self.fin else None
        }
        return user_dict

    def __repr__(self) -> str:
        return f"<User(id={self.id}, pseudo='{self.pseudo}', active={self.is_active})>"

# ====================================================================
# MODÈLES DE DONNÉES - MODULE CRM (CUSTOMER RELATIONSHIP MANAGEMENT)
# ====================================================================

class Client(Base):
    """
    Modèle principal représentant un client dans le système CRM.
    
    Point central de la gestion client qui peut représenter soit un particulier
    soit un professionnel (entreprise, association). Utilise un système de
    polymorphisme avec des tables liées pour gérer les spécificités de chaque
    type de client.
    
    Architecture :
        - Table principale (Client) : Données communes
        - Table Part (Particulier) : Données spécifiques aux personnes physiques
        - Table Pro (Professionnel) : Données spécifiques aux personnes morales
    
    Relations :
        - Un client peut avoir plusieurs emails (table Mail)
        - Un client peut avoir plusieurs téléphones (table Telephone)
        - Un client peut avoir plusieurs adresses (table Adresse)
        - Un client peut passer plusieurs commandes
    """
    __tablename__ = '01_clients'

    # === IDENTIFIANT ET TYPE ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True, comment="Identifiant unique du client")
    type_client = mapped_column(Integer, nullable=False, comment="Type: 1=Particulier, 2=Professionnel")
    
    # === MÉTADONNÉES ===
    created_at = mapped_column(Date, default=func.now(), nullable=False, comment="Date de création du client")
    created_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant créé le client")
    modified_at = mapped_column(Date, default=func.now(), onupdate=func.now(), nullable=False, comment="Date de modification du client")
    modified_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant modifié le client")
    is_active = mapped_column(Boolean, default=True, nullable=False, comment="Client actif/inactif")
    notes = mapped_column(Text, nullable=True, comment="Notes libres sur le client")
    reduces = mapped_column(Numeric(4,3), default=0.10, nullable=False, comment="Réduction appliquée au client")

    # === JONCTION CLIENT ===
    part = relationship("Part", uselist=False, back_populates="client")
    pro = relationship("Pro", uselist=False, back_populates="client")
    tels = relationship("Telephone", back_populates="client")
    mails = relationship("Mail", back_populates="client")
    adresses = relationship("Adresse", back_populates="client")
    commandes = relationship("Commande", back_populates="client")
    factures = relationship("Facture", back_populates="client")

    @property
    def nom_affichage(self) -> str:
        if self.type_client == 1 and self.part:
            return f"{self.part.prenom} {self.part.nom}"
        elif self.type_client == 2 and self.pro:
            return self.pro.raison_sociale
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'objet Client en dictionnaire pour les API JSON.
        
        Returns:
            Dict[str, Any]: Dictionnaire contenant les données du client avec informations d'adresse
        """
        # Récupération de l'adresse principale (première active trouvée)
        adresse_principale = None
        for adresse in self.adresses:
            if adresse.is_active:
                adresse_principale = adresse
                break
        
        return {
            'id': self.id,
            'nom_affichage': self.nom_affichage,
            'type_client': self.type_client,
            'type_client_libelle': 'Particulier' if self.type_client == 1 else 'Professionnel',
            'code_postal': adresse_principale.code_postal if adresse_principale else '',
            'ville': adresse_principale.ville if adresse_principale else '',
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self) -> str:
        client_type = "Particulier" if self.type_client == 1 else "Professionnel"
        return f"<Client(id={self.id}, type={client_type}, active={self.is_active})>"

class Part(Base):
    """
    Modèle représentant les données spécifiques d'un client particulier.
    
    Contient les informations personnelles requises pour l'identification
    et la gestion administrative d'une personne physique.
    
    Conformité RGPD :
        - Données personnelles minimales nécessaires
        - Finalité : Identification et facturation
        - Conservation : Selon réglementation comptable (10 ans)
    """
    __tablename__ = '011_part'

    # === IDENTIFIANT ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True, comment=UNIQUE_ID)
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False, comment="Ref vers le client propriétaire")
    client = relationship("Client", back_populates="part")

    # === INFORMATIONS PERSONNELLES ===
    prenom = mapped_column(String(255), nullable=False, comment="Prénom")
    nom = mapped_column(String(255), nullable=False, comment="Nom de famille")
    
    # === INFORMATIONS D'ÉTAT CIVIL ===
    date_naissance = mapped_column(Date, nullable=True, comment="Date de naissance (vérification majorité)")
    lieu_naissance = mapped_column(String(255), nullable=True, comment="Lieu de naissance")
    
    def __repr__(self) -> str:
        return f"<Part(id={self.id}, nom='{self.nom}', prenom='{self.prenom}')>"

class Pro(Base):
    """
    Modèle représentant les données spécifiques d'un client professionnel.
    
    Gère les informations légales et administratives des personnes morales :
    entreprises, associations, administrations publiques.
    
    Types supportés :
        - Entreprises commerciales (SIREN obligatoire)
        - Associations (RNA optionnel selon statut)
        - Micro-entreprises
        - Administrations publiques
    """
    __tablename__ = '012_pro'

    # === IDENTIFIANT ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True, comment=UNIQUE_ID)
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False, comment="Ref vers le client propriétaire")
    client = relationship("Client", back_populates="pro")

    # === INFORMATIONS LÉGALES ===
    raison_sociale = mapped_column(String(255), nullable=False, comment="Dénomination sociale complète")
    type_pro = mapped_column(Integer, nullable=False, comment="Type: 1=Entreprise, 2=Association, 3=Administration")
    
    # === IDENTIFIANTS OFFICIELS ===
    siren = mapped_column(String(9), nullable=True, comment="Numéro SIREN (9 chiffres) - Obligatoire pour entreprises")
    rna = mapped_column(String(10), nullable=True, comment="Numéro RNA (associations) - Format: W123456789")
    
    def __repr__(self) -> str:
        return f"<Pro(id={self.id}, raison_sociale='{self.raison_sociale}', siren='{self.siren}')>"

# ====================================================================
# MODÈLES DE DONNÉES - MODULE GESTION DES CONTACTS
# ====================================================================

class Mail(Base):
    """
    Modèle de gestion des adresses email des clients.
    
    Permet l'association de plusieurs adresses email par client avec
    typologie et hiérarchisation. Essentiel pour la communication client
    et les campagnes marketing.
    
    Types d'emails supportés :
        - Professionnel : Communication business
        - Personnel : Communication informelle
        - Facturation : Envoi des factures et relances
        - Marketing : Newsletters et promotions
    
    Règles métier :
        - Un seul email principal par client
        - Validation du format email côté application
        - Gestion des bounces et désinscriptions
    """
    __tablename__ = '02_mail'

    # === IDENTIFIANT ET LIAISON CLIENT ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True, comment="Identifiant unique de l'email")
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False, comment="Référence vers le client propriétaire")
    client = relationship("Client", back_populates="mails")

    # === CLASSIFICATION ET DONNÉES ===
    type_mail = mapped_column(String(100), nullable=False, comment="Type: professionnel/personnel/facturation/marketing")
    detail = mapped_column(String(255), nullable=True, comment="Précision libre sur l'usage de cet email")
    mail = mapped_column(String(255), nullable=False, comment="Adresse email (validation format requise)")
    is_principal = mapped_column(Boolean, default=False, nullable=False, 
                                comment="Email principal pour ce client (un seul par client)")
    
    # === MÉTADONNÉES ===
    created_at = mapped_column(Date, default=func.now(), nullable=False)
    created_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant créé l'email")
    modified_at = mapped_column(Date, default=func.now(), onupdate=func.now(), nullable=False)
    modified_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant modifié l'email")
    is_inactive = mapped_column(Boolean, default=False, nullable=False)
    
    def __repr__(self) -> str:
        principal = " (Principal)" if self.is_principal else ""
        return f"<Mail(id={self.id}, client_id={self.id_client}, email='{self.mail}'{principal})>"

class Telephone(Base):
    """
    Modèle de gestion des numéros de téléphone des clients.
    
    Gère les différents moyens de contact téléphonique avec support
    international et classification par usage. Inclut la gestion
    des préférences de contact et horaires d'appel.
    
    Types de téléphones supportés :
        - Fixe professionnel : Numéro principal de l'entreprise
        - Mobile professionnel : Contact direct commercial
        - Fixe personnel : Contact privé (avec autorisation)
        - Mobile personnel : Contact d'urgence
        - Fax : Pour documents officiels
    
    Format international :
        - Indicatif pays (ex: +33 pour France)
        - Numéro local sans préfixe
        - Validation format selon pays
    """
    __tablename__ = '03_telephone'

    # === IDENTIFIANT ET LIAISON CLIENT ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True, comment="Identifiant unique du téléphone")
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False, comment="Référence vers le client propriétaire")
    client = relationship("Client", back_populates="tels")

    # === CLASSIFICATION ===
    type_telephone = mapped_column(String(100), nullable=False, 
                                  comment="Type: fixe_pro/mobile_pro/fixe_perso/mobile_perso/fax")
    detail = mapped_column(String(255), nullable=True, comment="Précision sur l'usage ou horaires de contact")
    
    # === DONNÉES TÉLÉPHONIQUES ===
    indicatif = mapped_column(String(5), nullable=True, comment="Indicatif pays (ex: +33, +1, +49)")
    telephone = mapped_column(String(255), nullable=False, comment="Numéro de téléphone local")
    is_principal = mapped_column(Boolean, default=False, nullable=False)

    # === MÉTADONNÉES ===
    created_at = mapped_column(Date, default=func.now(), nullable=False)
    created_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant créé le téléphone")
    modified_at = mapped_column(Date, default=func.now(), onupdate=func.now(), nullable=False, comment="Date de modification du téléphone")
    modified_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant modifié le téléphone")
    is_inactive = mapped_column(Boolean, default=False, nullable=False)
    
    def __repr__(self) -> str:
        numero_complet = f"{self.indicatif}{self.telephone}" if self.indicatif else self.telephone
        return f"<Telephone(id={self.id}, client_id={self.id_client}, numero='{numero_complet}', type='{self.type_telephone}')>"

class Adresse(Base):
    '''Représente une adresse associée à un client.'''
    __tablename__ = '04_adresse'

    # === IDENTIFIANT ET LIAISON CLIENT ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False)
    client = relationship("Client", back_populates="adresses")
    commandes = relationship("Commande", back_populates="adresse")

    # === DONNÉES D'ADRESSE ===
    adresse_l1 = mapped_column(String(255), nullable=False)
    adresse_l2 = mapped_column(String(255), nullable=True)
    code_postal = mapped_column(String(10), nullable=False)
    ville = mapped_column(String(100), nullable=False)
    pays = mapped_column(String(100), nullable=False, default='France')

    # === MÉTADONNÉES ===
    is_principal = mapped_column(Boolean, default=False, nullable=False, 
                                comment="Adresse principale pour ce client (une seule par client)")
    created_at = mapped_column(Date, default=func.now(), nullable=False)
    created_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant créé l'adresse")
    modified_at = mapped_column(Date, default=func.now(), onupdate=func.now(), nullable=False)
    modified_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant modifié l'adresse")
    is_inactive = mapped_column(Boolean, default=False, nullable=False)

# ====================================================================
# MODÈLES DE DONNÉES - MODULE GESTION DES COMMANDES ET FACTURATION
# ====================================================================

class Commande(Base):
    '''Représente une commande dans le système.'''
    __tablename__ = '11_commandes'

    # === IDENTIFIANT ET LIAISON CLIENT ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False)
    client = relationship("Client", back_populates="commandes")

    # === DONNÉES DE LA COMMANDE ===
    is_ad_livraison = mapped_column(Boolean, default=False, nullable=False)
    id_adresse = mapped_column(Integer, ForeignKey(PK_ADRESSE), nullable=True)
    adresse = relationship("Adresse", back_populates="commandes")
    descriptif = mapped_column(String(255), nullable=True)
    date_commande = mapped_column(Date, default=func.now(), nullable=False)
    montant = mapped_column(Numeric(10, 2), nullable=False, default=0.00)
    devises = relationship("DevisesFactures", back_populates="commande")
    facture = relationship("Facture", back_populates="commande")

    # === ÉTAT DE LA COMMANDE (GLOBAL) ===
    is_annulee = mapped_column(Boolean, default=False, nullable=False)
    is_facture = mapped_column(Boolean, default=False, nullable=False,
                              comment="True quand toute la commande est facturée")
    is_expedie = mapped_column(Boolean, default=False, nullable=False,
                              comment="True quand toute la commande est expédiée")
    
    # === DATES HÉRITÉES (POUR COMPATIBILITÉ) ===
    date_facturation = mapped_column(Date, nullable=True,
                                    comment="Date de première facturation (compatibilité)")
    date_expedition = mapped_column(Date, nullable=True,
                                   comment="Date de première expédition (compatibilité)")
    id_suivi = mapped_column(String(100), nullable=True,
                            comment="Premier numéro de suivi (compatibilité)")

    # === MÉTADONNÉES ===
    created_at = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant créé la commande")
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    modified_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant modifié la commande")

class DevisesFactures(Base):
    '''Représente les éléments des commandes et des factures dans le système.'''
    __tablename__ = '12_devises_factures'

    # === IDENTIFIANT ET LIAISON ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_commande = mapped_column(Integer, ForeignKey(PK_COMMANDE), nullable=False)
    commande = relationship("Commande", back_populates="devises")

    # === DONNÉES DE L'ÉLÉMENT ===
    reference = mapped_column(String(100), nullable=False)
    designation = mapped_column(String(255), nullable=False)
    qte = mapped_column(Integer, nullable=False, default=1)
    prix_unitaire = mapped_column(Numeric(10, 4), nullable=False, default=0.00)
    remise = mapped_column(Numeric(10, 4), nullable=False, default=0.10)
    prix_total = mapped_column(Numeric(10, 4), Computed('qte * prix_unitaire * (1 - remise)'))
    remise_euro = mapped_column(Numeric(10, 4), Computed('qte * prix_unitaire * remise'))
    
    # === ÉTAT DE FACTURATION ET EXPÉDITION ===
    is_facture = mapped_column(Boolean, default=False, nullable=False, 
                              comment="Indique si cette ligne a été facturée")
    id_facture = mapped_column(Integer, nullable=True)
    facture = relationship("Facture", back_populates="composantes_factures", 
                          primaryjoin="foreign(DevisesFactures.id_facture) == Facture.id")
    facture_by = mapped_column(String(100), nullable=True,
                              comment="Utilisateur qui a facturé cette ligne")
    
    is_expedie = mapped_column(Boolean, default=False, nullable=False,
                              comment="Indique si cette ligne a été expédiée")
    id_expedition = mapped_column(String(50), nullable=True,
                                     comment="Numéro d'expédition de cette ligne")
    id_expedition = mapped_column(Integer, ForeignKey('14_expeditions.id'), nullable=True)
    expedition = relationship("Expeditions", back_populates="devises")
    expedie_by = mapped_column(String(100), nullable=True,
                              comment="Utilisateur qui a expédié cette ligne")
    
    # === MÉTADONNÉES ===
    created_by = mapped_column(String(100), nullable=True,
                              comment="Utilisateur qui a créé cette ligne")
    created_at = mapped_column(DateTime, default=func.now(), nullable=False,
                              comment="Date de création de cette ligne")
    modified_by = mapped_column(String(100), nullable=True,
                              comment="Utilisateur qui a modifié cette ligne")
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False,
                              comment="Date de dernière modification")

class Facture(Base):
    '''Représente une facture dans le système.'''
    __tablename__ = '13_factures'

    # === IDENTIFIANT ET LIAISON ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_fiscal = mapped_column(String(20), unique=True)  # Augmenté pour supporter le format YYYY-MM-NNNNNN-C
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False)
    client = relationship("Client", back_populates="factures")
    id_commande = mapped_column(Integer, ForeignKey(PK_COMMANDE), nullable=False)
    commande = relationship("Commande", back_populates="facture")

    # === DONNÉES DE FACTURATION ===
    is_adresse_facturation = mapped_column(Boolean, default=False, nullable=False)
    id_adresse = mapped_column(Integer, ForeignKey(PK_ADRESSE), nullable=False)
    date_facturation = mapped_column(Date, nullable=False, default=func.now())
    montant_facture = mapped_column(Numeric(10, 2), nullable=False, default=0.00)

    # === ÉTAT DE LA FACTURE ===
    is_imprime = mapped_column(Boolean, default=False, nullable=False)
    date_impression = mapped_column(Date, nullable=True)
    is_prestation_facturee = mapped_column(Boolean, default=False, nullable=False)
    composantes_factures = relationship("DevisesFactures", primaryjoin="Facture.id == foreign(DevisesFactures.id_facture)",
                                        back_populates="facture")

    # === MÉTADONNÉES ===
    created_at = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant créé la facture")

    # --- Méthodes de la classe Facture
    def generate_fiscal_id(self) -> str:
        """
        Génère un identifiant fiscal au format YYYY-MM-DD-XXXXXX-C.
        """
        year = self.date_facturation.year
        month = f'{str(self.date_facturation.month).zfill(2)}'
        id_str = f'{str(self.id).zfill(6)}'
        base_code = f'{year}{month}{id_str}'
        cle = self.cle_ean13(base_code)
        return f'{year}-{month}-{id_str}-{cle}'
    
    def cle_ean13(self, base_code: str) -> str:
        """Calcule la clé EAN-13 à partir du code de base de 12 chiffres."""
        # Calcul de la clé EAN-13
        digits = [int(d) for d in base_code if d.isdigit()]
        if len(digits) != 12:
            raise ValueError("Base code must be 12 digits long")

        # Calcul de la clé
        total = sum(d if i % 2 == 0 else d * 3 for i, d in enumerate(digits))
        return str((10 - (total % 10)) % 10)

    @staticmethod
    def set_id_fiscal_after_insert(mapper: Mapper[Any], connection: Connection, target: 'Facture') -> None:
        """Handler after_insert: calcule l'id_fiscal et le persiste via la connexion fournie.

        On passe par une mise à jour SQL pour éviter d'appeler session.commit() depuis un event listener.
        """
        if not getattr(target, 'id_fiscal', None):
            new_id = target.generate_fiscal_id()
            # Mettre à jour la colonne en base
            connection.execute(
                Facture.__table__.update().where(Facture.id == target.id).values(id_fiscal=new_id)
            )
            # Mettre à jour l'instance en mémoire
            target.id_fiscal = new_id

# Enregistrement de l'écouteur qui délègue la logique à la méthode de la classe
event.listen(Facture, 'after_insert', Facture.set_id_fiscal_after_insert)

class Expeditions(Base):
    """Table des expéditions simplifiée"""
    __tablename__ = '14_expeditions'
    
    # === IDENTIFIANT ET LIAISON ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_commande = mapped_column(Integer, ForeignKey('11_commandes.id'), nullable=False)
    devises = relationship("DevisesFactures", back_populates="expedition")

    # === DONNÉES DE L'EXPÉDITION ===
    is_main_propre = mapped_column(Boolean, default=False, nullable=False)
    numero_expedition = mapped_column(String(50), nullable=False)
    date_expedition_remise = mapped_column(Date, nullable=False)

    # === MÉTADONNÉES ===
    created_by = mapped_column(String(50), nullable=True)
    created_at = mapped_column(DateTime, default=func.now())
    modified_by = mapped_column(String(50), nullable=True)
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())

# ====================================================================
# MODÈLES DE DONNÉES - MODULE GESTION DES PRODUITS
# ====================================================================

class Catalogue(Base):
    """
    Classe représentant un catalogue de produits.
    La classe Catalogue gère l'ensemble des produits disponibles à la vente.
    +==================================================+
    ||        ATTENTION                               ||
    ||  Vérifier que les changements sont identiques  ||
    ||  à ceux du fichier d'initialisation init_db.*  ||
    +==================================================+
    """
    __tablename__ = '21_catalogue'

    # === IDENTIFIANT ET LIAISON ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)

    # === DONNÉES DU PRODUIT ===
    type_produit = mapped_column(String(100), nullable=False)
    stype_produit = mapped_column(String(100), nullable=False)
    millesime = mapped_column(Integer, nullable=False)
    prix_unitaire_ht = mapped_column(Numeric(10, 2), nullable=False, default=0.00)
    geographie = mapped_column(String(10), Computed("UPPER(SUBSTRING_INDEX(SUBSTRING_INDEX(stype_produit, ' ', 4), ' ', -1))", persisted=True))
    poids = mapped_column(String(5), Computed("SUBSTRING_INDEX(SUBSTRING_INDEX(stype_produit, ' ', 3), ' ', -1)", persisted=True))

    # === MÉTADONNÉES ===
    created_at = mapped_column(Date, server_default=func.current_date(), nullable=False)
    created_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant créé le produit")
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    modified_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant modifié le produit")

    # === PROPRIÉTÉS CALCULÉES (ref_auto et des_auto) ===
    @property
    def ref_auto(self) -> str:
        """
        Génère la référence automatique (ref_auto) en fonction des données de la ligne.
        Cette logique est également gérée par un trigger dans la base de données.
        """
        return f"{str(self.millesime)[-2:]}{self.type_produit[:4].upper()}{str(self.id).zfill(2)}"

    @property
    def des_auto(self) -> str:
        """
        Génère la description automatique (des_auto) en fonction des données de la ligne.
        Cette logique est également gérée par un trigger dans la base de données.
        """
        return f'{self.stype_produit.upper()} TARIF {self.millesime}'

    def __repr__(self) -> str:
        return f"<Catalogue(id={self.id}, type_produit='{self.type_produit}', ref_auto='{self.ref_auto}')>"

# ====================================================================
# MODÈLES DE DONNÉES - MODULE GESTION COMPTABLE
# ====================================================================

class PCG(Base):
    """Classe représentant un Plan Comptable Général (PCG)."""
    __tablename__ = '30_pcg'

    # === IDENTIFIANT DES COMPTES ===
    classe = mapped_column(Integer, nullable=False)
    categorie_1 = mapped_column(Integer, nullable=False)
    categorie_2 = mapped_column(Integer, nullable=False)
    compte = mapped_column(Integer, primary_key=True)
    denomination = mapped_column(String(100), nullable=False)

class Operations(Base):
    """Classe représentant les opérations comptables."""
    __tablename__ = '31_operations'

    # === IDENTIFIANT DE L'OPÉRATION ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)

    # === DONNEES DE L'OPÉRATION ===
    date_operation = mapped_column(Date, nullable=False)
    libelle_operation = mapped_column(String(100), nullable=False)
    montant_operation = mapped_column(Numeric(10, 2), nullable=False)
    annee_comptable = mapped_column(Integer, nullable=False)

    # === RELATIONS ===
    ventilations = relationship("Ventilations", back_populates="operation")
    documents = relationship("Documents", back_populates="operation")

    # === MÉTADONNÉES ===
    created_at = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant créé l'opération")
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    modified_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant modifié l'opération")
    is_inactive = mapped_column(Boolean, default=False, nullable=False, comment="Opération inactive (soft delete)")

class Ventilations(Base):
    """Classe représentant les ventilations comptables."""
    __tablename__ = '32_ventilations'

    # === IDENTIFIANT ET REFERENCES DE LA VENTILATION ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_operation = mapped_column(Integer, ForeignKey(PK_OPERATION), nullable=False)
    compte_id = mapped_column(Integer, ForeignKey(PK_COMPTE), nullable=False)

    # === DONNEES DE LA VENTILATION ===
    sens = mapped_column(String(10), nullable=False)
    montant_debit = mapped_column(Numeric(10, 2), nullable=True)
    montant_credit = mapped_column(Numeric(10, 2), nullable=True)
    banque = mapped_column(String(100), nullable=True)
    id_facture = mapped_column(String(13), nullable=True)
    id_cheque = mapped_column(String(7), nullable=True)

    # === RELATIONS ===
    compte = relationship('PCG', primaryjoin='Ventilations.compte_id == PCG.compte')
    operation = relationship("Operations", back_populates="ventilations")

    # === MÉTADONNÉES ===
    created_at = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant créé la ventilation")
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    modified_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant modifié la ventilation")
    is_inactive = mapped_column(Boolean, default=False, nullable=False, comment="Ventilation inactive (soft delete)")

class Documents(Base):
    """Classe représentant les documents comptables."""
    __tablename__ = '33_documents'

    # === IDENTIFIANT ET REFECRENCES DU DOCUMENT ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)

    # === DONNEES DU DOCUMENT ===
    id_operation = mapped_column(Integer, ForeignKey(PK_OPERATION), nullable=False)
    type_document = mapped_column(String(50), nullable=True)
    date_document = mapped_column(Date, nullable=True)
    montant_document = mapped_column(Numeric(10, 2), nullable=True)
    document = mapped_column(LargeBinary, nullable=False)

    # === RELATIONS ===
    operation = relationship("Operations", back_populates="documents")

    # === MÉTADONNÉES ===
    created_at = mapped_column(DateTime, default=func.now(), nullable=False)
    created_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant créé le document")
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    modified_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant modifié le document")
    is_inactive = mapped_column(Boolean, default=False, nullable=False, comment="Document inactif (soft delete)")

# ====================================================================
# MODÈLES DE DONNÉES - MODULE GESTION DES STOCKS
# ====================================================================

class Stock(Base):
    """Classe représentant le stock des timbres."""
    __tablename__ = '40_stock'

    type_code = mapped_column(Integer, primary_key=True, nullable=False)     # 1: Francs (FR), 2: Euros (EU), 3: Valeur Permanente France (VPF), 4: Valeur Permanente Europe (VPE), 5: Valeur Permanente Monde (VPM)
    type_valeur = mapped_column(String(3), Computed(
        """
        CASE
            WHEN type_code = 1 THEN 'FR'
            WHEN type_code = 2 THEN 'EU'
            WHEN type_code = 3 THEN 'VPF'
            WHEN type_code = 4 THEN 'VPE'
            WHEN type_code = 5 THEN 'VPM'
            ELSE 'NAN'
        END
        """
    ))
    val_code = mapped_column(String(4), Computed(
        """
        CASE
            WHEN type_code <= 2 THEN LPAD(ROUND(val_valeur * 100), 4, '0')
            ELSE LPAD(SUBSTRING_INDEX(SUBSTRING_INDEX(tvp_poids, ' ', 3), ' ', -1), 4, '0')
        END
        """
    ))
    code_produit = mapped_column(String(6), Computed(
        """
            CONCAT(type_valeur, val_code)
        """
    ))
    val_valeur = mapped_column(Numeric(5, 2), primary_key=True, nullable=False, default=0.00)
    qte = mapped_column(Integer, nullable=False, default=0)
    tvp_valeur = mapped_column(Numeric(5, 2), nullable=True)
    tvp_poids = mapped_column(String(4), nullable=True)
    pu_ht = mapped_column(Numeric(8, 4), Computed(
        """
        CASE
            WHEN type_code >= 3 THEN tvp_valeur
            WHEN type_code = 2 THEN val_valeur
            ELSE val_valeur / 6.55957
        END
        """
    ))
    pt_fr = mapped_column(Numeric(5, 2), Computed(
        """
        CASE
            WHEN type_code = 1 THEN val_valeur * qte
            ELSE 0
        END
        """
    ))
    pt_eu = mapped_column(Numeric(5, 2), Computed(
        """
        CASE
            WHEN type_code = 1 THEN pt_fr / 6.55957
            WHEN type_code = 2 THEN val_valeur * qte
            ELSE qte * tvp_valeur
        END
        """
    ))

# ====================================================================
# MODÈLES DE DONNÉES - MODULE TECHNIQUE
# ====================================================================

class Villes(Base):
    """Classe représentant les villes."""
    __tablename__ = '91_villes'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom = mapped_column(String(100), nullable=False)
    code_postal = mapped_column(Integer, nullable=False)

class IndicatifsTel(Base):
    """Classe représentant les indicatifs téléphoniques."""
    __tablename__ = '92_indicatifs_tel'

    tri = mapped_column(Integer, primary_key=True)
    indicatif = mapped_column(String(4), nullable=False)
    pays = mapped_column(String(100), nullable=False)

class Moi(Base):
    """Classe représentant l'entreprise propriétaire de la base de données."""
    __tablename__ = '93_moi'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom = mapped_column(String(100), nullable=False)
    adresse_l1 = mapped_column(String(255), nullable=False)
    adresse_l2 = mapped_column(String(255), nullable=True)
    code_postal = mapped_column(Integer, nullable=False)
    ville = mapped_column(String(100), nullable=False)
    siret = mapped_column(String(14), nullable=False)
    siren = mapped_column(String(9), Computed(
        """
        CONCAT(SUBSTRING(siret, 1, 9))
        """
    ))
    is_tva_intra = mapped_column(Boolean, nullable=False, default=False)
    id_tva_intra = mapped_column(String(15), nullable=True)
    logo = mapped_column(LargeBinary, nullable=True)
    type_activite = mapped_column(String(100), nullable=False)
    telephone = mapped_column(String(15), nullable=False)
    mail = mapped_column(String(100), nullable=False)
    mois_comptable = mapped_column(Integer, nullable=False)

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
    import time
    from sqlalchemy.exc import OperationalError, DatabaseError
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Tentative {attempt}/{max_retries} de connexion à la base de données...")
            
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
                    f"Impossible de se connecter à la base de données après {max_retries} tentatives. "
                    f"Dernière erreur: {e}"
                ) from e
            
            print(f"⚠️  Tentative {attempt} échouée: {e}")
            print(f"🕒 Nouvelle tentative dans {retry_delay}s...")
            time.sleep(retry_delay)

class MyAccount:
    """
    Classe de gestion du compte utilisateur et des paramètres.

    Fournit des méthodes pour récupérer les informations utilisateur,
    vérifier les permissions, valider les entrées de formulaire et gérer
    les paramètres du compte.
    """
    @staticmethod
    def get_user_or_error(db_session: SessionBdDType, pseudo: str) -> Any:
        """
        Récupère l'utilisateur par son pseudo ou retourne une page d'erreur 400 si non trouvé.
        Args:
            db_session (SessionBdDType): Session de base de données
            pseudo (str): Pseudo de l'utilisateur à récupérer
        Returns:
            User ou page d'erreur 400 si non trouvé
        """
        user: User = db_session.query(User).filter_by(pseudo=pseudo).first()
        if not user:
            return PrepareTemplates.error_4xx(status_code=404, log=True,
                                              status_message=Constants.messages('user', 'not_found'))
        return user

    @staticmethod
    def check_user_permission(pseudo: str) -> Any:
        """
        Vérifie que l'utilisateur connecté a la permission d'accéder au compte demandé.
        Args:
            pseudo (str): Pseudo de l'utilisateur à vérifier
        Raises:
            Forbidden: Si l'utilisateur n'a pas la permission d'accéder au compte
        """
        if session.get('pseudo') != pseudo:
            raise Forbidden("Vous n'êtes pas autorisé à accéder à ce compte.")

    @staticmethod
    def get_request_form(request: Request, user: User) -> str | List[str]:
        """
        Récupère les données du formulaire de la requête.
        Args:
            request (Request): Objet de requête Flask
        Returns:
            Liste des valeurs du formulaire [prenom, nom, email, telephone]
        """
        first_name = request.form.get('prenom', '').strip()
        last_name = request.form.get('nom', '').strip()
        mail = request.form.get('email', '').strip()
        phone = request.form.get('telephone', '').strip()
        _form_return = [first_name, last_name, mail, phone]

        # Retour à la page de paramètres si des champs obligatoires sont vides
        if '' in _form_return:
            return PrepareTemplates.users(subcontext='parameters', objects=[user],
                                              message="Tous les champs sont obligatoires.")
        return [first_name, last_name, mail, phone]

    @staticmethod
    def valid_mail(mail: str, user:User, db_session: SessionBdDType) -> Any:
        """
        Validation de l'adresse email. Retour de la page de paramètre avec un message si invalide.
        Validation que l'email n'est pas déjà utilisé par un autre compte.
        Args:
            mail (str): Adresse email à valider
            user (User): Instance de l'utilisateur actuel
            db_session (SessionBdDType): Session de base de données
        Returns:
            True si l'email est valide et non utilisé, sinon page de paramètre avec message d'erreur
                1. Format invalide
                2. Email déjà utilisé
        """
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'

        if not re.match(email_pattern, mail): return PrepareTemplates.users(
            message="Le format de l'adresse email n'est pas valide.",
            objects=[user],
            subcontext='parameters'
        )
        elif mail != user.email:
            existing_user = db_session.query(User).filter_by(email=mail).first()
            if existing_user: return PrepareTemplates.users(
                message="Cette adresse email est déjà utilisée par un autre compte.",
                objects=[user],
                subcontext='parameters'
            )
        return re.match(email_pattern, mail) is not None
    
    @staticmethod
    def update_user_settings(user: User, data_list: str | List[str]):
        """
        Met à jour les paramètres de l'utilisateur connecté avec les données du formulaire.
        Retourne la page de paramètres avec un message de succès ou d'erreur.
        Returns:
            Page de paramètres avec message de succès ou d'erreur
        """
        # Mise à jour des données utilisateur et de la session
        session['first_name'] = user.prenom = data_list[0]
        session['last_name'] = user.nom = data_list[1]
        session['email'] = user.email = data_list[2]
        session['telephone'] = user.telephone = data_list[3]
    
        return user

class Constants:
    '''
    Classe contenant des constantes utilisées dans l'application.
        - log_files(type_log: str) -> str
    '''
    @staticmethod
    def messages(type_msg: str, second_type_message: str) -> str:
        '''
        Retourne le message en fonction du type.

        Args:
            type_msg (str):
                - 'error_400'
                - 'error_500'
                - 'client'
                - 'phone'
                - 'email'
                - 'address'
                - 'user'
                - 'security'
                - 'commandes'
                - 'factures'
                - 'comptabilite'
                - 'stock'
                - 'commercial'
                - 'warning'
                - 'debug'
                - 'info'
            second_type_message (str):
                - 'error_400': 'wrong_road' + 'not_found' + 'default'
                - 'error_500': 'default'
                - 'client': 'create', 'update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search', 'delete_forbidden'
                - 'phone': 'missing', 'invalid', 'exists', 'valid', 'default'
                - 'email': 'missing', 'invalid', 'exists', 'valid', 'default'
                - 'address': 'missing', 'invalid', 'exists', 'valid', 'default'
                - 'user': 'create', 'update', 'to_update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search'
                - 'security': 'default'
                - 'commandes': 'create', 'update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search'
                - 'factures': 'create', 'update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search'
                - 'comptabilite': 'create', 'update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search'
                - 'stock': 'create', 'update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search'
                - 'commercial': 'create', 'update', 'delete', 'not_found', 'exists', 'list', 'detail', 'form', 'search'
                - 'warning': 'default'
                - 'debug': 'default'
                - 'info': 'default'
        Returns:
            str: Message formaté
        '''
        messages = {
            'error_400': {
                'wrong_road': "Erreur 403 ou 405 : Méthode non autorisée ou droits insuffisants.",
                'not_found': "Erreur 400 ou 404 : La ressource demandée est introuvable.",
                'default': "Erreur 400 : Requête incorrecte."
            },
            'error_500': {
                'default': "Erreur 500 : Une erreur interne est survenue. Veuillez réessayer plus tard."
            },
            'client': {
                'create': "Nouveau client créé avec succès.",
                'update': "Client mis à jour avec succès.",
                'delete': "Client supprimé avec succès.",
                'not_found': "Client non trouvé.",
                'exists': "Le client existe déjà.",
                'list': "Liste des clients chargée avec succès.",
                'detail': "Détails du client affichés avec succès.",
                'form': "Formulaire de client prêt à être rempli.",
                'search': "Résultats de la recherche de clients affichés.",
                'delete_forbidden': "Suppression interdite : Le client a des commandes ou des factures associées de moins de 5 ans."
            },
            'phone': {
                'missing': "Le numéro de téléphone est obligatoire.",
                'invalid': "Le format du numéro de téléphone est invalide.",
                'exists': "Le numéro de téléphone existe déjà.",
                'valid': "Le numéro de téléphone est valide.",
                'default': "Vérification du numéro de téléphone effectuée."
            },
            'email': {
                'missing': "L'adresse email est obligatoire.",
                'invalid': "Le format de l'adresse email est invalide.",
                'exists': "L'adresse email existe déjà.",
                'valid': "L'adresse email est valide.",
                'default': "Vérification de l'adresse email effectuée."
            },
            'address': {
                'missing': "L'adresse est obligatoire.",
                'invalid': "Le format de l'adresse est invalide.",
                'exists': "L'adresse existe déjà.",
                'valid': "L'adresse est valide.",
                'default': "Vérification de l'adresse effectuée."
            },
            'user': {
                'create': "Nouvel utilisateur créé avec succès.",
                'update': "Utilisateur mis à jour avec succès.",
                'to_update': "L'utilisation doit être mis à jour.",
                'delete': "Utilisateur supprimé avec succès.",
                'not_found': "Utilisateur non trouvé.",
                'exists': "Le nom d'utilisateur ou l'email existe déjà.",
                'list': "Liste des utilisateurs chargée avec succès.",
                'detail': "Détails de l'utilisateur affichés avec succès.",
                'form': "Formulaire d'utilisateur prêt à être rempli.",
                'search': "Résultats de la recherche d'utilisateurs affichés."
            },
            'security': {
                'default': "Action de sécurité enregistrée."
            },
            'commandes': {
                'create': "Nouvelle commande créée avec succès.",
                'update': "Commande mise à jour avec succès.",
                'delete': "Commande supprimée avec succès.",
                'not_found': "Commande non trouvée.",
                'exists': "La commande existe déjà.",
                'list': "Liste des commandes chargée avec succès.",
                'detail': "Détails de la commande affichés avec succès.",
                'form': "Formulaire de commande prêt à être rempli.",
                'search': "Résultats de la recherche de commandes affichés."
            },
            'factures': {
                'create': "Nouvelle facture créée avec succès.",
                'update': "Facture mise à jour avec succès.",
                'delete': "Facture supprimée avec succès.",
                'not_found': "Facture non trouvée.",
                'exists': "La facture existe déjà.",
                'list': "Liste des factures chargée avec succès.",
                'detail': "Détails de la facture affichés avec succès.",
                'form': "Formulaire de facture prêt à être rempli.",
                'search': "Résultats de la recherche de factures affichés."
            },
            'comptabilite': {
                'create': "Nouvelle opération comptable créée avec succès.",
                'update': "Opération comptable mise à jour avec succès.",
                'delete': "Opération comptable supprimée avec succès.",
                'not_found': "Opération comptable non trouvée.",
                'exists': "L'opération comptable existe déjà.",
                'list': "Liste des opérations comptables chargée avec succès.",
                'detail': "Détails de l'opération comptable affichés avec succès.",
                'form': "Formulaire d'opération comptable prêt à être rempli.",
                'search': "Résultats de la recherche d'opérations comptables affichés."
            },
            'stock': {
                'update': "Stock mis à jour avec succès.",
                'not_found': "Produit en stock non trouvé.",
                'list': "Liste des produits en stock chargée avec succès.",
                'detail': "Détails du produit en stock affichés avec succès.",
                'form': "Formulaire de produit en stock prêt à être rempli.",
                'search': "Résultats de la recherche de produits en stock affichés."
            },
            'commercial': {
                'create': "Nouvelle cible commerciale créée avec succès.",
                'update': "Cible commerciale mise à jour avec succès.",
                'delete': "Cible commerciale supprimée avec succès.",
                'not_found': "Cible commerciale non trouvée.",
                'exists': "La cible commerciale existe déjà.",
                'list': "Liste des cibles commerciales chargée avec succès.",
                'detail': "Détails de la cible commerciale affichés avec succès.",
                'form': "Formulaire de cible commerciale prêt à être rempli.",
                'search': "Résultats de la recherche de cibles commerciales affichés."
            },
            'warning': {
                'default': "Avertissement : Veuillez vérifier les informations fournies."
            },
            'debug': {
                'default': "Debug : Informations de débogage enregistrées."
            },
            'info': {
                'default': "Info : Opération effectuée avec succès."
            }
        }
        type_messages = messages.get(type_msg, {})
        return type_messages.get(second_type_message, "Action effectuée.")

    @staticmethod
    def log_files(type_log: str) -> str:
        '''
        Retourne le nom du fichier de log en fonction du type.

        Args:
            type_log (str):
                - '400'
                - '500'
                - 'client'
                - 'user'
                - 'security'
                - 'commandes'
                - 'factures'
                - 'comptabilite'
                - 'stock'
                - 'commercial'
                - 'warning'
                - 'debug'
                - 'info'
        Returns:
            str: Nom du fichier de log
        '''
        log_files = {
            '400': 'error_400.log',
            '500': 'error_500.log',
            'client': 'client.log',
            'user': 'users.log',
            'security': 'security.log',
            'commandes': 'commandes.log',
            'factures': 'factures.log',
            'comptabilite': 'comptabilite.log',
            'stock': 'stock.log',
            'commercial': 'commercial.log',
            'warning': 'warning.log',
            'debug': 'debug.log',
            'info': 'info.log'
        }
        return log_files.get(type_log, 'general.log')
    
    @staticmethod
    def templates(name: str) -> str:
        '''
        Retourne le nom du template en fonction du nom fourni.

        Args:
            name (str):
                - 'base' + '400' + '500' + 'default' + 'footer' + 'header' + 'login' + 'main'
                - 'admin' + 'adm-chg-pwd' + 'adm-users'
                - 'catalogue'
                - 'clients' + 'client-detail' + 'client-form' + 'client-search'
                - 'commandes' + 'commande-detail' + 'commande-form' + 'commande-print' + 'factures' + 'facture-print'
                - 'commercial' + 'commercial-clt-target'
                - 'comptabilite'
                - 'dashboard' + 'dashboard-cmd' + 'dashboard-fact' + 'dashboard-stock' + 'dashboard-commercial'
                - 'users'
        Returns:
            str: Nom du template
        '''
        templates = {
            'base': 'base.html',
                '400': '400.html',
                '500': '500.html',
                'default': 'default.html',
                'footer': 'footer.html',
                'header': 'header.html',
                'login': 'login.html',
                'main': 'main.html',
            'admin': 'admin/admin.html',
                'adm-chg-pwd': 'admin/change_password.html',
                'adm-users': 'admin/users.html',
            'catalogue': 'catalogue/catalogue.html',
            'clients': 'clients/clients.html',
                'client-detail': 'clients/client_detail.html',
                'client-form': 'clients/client_form.html',
                'client-search': 'clients/client_search.html',
            'commandes': 'commandes/commandes.html',
                'commande-detail': 'commandes/commande_detail_content.html',
                'commande-form': 'commandes/commande_form_content.html',
                'commande-print': 'commandes/commande_bon_impression.html',
                'factures': 'commandes/factures_details.html',
                'facture-print': 'commandes/facture_impression.html',
            'commercial': 'commercial/commercial.html',
                'commercial-clt-target': 'commercial/commercial_clients_target.html',
            'comptabilite': 'comptabilite/comptabilite.html',
            'dashboard': 'default.html',
                'dashboard-cmd': 'dashboard/commandes_en_cours.html',
                'dashboard-fact': 'dashboard/factures_en_cours.html',
                'dashboard-stock': 'dashboard/stock_alert.html',
                'dashboard-commercial': 'dashboard/indicateurs_commerciaux.html',
            'users': 'users.html',
        }
        return templates.get(name, '')
    
    @staticmethod
    def return_pages(domain: str, sub_domain: str) -> str:
        '''
        Retourne le nom du template de la page en fonction du domaine et du sous-domaine.

        Args:
            domain (str):
                - 'admin'
                - 'clients'
                - 'commandes'
                - 'comptabilite'
                - 'commercial'
                - 'factures'
                - 'stock'
                - 'users'
            sub_domain (str):
                - admin :
                    - 'accueil'
                    - 'logs-dashboard'
                    - 'logs-export'
                - clients :
                    - 'recherche'
                    - 'recherche-api'
                    - 'creation'
                    - 'detail'
                    - 'modifier-get'
                    - 'modifier-post'
                    - 'phone-add'
                    - 'mail-add'
                - commandes :
                    - 'commande-detail'
                    - 'commande-form'
                    - 'commande-print'
                    - 'factures'
                    - 'commercial-clt-target'
                - commercial :
                    - 'accueil'
                    - 'filtrage'
                    - 'filtrage-api'
                - comptabilite :
                    - 'accueil'
                - factures : {}
                - stocks :
                    - 'accueil'
                - users : {}
                - catalogue :
                    - 'accueil'
        Returns:
            str: Nom du template de la page
        '''
        pages: Dict[str, Dict[str, str]] = {
            'admin': {
                'accueil': 'admin.admin_list',
                'logs-dashboard': 'admin.logs_dashboard',
                'logs-export': 'admin.logs_export',
            },
            'clients': {
                'recherche': 'clients.clients_list',
                'recherche-api': 'clients.recherche_avancee',
                'creation': 'clients.create_client',
                'detail': 'clients.get_client',
                'modifier-get': 'clients.edit_client',
                'modifier-post': 'clients.update_client',
                'supprimer': 'clients.delete_client',
                'phone-add': 'clients.add_phone',
                'mail-add': 'clients.add_email',
                'address-add': 'clients.add_address',
                'phone-del': 'clients.del_phone',
                'mail-del': 'clients.del_email',
                'address-del': 'clients.del_address',
                'phone-mod': 'clients.mod_phone',
                'mail-mod': 'clients.mod_email',
                'address-mod': 'clients.mod_address',
            },
            'commandes': {
                'commande-detail': 'commandes.commande_detail',
                'commande-form': 'commandes.commande_form',
                'commande-print': 'commandes.commande_print',
                'factures': 'commandes.factures',
            },
            'commercial': {
                'accueil': 'commercial.commercial_index',
                'filtrage': 'commercial.clients_liste',
                'filtrage-api': 'commercial.clients_api_search',
            },
            'comptabilite': {
                'accueil': 'comptabilite.comptabilite_index',
            },
            'factures': {},
            'stocks': {
                'accueil': 'stocks.stocks_index',
            },
            'users': {},
            'catalogue':{
                'accueil': 'catalogue.index',
            }
        }
        return pages.get(domain, {}).get(sub_domain, '')

class PrepareTemplates:
    '''
    Classe statique pour la préparation des templates de pages.
    Fournit des méthodes pour générer les templates de différentes pages.
    Utilisation:
        - PrepareTemplates.login(message="Bienvenue", context="login")
        - PrepareTemplates.clients(message="Liste des clients")
        - PrepareTemplates.users(message="Gestion des utilisateurs", objects=user_list)
    '''
    BASE: str = Constants.templates('base')

    @staticmethod
    def login(message: Optional[str]=None, subcontext: str='login', log: bool=False, **kwargs: Any) -> str:
        '''
        Génère le template de la page de login.

        Args:
            message (Optional[str]): Message à afficher sur la page de login.
        Returns:
            str: Template de la page de login
        '''
        if log:
            acfc_log.log(level=INFO, message=message or '',
                         specific_logger=Constants.log_files('user'),
                         user=session.get('pseudo', 'N/A'), db_log=True)
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Authentification',
                               context='login',
                               subcontext=subcontext,
                               message=message,
                               **kwargs)

    @staticmethod
    def admin(message: Optional[str]=None, log: bool=False, **kwargs: Any) -> str:
        '''
        Génère le template de la page d'administration.

        Args:
            message (Optional[str]): Message à afficher sur la page d'administration.
        Returns:
            str: Template de la page d'administration
        '''
        if log:
            acfc_log.log(level=INFO, message=message or '',
                         specific_logger=Constants.log_files('security'),
                         user=session.get('pseudo', 'N/A'), db_log=True)
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Administration',
                               context='admin',
                               today=datetime.now().strftime('%Y-%m-%d'),
                               **kwargs)

    @staticmethod
    def clients(sub_context: Optional[str]=None, message: Optional[str]=None, log: bool=False, **kwargs: Any) -> str:
        '''
        Génère le template de la page clients.

        Args:
            message (Optional[str]): Message à afficher sur la page clients.
        Returns:
            str: Template de la page clients
        '''
        if log:
            acfc_log.log(level=INFO, message=message or '',
                         specific_logger=Constants.log_files('client'),
                         user=session.get('pseudo', 'N/A'), db_log=True)
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Gestion Clients',
                               context='clients',
                               message=message,
                               subcontext=sub_context,
                               **kwargs)

    @staticmethod
    def users(subcontext: Optional[str]=None, message: Optional[str]=None, log: bool=False, **kwargs: Any) -> str:
        '''
        Génère le template de la page utilisateurs.

        Args:
            message (Optional[str]): Message à afficher sur la page utilisateurs.
        Returns:
            str: Template de la page utilisateurs
        '''
        if log:
            acfc_log.log(level=INFO, message=message or '',
                         specific_logger=Constants.log_files('user'),
                         user=session.get('pseudo', 'N/A'), db_log=True)
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Administration Utilisateurs',
                               context='user',
                               message=message,
                               subcontext=subcontext,
                               **kwargs)

    @staticmethod
    def default(objects: Optional[List[Any]], message: Optional[str]=None) -> str:
        '''
        Génère le template de la page par défaut.

        Args:
            message (Optional[str]): Message à afficher sur la page par défaut.
        Returns:
            str: Template de la page par défaut
        '''
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Accueil',
                               context='default',
                               message=message,
                               objects=objects)

    @staticmethod
    def error_4xx(status_code: int, status_message: str, log: bool=False, specific_log: Optional[str]=None) -> str:
        '''
        Génère le template de la page d'erreur 4xx.

        Args:
            message (Optional[str]): Message à afficher sur la page d'erreur.
        Returns:
            str: Template de la page d'erreur 4xx
        '''
        username = session.get('pseudo', 'N/A')
        message = Constants.messages('error_400', 'default') \
                    + f'\ncode erreur : {status_code}' \
                    + f'\ndescription : {status_message}'
        if log:
            acfc_log.log(level=ERROR, message=message,
                         specific_logger=Constants.log_files(specific_log or '400'),
                         db_log=True, user=username or 'N/A')
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Erreur chez vous',
                               context='400', message=message,
                               status_code=status_code,
                               status_message=status_message)

    @staticmethod
    def error_5xx(status_code: int, status_message: str, log: bool=False, specific_log: Optional[str]=None) -> str:
        '''
        Génère le template de la page d'erreur 5xx.

        Args:
            message (Optional[str]): Message à afficher sur la page d'erreur.
        Returns:
            str: Template de la page d'erreur 5xx
        '''
        username = session.get('pseudo', 'N/A')
        message = Constants.messages('error_500', 'default') \
                    + f'\ncode erreur : {status_code}' \
                    + f'\ndescription : {status_message}'
        if log:
            acfc_log.log(level=ERROR, message=message or '',
                         specific_logger=Constants.log_files(specific_log or '500'),
                         db_log=True, user=username)
        return render_template(PrepareTemplates.BASE,
                               title='ACFC - Erreur chez nous',
                               context='500', message=message,
                               status_code=status_code,
                               status_message=status_message)
