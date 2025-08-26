from flask import Blueprint, jsonify

commercial_bp = Blueprint('commercial',
                          __name__,
                          url_prefix='/commercial',
                          static_folder='statics/commercial')


@commercial_bp.route('/')
def commercial_index():
    return jsonify({'offers': []})


@commercial_bp.route('/hello')
def hello_commercial():
    return 'Commercial blueprint: hello'

@commercial_bp.route('/commandes/create/client/<id_client>', methods=['GET'])
def create_commande(id_client):
    # Logique pour créer une commande
    return jsonify({'message': 'Commande créée avec succès'}), 201

@commercial_bp.route('/factures/<int:id_facture>', methods=['GET'])
def factures_details(id_facture):
    # Logique pour afficher les détails de la facture
    return jsonify({'facture_id': id_facture, 'details': 'Détails de la facture'})

@commercial_bp.route('/commandes/<int:id_commande>', methods=['GET'])
def commandes_details(id_commande):
    # Logique pour afficher les détails de la commande
    return jsonify({'commande_id': id, 'details': 'Détails de la commande'})