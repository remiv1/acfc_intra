"""
Module des fonctions utilitaires pour les opérations sur les commandes.
Contient des fonctions pour récupérer les commandes en cours et les indicateurs commerciaux.
"""

from typing import List, Dict, Any
from datetime import date
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from app_acfc.config.config_models import get_db_session, SessionBdDType
from app_acfc.db_models.orders import Order
from app_acfc.db_models.clients import Client

# ====================================================================
# FONCTIONS DE RECHERCHES - HORS ROUTES
# ====================================================================

def get_current_orders(id_client: int = 0) -> List[Order]:
    """
    Récupère les commandes en cours pour un client donné.

    Args:
        id_client (int): ID du client, 0 pour tous les clients

    Returns:
        List[Order]: Liste des commandes en cours
    """
    # Ouverture de la session
    db_session: SessionBdDType = get_db_session()

    # Récupération des commandes en cours sans notion de client
    if id_client == 0:
        commandes: List[Order] = (
            db_session.query(Order)
            .options(
                joinedload(Order.client).joinedload(Client.part),  # Eager loading du client part
                joinedload(Order.client).joinedload(Client.pro)    # Eager loading du client pro
            )
            .filter(or_(
                Order.is_facturee.is_(False),
                Order.is_expediee.is_(False)
            ))
            .all()
        )

    # Récupération des commandes en cours pour un client spécifique
    else:
        commandes: List[Order] = (
            db_session.query(Order)
            .options(
                joinedload(Order.client).joinedload(Client.part),  # Eager loading du client part
                joinedload(Order.client).joinedload(Client.pro)    # Eager loading du client pro
            )
            .filter(and_(
                Order.id_client == id_client,
                or_(
                    Order.is_facturee.is_(False),
                    Order.is_expediee.is_(False)
                )
            ))
            .all()
        )

    return commandes

def get_commercial_indicators() -> Dict[str, Any] | None:
    """
    Récupère les indicateurs commerciaux:
        - Chiffre d'affaire mensuel
        - Chiffre d'affaire annuel
        - Panier moyen
        - Clients actifs
        - Commandes annuelles

    Returns:
        Dict[str, Any]: Dictionnaire des indicateurs commerciaux
    """
    # Ouverture de la session
    db_session: SessionBdDType = get_db_session()

    # Récupération des dates de référence
    today = date.today()
    first_day_of_month = today.replace(day=1)
    first_day_of_year = today.replace(month=1, day=1)

    # Récupération des indicateurs commerciaux et gestion des exceptions
    try:
        indicators: Dict[str, List[int | float | str]] | None = {
            # Chiffre d'affaire total facturé pour le mois en cours
            "ca_current_month": [
                round(db_session.query(func.sum(Order.montant))
                .filter(
                    Order.is_facturee.is_(True),
                    Order.date_commande >= first_day_of_month
                ).scalar() or 0.0, 2),
                'CA Mensuel'
            ],

            # Chiffre d'affaire total facturé pour l'année en cours
            "ca_current_year": [
                round(db_session.query(func.sum(Order.montant))
                .filter(
                    Order.is_facturee.is_(True),
                    Order.date_commande >= first_day_of_year
                ).scalar() or 0.0, 2),
                'CA Annuel'
            ],

            # Panier moyen annuel
            "average_basket": [
                round(db_session.query(func.avg(Order.montant))
                .filter(
                    Order.is_facturee.is_(True),
                    Order.date_commande >= first_day_of_year
                ).scalar() or 0.0, 2),
                'Panier Moyen'
            ],

            # Clients actifs
            "active_clients": [
                db_session.query(func.count(func.distinct(Order.id_client)))    # pylint: disable=not-callable
                .filter(
                    Order.is_facturee.is_(True),
                    Order.date_commande >= first_day_of_year
                ).scalar() or 0,
                'Clients Actifs'
            ],

            # Nombre de commandes par an
            "orders_per_year": [
                db_session.query(func.count(Order.id))  # pylint: disable=not-callable
                .filter(
                    Order.is_facturee.is_(True),
                    Order.date_commande >= first_day_of_year
                ).scalar() or 0,
                'Commandes Annuelles'
            ]
        }
    except SQLAlchemyError:
        indicators = None
    return indicators
