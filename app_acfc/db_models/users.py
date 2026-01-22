"""Modèles de données pour le module utilisateurs et authentification de l'application ACFC."""

from typing import Any, Dict
from sqlalchemy import Boolean, Date, Integer, String, func
from sqlalchemy.orm import mapped_column
from app_acfc.config.orm_base import Base
from app_acfc.db_models.constants import UNIQUE_ID

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
    pseudo = mapped_column(String(100), nullable=False, unique=True,
                           comment="Nom utilisateur de connexion")
    email = mapped_column(String(100), nullable=False, unique=True,
                          comment="Adresse email professionnelle")
    telephone = mapped_column(String(20), nullable=False, comment="Numéro téléphone professionnel")

    # === SÉCURITÉ ET AUTHENTIFICATION ===
    sha_mdp = mapped_column(String(255), nullable=False, comment="Mot de passe haché avec Argon2")
    is_chg_mdp = mapped_column(Boolean, default=False, nullable=False,
                              comment="Force le changement de mdp à la prochaine connexion")
    date_chg_mdp = mapped_column(Date, default=func.current_date(), nullable=False,  # pylint: disable=not-callable
                                 comment="Date du dernier changement de mot de passe")
    nb_errors = mapped_column(Integer, default=0, nullable=False,
                             comment="Nombre d'erreurs d'authentification consécutives")
    is_locked = mapped_column(Boolean, default=False, nullable=False,
                             comment="Compte verrouillé après trop d'échecs d'authentification")
    permission = mapped_column(String(10), nullable=False, comment="Habilitations de l'utilisateur")

    # === CYCLE DE VIE ET ACTIVATION ===
    created_at = mapped_column(Date, default=func.current_date(), nullable=False,   # pylint: disable=not-callable
                               comment="Date de création du compte")
    is_active = mapped_column(Boolean, default=True, nullable=False, comment="Compte actif/inactif")
    debut = mapped_column(Date, nullable=False, default=func.current_date(),    # pylint: disable=not-callable
                          comment="Date de début de validité")
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
