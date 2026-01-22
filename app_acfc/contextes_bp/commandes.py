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

from datetime import datetime
from flask import Blueprint, request, redirect, url_for
from sqlalchemy.orm import Session as SessionBdDType, joinedload
from sqlalchemy.exc import SQLAlchemyError
from werkzeug import Response
from werkzeug.exceptions import NotFound
from app_acfc.db_models import (Client, DevisesFactures, Facture, Order)
from app_acfc.config.config_models import get_db_session
from app_acfc.habilitations import validate_habilitation, CLIENTS, FORCE_DE_VENTE
from app_acfc.models.templates_models import PrepareTemplates, Constants as c
from app_acfc.models.orders_models import OrdersModel
from app_acfc.models.bills_models import BillsModels
from app_acfc.functions.visuals import generate_qrcode
from app_acfc.common import BillsDocument

# Création du blueprint
commandes_bp = Blueprint(name='commandes', import_name=__name__, url_prefix='/commandes')

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
@validate_habilitation([CLIENTS, FORCE_DE_VENTE])
def new_order(id_client: int) -> str | Response:
    """
    Créer une nouvelle commande pour un client.
    Affiche un formulaire pour sélectionner des produits et saisir les détails de la commande.
    1. Récupère le client par son ID.
    2. Si la méthode est POST, traite le formulaire :
        - Type d'action
    """

    # === GET : Gestion de la demande de formulaire ===
    if request.method == 'GET':
        session_db: SessionBdDType = get_db_session()
        client = session_db.query(Client).filter(Client.id == id_client).first()
        return PrepareTemplates.orders(subcontext='form', id_client=id_client,
                                       form_sub_context='create', client=client)

    # === POST : Gestion de la soumission du formulaire ===
    elif request.method == 'POST':
        session_db: SessionBdDType = get_db_session()

        # Créer la nouvelle commande avec les données du formulaire
        new_order_object = OrdersModel(request) \
                                .post_order_data(id_client=id_client, id_order=None)
        try:
            # Enregistrer la commande et ses entrées associées
            session_db.add(new_order_object.order)
            session_db.flush()  # Pour obtenir l'ID de la commande

            # Enregistrer les entrées associées
            for entry in new_order_object.client_entries:
                entry.id = None
                entry.id_order = new_order_object.order.id
                session_db.add(entry)

            # Finaliser la transaction
            session_db.commit()

            # Retourner à la fiche de la commande nouvellement créée
            message = c.messages(type_msg='commandes', second_type_message='created')
            return redirect(url_for(c.return_pages('commandes', 'detail'),
                                    id_client=id_client,
                                    id_order=new_order_object.order.id))
        except SQLAlchemyError as e:
            error_message = c.messages(type_msg='error_500',
                                       second_type_message='default') + f' : ({e})'
            return redirect(url_for(c.return_pages('commandes', 'detail'),
                                    id_client=id_client,
                                    id_order=new_order_object.order.id,
                                    error_message=error_message))

    # === Par défaut, rediriger vers la fiche client ===
    else:
        message = c.messages(type_msg='error_400', second_type_message='wrong_road')
        return redirect(url_for(c.return_pages('clients', 'detail'),
                                id_client=id_client,
                                error_message=message))

@commandes_bp.route('/client-<int:id_client>/commande-<int:id_order>/details')
@validate_habilitation([CLIENTS, FORCE_DE_VENTE])
def order_details(id_order: int, id_client: int):
    """Afficher les détails d'une commande"""
    try:
        # Récupérer les données de la commande
        order_details_object = OrdersModel(request) \
                    .get_order_data(id_order=id_order)
        return PrepareTemplates.orders(subcontext='details',
                                       order=order_details_object.order_details, log=True,
                                       id_client=id_client, message=order_details_object.message,
                                       error_message=order_details_object.error_message,
                                       success_message=order_details_object.success_message)

    except SQLAlchemyError as e:
        message = c.messages(type_msg='error_500', second_type_message='default') + f' : ({e})'
        return redirect(url_for(c.return_pages('clients', 'detail'),
                                id_client=id_client,
                                error_message=message,
                                tab='order'))

@commandes_bp.route('/client-<int:id_client>/commande-<int:id_order>/modifier',
                    methods=['GET', 'POST'])
@validate_habilitation([CLIENTS, FORCE_DE_VENTE])
def edit_order(id_client: int, id_order: int):
    """Modifier une commande existante"""
    # === Gestion de la demande de formulaire ===
    if request.method == 'GET':
        order = OrdersModel(request) \
                    .get_order_data(id_order=id_order)
        if not order.order_details:
            raise NotFound(c.messages(type_msg='error_404', second_type_message='not_found'))
        return PrepareTemplates.orders(subcontext='form',
                                       form_sub_context='edit',
                                       order=order.order_details)

    # === Gestion de la soumission du formulaire ===
    elif request.method == 'POST':
        try:
            # Mettre à jour la commande avec les nouvelles données
            order = OrdersModel(request) \
                        .post_order_data(id_client=id_client, id_order=id_order) \
                        .check_entries_changements()

            # Mettre à jour les éléments de la commande dans la base de données
            for entry in order.entries_to_merge:
                order.db_session.merge(entry)

            # Mettre à jour la commande en base de données
            order.db_session.merge(order.order)
            order.db_session.commit()

            # Retourner à la fiche de la commande modifiée
            message = c.messages(type_msg='commandes', second_type_message='updated')
            return redirect(url_for(c.return_pages('commandes', 'detail'),
                                    id_client=id_client,
                                    id_order=id_order,
                                    success_message=message))
        except SQLAlchemyError as e:
            message = c.messages(type_msg='error_500', second_type_message='default') + f' : ({e})'
            return redirect(url_for(c.return_pages('commandes', 'detail'),
                                    id_client=id_client,
                                    id_order=id_order,
                                    error_message=message))
    # === Par défaut, rediriger vers la fiche client ===
    else:
        message = c.messages(type_msg='error_400', second_type_message='wrong_road')
        return redirect(url_for(c.return_pages('clients', 'detail'),
                                id_client=id_client,
                                error_message=message,
                                tab='order'))

@commandes_bp.route('/client-<int:id_client>/commande-<int:id_order>/annuler', methods=['POST'])
@validate_habilitation(CLIENTS)
def cancel_order(id_order: int, id_client: int):
    """Annuler une commande (soft delete)"""
    session_db: SessionBdDType = get_db_session()

    # Récupérer les données de la commande
    order_details_object = OrdersModel(request) \
                .cancel_order(id_client=id_client, id_order=id_order)
    try:
        # Mettre à jour la commande et ses entrées associées
        session_db.merge(order_details_object.order)
        for entry in order_details_object.order.devises:
            session_db.merge(entry)

        # Finaliser la transaction
        session_db.commit()

        # Retourner à la fiche de la commande annulée
        message = c.messages(type_msg='commandes', second_type_message='deleted')
        return redirect(url_for(c.return_pages('commandes', 'detail'),
                                id_client=id_client,
                                id_order=id_order,
                                success_message=message))

    # === Gestion des erreurs de la base de données ===
    except SQLAlchemyError as e:
        message = c.messages(type_msg='error_500', second_type_message='default') + f' : ({e})'
        return redirect(url_for(c.return_pages('commandes', 'detail'),
                                id_client=id_client,
                                id_order=id_order,
                                error_message=message))

@commandes_bp.route('/client-<int:id_client>/commande-<int:id_order>/bon-impression')
@validate_habilitation(CLIENTS)
def order_purchase(id_order: int, id_client: int):
    """Afficher le bon de commande pour impression"""
    # Récupérer les données de la commande
    order = OrdersModel(request) \
                .get_order_data(id_order=id_order).order_details

    # Générer l'URL de gestion de la commande
    commande_url = url_for(c.return_pages('commandes', 'detail'),
                           id_client=id_client, id_order=id_order, _external=True)

    # Générer le QR code pour l'URL de la commande
    qr_code_base64 = generate_qrcode(commande_url)

    # Renvoyer le template avec les données de la commande et le QR code
    return PrepareTemplates.notes(template=c.templates('commande-print'), order=order,
                                  order_url=commande_url, qr_code_base64=qr_code_base64,
                                  now=datetime.now())

@commandes_bp.route('/client-<int:id_client>/commande-<int:id_order>/facturer', methods=['POST'])
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
            # Enregistrer la nouvelle facture en base de données
            order_to_bill.session_db.commit()

            # Mettre à jour la commande associée
            order_to_bill.mark_order_as_billed()

            # Finaliser la transaction
            order_to_bill.session_db.commit()

            # Retourner à la fiche de la commande facturée
            message = c.messages(type_msg='factures', second_type_message='created')
            return redirect(url_for(c.return_pages('factures', 'detail'),
                                    id_client=id_client,
                                    id_order=id_order,
                                    success_message=message))

        except SQLAlchemyError as e:
            message = c.messages(type_msg='error_500', second_type_message='default') + f' : ({e})'
            return redirect(url_for(c.return_pages('commandes', 'detail'),
                                    id_client=id_client,
                                    id_order=id_order,
                                    error_message=message))
    else:
        message = c.messages(type_msg='error_400', second_type_message='wrong_road')
        return redirect(url_for(c.return_pages('clients', 'detail'),
                                id_client=id_client,
                                error_message=message,
                                tab='order'))

@commandes_bp.route('/client-<int:id_client>/commande-<int:id_order>/expedier', methods=['POST'])
@validate_habilitation(CLIENTS)
def order_ship(id_client: int, id_order: int):
    """Traiter l'expédition de lignes sélectionnées"""
    #TODO: Créer la fonction d'expédition des commandes
    pass

@commandes_bp.route('/client-<int:id_client>/facture-<int:id_facture>/details', methods=['GET'])
@validate_habilitation(CLIENTS)
def bill_details(id_client: int, id_facture: int):
    """Affiche le détail d'une facture"""
    session_db: SessionBdDType = get_db_session()
    bill = session_db.query(Facture) \
                     .options(joinedload(Facture.commande).joinedload(Order.client),
                              joinedload(Facture.commande).joinedload(Order.devises),
                              joinedload(Facture.commande).joinedload(Order.adresse_facturation),
                              joinedload(Facture.commande).joinedload(Order.adresse_livraison)) \
                     .filter(Facture.id == id_facture, Facture.id_client == id_client) \
                     .first()
    if not bill:
        raise NotFound(c.messages(type_msg='error_404', second_type_message='not_found'))
    # Rediriger vers la page de la facture
    return PrepareTemplates.bill(sub_context='detail', id_client=id_client, bill=bill)

@commandes_bp.route('/client-<int:id_client>/facture-<int:id_facture>/print-save-<fiscal_id>',
                    methods=['GET'])
@validate_habilitation(CLIENTS)
def bill_print(id_client: int, id_facture: int, fiscal_id: str):
    """Générer le PDF d'une facture pour impression"""
    # Récupération du lieu d'impression
    print_location = request.args.get('print_location', default='local', type=str)

    # Générer le PDF de la facture
    session_db: SessionBdDType = get_db_session()
    bill = session_db.query(Facture) \
                     .filter(Facture.id == id_facture, Facture.id_client == id_client) \
                     .first()

    if not bill:
        raise NotFound(c.messages(type_msg='error_404', second_type_message='not_found'))

    # Créer le QR code pour le lien de règlement
    bill_url = url_for(c.return_pages('factures', 'detail'), id_client=id_client,
                       id_order=bill.id_order, _external=True)
    qr_code_base64 = generate_qrcode(bill_url)

    template = PrepareTemplates.bill_pdf(bill=bill, qr_code_base64=qr_code_base64)
    bill_document = BillsDocument()
    bill_document.upload(ref=fiscal_id, rendered_template=template)

    if print_location == 'local':
        return bill_document.download(ref=fiscal_id)
    return bill_document.print_with_cups()

@commandes_bp.route('/client-<int:id_client>/facture-<int:id_facture>/telecharger', methods=['GET'])
@validate_habilitation(CLIENTS)
def bill_download(id_client: int, id_facture: int):
    """Téléchargement du document PDF de la facture"""
    #TODO: Créer la fonction de téléchargement des factures
    pass
