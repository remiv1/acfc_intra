from flask import Blueprint, jsonify

comptabilite_bp = Blueprint('comptabilite',
                            __name__,
                            url_prefix='/comptabilite',
                            static_folder='statics/comptabilite')


@comptabilite_bp.route('/')
def comptabilite_index():
    return jsonify({'entries': []})


@comptabilite_bp.route('/hello')
def hello_compta():
    return 'Comptabilité blueprint: hello'
