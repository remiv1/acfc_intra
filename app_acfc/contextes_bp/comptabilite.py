"""Module de gestion comptable. Contient les routes et API pour la comptabilité."""

from flask import Blueprint, jsonify

comptabilite_bp = Blueprint('comptabilite', __name__, url_prefix='/comptabilite',
                            static_folder='statics/comptabilite')


@comptabilite_bp.route('/')
def comptabilite_index():
    """Page d'accueil du module comptabilité."""
    return jsonify({'entries': []})
