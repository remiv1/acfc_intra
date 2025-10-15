from flask import Request, session
from typing import List, Optional
import json
from modeles import Order, DevisesFactures, Client
from datetime import datetime
from app_acfc.modeles import get_db_session, SessionBdDType
from sqlalchemy.orm import joinedload

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
        return self