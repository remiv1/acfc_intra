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
from app_acfc.modeles import (Order, Catalogue, Client, DevisesFactures, Mail, Telephone,
                              Facture, Operations, Ventilations, get_db_session)
from app_acfc.habilitations import validate_habilitation, CLIENTS
from logs.logger import acfc_log, DEBUG
from typing import List
import qrcode
from io import BytesIO
import base64
from app_acfc.models.templates_models import PrepareTemplates, Constants
from app_acfc.models.orders_models import OrdersModel
from app_acfc.models.products_models import ProductsModel
from typing import Any, Dict

# Création du blueprint
commandes_bp = Blueprint(name='commandes',
                         import_name=__name__,
                         url_prefix='/commandes')

# ====================================================================
# FILTRES JINJA2 PERSONNALISÉS
# ====================================================================

@commandes_bp.app_template_filter('entries_jsonify')
def entries_jsonify(entry: DevisesFactures) -> str:
    """Convertit une liste d'entrées en JSON."""
    entry.remise = entry.remise * 100 or 0
    return f'{entry.to_dict()}' \
                .replace("'", '"') \
                .replace('None', 'null') \
                .replace('True', 'true') \
                .replace('False', 'false')

# ====================================================================
# ROUTES DU BLUEPRINT
# ====================================================================

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
        client = session_db.query(Client).filter(Client.id == id_client).first()
        return PrepareTemplates.orders(subcontext='form',
                                       id_client=id_client,
                                       form_sub_context='create',
                                       client=client)

    # === Gestion de la soumission du formulaire ===
    elif request.method == 'POST':
        new_order = OrdersModel(request) \
                        .post_order_data(id_client=id_client, id_order=None)
        session_db: SessionBdDType = get_db_session()
        try:
            session_db.add(new_order.order)
            session_db.flush()  # Pour obtenir l'ID de la commande
            for entry in new_order.client_entries:
                entry.id = None
                entry.id_order = new_order.order.id
                session_db.add(entry)
            session_db.commit()
            message = Constants.messages(type_msg='commandes', second_type_message='created')
            return redirect(url_for(Constants.return_pages('commandes', 'detail'),
                                    id_client=id_client,
                                    id_order=new_order.order.id))
        except Exception as e:
            error_message = Constants.messages(type_msg='error_500', second_type_message='default') + f' : ({e})'
            return redirect(url_for(Constants.return_pages('commandes', 'detail'),
                                    id_client=id_client,
                                    id_order=new_order.order.id,
                                    error_message=error_message))
        
    # === Par défaut, rediriger vers la fiche client ===
    else:
        message = Constants.messages(type_msg='error_400', second_type_message='wrong_road')
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=id_client,
                                error_message=message))

@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_order>/details')
@validate_habilitation(CLIENTS)
def order_details(id_order: int, id_client: int):
    """Afficher les détails d'une commande"""
    try:
        order = OrdersModel(request) \
                    .get_order_data(id_order=id_order)
        return PrepareTemplates.orders(subcontext='details',
                                       order=order.order_details,
                                       log=True,
                                       id_client=id_client,
                                       message=order.message,
                                       error_message=order.error_message,
                                       success_message=order.success_message)
        
    except Exception as e:
        raise NotFound(Constants.messages(type_msg='error_500', second_type_message='default') + f' : ({e})')

@commandes_bp.route('/client-<int:id_client>/commande-<int:id_order>/modifier', methods=['GET', 'POST'])
@validate_habilitation(CLIENTS)
def edit_order(id_client: int, id_order: int):
    """Modifier une commande existante"""
    # === Gestion de la demande de formulaire ===
    if request.method == 'GET':
        order = OrdersModel(request) \
                    .get_order_data(id_order=id_order)
        if not order.order_details:
            raise NotFound(Constants.messages(type_msg='error_404', second_type_message='not_found'))
        return PrepareTemplates.orders(subcontext='form',
                                       form_sub_context='edit',
                                       order=order.order_details)
    # === Gestion de la soumission du formulaire ===
    elif request.method == 'POST':
        try:
            order = OrdersModel(request) \
                        .post_order_data(id_client=id_client, id_order=id_order) \
                        .check_entries_changements()
            session_db: SessionBdDType = get_db_session()
            for entry in order.entries_to_merge:
                session_db.merge(entry)
            session_db.merge(order.order)
            session_db.commit()
            message = Constants.messages(type_msg='commandes', second_type_message='updated')
            return redirect(url_for(Constants.return_pages('commandes', 'detail'),
                                    id_client=id_client,
                                    id_order=id_order,
                                    success_message=message))
        except Exception as e:
            error_message = Constants.messages(type_msg='error_500', second_type_message='default') + f' : ({e})'
            return redirect(url_for(Constants.return_pages('commandes', 'detail'),
                                    id_client=id_client,
                                    id_order=id_order,
                                    error_message=error_message))
    # === Par défaut, rediriger vers la fiche client ===
    else:
        message = Constants.messages(type_msg='error_400', second_type_message='wrong_road')
        return redirect(url_for(Constants.return_pages('clients', 'detail'),
                                id_client=id_client,
                                error_message=message,
                                tab='order'))

@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_order>/annuler', methods=['POST'])
@validate_habilitation(CLIENTS)
def cancel_order(id_order: int, id_client: int):
    """Annuler une commande (soft delete)"""
    order_details = OrdersModel(request) \
                .cancel_order(id_client=id_client, id_order=id_order)
    session_db: SessionBdDType = get_db_session()
    try:
        session_db.merge(order_details.order)
        for entry in order_details.order.devises:
            session_db.merge(entry)
        session_db.commit()
        message = Constants.messages(type_msg='commandes', second_type_message='deleted')
        return redirect(url_for(Constants.return_pages('commandes', 'detail'),
                                id_client=id_client,
                                id_order=id_order,
                                success_message=message))
    except Exception as e:
        error_message = Constants.messages(type_msg='error_500', second_type_message='default') + f' : ({e})'
        return redirect(url_for(Constants.return_pages('commandes', 'detail'),
                                id_client=id_client,
                                id_order=id_order,
                                error_message=error_message))

@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_order>/bon-impression')
@validate_habilitation(CLIENTS)
def order_purchase(id_order: int, id_client: int):
    """Afficher le bon de commande pour impression"""
    order = OrdersModel(request) \
                .get_order_data(id_order=id_order)
    

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
