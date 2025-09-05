from flask import Blueprint, jsonify
from app_acfc.habilitations import (
    validate_habilitation, GESTIONNAIRE
    )

catalogue_bp = Blueprint('catalogue',
                         __name__,
                         url_prefix='/catalogue',
                         static_folder='statics/catalogue')

@validate_habilitation(GESTIONNAIRE)
@catalogue_bp.route('/')
def index():
    return jsonify({'products': []})
