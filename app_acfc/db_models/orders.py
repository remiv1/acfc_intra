"""Modèles de données pour le module gestion des commandes/factures de l'application ACFC."""

from typing import Any, Dict
from sqlalchemy import Boolean, Date, Integer, String, DateTime, Text, Numeric, func
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import ForeignKey
from sqlalchemy import Computed, event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapper
from app_acfc.config.orm_base import Base
from app_acfc.db_models.constants import PK_CLIENTS, PK_ADRESSE, PK_COMMANDE, PK_EXPEDITION

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
    adresse_livraison = relationship("Adresse", foreign_keys=[id_adresse_livraison],
                                     back_populates="commandes_livrees")
    id_adresse_facturation = mapped_column(Integer, ForeignKey(PK_ADRESSE), nullable=True)
    adresse_facturation = relationship("Adresse", foreign_keys=[id_adresse_facturation],
                                       back_populates="commandes_facturees")
    descriptif = mapped_column(String(255), nullable=True)
    date_commande = mapped_column(Date, default=func.current_date, nullable=False)
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
    created_at = mapped_column(DateTime, default=func.current_timestamp, nullable=False)
    created_by = mapped_column(String(100), nullable=True,
                               comment="Utilisateur ayant créé la commande")
    modified_at = mapped_column(DateTime, default=func.current_timestamp,
                                onupdate=func.current_timestamp, nullable=False)
    modified_by = mapped_column(String(100), nullable=True,
                                comment="Utilisateur ayant modifié la commande")

    def __repr__(self) -> str:
        """
        Représentation sous forme de chaîne de l'objet Order
        lors de l'utilisation de print() ou dans le shell.
        """
        return f"<Order(id={self.id}, client_id={self.id_client}, " \
            + f"date_commande={self.date_commande}, montant={self.montant})>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Retourne un dictionnaire représentant la commande
        """
        return {
            'id': self.id,
            'id_client': self.id_client,
            'is_ad_livraison': self.is_ad_livraison,
            'id_adresse_livraison': self.id_adresse_livraison,
            'id_adresse_facturation': self.id_adresse_facturation,
            'descriptif': self.descriptif,
            'date_commande': self.date_commande.isoformat() if self.date_commande else None,
            'montant': float(self.montant) if self.montant is not None else None,
            'is_annulee': self.is_annulee,
            'is_expediee': self.is_expediee,
            'is_facturee': self.is_facturee,
            'date_expedition': self.date_expedition.isoformat() if self.date_expedition else None,
            'date_facturation': self.date_facturation.isoformat() if self.date_facturation \
                                        else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'modified_by': self.modified_by
        }

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
    created_at = mapped_column(DateTime, default=func.current_timestamp, nullable=False,
                              comment="Date de création de cette ligne")
    created_by = mapped_column(String(100), nullable=True,
                              comment="Utilisateur qui a créé cette ligne")
    modified_at = mapped_column(DateTime, default=func.current_timestamp,
                                onupdate=func.current_timestamp, nullable=False,
                                comment="Date de dernière modification")
    modified_by = mapped_column(String(100), nullable=True,
                              comment="Utilisateur qui a modifié cette ligne")

    def __repr__(self) -> str:
        """
        Représentation sous forme de chaîne de l'objet DevisesFactures
        lors de l'utilisation de print() ou dans le shell.
        """
        return f"<DevisesFactures(id={self.id}, commande_id={self.id_order}, " \
            + f"reference='{self.reference}', qte={self.qte}, prix_total={self.prix_total})>"

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
    id_fiscal = mapped_column(String(20), unique=True)
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False)
    client = relationship("Client", back_populates="factures")
    id_order = mapped_column(Integer, ForeignKey(PK_COMMANDE), nullable=False)
    commande = relationship("Order", back_populates="facture")

    # === DONNÉES DE FACTURATION ===
    date_facturation = mapped_column(Date, nullable=False, default=func.current_timestamp)
    montant_facture = mapped_column(Numeric(10, 2), nullable=False, default=0.00)

    # === ÉTAT DE LA FACTURE ===
    is_imprime = mapped_column(Boolean, default=False, nullable=False)
    date_impression = mapped_column(Date, nullable=True)
    is_prestation_facturee = mapped_column(Boolean, default=False, nullable=False)
    composantes_factures = relationship("DevisesFactures",
                                    primaryjoin="Facture.id == foreign(DevisesFactures.id_facture)",
                                    back_populates="facture")

    # === MÉTADONNÉES ===
    created_at = mapped_column(DateTime, default=func.current_timestamp, nullable=False)
    created_by = mapped_column(String(100), nullable=True,
                               comment="Utilisateur ayant créé la facture")

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
    def set_id_fiscal_after_insert(mapper: Mapper[Any], # pylint: disable=unused-argument
                                   connection: Connection,
                                   target: 'Facture') -> None:
        """Handler after_insert: calcule l'id_fiscal et le persiste via la connexion fournie.
        On passe par une mise à jour SQL pour éviter d'appeler session.commit() depuis un event
        listener.
        """
        if not getattr(target, 'id_fiscal', None):
            new_id = target.generate_fiscal_id()
            # Mettre à jour la colonne en base
            connection.execute(
                Facture.__table__.update().where(Facture.id == target.id).values(id_fiscal=new_id)
            )
            # Mettre à jour l'instance en mémoire
            target.id_fiscal = new_id

    def __repr__(self) -> str:
        """
        Représentation sous forme de chaîne de l'objet Facture
        lors de l'utilisation de print() ou dans le shell.
        """
        return f"<Facture(id={self.id}, id_fiscal='{self.id_fiscal}', "\
            + f"id_client={self.id_client}, montant_facture={self.montant_facture})>"

# Enregistrement de l'écouteur qui délègue la logique à la méthode de la classe
event.listen(Facture, 'after_insert', Facture.set_id_fiscal_after_insert)

class Expeditions(Base):
    """Table des expéditions simplifiée"""
    __tablename__ = '14_expeditions'

    # === IDENTIFIANT ET LIAISON ===
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_devises_factures = mapped_column(Integer, ForeignKey('12_devises_factures.id'),
                                        nullable=False)
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
    created_at = mapped_column(DateTime, default=func.current_timestamp, nullable=False)
    created_by = mapped_column(String(100), nullable=True)
    modified_at = mapped_column(DateTime, default=func.current_timestamp,
                                onupdate=func.current_timestamp, nullable=True)
    modified_by = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        """
        Représentation sous forme de chaîne de l'objet Expeditions
        lors de l'utilisation de print() ou dans le shell.
        """
        return f"<Expeditions(id={self.id}, id_devises_factures={self.id_devises_factures}, "\
            + f"numero_expedition='{self.numero_expedition}', " \
            + f"date_expedition_remise={self.date_expedition_remise})>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Retourne un dictionnaire représentant l'expédition
        """
        return {
            'id': self.id,
            'id_devises_factures': self.id_devises_factures,
            'c_qualite': self.c_qualite,
            'is_main_propre': self.is_main_propre,
            'numero_expedition': self.numero_expedition,
            'date_expedition_remise': self.date_expedition_remise.isoformat() \
                                        if self.date_expedition_remise else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'modified_by': self.modified_by
        }
