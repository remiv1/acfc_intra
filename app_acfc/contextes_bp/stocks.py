"""Module de gestion des stocks. Contient les routes et API pour la gestion des stocks."""

from flask import Blueprint, jsonify

stocks_bp = Blueprint('stocks', __name__, url_prefix='/stocks', static_folder='statics/stocks')


@stocks_bp.route('/')
def stocks_index():
    """Page d'accueil du module stocks."""
    return jsonify({'stocks': []})
