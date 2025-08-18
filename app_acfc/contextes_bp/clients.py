from flask import Blueprint, render_template, jsonify
from typing import Dict, List, Any

clients_bp = Blueprint('clients',
                       __name__,
                       url_prefix='/clients',
                       static_folder='statics/clients')


@clients_bp.route('/rechercher', methods=['GET'])
def clients_list()  :
    return render_template('base.html', context='clients', sub_context='research')

@clients_bp.route('/clients', methods=['GET'])
def get_clients():
    clients: List[Dict[str, Any]] = [
        {"id": 1, "global_name": "Client A"},
        {"id": 2, "global_name": "Client B"},
        {"id": 3, "global_name": "Client C"},
    ]
    return jsonify(clients)

@clients_bp.route('/hello')
def hello_clients():
    return 'Clients blueprint: hello'
