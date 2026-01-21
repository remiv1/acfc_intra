"""Modèles de données pour le module gestion des contacts de l'application ACFC."""

from typing import Any, Dict
from sqlalchemy import Boolean, Date, Integer, String, DateTime, func
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import ForeignKey
from app_acfc.db_models.base import Base
from app_acfc.db_models.constants import PK_CLIENTS

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
    id = mapped_column(Integer, primary_key=True, autoincrement=True,
                       comment="Identifiant unique de l'email")
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False,
                              comment="Référence vers le client propriétaire")
    client = relationship("Client", back_populates="mails")

    # === CLASSIFICATION ET DONNÉES ===
    type_mail = mapped_column(String(100), nullable=False,
                              comment="Type: professionnel/personnel/facturation/marketing")
    detail = mapped_column(String(255), nullable=True,
                           comment="Précision libre sur l'usage de cet email")
    mail = mapped_column(String(255), nullable=False,
                         comment="Adresse email (validation format requise)")
    is_principal = mapped_column(Boolean, default=False, nullable=False,
                                comment="Email principal pour ce client (un seul par client)")

    # === MÉTADONNÉES ===
    created_at = mapped_column(Date, default=func.current_date, nullable=False)
    created_by = mapped_column(String(100), nullable=True, comment="Utilisateur ayant créé l'email")
    modified_at = mapped_column(DateTime, default=func.current_timestamp,
                                onupdate=func.current_timestamp, nullable=False)
    modified_by = mapped_column(String(100), nullable=True,
                                comment="Utilisateur ayant modifié l'email")
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
    id = mapped_column(Integer, primary_key=True, autoincrement=True,
                       comment="Identifiant unique du téléphone")
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False,
                              comment="Référence vers le client propriétaire")
    client = relationship("Client", back_populates="tels")

    # === CLASSIFICATION ===
    type_telephone = mapped_column(String(100), nullable=False,
                                  comment="Type: fixe_pro/mobile_pro/fixe_perso/mobile_perso/fax")
    detail = mapped_column(String(255), nullable=True,
                           comment="Précision sur l'usage ou horaires de contact")

    # === DONNÉES TÉLÉPHONIQUES ===
    indicatif = mapped_column(String(5), nullable=True, comment="Indicatif pays (ex: +33, +1, +49)")
    telephone = mapped_column(String(255), nullable=False, comment="Numéro de téléphone local")
    is_principal = mapped_column(Boolean, default=False, nullable=False)

    # === MÉTADONNÉES ===
    created_at = mapped_column(Date, default=func.current_date, nullable=False)
    created_by = mapped_column(String(100), nullable=True,
                               comment="Utilisateur ayant créé le téléphone")
    modified_at = mapped_column(DateTime, default=func.current_timestamp,
                                onupdate=func.current_timestamp, nullable=False,
                                comment="Date de modification du téléphone")
    modified_by = mapped_column(String(100), nullable=True,
                                comment="Utilisateur ayant modifié le téléphone")
    is_inactive = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        numero_complet = f"{self.indicatif}{self.telephone}" if self.indicatif else self.telephone
        return f"<Telephone(id={self.id}, client_id={self.id_client}, numero='{numero_complet}', " \
            + f"type='{self.type_telephone}')>"

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
    created_at = mapped_column(Date, default=func.current_date, nullable=False)
    created_by = mapped_column(String(100), nullable=True,
                               comment="Utilisateur ayant créé l'adresse")
    modified_at = mapped_column(DateTime, default=func.current_timestamp,
                                onupdate=func.current_timestamp, nullable=False)
    modified_by = mapped_column(String(100), nullable=True,
                                comment="Utilisateur ayant modifié l'adresse")
    is_inactive = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Adresse(id={self.id}, client_id={self.id_client}, cp/ville={self.code_postal} " \
            + f"'{self.ville.capitalize()}', {'Princip.' if self.is_principal else 'Secondaire'})>"

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
