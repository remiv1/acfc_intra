from flask import Request, session
from typing import List, Optional
import json
from modeles import Order, DevisesFactures, Client
from datetime import datetime
from app_acfc.modeles import get_db_session, SessionBdDType
from logs.logger import acfc_log, WARNING
from sqlalchemy.orm import joinedload

class OrdersModel:
    def __init__(self, request: Request) -> None:
        # Récupération des messages de la requête
        self.message = request.args.get('message', None)
        self.error_message = request.args.get('error_message', None)
        self.success_message = request.args.get('success_message', None)
        self.db_session: SessionBdDType = get_db_session()
        self.request = request

    def _check_order_status(self, *, id_order: Optional[int], id_client: int, order: Optional[Order]=None) -> None:
        """
        Détermine self.order et self.entries en fonction de l'ID de la commande.
        """
        if id_order:
            self.is_new = False
            self.order: Order = self.db_session.query(Order) \
                                        .filter_by(id=id_order, id_client=id_client) \
                                        .first()
            if not self.order:
                raise ValueError("Order non trouvée")
            self.serveur_entries: List[DevisesFactures] = self.db_session.query(DevisesFactures).filter_by(id_order=id_order).all()
            if not self.serveur_entries:
                raise ValueError("Aucune entrée trouvée pour cette commande")
        else:
            self.is_new = True
            self.order = Order() if not order else order
            self.serveur_entries: List[DevisesFactures] = []

    def _check_entries_status(self, *, id_order: int, id_client: int) -> None:
        """
        Vérifie l'état des entrées de la commande.
        """
        # Récupération de la commande depuis la base de données
        order = self.db_session.query(Order) \
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
                            Order.id == id_order,
                            Order.id_client == id_client
                        ).first()

        # Détermination des états de la commande
        if order:
            self.canceled = order.is_annulee
            self.invoiced = order.is_expediee
            self.billed = order.is_facturee
            self.part_billed = False
            for entry in order.devises:
                if entry.is_expedie:
                    self.part_billed = True
                    break
        else:
            self.canceled = False
            self.invoiced = False
            self.billed = False
            self.part_billed = False        

    def _complete_create_or_update(self, *, entry: DevisesFactures) -> DevisesFactures:
        """
        Complète les champs nécessaires pour la création ou la mise à jour d'une entrée.
        """
        if self.is_new: entry.created_by = session.get('pseudo', 'system')
        else: entry.modified_by = session.get('pseudo', 'system')
        return entry
    
    def _canceled_entries_filter(self) -> None:
        """
        Filtre les entrées annulées.
        """
        if self.order_details:
            self.order_details.devises = [entry for entry in self.order_details.devises if not entry.is_annulee]
        else:
            raise ValueError("order_details n'est pas défini")
        
    def _is_new_line(self, *, entry_id: str | None, is_new_order: bool = False) -> Optional[int]:
        """
        Détermine si une entrée est nouvelle en fonction de son ID.

        Args:
            entry_id (str): L'ID de l'entrée à vérifier.

        Returns:
            Optional[int]: None si l'entrée est nouvelle, sinon l'ID converti en int.
        """
        if is_new_order:
            return None
        elif str(entry_id).startswith('new') or entry_id is None:
            return None
        else:
            return int(entry_id)

    def post_order_data(self, *, id_client: int, id_order: Optional[int]) -> 'OrdersModel':
        """
        Récupère les données de la commande depuis la requête.

        Returns:
            OrdersModel: Instance de OrdersModel contenant les données de la commande
        """
        self._check_order_status(id_order=id_order, id_client=id_client)

        # Gestion de la commande
        self.order.id_client = id_client
        self.order.date_commande = datetime.strptime(self.request.form.get('date_commande', ''), '%Y-%m-%d').date()
        self.order.id_adresse_facturation = self.request.form.get('id_adresse_facturation', None)
        self.order.id_adresse_livraison = self.request.form.get('id_adresse_livraison', self.order.id_adresse_facturation)
        self.order.descriptif = self.request.form.get('descriptif', '').strip()
        self.order.is_ad_livraison = (self.order.id_adresse_livraison != self.order.id_adresse_facturation)

        # Extraction des entrées du formulaire
        self.client_entries: List[DevisesFactures] = []
        for key in self.request.form:
            # Toutes les clés de lignes sont censées commencer par 'lignes_'
            if key.startswith('lignes_'):
                # Ici, on récupère les données JSON de la ligne dans le champs caché
                raw_json = self.request.form.get(key)
                if raw_json:
                    try:
                        # Ensuite, on transforme la chaîne JSON en objet de classe (base de données)
                        product = json.loads(raw_json)
                        _id = self._is_new_line(entry_id=product.get('id', None), is_new_order=self.is_new)
                        entry = DevisesFactures(
                            id=_id,
                            reference=product.get('reference', ''),
                            designation=product.get('designation', ''),
                            prix_unitaire=float(product.get('prix_unitaire', 0.0)),
                            qte=int(product.get('qte', 1)),
                            remise=float(product.get('remise', 0.0)) / 100
                        )
                        entry = self._complete_create_or_update(entry=entry)
                        self.client_entries.append(entry)
                    except json.JSONDecodeError:
                        continue

        # Validation du montant total entre le client et le serveur, avec une tolérance de 0.01
        sum_client_value = float(self.request.form.get('montant', '0').replace(',', '.'))
        sum_server_value = round(float(
            sum(entry.prix_unitaire * entry.qte * (1 - entry.remise) for entry in self.serveur_entries)
            ), 2)
        if abs(sum_client_value - sum_server_value) > 0.01:
            self.order.montant = sum_client_value
        else:
            # Log d'une erreur importante de montant pour correction par équipe technique
            acfc_log.log(level=WARNING,
                         message=f'Erreur importante de montant détectée pour la commande ID {self.order.id} du client ID {id_client} : {sum_client_value} != {sum_server_value}',
                         db_log=True
                         )
            self.order.montant = sum_server_value

        return self
    
    def get_order_data(self, *, id_order: int) -> 'OrdersModel':
        """
        Prépare les données de la commande pour l'affichage.
        """
        order_details = self.db_session.query(Order) \
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
                            Order.id == id_order
                        ).first()
        self.order_details = order_details if order_details else None
        self._canceled_entries_filter()
        return self

    def check_entries_changements(self) -> 'OrdersModel':
        """
        Compare les entrées du client avec celles du serveur pour déterminer les ajouts, suppressions et modifications.
        """
        serveur_dict = {entry.id: entry for entry in self.serveur_entries}
        client_entries = {entry.id: entry for entry in self.client_entries}

        # Ajouter les nouveaux produits

        entries_to_add: List[DevisesFactures] = [entry for entry in self.client_entries if entry.id == None]

        # Mettre à jour les produits existants
        entries_to_update: List[DevisesFactures] = [entry for entry in self.client_entries if entry.id in serveur_dict]

        # Supprimer les produits retirés
        entries_to_delete: List[DevisesFactures] = [entry for entry in self.serveur_entries if entry.id not in client_entries]

        # Création d'une liste combinée pour les mises à jour
        self.entries_to_merge: List[DevisesFactures] = []
        import logging
        for entry in entries_to_add:
            entry.id = None  # Pour forcer l'insertion
            entry.id_order = self.order.id
            logging.error(f"Type entry à merger : {type(entry)} | entry={entry}")
            self.entries_to_merge.append(entry)

        for entry in entries_to_update:
            logging.error(f"Type entry à merger : {type(entry)} | entry={entry}")
            self.entries_to_merge.append(entry)

        for entry in entries_to_delete:
            entry.is_annulee = True
            logging.error(f"Type entry à merger : {type(entry)} | entry={entry}")
            self.entries_to_merge.append(entry)

        return self
    
    def cancel_order(self, *, id_client: int, id_order: int) -> 'OrdersModel':
        """
        Annule une commande et toutes ses entrées.
        """
        # Vérification que les entrées sont toutes non facturées
        self._check_order_status(id_order=id_order, id_client=id_client)
        self._check_entries_status(id_order=id_order, id_client=id_client)
        if self.billed or self.part_billed:
            raise ValueError("Impossible d'annuler une commande facturée ou partiellement facturée.")
        else:
            self.order.is_annulee = True
            for entry in self.serveur_entries:
                entry.is_annule = True
        return self
    