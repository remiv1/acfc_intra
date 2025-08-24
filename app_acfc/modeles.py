from sqlalchemy import Integer, String, Date, Boolean, Text, Numeric, event, Computed, LargeBinary, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapper, relationship, mapped_column
from typing import Any
from sqlalchemy.engine import Connection
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
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
    load_dotenv()
    db_user: str | None = getenv("DB_USER")
    db_password: str | None = getenv("DB_PASSWORD")
    db_host: str | None = getenv("DB_HOST")
    db_name: str | None = getenv("DB_NAME")
    
    if db_user is None or db_password is None or db_host is None or db_name is None:
        raise ValueError(
            "Les variables d'environnement DB_USER, DB_PASSWORD, DB_HOST et DB_NAME "
            "doivent être définies dans le fichier .env"
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
        load_dotenv()
        
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

# Création automatique des tables si elles n'existent pas
Base.metadata.create_all(engine)

# Factory de sessions pour l'accès aux données
SessionBdD = sessionmaker(
    autocommit=False,                   # Transactions manuelles pour meilleur contrôle
    autoflush=False,                    # Flush manuel pour optimiser les performances
    bind=engine                         # Liaison à l'engine configuré
)

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
    
    # === CYCLE DE VIE ET ACTIVATION ===
    created_at = mapped_column(Date, default=func.now(), nullable=False, comment="Date de création du compte")
    is_active = mapped_column(Boolean, default=True, nullable=False, comment="Compte actif/inactif")
    debut = mapped_column(Date, nullable=False, default=func.now(), comment="Date de début de validité")
    fin = mapped_column(Date, nullable=True, comment="Date de fin de validité (optionnelle)")
    
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
    is_active = mapped_column(Boolean, default=True, nullable=False, comment="Client actif/inactif")
    notes = mapped_column(Text, nullable=True, comment="Notes libres sur le client")

    # === JONCTION CLIENT ===
    part = relationship("Part", uselist=False, back_populates="01_clients")
    pro = relationship("Pro", uselist=False, back_populates="01_clients")
    tels = relationship("Telephone", back_populates="01_clients")
    mails = relationship("Mail", back_populates="01_clients")
    adresses = relationship("Adresse", back_populates="01_clients")
    commandes = relationship("Commande", back_populates="01_clients")
    factures = relationship("Facture", back_populates="01_clients")

    @property
    def nom_affichage(self) -> str:
        if self.type_client == 1 and self.part:
            return f"{self.part.prenom} {self.part.nom}"
        elif self.type_client == 2 and self.pro:
            return self.pro.raison_sociale
        return ""
    
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
    
    # === INFORMATIONS PERSONNELLES ===
    prenom = mapped_column(String(255), nullable=False, comment="Prénom")
    nom = mapped_column(String(255), nullable=False, comment="Nom de famille")
    
    # === INFORMATIONS D'ÉTAT CIVIL ===
    date_naissance = mapped_column(Date, nullable=False, comment="Date de naissance (vérification majorité)")
    lieu_naissance = mapped_column(String(255), nullable=False, comment="Lieu de naissance")
    
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
    
    # === CLASSIFICATION ET DONNÉES ===
    type_mail = mapped_column(String(100), nullable=False, comment="Type: professionnel/personnel/facturation/marketing")
    detail = mapped_column(String(255), nullable=True, comment="Précision libre sur l'usage de cet email")
    mail = mapped_column(String(255), nullable=False, comment="Adresse email (validation format requise)")
    is_principal = mapped_column(Boolean, default=False, nullable=False, 
                                comment="Email principal pour ce client (un seul par client)")
    
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
    id_client = mapped_column(Integer, nullable=False, comment="Référence vers le client propriétaire")
    
    # === CLASSIFICATION ===
    type_telephone = mapped_column(String(100), nullable=False, 
                                  comment="Type: fixe_pro/mobile_pro/fixe_perso/mobile_perso/fax")
    detail = mapped_column(String(255), nullable=True, comment="Précision sur l'usage ou horaires de contact")
    
    # === DONNÉES TÉLÉPHONIQUES ===
    indicatif = mapped_column(String(5), nullable=True, comment="Indicatif pays (ex: +33, +1, +49)")
    telephone = mapped_column(String(255), nullable=False, comment="Numéro de téléphone local")
    is_principal = mapped_column(Boolean, default=False, nullable=False)
    
    def __repr__(self) -> str:
        numero_complet = f"{self.indicatif}{self.telephone}" if self.indicatif else self.telephone
        return f"<Telephone(id={self.id}, client_id={self.id_client}, numero='{numero_complet}', type='{self.type_telephone}')>"

class Adresse(Base):
    '''Représente une adresse associée à un client.'''
    __tablename__ = '04_adresse'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False)
    adresse_l1 = mapped_column(String(255), nullable=False)
    adresse_l2 = mapped_column(String(255), nullable=True)
    code_postal = mapped_column(String(10), nullable=False)
    ville = mapped_column(String(100), nullable=False)
    created_at = mapped_column(Date, default=func.now(), nullable=False)
    is_active = mapped_column(Boolean, default=True, nullable=False)

# ====================================================================
# MODÈLES DE DONNÉES - MODULE GESTION DES COMMANDES ET FACTURATION
# ====================================================================

class Commande(Base):
    '''Représente une commande dans le système.'''
    __tablename__ = '11_commandes'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_client = mapped_column(Integer, ForeignKey('clients.id'), nullable=False)
    is_ad_livraison = mapped_column(Boolean, default=False, nullable=False)
    id_adresse = mapped_column(Integer, ForeignKey('adresses.id'), nullable=True)
    descriptif = mapped_column(String(255), nullable=True)
    date_commande = mapped_column(Date, default=func.now(), nullable=False)
    montant = mapped_column(Numeric(10, 2), nullable=False, default=0.00)
    is_facture = mapped_column(Boolean, default=False, nullable=False)
    date_facturation = mapped_column(Date, nullable=True)
    is_expedie = mapped_column(Boolean, default=False, nullable=False)
    date_expedition = mapped_column(Date, nullable=True)
    id_suivi = mapped_column(String(100), nullable=True)

class DevisesFactures(Base):
    '''Représente les éléments des commandes et des factures dans le système.'''
    __tablename__ = '12_devises_factures'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_commande = mapped_column(Integer, ForeignKey(PK_COMMANDE), nullable=False)
    id_facture = mapped_column(Integer, nullable=True)
    reference = mapped_column(String(100), nullable=False)
    designation = mapped_column(String(255), nullable=False)
    qte = mapped_column(Integer, nullable=False, default=1)
    prix_unitaire = mapped_column(Numeric(10, 4), nullable=False, default=0.00)
    remise = mapped_column(Numeric(10, 4), nullable=False, default=0.10)
    prix_total = mapped_column(Numeric(10, 4), Computed('qte * prix_unitaire * (1 - remise)'), nullable=False)
    remise_euro = mapped_column(Numeric(10, 4), Computed('qte * prix_unitaire * remise'), nullable=False)

class Facture(Base):
    '''Représente une facture dans le système.'''
    __tablename__ = '13_factures'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_fiscal = mapped_column(String(13), unique=True)
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False)
    id_commande = mapped_column(Integer, ForeignKey(PK_COMMANDE), nullable=False)
    is_adresse_facturation = mapped_column(Boolean, default=False, nullable=False)
    id_adresse = mapped_column(Integer, ForeignKey(PK_ADRESSE), nullable=False)
    date_facturation = mapped_column(Date, nullable=False, default=func.now())
    montant_facture = mapped_column(Numeric(10, 2), nullable=False, default=0.00)
    is_imprime = mapped_column(Boolean, default=False, nullable=False)
    date_impression = mapped_column(Date, nullable=True)
    is_prestation_facturee = mapped_column(Boolean, default=False, nullable=False)
    composantes_factures = relationship("DevisesFactures", primaryjoin="Facture.id==DevisesFactures.id_facture",
                                        back_populates="13_factures")

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

# ====================================================================
# MODÈLES DE DONNÉES - MODULE GESTION DES PRODUITS
# ====================================================================

class Catalogue(Base):
    __tablename__ = '21_catalogue'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_produit = mapped_column(String(100), nullable=False)
    stype_produit = mapped_column(String(100), nullable=False)
    millesime = mapped_column(Integer, nullable=True)
    ref_auto = mapped_column(String(8), Computed('calculate_ref_auto()'), nullable=False)
    des_auto = mapped_column(String(100), Computed('calculate_designation_auto()'), nullable=False)
    prix_unitaire_ht = mapped_column(Numeric(10, 2), nullable=True, default=0.00)
    geographie = mapped_column(String(10), Computed('get_geographie()'))
    poids = mapped_column(String(5), Computed('get_weight()'))
    created_at = mapped_column(Date, default=func.now(), nullable=False)
    updated_at = mapped_column(Date, default=func.now(), onupdate=func.now(), nullable=False)

    # --- Méthodes de la classe Catalogue ---
    def calculate_ref_auto(self) -> str:
        """
        Calcule la référence automatique du produit au format AATYPE:4ID:2.
        """
        _ref_auto = f'{str(self.millesime)[-2:]}{str(self.type_produit[:4]).upper()}{str(self.id).zfill(2)}'
        return _ref_auto
    
    def calculate_designation_auto(self) -> str:
        """
        Calcule la désignation automatique du produit au format STYPE TARIF MILLESIME:4.
        """
        _des_auto = f'{str(self.stype_produit.upper())} TARIF {str(self.millesime)}'
        return _des_auto
    
    def get_geographie(self) -> str:
        """
        Calcule la géographie automatique du produit au format REGION.
        """
        _geo = str(self.stype_produit).split(' ')[3].capitalize()
        return _geo
    
    def get_weight(self) -> str:
        """
        Calcule le poids automatique du produit au format WEIGHT.
        """
        _weight = str(self.stype_produit).split(' ')[2]
        return _weight
    
# ====================================================================
# MODÈLES DE DONNÉES - MODULE GESTION COMPTABLE
# ====================================================================

class PCG(Base):
    """Classe représentant un Plan Comptable Général (PCG)."""
    __tablename__ = '30_pcg'

    classe = mapped_column(Integer, nullable=False)
    categorie = mapped_column(Integer, nullable=False)
    compte = mapped_column(Integer, primary_key=True)
    denomination = mapped_column(String(100), nullable=False)

class Operations(Base):
    """Classe représentant les opérations comptables."""
    __tablename__ = '31_operations'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_operation = mapped_column(Date, nullable=False)
    libelle_operation = mapped_column(String(100), nullable=False)
    montant_operation = mapped_column(Numeric(10, 2), nullable=False)
    annee_comptable = mapped_column(Integer, nullable=False)

    # Gestion des ventilations de l'opération
    ventilations = relationship("Ventilations", back_populates="31_operations")
    documents = relationship("Documents", back_populates="31_operations")

class Ventilations(Base):
    """Classe représentant les ventilations comptables."""
    __tablename__ = '32_ventilations'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_operation = mapped_column(Integer, ForeignKey(PK_OPERATION), nullable=False)
    compte_id = mapped_column(Integer, ForeignKey(PK_COMPTE), nullable=False)
    compte = relationship('PCG', primaryjoin='Ventilations.compte_id == PCG.compte')
    sens = mapped_column(String(10), nullable=False)
    montant_debit = mapped_column(Numeric(10, 2), nullable=True)
    montant_credit = mapped_column(Numeric(10, 2), nullable=True)
    banque = mapped_column(String(100), nullable=True)
    id_facture = mapped_column(String(13), nullable=True)
    id_cheque = mapped_column(String(7), nullable=True)

class Documents(Base):
    """Classe représentant les documents comptables."""
    __tablename__ = '33_documents'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_operation = mapped_column(Integer, ForeignKey(PK_OPERATION), nullable=False)
    type_document = mapped_column(String(50), nullable=True)
    date_document = mapped_column(Date, nullable=True)
    montant_document = mapped_column(Numeric(10, 2), nullable=True)
    document = mapped_column(LargeBinary, nullable=False)

# ====================================================================
# MODÈLES DE DONNÉES - MODULE GESTION DES STOCKS
# ====================================================================

class Stock(Base):
    """Classe représentant le stock des timbres."""
    __tablename__ = '40_stock'

    type_code = mapped_column(Integer, primary_key=True, nullable=False)     # 1: Francs (FR), 2: Euros (EU), 3: Valeur Permanente France (VPF), 4: Valeur Permanente Europe (VPE), 5: Valeur Permanente Monde (VPM)
    type_valeur = mapped_column(String(3), Computed('_get_type_valeur()'), nullable=False)
    val_code = mapped_column(String(4), Computed('_calculate_val_code()'), nullable=False)
    code_produit = mapped_column(String(6), Computed('_calculate_code_produit()'), nullable=False)
    val_valeur = mapped_column(Numeric(5, 2), primary_key=True, nullable=False, default=0.00)
    qte = mapped_column(Integer, nullable=False, default=0)
    tvp_valeur = mapped_column(Numeric(5, 2), nullable=True)
    tvp_poids = mapped_column(String(4), nullable=True)
    pu_ht = mapped_column(Numeric(8, 4), Computed('_calculate_pu_ht()'), nullable=False, default=0.00)
    pt_fr = mapped_column(Numeric(5, 2), Computed('_calculate_pt_fr()'), nullable=False, default=0.00)
    pt_eu = mapped_column(Numeric(5, 2), Computed('_calculate_pt_eu()'), nullable=False, default=0.00)


    # --- Méthodes de la classe Stock ---
    def _calculate_code_produit(self) -> str:
        """
        Calcule le code produit au format TYPE:4VAL:2.
        """
        return f'{self.type_valeur}{self.val_code}'


    def _get_type_valeur(self) -> str:
        """
        Retourne le code type de valeur au format TYPE:3.
        """
        match self.type_code:
            case 1: return "FR"
            case 2: return "EU"
            case 3: return "VPF"
            case 4: return "VPE"
            case 5: return "VPM"
            case _: return "NAN"


    def _calculate_val_code(self) -> str:
        """
        Calcule la val_code au format VAL:4.
        """
        if self.type_code in (1, 2):
            return f'{(self.val_valeur*100).zfill(4)}'
        else:
            return f'{str(self.tvp_poids)[:-1].zfill(3)}'


    def _calculate_pu_ht(self) -> float:
        """
        Calcule le prix unitaire hors taxes (PU HT).
        """
        if self.type_code >= 3:
            return float(self.tvp_valeur)
        elif self.type_code == 2:
            return float(self.val_valeur)
        else:
            return float(self.val_valeur / 6.55957)

    def _calculate_pt_fr(self) -> float:
        """
        Calcule le prix total en francs (PT FR).
        """
        if self.type_code == 1:
            return float(self.val_valeur * self.qte)
        else:
            return 0.0


    def _calculate_pt_eu(self) -> float:
        """
        Calcule le prix total en euros (PT EU).
        """
        if self.type_code == 1:
            return float(self.pt_fr / 6.55957)        
        elif self.type_code == 2:
            return float(self.val_valeur * self.qte)
        else:
            return float(self.qte * self.tvp_valeur)
        
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
    siren = mapped_column(String(9), Computed('get_siren()'), nullable=False)
    is_tva_intra = mapped_column(Boolean, nullable=False, default=False)
    id_tva_intra = mapped_column(String(15), nullable=True)
    logo = mapped_column(LargeBinary, nullable=True)
    type_activite = mapped_column(String(100), nullable=False)
    telephone = mapped_column(String(15), nullable=False)
    mail = mapped_column(String(100), nullable=False)
    mois_comptable = mapped_column(Integer, nullable=False)

    def get_siren(self) -> str:
        """
        Retourne le SIREN de l'entreprise.
        """
        return str(self.siret)[:9]
