"""API REST - Routes utilitaires diverses pour l'application ACFC."""

from typing import Any, Dict, List
from flask.blueprints import Blueprint
from flask import request, jsonify
from app_acfc.config.config_models import GeoMethods
from app_acfc.models.templates_models import PrepareTemplates, Constants

api_bp = Blueprint('api',
                   __name__,
                   url_prefix='/api',
                   static_folder='statics/api')

# ====================================================================
# Routes utilitaires diverses
# ====================================================================

@api_bp.route('/indic-tel', methods=['GET'])
def get_indic_tel() -> Any:
    """
    API REST pour récupérer les indicatifs téléphoniques par pays.
    
    Args:
        ilike_pays (str): Nom du pays (partiel, insensible à la casse)
        
    Returns:
        JSON: Liste des indicatifs téléphoniques
    """
    if request.method != 'GET':
        return PrepareTemplates.error_4xx(status_code=405,
                                    status_message=Constants.messages('error_400', 'wrong_road'),
                                    log=True)
    try:
        indicatifs = GeoMethods.get_indicatifs_tel()
        indicatifs_list: List[Dict[str, str]] = [
            {
                'label': f'{ind.pays} ({ind.indicatif})',
                'value': f'+{ind.indicatif}'
            } for ind in indicatifs
        ]
        return jsonify(indicatifs_list), 200
    except AttributeError as e:
        message = f"Erreur d'attribut lors de la récupération des indicatifs : {str(e)}"
        return PrepareTemplates.error_5xx(status_code=500,
                                          status_message=message,
                                          log=True, specific_log=Constants.log_files('500'))
    except TypeError as e:
        message = f"Erreur de type lors de la récupération des indicatifs : {str(e)}"
        return PrepareTemplates.error_5xx(status_code=500,
                                          status_message=message,
                                          log=True, specific_log=Constants.log_files('500'))
