"""
ACFC - Module Commandes - Gestion des Commandes Clients
=======================================================

Blueprint Flask pour la gestion des commandes clients.
Ce module gère la création, modification et suivi des commandes.

Fonctionnalités principales :
- Création de commandes à partir de la fiche client
- Sélection de produits du catalogue avec filtres
- Gestion des états (facturation, expédition)
- Calcul automatique des montants

Auteur : Développement ACFC
Version : 1.0
"""

from flask import Blueprint, request, redirect, url_for
from datetime import datetime
from sqlalchemy.orm import Session as SessionBdDType, joinedload
from werkzeug import Response
from werkzeug.exceptions import NotFound
from app_acfc.modeles import (Commande, Catalogue, Client, Adresse, Mail, Telephone,
                              Facture, Operations, Ventilations, get_db_session)
from app_acfc.habilitations import validate_habilitation, CLIENTS
from typing import List
import qrcode
from io import BytesIO
import base64
from app_acfc.models.templates_models import PrepareTemplates, Constants
from app_acfc.models.orders_models import OrdersModel

# Création du blueprint
commandes_bp = Blueprint(name='commandes',
                         import_name=__name__,
                         url_prefix='/commandes')

@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_commande>/details')
@validate_habilitation(CLIENTS)
def order_details(id_commande: int, id_client: int):
    """Afficher les détails d'une commande"""
    session_db = get_db_session()
    try:
        commande = session_db.query(Commande) \
                        .options(
                            joinedload(Commande.client)
                                .joinedload(Client.mails),
                            joinedload(Commande.client)
                                .joinedload(Client.tels),
                            joinedload(Commande.adresse_livraison),
                            joinedload(Commande.adresse_facturation),
                            joinedload(Commande.devises)
                        ).filter(Commande.id == id_commande) \
                        .first()
        if not commande:
            raise NotFound("Commande non trouvée")

        return PrepareTemplates.orders(subcontext='details', commande=commande, log=True, id_client=id_client)
        
    except Exception as e:
        raise NotFound(Constants.messages(type_msg='error_500', second_type_message='default') + f' : ({e})')

@commandes_bp.route('/client-<int:id_client>/nouvelle-commande', methods=['GET', 'POST'])
@validate_habilitation(CLIENTS)
def new_order(id_client: int) -> str | Response:
    """
    Créer une nouvelle commande pour un client.
    Affiche un formulaire pour sélectionner des produits et saisir les détails de la commande.
    1. Récupère le client par son ID.
    2. Si la méthode est POST, traite le formulaire :
        - Type d'action
    """

    # === Gestion de la demande de formulaire ===
    if request.method == 'GET':
        session_db: SessionBdDType = get_db_session()
        current_year = datetime.now().year
        products: List[Catalogue] = session_db.query(Catalogue) \
                                        .filter(Catalogue.millesime >= current_year - 1,
                                                Catalogue.millesime <= current_year + 1) \
                                        .all()
        return PrepareTemplates.orders(subcontext='form',
                                       id_client=id_client,
                                       form_sub_context='create',
                                       catalogue_complet=products)
    
    # === Gestion de la soumission du formulaire ===
    elif request.method == 'POST':
        new_order = OrdersModel(request) \
                        .post_order_data(id_client=id_client, id_commande=None)
        session_db: SessionBdDType = get_db_session()
        try:
            session_db.add(new_order.order)
            session_db.flush()  # Pour obtenir l'ID de la commande
            for entry in new_order.client_entries:
                entry.id = None
                entry.id_commande = new_order.order.id
                session_db.add(entry)
            session_db.commit()
            message = Constants.messages(type_msg='commandes', second_type_message='created')
            return redirect(url_for(Constants.return_pages('commandes', 'detail'),
                                    id_client=id_client,
                                    id_commande=new_order.order.id))
        except Exception as e:
            error_message = Constants.messages(type_msg='error_500', second_type_message='default') + f' : ({e})'
            return redirect(url_for(Constants.return_pages('commandes', 'detail'),
                                    id_client=id_client,
                                    id_commande=new_order.order.id,
                                    error_message=error_message))
        
    # === Par défaut, rediriger vers la fiche client ===
    else:
        message = Constants.messages(type_msg='error_400', second_type_message='wrong_road')
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=id_client,
                                error_message=message))

@commandes_bp.route('/client-<int:id_client>/commande-<int:id_commande>/modifier', methods=['GET', 'POST'])
@validate_habilitation(CLIENTS)
def edit_order(id_client: int, id_commande: int):
    """Modifier une commande existante"""
    pass

@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_commande>/annuler', methods=['POST'])
@validate_habilitation(CLIENTS)
def cancel_order(id_commande: int, id_client: int):
    """Annuler une commande (soft delete)"""
    pass

@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_commande>/bon-impression')
@validate_habilitation(CLIENTS)
def order_purchase(id_commande: int, id_client: int):
    """Afficher le bon de commande pour impression"""
    pass

# Route pour obtenir les adresses d'un client (AJAX)
@commandes_bp.route('/api/client/<int:id_client>/adresses')
@validate_habilitation(CLIENTS)
def get_client_adresses(id_client: int):
    """API pour récupérer les adresses d'un client"""
    pass

@commandes_bp.route('/traiter_facturation', methods=['POST'])
@validate_habilitation(CLIENTS)
def traiter_facturation():
    """Traiter la facturation de lignes sélectionnées"""
    pass

@commandes_bp.route('/traiter_expedition', methods=['POST'])
@validate_habilitation(CLIENTS)
def traiter_expedition():
    """Traiter l'expédition de lignes sélectionnées"""
    pass

@commandes_bp.route('/facturer_commande', methods=['POST'])
@validate_habilitation(CLIENTS)
def facturer_commande():
    """Facturer les lignes sélectionnées d'une commande"""
    pass

@commandes_bp.route('/client/<int:id_client>/facture/<int:id_facture>')
@validate_habilitation(CLIENTS)
def bill_details(id_client: int, id_facture: int):
    """Afficher les détails d'une facture"""
    pass

@commandes_bp.route('/client/<int:id_client>/facture/<int:id_facture>/impression')
@validate_habilitation(CLIENTS)
def bill_print(id_client: int, id_facture: int):
    """Afficher la facture pour impression"""
    pass
