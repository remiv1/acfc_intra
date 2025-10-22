from sqlalchemy import (
    Integer, String, Date, DateTime, Boolean, Text, Numeric, event, Computed,
    LargeBinary, ForeignKey, text
    )
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session as SessionBdDType, scoped_session, sessionmaker, Mapper, relationship, mapped_column
from sqlalchemy.orm.session import Session as SessionBdDType
from typing import Any, Dict, List
from sqlalchemy.engine import Connection
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from flask import g
from dotenv import load_dotenv
from os import getenv
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
PK_FACTURE = '12_factures.id'          # Référence vers la table factures
PK_OPERATION = '31_operations.id'      # Référence vers la table opérations comptables
PK_COMPTE = '30_pcg.compte'            # Référence vers le plan comptable général
PK_EXPEDITION = '14_expeditions.id'     # Référence vers la table expéditions

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
    created_at = mapped_column(DateTime, default=func.now(), nullable=False, comment="Date de création du client")
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
    commandes = relationship("Order", back_populates="client")
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
            if not adresse.is_inactive:
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
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    modified_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant modifié l'email")
    is_inactive = mapped_column(Boolean, default=False, nullable=False)
    
    def __repr__(self) -> str:
        principal = " (Principal)" if self.is_principal else ""
        return f"<Mail(id={self.id}, client_id={self.id_client}, email='{self.mail}'{principal})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Retourne un dictionnaire représentant l'email
        """
        return {
            'id': self.id,
            'id_client': self.id_client,
            'type_mail': self.type_mail,
            'detail': self.detail,
            'mail': self.mail,
            'is_principal': self.is_principal,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'modified_by': self.modified_by,
            'is_inactive': self.is_inactive
        }

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
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="Date de modification du téléphone")
    modified_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant modifié le téléphone")
    is_inactive = mapped_column(Boolean, default=False, nullable=False)
    
    def __repr__(self) -> str:
        numero_complet = f"{self.indicatif}{self.telephone}" if self.indicatif else self.telephone
        return f"<Telephone(id={self.id}, client_id={self.id_client}, numero='{numero_complet}', type='{self.type_telephone}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Retourne un dictionnaire représentant le téléphone
        """
        return {
            'id': self.id,
            'id_client': self.id_client,
            'type_telephone': self.type_telephone,
            'detail': self.detail,
            'indicatif': self.indicatif,
            'telephone': self.telephone,
            'is_principal': self.is_principal,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'modified_by': self.modified_by,
            'is_inactive': self.is_inactive
        }

class Adresse(Base):
    '''Représente une adresse associée à un client.'''
    __tablename__ = '04_adresse'

    # === IDENTIFIANT ET LIAISON CLIENT ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False)
    client = relationship("Client", back_populates="adresses")
    commandes_livrees = relationship("Order", back_populates="adresse_livraison",
                                     foreign_keys='Order.id_adresse_livraison')
    commandes_facturees = relationship("Order", back_populates="adresse_facturation",
                                      foreign_keys='Order.id_adresse_facturation')

    # === DONNÉES D'ADRESSE ===
    adresse_l1 = mapped_column(String(255), nullable=False)
    adresse_l2 = mapped_column(String(255), nullable=True)
    code_postal = mapped_column(String(10), nullable=False)
    ville = mapped_column(String(100), nullable=False)
    pays = mapped_column(String(100), nullable=False, default='France')
    detail = mapped_column(String(255), nullable=True, comment="Précision libre sur l'adresse")

    # === MÉTADONNÉES ===
    is_principal = mapped_column(Boolean, default=False, nullable=False,
                                comment="Adresse principale pour ce client (une seule par client)")
    created_at = mapped_column(Date, default=func.now(), nullable=False)
    created_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant créé l'adresse")
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    modified_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant modifié l'adresse")
    is_inactive = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Adresse(id={self.id}, client_id={self.id_client}, cp/ville={self.code_postal} " + \
            f"'{self.ville.capitalize()}', {'Principale' if self.is_principal else 'Secondaire'})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Retourne un dictionnaire représentant l'adresse
        """
        return {
            'id': self.id,
            'id_client': self.id_client,
            'adresse_l1': self.adresse_l1,
            'adresse_l2': self.adresse_l2,
            'code_postal': self.code_postal,
            'ville': self.ville,
            'pays': self.pays,
            'is_principal': self.is_principal,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'modified_by': self.modified_by,
            'is_inactive': self.is_inactive
        }

# ====================================================================
# MODÈLES DE DONNÉES - MODULE GESTION DES COMMANDES ET FACTURATION
# ====================================================================

class Order(Base):
    '''
    Représente une commande dans le système.
    Gère les informations de la commande, son état,
    les adresses de livraison et facturation, ainsi que les
    articles commandés.
    '''
    __tablename__ = '11_commandes'

    # === IDENTIFIANT ET LIAISON CLIENT ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False)
    client = relationship("Client", back_populates="commandes")

    # === DONNÉES DE LA COMMANDE ===
    is_ad_livraison = mapped_column(Boolean, default=False, nullable=False)
    id_adresse_livraison = mapped_column(Integer, ForeignKey(PK_ADRESSE), nullable=True)
    adresse_livraison = relationship("Adresse", foreign_keys=[id_adresse_livraison], back_populates="commandes_livrees")
    id_adresse_facturation = mapped_column(Integer, ForeignKey(PK_ADRESSE), nullable=True)
    adresse_facturation = relationship("Adresse", foreign_keys=[id_adresse_facturation], back_populates="commandes_facturees")
    descriptif = mapped_column(String(255), nullable=True)
    date_commande = mapped_column(Date, default=func.now(), nullable=False)
    montant = mapped_column(Numeric(10, 2), nullable=False, default=0.00)
    devises = relationship("DevisesFactures", back_populates="commande")
    facture = relationship("Facture", back_populates="commande")

    # === ÉTAT DE LA COMMANDE (GLOBAL) ===
    is_annulee = mapped_column(Boolean, default=False, nullable=False)
    is_expediee = mapped_column(Boolean, default=False, nullable=False,
                              comment="True quand toute la commande est expédiée")
    is_facturee = mapped_column(Boolean, default=False, nullable=False,
                              comment="True quand toute la commande est facturée")
    
    # === DATES HÉRITÉES (POUR COMPATIBILITÉ) ===
    date_expedition = mapped_column(Date, nullable=True,
                                   comment="Date de dernière expédition (compatibilité)")
    date_facturation = mapped_column(Date, nullable=True,
                                    comment="Date de dernière facturation (compatibilité)")

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
    id_order = mapped_column(Integer, ForeignKey(PK_COMMANDE), nullable=False)
    commande = relationship("Order", back_populates="devises")

    # === DONNÉES DE L'ÉLÉMENT ===
    reference = mapped_column(String(100), nullable=False)
    designation = mapped_column(String(255), nullable=False)
    qte = mapped_column(Integer, nullable=False, default=1)
    prix_unitaire = mapped_column(Numeric(10, 4), nullable=False, default=0.00)
    remise = mapped_column(Numeric(10, 4), nullable=False, default=0.10)
    prix_total = mapped_column(Numeric(10, 4), Computed('qte * prix_unitaire * (1 - remise)'))
    remise_euro = mapped_column(Numeric(10, 4), Computed('qte * prix_unitaire * remise'))
    is_annulee = mapped_column(Boolean, default=False, nullable=False)
    
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
    id_expedition = mapped_column(Integer, ForeignKey(PK_EXPEDITION), nullable=True)
    expedition = relationship("Expeditions", back_populates="devises_factures",
                              primaryjoin="foreign(DevisesFactures.id_expedition) == Expeditions.id")
    expedie_by = mapped_column(String(100), nullable=True,
                              comment="Utilisateur qui a expédié cette ligne")
    
    # === MÉTADONNÉES ===
    created_at = mapped_column(DateTime, default=func.now(), nullable=False,
                              comment="Date de création de cette ligne")
    created_by = mapped_column(String(100), nullable=True,
                              comment="Utilisateur qui a créé cette ligne")
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False,
                              comment="Date de dernière modification")
    modified_by = mapped_column(String(100), nullable=True,
                              comment="Utilisateur qui a modifié cette ligne")
    
    def __repr__(self) -> str:
        """
        Représentation sous forme de chaîne de l'objet DevisesFactures
        lors de l'utilisation de print() ou dans le shell.
        """
        return f"<DevisesFactures(id={self.id}, commande_id={self.id_order}, reference='{self.reference}', qte={self.qte}, prix_total={self.prix_total})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Retourne un dictionnaire représentant l'élément de commande/facture
        """
        return {
            'id': self.id,
            'id_order': self.id_order,
            'reference': self.reference,
            'designation': self.designation,
            'qte': self.qte,
            'prix_unitaire': float(self.prix_unitaire),
            'remise': float(self.remise),
            'prix_total': float(self.prix_total) if self.prix_total is not None else None,
            'remise_euro': float(self.remise_euro) if self.remise_euro is not None else None,
            'is_annulee': self.is_annulee,
            'is_facture': self.is_facture,
            'id_facture': self.id_facture,
            'facture_by': self.facture_by,
            'is_expedie': self.is_expedie,
            'id_expedition': self.id_expedition,
            'expedie_by': self.expedie_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'modified_by': self.modified_by
        }
    
    @classmethod
    def to_obj(cls, data: Dict[str, Any]) -> 'DevisesFactures':
        """
        Crée une instance DevisesFactures à partir d'un dictionnaire.
        
        Args:
            data (Dict[str, Any]): Dictionnaire contenant les données de l'élément
        
        Returns:
            DevisesFactures: Instance créée avec les données fournies
        """
        return cls(
            id=data.get('id', None),
            id_order=data.get('id_order', None),
            reference=data.get('reference', None),
            designation=data.get('designation', None),
            qte=data.get('qte', 1),
            prix_unitaire=data.get('prix_unitaire', 0.00),
            remise=data.get('remise', 0.10),
            is_annulee=data.get('is_annulee', False),
            is_facture=data.get('is_facture', False),
            id_facture=data.get('id_facture', None),
            facture_by=data.get('facture_by', None),
            is_expedie=data.get('is_expedie', False),
            id_expedition=data.get('id_expedition', None),
            expedie_by=data.get('expedie_by', None),
            created_by=data.get('created_by', None),
            modified_by=data.get('modified_by', None)
        )

class Facture(Base):
    '''Représente une facture dans le système.'''
    __tablename__ = '13_factures'

    # === IDENTIFIANT ET LIAISON ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_fiscal = mapped_column(String(20), unique=True)  # Augmenté pour supporter le format YYYY-MM-NNNNNN-C
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False)
    client = relationship("Client", back_populates="factures")
    id_order = mapped_column(Integer, ForeignKey(PK_COMMANDE), nullable=False)
    commande = relationship("Order", back_populates="facture")

    # === DONNÉES DE FACTURATION ===
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
    id_devises_factures = mapped_column(Integer, ForeignKey('12_devises_factures.id'), nullable=False)
    devises_factures = relationship("DevisesFactures", back_populates="expedition",
                                     primaryjoin="Expeditions.id == foreign(DevisesFactures.id_expedition)")
    
    # === DONNÉES DE CONTRÔLE QUALITE ===
    #TODO: Ajouter les champs de formulaire sur l'expédition
    c_qualite = mapped_column(Text, nullable=True, comment="Détail de la préparation de commande")

    # === DONNÉES DE L'EXPÉDITION ===
    is_main_propre = mapped_column(Boolean, default=False, nullable=False)
    numero_expedition = mapped_column(String(50), nullable=True)
    date_expedition_remise = mapped_column(Date, nullable=False)

    # === MÉTADONNÉES ===
    created_at = mapped_column(DateTime, default=func.now())
    created_by = mapped_column(String(100), nullable=True)
    modified_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    modified_by = mapped_column(String(100), nullable=True)

# ====================================================================
# MODÈLES DE DONNÉES - MODULE GESTION DES PRODUITS
# ====================================================================

class Catalogue(Base):
    """
    Classe représentant un catalogue de produits.
    La classe Catalogue gère l'ensemble des produits disponibles à la vente.
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
    created_by = mapped_column(String(100), default='system', nullable=False, comment="Utilisateur ayant créé le produit")
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
    code_postal = mapped_column(String(10), nullable=False)

class IndicatifsTel(Base):
    """Classe représentant les indicatifs téléphoniques."""
    __tablename__ = '92_indicatifs_tel'

    id = mapped_column(Integer, primary_key=True)
    indicatif = mapped_column(String(4), nullable=False)
    pays = mapped_column(String(100), nullable=False)

class Moi(Base):
    """Classe représentant l'entreprise propriétaire de la base de données."""
    __tablename__ = '93_moi'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom = mapped_column(String(100), nullable=False)
    adresse_l1 = mapped_column(String(255), nullable=False)
    adresse_l2 = mapped_column(String(255), nullable=True)
    code_postal = mapped_column(String(10), nullable=False)
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
