from flask import Blueprint, jsonify

clients_bp = Blueprint('clients',
                       __name__,
                       url_prefix='/clients',
                       static_folder='statics/clients')


@clients_bp.route('/')
def clients_list()  :
    # minimal implementation — can be extended
    return jsonify({'clients': []})


@clients_bp.route('/hello')
def hello_clients():
    return 'Clients blueprint: hello'
