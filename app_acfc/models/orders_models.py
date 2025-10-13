from flask import Request
from typing import List, Optional
import json
from modeles import Commande, DevisesFactures
from datetime import datetime

class OrdersModel:
    def __init__(self, request: Request) -> None:
        self.request = request

    def _check_order_status(self, id_commande: Optional[int], id_client: int) -> None:
        """
        Détermine self.order et self.entries en fonction de l'ID de la commande.
        """
        if id_commande:
            self.is_new = False
            self.order = Commande.query.filter_by(id=id_commande, id_client=id_client).first()
            if not self.order:
                raise ValueError("Commande non trouvée")
            self.serveur_entries = DevisesFactures.query.filter_by(id_commande=id_commande).all()
            if not self.serveur_entries:
                raise ValueError("Aucune entrée trouvée pour cette commande")
        else:
            self.is_new = True
            self.order = Commande()
            self.serveur_entries: List[DevisesFactures] = []

    def post_order_data(self, id_client: int, id_commande: Optional[int]) -> 'OrdersModel':
        """
        Récupère les données de la commande depuis la requête.

        Returns:
            OrdersModel: Instance de OrdersModel contenant les données de la commande
        """
        self._check_order_status(id_commande, id_client)

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
                        self.client_entries.append(DevisesFactures(
                            id=product.get('id', None),
                            reference=product.get('reference', ''),
                            designation=product.get('designation', ''),
                            prix_unitaire=product.get('prix', 0.0),
                            qte=product.get('quantite', 1),
                            remise=product.get('remise', 0.0)
                        ))
                    except json.JSONDecodeError:
                        continue
        sum_client_value = float(self.request.form.get('montant', '0').replace(',', '.'))
        sum_server_value = round(float(
            sum(entry.prix * entry.quantite * (1 - entry.remise) for entry in self.serveur_entries)
            ), 2)
        if abs(sum_client_value - sum_server_value) > 0.01:
            self.order.montant = sum_client_value
        else:
            self.order.montant = sum_server_value

        return self
    
    def check_entries_changements(self) -> 'OrdersModel':
        """
        Compare les entrées du client avec celles du serveur pour déterminer les ajouts, suppressions et modifications.
        """
        serveur_dict = {entry.id: entry for entry in self.serveur_entries}
        client_entries = {entry.id: entry for entry in self.client_entries}

        self.entries_to_add: List[DevisesFactures] = []
        self.entries_to_update: List[DevisesFactures] = []
        self.entries_to_delete: List[DevisesFactures] = []

        # Ajouter les nouveaux produits
        self.entries_to_add = [entry for entry in self.client_entries if entry.id == 'new']

        # Mettre à jour les produits existants
        self.entries_to_update = [entry for entry in self.client_entries if entry.id in serveur_dict]

        # Supprimer les produits retirés
        self.entries_to_delete = [entry for entry in self.serveur_entries if entry.id not in client_entries]

        return self