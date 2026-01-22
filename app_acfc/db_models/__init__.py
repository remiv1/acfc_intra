"""
ACFC - Modèles de Données
==========================

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
Version : 2.0
"""

from app_acfc.db_models.accounting import PCG, Operations, Ventilations, Documents # type: ignore
from app_acfc.db_models.clients import Client, Part, Pro # type: ignore
from app_acfc.db_models.contacts import Telephone, Mail, Adresse # type: ignore
from app_acfc.db_models.orders import Order, Facture, DevisesFactures # type: ignore
from app_acfc.db_models.constants import (PK_ADRESSE, PK_CLIENTS, PK_COMMANDE,  # type: ignore
                                          PK_EXPEDITION, # type: ignore
                                          PK_FACTURE, PK_OPERATION, # type: ignore
                                          PK_COMPTE, UNIQUE_ID) # type: ignore
from app_acfc.db_models.products import Catalogue, Stock # type: ignore
from app_acfc.db_models.technical import Moi, IndicatifsTel, Villes # type: ignore
from app_acfc.db_models.users import User # type: ignore
