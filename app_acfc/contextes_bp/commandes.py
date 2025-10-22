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
from app_acfc.modeles import (Client, DevisesFactures, Facture, Order, get_db_session)
from app_acfc.habilitations import validate_habilitation, CLIENTS
import qrcode
from io import BytesIO
import base64
from app_acfc.models.templates_models import PrepareTemplates, Constants
from app_acfc.models.orders_models import OrdersModel
from app_acfc.models.bills_models import BillsModels
from app_acfc.models.templates_models import Constants

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
            for entry in order.entries_to_merge:
                order.db_session.merge(entry)
            order.db_session.merge(order.order)
            order.db_session.commit()
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
    # Récupérer les données de la commande
    order = OrdersModel(request) \
                .get_order_data(id_order=id_order).order_details

    # Générer l'URL de gestion de la commande
    commande_url = url_for(Constants.return_pages('commandes', 'detail'),
                           id_client=id_client, id_order=id_order, _external=True)
    
    # Créer le QR code
    qr = qrcode.QRCode(version=1,
        error_correction=qrcode.ERROR_CORRECT_L,
        box_size=3,border=1)
    qr.add_data(commande_url)
    qr.make(fit=True)

    # Générer l'image QR code en base64
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, 'PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Renvoyer le template avec les données de la commande et le QR code
    return PrepareTemplates.notes(template=Constants.templates('commande-print'),
                                  order=order,
                                  order_url=commande_url,
                                  qr_code_base64=qr_code_base64,
                                  now=datetime.now())

@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_order>/facturer', methods=['POST'])
@validate_habilitation(CLIENTS)
def order_bill(id_client: int, id_order: int):
    """Traiter la facturation de lignes sélectionnées"""
    if request.method == 'POST':
        # Récupérer les données de facturation depuis la requête avec la classe dédiée
        # et créer la nouvelle facture
        order_to_bill = BillsModels(request) \
                            .post_bill_data(id_client=id_client, id_order=id_order) \
                            .create_new_bill()
        try:
            order_to_bill.session_db.commit()
        except Exception as e:
            raise ValueError(Constants.messages(type_msg='error_500', second_type_message='default') + f' : ({e})')
        
        # Mettre à jour la commande associée
        order_to_bill.mark_order_as_billed()

        try:
            order_to_bill.session_db.commit()
        except Exception as e:
            raise ValueError(Constants.messages(type_msg='error_500', second_type_message='default') + f' : ({e})')

        message = Constants.messages(type_msg='factures', second_type_message='created')
        return redirect(url_for(Constants.return_pages('commandes', 'detail'),
                                id_client=id_client,
                                id_order=id_order,
                                success_message=message))

@commandes_bp.route('/client/<int:id_client>/commandes/<int:id_order>/expedier', methods=['POST'])
@validate_habilitation(CLIENTS)
def order_ship(id_client: int, id_order: int):
    """Traiter l'expédition de lignes sélectionnées"""
    pass

@commandes_bp.route('/client/<int:id_client>/facture/<int:id_facture>')
@validate_habilitation(CLIENTS)
def bill_details(id_client: int, id_facture: int):
    """Afficher les détails d'une facture"""
    pass

@commandes_bp.route('/client-<int:id_client>/facture-<int:id_facture>/imprimer', methods=['POST'])
@validate_habilitation(CLIENTS)
def bill_print(id_client: int, id_facture: int):
    """Imprimer la facture immédiatement
    Vérifie si la facture peut être imprimée (non déjà imprimée)."""
    session_db: SessionBdDType = get_db_session()
    bill = session_db \
                .query(Facture) \
                .options(
                    joinedload(Facture.commande)
                        .joinedload(Order.client),
                    joinedload(Facture.commande)
                        .joinedload(Order.devises),
                    joinedload(Order.adresse_facturation),
                    joinedload(Order.adresse_livraison)
                ).filter(
                    Facture.id == id_facture,
                    Facture.id_client == id_client
                ).first()
    if not bill:
        raise NotFound(Constants.messages(type_msg='error_404', second_type_message='not_found'))
    elif bill.is_imprime:
        error_message = Constants.messages(type_msg='factures', second_type_message='exists')
        return redirect(url_for(Constants.return_pages('commandes', 'detail'),
                                id_client=id_client,
                                id_facture=id_facture,
                                error_message=error_message))
    else:
        # Marquer la facture comme imprimée
        bill.is_imprime = True
        bill.date_impression = datetime.now()
        try:
            session_db.merge(bill)
            session_db.commit()
        except Exception as e:
            error_message = Constants.messages(type_msg='error_500', second_type_message='default') + f' : ({e})'
            return redirect(url_for(Constants.return_pages('commandes', 'bill_detail'),
                                    id_client=id_client,
                                    id_facture=id_facture,
                                    error_message=error_message))
        
        #TODO: Générer le PDF de la facture et l'enregistrer dans le système de fichiers ou le service de stockage
        
        # Rediriger vers la page d'impression de la facture
        return redirect(url_for(Constants.return_pages('commandes', 'bill_print'),
                                id_client=id_client,
                                id_facture=id_facture))

@commandes_bp.route('/client/<int:id_client>/facture/<int:id_facture>/impression')
@validate_habilitation(CLIENTS)
def bill_print(id_client: int, id_facture: int):
    """Afficher la facture pour impression"""
    pass
