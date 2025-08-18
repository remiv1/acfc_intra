from sqlalchemy import Column, Integer, String, Date, Boolean, Text, Numeric, event, Computed, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapper, relationship, mapped_column
from typing import Any
from sqlalchemy.engine import Connection
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from dotenv import load_dotenv
from os import getenv


# Injection des variables d'environnement depuis le fichier .env
def verify_env() -> bool:
    """Vérifie si le fichier .env existe et charge les variables d'environnement."""
    load_dotenv()
    db_user: str | None = getenv("DB_USER")
    db_password: str | None = getenv("DB_PASSWORD")
    db_host: str | None = getenv("DB_HOST")
    db_name: str | None = getenv("DB_NAME")
    if db_user is None or db_password is None or db_host is None or db_name is None:
        raise ValueError("Les variables d'environnement DB_USER, DB_PASSWORD, DB_HOST et DB_NAME doivent être définies.")
    return True


class Configuration():
    """Configuration de l'application."""
    def __init__(self) -> None:
        load_dotenv()
        # Chargement des variables d'environnement
        db_port_env: str | None = getenv("DB_PORT")
        if db_port_env is not None:
            try:
                self.db_port: int = int(db_port_env)
            except ValueError:
                self.db_port: int = 3306
        else:
            self.db_port: int = 3306
        if verify_env():
            self.db_name: str = getenv("DB_NAME", "airlines")
            self.db_user: str = getenv("DB_USER", "root")
            self.db_password: str = getenv("DB_PASSWORD", "root")
            self.db_host: str = getenv("DB_HOST", "localhost")
            self.api_key_l: str = getenv("API_URL", "default_api_key")
            self.api_secret_l: str = getenv("API_SECRET", "default_api_secret")
        else:
            self.api_key_l: str = "default_api_key"
        if not all([self.db_user, self.db_password, self.db_host, self.db_name]):
            raise ValueError("Une ou plusieurs variables d'environnement de base de données (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME) ne sont pas définies.")

conf: Configuration = Configuration()

Base = declarative_base()
db_url = URL.create(
    drivername="mysql+mysqlconnector",
    username=conf.db_user,
    password=conf.db_password,
    host=conf.db_host,
    port=conf.db_port,
    database=conf.db_name,
    query={"charset": "utf8mb4"}
)

# Créer l'engin SQLAlchemy
engine = create_engine(db_url, echo=False)

# Créer les tables de la base de données
Base.metadata.create_all(engine)

# Créer une session de base de données
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

PK_CLIENTS = '01_clients.id'
PK_ADRESSE = '04_adresse.id'
PK_COMMANDE = '11_commandes.id'
PK_OPERATION = '31_operations.id'
PK_COMPTE = '30_pcg.compte'

class User(Base):
    '''Représente un utilisateur dans le système.'''
    __tablename__ = "99_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prenom = Column(String(100), nullable=False)
    nom = Column(String(100), nullable=False)
    pseudo = Column(String(100), nullable=False)
    sha_mdp = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False)
    telephone = Column(String(20), nullable=False)
    created_at = Column(Date, default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    debut = Column(Date, nullable=False, default=func.now())
    fin = Column(Date, nullable=True)
    nb_errors = Column(Integer, default=0, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)

class Client(Base):
    '''Représente un client dans le système, qu'il soit particulier ou professionnel.'''
    __tablename__ = '01_clients'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_client = Column(Integer, nullable=False)
    id_part = Column(Integer, nullable=True, foreign_key='011_part.id')
    id_pro = Column(Integer, nullable=True, foreign_key='012_pro.id')
    created_at = Column(Date, default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)

class Part(Base):
    '''Représente un particulier dans le système.'''
    __tablename__ = '011_part'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prenom = Column(String(255), nullable=False)
    nom = Column(String(255), nullable=False)
    date_naissance = Column(Date, nullable=False)
    lieu_naissance = Column(String(255), nullable=False)

class Pro(Base):
    '''Représente un professionnel dans le système.'''
    __tablename__ = '012_pro'

    id = Column(Integer, primary_key=True, autoincrement=True)
    raison_sociale = Column(String(255), nullable=False)
    type_pro = Column(Integer, nullable=False)
    siren = Column(String(9), nullable=True)
    rna = Column(String(10), nullable=True)

class Mail(Base):
    '''Représente une adresse e-mail associée à un client.'''
    __tablename__ = '02_mail'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_client = Column(Integer, nullable=False, foreign_key=PK_CLIENTS)
    type_mail = Column(String(100), nullable=False)
    detail = Column(String(255), nullable=True)
    mail = Column(String(255), nullable=False)
    is_principal = Column(Boolean, default=False, nullable=False)

class Telephone(Base):
    '''Représente un numéro de téléphone associé à un client.'''
    __tablename__ = '03_telephone'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_client = Column(Integer, nullable=False, foreign_key=PK_CLIENTS)
    type_telephone = Column(String(100), nullable=False)
    detail = Column(String(255), nullable=True)
    indicatif = Column(String(5), nullable=True)
    telephone = Column(String(255), nullable=False)
    is_principal = Column(Boolean, default=False, nullable=False)

class Adresse(Base):
    '''Représente une adresse associée à un client.'''
    __tablename__ = '04_adresse'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_client = Column(Integer, nullable=False, foreign_key=PK_CLIENTS)
    adresse_l1 = Column(String(255), nullable=False)
    adresse_l2 = Column(String(255), nullable=True)
    code_postal = Column(String(10), nullable=False)
    ville = Column(String(100), nullable=False)
    created_at = Column(Date, default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

class Commande(Base):
    '''Représente une commande dans le système.'''
    __tablename__ = '11_commandes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_client = Column(Integer, nullable=False, foreign_key=PK_CLIENTS)
    is_ad_livraison = Column(Boolean, default=False, nullable=False)
    id_adresse = Column(Integer, nullable=True, foreign_key=PK_ADRESSE)
    descriptif = Column(String(255), nullable=True)
    date_commande = Column(Date, default=func.now(), nullable=False)
    montant = Column(Numeric(10, 2), nullable=False, default=0.00)
    is_facture = Column(Boolean, default=False, nullable=False)
    date_facturation = Column(Date, nullable=True)
    is_expedie = Column(Boolean, default=False, nullable=False)
    date_expedition = Column(Date, nullable=True)
    id_suivi = Column(String(100), nullable=True)

class DevisesFactures(Base):
    '''Représente les éléments des commandes et des factures dans le système.'''
    __tablename__ = '12_devises_factures'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_commande = Column(Integer, nullable=False, foreign_key=PK_COMMANDE)
    id_facture = Column(Integer, nullable=True)
    reference = Column(String(100), nullable=False)
    designation = Column(String(255), nullable=False)
    qte = Column(Integer, nullable=False, default=1)
    prix_unitaire = Column(Numeric(10, 4), nullable=False, default=0.00)
    remise = Column(Numeric(10, 4), nullable=False, default=0.10)
    prix_total = Column(Numeric(10, 4), computed=Computed('qte * prix_unitaire * (1 - remise)'), nullable=False, persisted=True)
    remise_euro = Column(Numeric(10, 4), computed=Computed('qte * prix_unitaire * remise'), nullable=False, persisted=True)

class Facture(Base):
    '''Représente une facture dans le système.'''
    __tablename__ = '13_factures'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_fiscal = Column(String(13), unique=True)
    id_client = Column(Integer, nullable=False, foreign_key=PK_CLIENTS)
    id_commande = Column(Integer, nullable=False, foreign_key=PK_COMMANDE)
    is_adresse_facturation = Column(Boolean, default=False, nullable=False)
    id_adresse = Column(Integer, nullable=False, foreign_key=PK_ADRESSE)
    date_facturation = Column(Date, nullable=False, default=func.now())
    montant_facture = Column(Numeric(10, 2), nullable=False, default=0.00)
    is_imprime = Column(Boolean, default=False, nullable=False)
    date_impression = Column(Date, nullable=True)
    is_prestation_facturee = Column(Boolean, default=False, nullable=False)

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

class Catalogue(Base):
    __tablename__ = '21_catalogue'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_produit = Column(String(100), nullable=False)
    stype_produit = Column(String(100), nullable=False)
    millesime = Column(Integer, nullable=True)
    ref_auto = Column(String(8), nullable=False, computed=Computed('calculate_ref_auto()'), persisted=True)
    des_auto = Column(String(100), nullable=False, computed=Computed('calculate_designation_auto()'), persisted=True)
    prix_unitaire_ht = Column(Numeric(10, 2), nullable=True, default=0.00)
    geographie = Column(String(10), computed=Computed('get_geographie()'), persisted=True)
    poids = Column(String(5), computed=Computed('get_weight()'), persisted=True)
    created_at = Column(Date, default=func.now(), nullable=False)
    updated_at = Column(Date, default=func.now(), onupdate=func.now(), nullable=False)

    def calculate_ref_auto(self) -> str:
        """
        Calcule la référence automatique du produit au format AATYPE:4ID:2.
        """
        codage = f'{str(self.millesime)[-2:]}{str(self.type_produit[:4]).upper()}{str(self.id).zfill(2)}'
        return codage
    
    def calculate_designation_auto(self) -> str:
        """
        Calcule la désignation automatique du produit au format STYPE TARIF MILLESIME:4.
        """
        codage = f'{str(self.stype_produit.upper())} TARIF {str(self.millesime)}'
        return codage
    
    def get_geographie(self) -> str:
        """
        Calcule la géographie automatique du produit au format REGION.
        """
        geo = str(self.stype_produit).split(' ')[3].capitalize()
        return geo
    
    def get_weight(self) -> str:
        """
        Calcule le poids automatique du produit au format WEIGHT.
        """
        weight = str(self.stype_produit).split(' ')[2]
        return weight
    
class PCG(Base):
    """Classe représentant un Plan Comptable Général (PCG)."""
    __tablename__ = '30_pcg'

    classe = Column(Integer, nullable=False)
    categorie = Column(Integer, nullable=False)
    compte = Column(Integer, primary_key=True)
    denomination = Column(String(100), nullable=False)

class Operations(Base):
    """Classe représentant les opérations comptables."""
    __tablename__ = '31_operations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date_operation = Column(Date, nullable=False)
    libelle_operation = Column(String(100), nullable=False)
    montant_operation = Column(Numeric(10, 2), nullable=False)
    annee_comptable = Column(Integer, nullable=False)

class Ventilations(Base):
    """Classe représentant les ventilations comptables."""
    __tablename__ = '32_ventilations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_operation = Column(Integer, nullable=False, foreign_key=PK_OPERATION)
    compte_id = Column(Integer, nullable=False, foreign_key=PK_COMPTE)
    compte = relationship('PCG', primaryjoin='Ventilations.compte_id == PCG.compte')
    sens = Column(String(10), nullable=False)
    montant_debit = Column(Numeric(10, 2), nullable=True)
    montant_credit = Column(Numeric(10, 2), nullable=True)
    banque = Column(String(100), nullable=True)
    id_facture = Column(String(13), nullable=True)
    id_cheque = Column(String(7), nullable=True)

class Documents(Base):
    """Classe représentant les documents comptables."""
    __tablename__ = '33_documents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_operation = Column(Integer, nullable=False, foreign_key=PK_OPERATION)
    type_document = Column(String(50), nullable=True)
    date_document = Column(Date, nullable=True)
    montant_document = Column(Numeric(10, 2), nullable=True)
    document = Column(LargeBinary, nullable=False)

class Stock(Base):
    """Classe représentant le stock des timbres."""
    __tablename__ = '40_stock'

    type_code = mapped_column(Integer, nullable=False)     # 1: Francs (FR), 2: Euros (EU), 3: Valeur Permanente France (VPF), 4: Valeur Permanente Europe (VPE), 5: Valeur Permanente Monde (VPM)
    type_valeur = mapped_column(String(3), computed=Computed('get_type_valeur()'), persisted=True, nullable=False)
    val_code = mapped_column(String(4), computed=Computed('calculate_val_code()'), persisted=True, nullable=False)
    code_produit = mapped_column(String(6), computed=Computed('calculate_code_produit()'), persisted=True, nullable=False)
    val_valeur = mapped_column(Numeric(5, 2), nullable=False, default=0.00)
    qte = mapped_column(Integer, nullable=False, default=0)
    tvp_valeur = mapped_column(Numeric(5, 2), nullable=True)
    tvp_poids = mapped_column(String(4), nullable=True)
    pu_ht = mapped_column(Numeric(8, 4), computed=Computed('calculate_pu_ht()'), persisted=True, nullable=False, default=0.00)
    pt_fr = mapped_column(Numeric(5, 2), computed=Computed('calculate_pt_fr()'), persisted=True, nullable=False, default=0.00)
    pt_eu = mapped_column(Numeric(5, 2), computed=Computed('calculate_pt_eu()'), persisted=True, nullable=False, default=0.00)

    def calculate_code_produit(self) -> str:
        """
        Calcule le code produit au format TYPE:4VAL:2.
        """
        return f'{self.type_valeur}{self.val_code}'
    
    def get_type_valeur(self) -> str:
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

    def calculate_val_code(self) -> str:
        """
        Calcule la val_code au format VAL:4.
        """
        if self.type_code in (1, 2):
            return f'{(self.val_valeur*100).zfill(4)}'
        else:
            return f'{str(self.tvp_poids)[:-1].zfill(3)}'
        
    def calculate_pu_ht(self) -> float:
        """
        Calcule le prix unitaire hors taxes (PU HT).
        """
        if self.type_code >= 3:
            return float(self.tvp_valeur)
        elif self.type_code == 2:
            return float(self.val_valeur)
        else:
            return float(self.val_valeur / 6.55957)

    def calculate_pt_fr(self) -> float:
        """
        Calcule le prix total en francs (PT FR).
        """
        if self.type_code == 1:
            return float(self.val_valeur * self.qte)
        else:
            return 0.0
        
    def calculate_pt_eu(self) -> float:
        """
        Calcule le prix total en euros (PT EU).
        """
        if self.type_code == 1:
            return float(self.pt_fr / 6.55957)        
        elif self.type_code == 2:
            return float(self.val_valeur * self.qte)
        else:
            return float(self.qte * self.tvp_valeur)
        
class Villes(Base):
    """Classe représentant les villes."""
    __tablename__ = '91_villes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(100), nullable=False)
    code_postal = Column(Integer, nullable=False)

class IndicatifsTel(Base):
    """Classe représentant les indicatifs téléphoniques."""
    __tablename__ = '92_indicatifs_tel'

    tri = Column(Integer, primary_key=True)
    indicatif = Column(String(4), nullable=False)
    pays = Column(String(100), nullable=False)

class Moi(Base):
    """Classe représentant l'entreprise propriétaire de la base de données."""
    __tablename__ = '93_moi'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(100), nullable=False)
    adresse_l1 = Column(String(255), nullable=False)
    adresse_l2 = Column(String(255), nullable=True)
    code_postal = Column(Integer, nullable=False)
    ville = Column(String(100), nullable=False)
    siret = Column(String(14), nullable=False)
    siren = Column(String(9), computed=Computed('get_siren()'), nullable=False)
    is_tva_intra = Column(Boolean, nullable=False, default=False)
    id_tva_intra = Column(String(15), nullable=True)
    logo = Column(LargeBinary, nullable=True)
    type_activite = Column(String(100), nullable=False)
    telephone = Column(String(15), nullable=False)
    mail = Column(String(100), nullable=False)
    mois_comptable = Column(Integer, nullable=False)

    def get_siren(self) -> str:
        """
        Retourne le SIREN de l'entreprise.
        """
        return str(self.siret)[:9]
