"""Modèles de données pour le module gestion des produits de l'application ACFC."""

from typing import Dict, Any
from sqlalchemy import Date, Integer, String, DateTime, Numeric, func, Computed
from sqlalchemy.orm import mapped_column
from app_acfc.config.orm_base import Base

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
    geographie = mapped_column(String(10),
            Computed("UPPER(SUBSTRING_INDEX(SUBSTRING_INDEX(stype_produit, ' ', 4), ' ', -1))",
                     persisted=True))
    poids = mapped_column(String(5),
            Computed("SUBSTRING_INDEX(SUBSTRING_INDEX(stype_produit, ' ', 3), ' ', -1)",
                     persisted=True))

    # === MÉTADONNÉES ===
    created_at = mapped_column(Date, default=func.current_date(), nullable=False)  # pylint: disable=not-callable
    created_by = mapped_column(String(100), default='system', nullable=False,
                               comment="Utilisateur ayant créé le produit")
    modified_at = mapped_column(DateTime, default=func.current_timestamp(),  # pylint: disable=not-callable
                                onupdate=func.current_timestamp(), nullable=False)  # pylint: disable=not-callable
    modified_by = mapped_column(String(100), nullable=True,
                                comment="Utilisateur ayant modifié le produit")

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
        return f"<Catalogue(id={self.id}, type_produit='{self.type_produit}', " \
            + f"ref_auto='{self.ref_auto}')>"

# ====================================================================
# MODÈLES DE DONNÉES - MODULE GESTION DES STOCKS
# ====================================================================

class Stock(Base):
    """Classe représentant le stock des timbres."""
    __tablename__ = '40_stock'

    # 1: Francs (FR), 2: Euros (EU), 3: Valeur Permanente France (VPF),
    # 4: Valeur Permanente Europe (VPE), 5: Valeur Permanente Monde (VPM)
    type_code = mapped_column(Integer, primary_key=True, nullable=False)
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

    def __repr__(self) -> str:
        return f"<Stock(type_code={self.type_code}, val_code='{self.val_code}', " \
               f"code_produit='{self.code_produit}', qte={self.qte})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet Stock en dictionnaire."""
        stock_dict: Dict[str, Any] = {
            "type_code": self.type_code,
            "type_valeur": self.type_valeur,
            "val_code": self.val_code,
            "code_produit": self.code_produit,
            "val_valeur": float(self.val_valeur),
            "qte": self.qte,
            "tvp_valeur": float(self.tvp_valeur) if self.tvp_valeur is not None else None,
            "tvp_poids": self.tvp_poids,
            "pu_ht": float(self.pu_ht),
            "pt_fr": float(self.pt_fr),
            "pt_eu": float(self.pt_eu)
        }
        return stock_dict
