"""Modèles de données pour le module technique de l'application ACFC."""

from sqlalchemy import (Integer, String, Boolean, Computed,
                        LargeBinary)
from sqlalchemy.orm import mapped_column
from app_acfc.db_models.base import Base

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
