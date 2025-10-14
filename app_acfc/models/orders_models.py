from flask import Request, session
from typing import List, Optional
import json
from modeles import Order, DevisesFactures, Client
from datetime import datetime
from app_acfc.modeles import get_db_session, SessionBdDType
from sqlalchemy.orm import joinedload

class OrdersModel:
    def __init__(self, request: Request) -> None:
        # Récupération des messages de la requête
        self.message = request.args.get('message', None)
        self.error_message = request.args.get('error_message', None)
        self.success_message = request.args.get('success_message', None)

        self.request = request

    def _check_order_status(self, id_order: Optional[int], id_client: int) -> None:
        """
        Détermine self.order et self.entries en fonction de l'ID de la commande.
        """
        session_db: SessionBdDType = get_db_session()
        if id_order:
            self.is_new = False
            self.order: Order = session_db.query(Order).filter_by(id=id_order, id_client=id_client).first()
            if not self.order:
                raise ValueError("Order non trouvée")
            self.serveur_entries: List[DevisesFactures] = session_db.query(DevisesFactures).filter_by(id_order=id_order).all()
            if not self.serveur_entries:
                raise ValueError("Aucune entrée trouvée pour cette commande")
        else:
            self.is_new = True
            self.order = Order()
            self.serveur_entries: List[DevisesFactures] = []

    def _complete_create_or_update(self, entry: DevisesFactures) -> DevisesFactures:
        """
        Complète les champs nécessaires pour la création ou la mise à jour d'une entrée.
        """
        if self.is_new: entry.created_by = session.get('pseudo', 'system')
        else: entry.modified_by = session.get('pseudo', 'system')
        return entry

    def post_order_data(self, id_client: int, id_order: Optional[int]) -> 'OrdersModel':
        """
        Récupère les données de la commande depuis la requête.

        Returns:
            OrdersModel: Instance de OrdersModel contenant les données de la commande
        """
        self._check_order_status(id_order, id_client)

        # Gestion de la commande
        self.order.id_client = id_client
        self.order.date_commande = datetime.strptime(self.request.form.get('date_commande', ''), '%Y-%m-%d').date()
        self.order.adresse_facturation = self.request.form.get('id_adresse_facturation', None)
        self.order.adresse_livraison = self.request.form.get('id_adresse_livraison', self.order.adresse_facturation)
        self.order.descriptif = self.request.form.get('descriptif', '').strip()
        self.order.is_ad_livraison = (self.order.adresse_livraison != self.order.adresse_facturation)

        # Extraction des entrées du formulaire
        self.client_entries: List[DevisesFactures] = []
        for key in self.request.form:
            if key.startswith('lignes_'):
                raw_json = self.request.form.get(key)
                if raw_json:
                    try:
                        product = json.loads(raw_json)
                        entry = DevisesFactures(
                            id=product.get('id', None),
                            reference=product.get('reference', ''),
                            designation=product.get('designation', ''),
                            prix_unitaire=float(product.get('prix_unitaire', 0.0)),
                            qte=int(product.get('qte', 1)),
                            remise=float(product.get('remise', 0.0)) / 100
                        )
                        entry = self._complete_create_or_update(entry)
                        self.client_entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        sum_client_value = float(self.request.form.get('montant', '0').replace(',', '.'))
        sum_server_value = round(float(
            sum(entry.prix_unitaire * entry.qte * (1 - entry.remise) for entry in self.serveur_entries)
            ), 2)
        if abs(sum_client_value - sum_server_value) > 0.01:
            self.order.montant = sum_client_value
        else:
            self.order.montant = sum_server_value

        return self
    
    def get_order_data(self, id_order: int) -> 'OrdersModel':
        """
        Prépare les données de la commande pour l'affichage.
        """
        session_db: SessionBdDType = get_db_session()
        order_details = session_db.query(Order) \
                        .options(
                            joinedload(Order.client),
                            joinedload(Order.client)
                                .joinedload(Client.mails),
                            joinedload(Order.client)
                                .joinedload(Client.tels),
                            joinedload(Order.adresse_livraison),
                            joinedload(Order.adresse_facturation),
                            joinedload(Order.devises)
                        ).filter(Order.id == id_order) \
                        .first()
        self.order_details = order_details if order_details else None
        
        return self

    def check_entries_changements(self) -> 'OrdersModel':
        """
        Compare les entrées du client avec celles du serveur pour déterminer les ajouts, suppressions et modifications.
        """
        serveur_dict = {entry.id: entry for entry in self.serveur_entries}
        client_entries = {entry.id: entry for entry in self.client_entries}

        # Ajouter les nouveaux produits
        
        entries_to_add: List[DevisesFactures] = [entry for entry in self.client_entries if entry.id == 'new']

        # Mettre à jour les produits existants
        entries_to_update: List[DevisesFactures] = [entry for entry in self.client_entries if entry.id in serveur_dict]

        # Supprimer les produits retirés
        entries_to_delete: List[DevisesFactures] = [entry for entry in self.serveur_entries if entry.id not in client_entries]

        # Création d'une liste combinée pour les mises à jour
        self.entries_to_merge: List[DevisesFactures] = []

        for entry in entries_to_add:
            entry.id = None  # Pour forcer l'insertion
            entry.id_order = self.order.id
            self.entries_to_merge.append(entry)

        for entry in entries_to_update:
            self.entries_to_merge.append(entry)

        for entry in entries_to_delete:
            entry.is_annulee = True
            self.entries_to_merge.append(entry)

        return self
    