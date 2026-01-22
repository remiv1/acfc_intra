"""Catalogue blueprint for managing product catalogue routes."""

from flask import Blueprint, jsonify
from app_acfc.habilitations import validate_habilitation, GESTIONNAIRE

catalogue_bp = Blueprint('catalogue',
                         __name__,
                         url_prefix='/catalogue',
                         static_folder='statics/catalogue')

@validate_habilitation(GESTIONNAIRE)
@catalogue_bp.route('/')
def index():
    """Récupération des produits du catalogue."""
    return jsonify({'products': []})
