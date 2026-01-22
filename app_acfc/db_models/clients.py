"""Modèles de données pour le module clients de l'application ACFC."""

from typing import Any, Dict
from sqlalchemy import Boolean, Date, Integer, String, DateTime, Text, Numeric, func
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import ForeignKey
from app_acfc.config.orm_base import Base
from app_acfc.db_models.constants import PK_CLIENTS, UNIQUE_ID

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
    id = mapped_column(Integer, primary_key=True, autoincrement=True, comment="Id unique client")
    type_client = mapped_column(Integer, nullable=False,
                                comment="Type: 1=Particulier, 2=Professionnel")

    # === MÉTADONNÉES ===
    created_at = mapped_column(DateTime, default=func.current_date(), nullable=False,   # pylint: disable=not-callable
                               comment="Date de création du client")
    created_by = mapped_column(String(100), nullable=True,
                               comment="Utilisateur ayant créé le client")
    modified_at = mapped_column(Date, default=func.current_date(), onupdate=func.current_date(),    # pylint: disable=not-callable
                                nullable=False, comment="Date de modification du client")
    modified_by = mapped_column(String(100), nullable=True,
                                comment="Utilisateur ayant modifié le client")
    is_active = mapped_column(Boolean, default=True, nullable=False, comment="Client actif/inactif")
    notes = mapped_column(Text, nullable=True, comment="Notes libres sur le client")
    reduces = mapped_column(Numeric(4,3), default=0.10, nullable=False,
                            comment="Réduction appliquée au client")

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
        """Affichage du nom complet du client selon son type."""
        if self.type_client == 1 and self.part:
            return f"{self.part.prenom} {self.part.nom}"
        elif self.type_client == 2 and self.pro:
            return self.pro.raison_sociale
        else:
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
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False,
                              comment="Ref vers le client propriétaire")
    client = relationship("Client", back_populates="part")

    # === INFORMATIONS PERSONNELLES ===
    prenom = mapped_column(String(255), nullable=False, comment="Prénom")
    nom = mapped_column(String(255), nullable=False, comment="Nom de famille")

    # === INFORMATIONS D'ÉTAT CIVIL ===
    date_naissance = mapped_column(Date, nullable=True,
                                   comment="Date de naissance (vérification majorité)")
    lieu_naissance = mapped_column(String(255), nullable=True, comment="Lieu de naissance")

    def __repr__(self) -> str:
        """Représentation en chaîne de caractères de l'objet Part."""
        return f"<Part(id={self.id}, nom='{self.nom}', prenom='{self.prenom}')>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Retourne un dictionnaire représentant le particulier
        """
        return {
            'id': self.id,
            'id_client': self.id_client,
            'prenom': self.prenom,
            'nom': self.nom,
            'date_naissance': self.date_naissance.isoformat() if self.date_naissance else None,
            'lieu_naissance': self.lieu_naissance
        }

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
    id_client = mapped_column(Integer, ForeignKey(PK_CLIENTS), nullable=False,
                              comment="Ref vers le client propriétaire")
    client = relationship("Client", back_populates="pro")

    # === INFORMATIONS LÉGALES ===
    raison_sociale = mapped_column(String(255), nullable=False,
                                   comment="Dénomination sociale complète")
    type_pro = mapped_column(Integer, nullable=False,
                             comment="Type: 1=Entreprise, 2=Association, 3=Administration")

    # === IDENTIFIANTS OFFICIELS ===
    siren = mapped_column(String(9), nullable=True,
                          comment="Numéro SIREN (9 chiffres) - Obligatoire pour entreprises")
    rna = mapped_column(String(10), nullable=True,
                        comment="Numéro RNA (associations) - Format: W123456789")

    def __repr__(self) -> str:
        """Représentation en chaîne de caractères de l'objet Pro."""
        return f"<Pro(id={self.id}, raison_sociale='{self.raison_sociale}', siren='{self.siren}')>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Retourne un dictionnaire représentant le professionnel
        """
        return {
            'id': self.id,
            'id_client': self.id_client,
            'raison_sociale': self.raison_sociale,
            'type_pro': self.type_pro,
            'siren': self.siren,
            'rna': self.rna
        }
