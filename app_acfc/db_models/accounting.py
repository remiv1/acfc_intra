"""Modèles de données - Comptabilité et Finance pour l'application ACFC."""

from typing import Dict, Any
from sqlalchemy import (Date, Integer, String, DateTime, Numeric, Boolean, ForeignKey,
                        LargeBinary, func)
from sqlalchemy.orm import mapped_column, relationship
from app_acfc.config.orm_base import Base
from app_acfc.db_models.constants import PK_COMPTE, PK_OPERATION

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

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet PCG en dictionnaire."""
        pcg: Dict[str, Any] =  {
            "classe": self.classe,
            "categorie_1": self.categorie_1,
            "categorie_2": self.categorie_2,
            "compte": self.compte,
            "denomination": self.denomination
        }
        return pcg

    def __repr__(self) -> str:
        """Représentation sous forme de chaîne de l'objet PCG."""
        return f"<PCG(classe={self.classe}, categorie_1={self.categorie_1}, " \
               f"categorie_2={self.categorie_2}, compte={self.compte}, " \
               f"denomination='{self.denomination}')>"

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
    created_at = mapped_column(DateTime, default=func.current_timestamp(), nullable=False)  # pylint: disable=not-callable
    created_by = mapped_column(String(100), nullable=True,
                               comment="Utilisateur ayant créé l'opération")
    modified_at = mapped_column(DateTime, default=func.current_timestamp(), # pylint: disable=not-callable
                                onupdate=func.current_timestamp(), nullable=False)  # pylint: disable=not-callable
    modified_by = mapped_column(String(100), nullable=True,
                                comment="Utilisateur ayant modifié l'opération")
    is_inactive = mapped_column(Boolean, default=False, nullable=False,
                                comment="Opération inactive (soft delete)")

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet Operations en dictionnaire."""
        operation: Dict[str, Any] =  {
            "id": self.id,
            "date_operation": self.date_operation.isoformat(),
            "libelle_operation": self.libelle_operation,
            "montant_operation": float(self.montant_operation),
            "annee_comptable": self.annee_comptable,
            "is_inactive": self.is_inactive
        }
        return operation

    def __repr__(self) -> str:
        """Représentation sous forme de chaîne de l'objet Operations."""
        return f"<Operations(id={self.id}, date_operation={self.date_operation}, " \
               f"libelle_operation='{self.libelle_operation}', " \
               f"montant_operation={self.montant_operation}, " \
               f"annee_comptable={self.annee_comptable}, " \
               f"is_inactive={self.is_inactive})>"

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
    created_at = mapped_column(DateTime, default=func.current_timestamp(), nullable=False)  # pylint: disable=not-callable
    created_by = mapped_column(String(100), nullable=True,
                               comment="Utilisateur ayant créé la ventilation")
    modified_at = mapped_column(DateTime, default=func.current_timestamp(), # pylint: disable=not-callable
                                onupdate=func.current_timestamp(), nullable=False)  # pylint: disable=not-callable
    modified_by = mapped_column(String(100), nullable=True,
                                comment="Utilisateur ayant modifié la ventilation")
    is_inactive = mapped_column(Boolean, default=False, nullable=False,
                                comment="Ventilation inactive (soft delete)")

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet Ventilations en dictionnaire."""
        ventilation: Dict[str, Any] =  {
            "id": self.id,
            "id_operation": self.id_operation,
            "compte_id": self.compte_id,
            "sens": self.sens,
            "montant_debit": float(self.montant_debit) if self.montant_debit else None,
            "montant_credit": float(self.montant_credit) if self.montant_credit else None,
            "banque": self.banque,
            "id_facture": self.id_facture,
            "id_cheque": self.id_cheque,
            "is_inactive": self.is_inactive
        }
        return ventilation

    def __repr__(self) -> str:
        """Représentation sous forme de chaîne de l'objet Ventilations."""
        return f"<Ventilations(id={self.id}, id_operation={self.id_operation}, " \
               f"compte_id={self.compte_id}, sens='{self.sens}', " \
               f"montant_debit={self.montant_debit}, montant_credit={self.montant_credit}, " \
               f"banque='{self.banque}', id_facture='{self.id_facture}', " \
               f"id_cheque='{self.id_cheque}', is_inactive={self.is_inactive})>"

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
    created_at = mapped_column(DateTime, default=func.current_timestamp(), nullable=False)  # pylint: disable=not-callable
    created_by = mapped_column(String(100), nullable=True,
                               comment="Utilisateur ayant créé le document")
    modified_at = mapped_column(DateTime, default=func.current_timestamp(), # pylint: disable=not-callable
                                onupdate=func.current_timestamp(), nullable=False)  # pylint: disable=not-callable
    modified_by = mapped_column(String(100), nullable=True,
                                comment="Utilisateur ayant modifié le document")
    is_inactive = mapped_column(Boolean, default=False, nullable=False,
                                comment="Document inactif (soft delete)")
