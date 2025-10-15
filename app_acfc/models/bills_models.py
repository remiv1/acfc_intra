from flask import Request, session
from typing import List, Optional
import json
from modeles import Order, DevisesFactures, Client
from datetime import datetime
from app_acfc.modeles import get_db_session, SessionBdDType
from sqlalchemy.orm import joinedload, with_loader_criteria

class BillsModels:
    def __init__(self, request: Request) -> None:
        self.request = request

    def get_bill_data(self, *, id_client: int, id_order: int) -> 'BillsModels':
        """
        Récupère les données nécessaires pour la facturation d'une commande.
        """
        return self

    def post_bill_data(self, *, id_client: int, id_order: int) -> 'BillsModels':
        """
        Traite les données de facturation soumises pour une commande.
        """
        date_facturation = self.request.form.get('date_facturation', datetime.now().strftime('%Y-%m-%d'))
        self.date_facturation = datetime.strptime(date_facturation, '%Y-%m-%d')
        ids_lignes_facturees = self.request.form.get('ids_lignes_facturees', None)
        self.ids_lignes_facturees = ids_lignes_facturees.split(",") if ids_lignes_facturees else []

        # Récupération de la commande et de ses composantes
        session_db: SessionBdDType = get_db_session()
        self.order_serveur = session_db \
                    .query(Order) \
                    .options(
                        joinedload(Order.client),
                        joinedload(Order.client)
                            .joinedload(Client.mails),
                        joinedload(Order.client)
                            .joinedload(Client.tels),
                        joinedload(Order.adresse_livraison),
                        joinedload(Order.adresse_facturation),
                        joinedload(Order.devises),
                        with_loader_criteria(
                            DevisesFactures,
                            lambda cls: cls.id.in_(ids_lignes_facturees),
                            include_aliases=True
                        )
                    ).filter(
                        Order.id == id_order,
                        Order.id_client == id_client
                    ).first()

        return self
    
    def check_last_bill_for_order(self, *, id_order: int) -> None:
        """
        Vérifie qu'il s'agit de la dernière facture
        """
        session_db: SessionBdDType = get_db_session()
        order_entries: List[DevisesFactures] = session_db.query(DevisesFactures) \
                                                    .filter(
                                                        DevisesFactures.id_order == id_order,
                                                        DevisesFactures.is_facture == True
                                                    ).all()
        self.last = len(order_entries) == 0
