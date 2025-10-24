from flask import Request, session
from typing import List
from modeles import Order, DevisesFactures, Client, Facture
from datetime import datetime
from app_acfc.modeles import get_db_session, SessionBdDType
from sqlalchemy.orm import joinedload
from decimal import Decimal
from logging import getLogger
from os import getenv

BILLS_PATH = getenv('BILLS_PATH', 'app/official/bills/')

class BillsModels:
    def __init__(self, request: Request) -> None:
        self.request = request

    def get_bill_data(self, *, id_client: int, id_order: int) -> 'BillsModels':
        """
        Récupère les données nécessaires pour la facturation d'une commande.
        """
        self.id_order = id_order
        self.id_client = id_client
        return self

    def post_bill_data(self, *, id_client: int, id_order: int) -> 'BillsModels':
        """
        Traite les données de facturation soumises pour une commande.
        """
        self.id_order = id_order
        self.id_client = id_client
        date_facturation = self.request.form.get('date_facturation', datetime.now().strftime('%Y-%m-%d'))
        self.date_facturation = datetime.strptime(date_facturation, '%Y-%m-%d')
        ids_lignes_facturees = self.request.form.get('ids_lignes_facturees', None)
        if ids_lignes_facturees:
            self.ids_lignes_facturees = [int(x) for x in ids_lignes_facturees.split(",") if x]
        else:
            self.ids_lignes_facturees = []
        # Récupération de la commande et de ses composantes
        self.session_db: SessionBdDType = get_db_session()
        self.order_serveur = self.session_db \
                    .query(Order) \
                    .options(
                        joinedload(Order.client),
                        joinedload(Order.client)
                            .joinedload(Client.mails),
                        joinedload(Order.client)
                            .joinedload(Client.tels),
                        joinedload(Order.adresse_livraison),
                        joinedload(Order.adresse_facturation),
                        joinedload(Order.devises)
                    ).filter(
                        Order.id == self.id_order,
                        Order.id_client == id_client
                    ).first()

        return self
    
    def _check_last_bill_for_order(self) -> bool:
        """
        Vérifie s'il reste des lignes non facturées dans la commande.
        Si toutes les lignes sont facturées, c'est la dernière facture.
        """
        
        # Utilise directement les devises de la commande chargée plutôt qu'une nouvelle requête
        if self.order_serveur and self.order_serveur.devises:
            # Vérifie si toutes les lignes de la commande sont maintenant facturées
            all_facturees = all(devise.is_facture for devise in self.order_serveur.devises if not devise.is_annulee)
            self.last = all_facturees
        else:
            # Fallback sur requête si les devises ne sont pas chargées
            self.session_db.flush()
            order_entries: List[DevisesFactures] = self.session_db.query(DevisesFactures) \
                                                        .filter(
                                                            DevisesFactures.id_order == self.id_order,
                                                            DevisesFactures.is_facture == False
                                                        ).all()
            self.last = order_entries == None or len(order_entries) == 0
        return self.last

    def create_new_bill(self) -> 'BillsModels':
        """
        Crée une nouvelle facture dans la base de données.
        """
        # Création de la nouvelle facture dans un premier temps
        new_bill = Facture(
            id_client=self.id_client,
            id_order=self.id_order,
            date_facturation=datetime.now(),
            created_by=session.get('pseudo', 'system'),
            created_at=self.date_facturation,
            montant_facture=0.0
        )

        # Ajout de la nouvelle facture à la session et flush pour obtenir l'ID
        self.session_db.add(new_bill)
        self.session_db.flush()
        id_facture = new_bill.id

        # Charger explicitement les devises à facturer pour garantir qu'elles soient attachées à la session
        self.devises_a_facturer = self.session_db.query(DevisesFactures).filter(
            DevisesFactures.id.in_(self.ids_lignes_facturees),
            DevisesFactures.id_order == self.id_order
        ).all()

        # Mise à jour des entrées de devises pour les marquer comme facturées
        total_amount = Decimal('0.0')
        for entry in self.devises_a_facturer:
            entry.is_facture = True
            entry.id_facture = id_facture
            entry.date_facturation = self.date_facturation.date()
            entry.modified_by = session.get('pseudo', 'system')
            total_amount += Decimal(entry.prix_total)

        # Mise à jour du montant total de la facture
        new_bill.montant_facture = total_amount
        self.session_db.merge(new_bill)

        return self
    
    def mark_order_as_billed(self) -> 'BillsModels':
        """
        Marque une commande comme facturée.
        """
        # Recharger la commande avec ses devises pour avoir l'état actuel après facturation
        self.order_serveur = self.session_db \
                    .query(Order) \
                    .options(
                        joinedload(Order.devises)
                        ) \
                    .filter(
                        Order.id == self.id_order,
                        Order.id_client == self.id_client
                    ).first()

        # Vérifie si c'est la dernière facture pour la commande
        self._check_last_bill_for_order()

        # Met à jour le statut de la commande. Si c'est la dernière facture, marque comme facturée
        if self.order_serveur:
            if self.last == True:
                self.order_serveur.is_facturee = True
                self.order_serveur.date_facturation = self.date_facturation.date()
            self.order_serveur.modified_by = session.get('pseudo', 'system')
            self.order_serveur.modified_at = self.date_facturation.date()
            self.session_db.merge(self.order_serveur)
        
        return self
