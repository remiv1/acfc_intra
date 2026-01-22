"""Module de gestion commerciale. Contient les routes et API pour la gestion des clients."""

from typing import Any, List
from flask import Blueprint, jsonify, request, render_template
from sqlalchemy.orm.session import Session as SessionBdD
from app_acfc.functions.clients import ClientsAPI

commercial_bp = Blueprint('commercial', __name__, url_prefix='/commercial',
                          static_folder='statics/commercial')

@commercial_bp.route('/')
def commercial_index():
    """Page d'accueil du module commercial."""
    return render_template('base.html', title='ACFC - Module Commercial', context='commercial')

@commercial_bp.route('/clients/liste')
def clients_liste():
    """
    Page de liste des clients avec filtres avancés.
    
    Permet de filtrer les clients par :
    - Type (Particulier/Professionnel)
    - Présence de téléphone
    - Présence d'email
    - Département (code postal)
    - Ville
    - Statut actif/inactif
    - Date de création
    """
    return render_template('base.html', title='ACFC - Commercial', context='commercial',
                           subcontext='filter_list')

@commercial_bp.route('/clients/api/search', methods=['GET'])
def clients_api_search():
    """
    API de recherche et filtrage des clients.
    
    Paramètres GET acceptés :
    - type_client : 1 (Particulier) ou 2 (Professionnel)
    - has_phone : 1 (avec téléphone) ou 0 (sans téléphone)
    - has_email : 1 (avec email) ou 0 (sans email)
    - departement : code département (2 premiers chiffres du code postal)
    - ville : nom de la ville (recherche partielle)
    - is_active : 1 (actif) ou 0 (inactif)
    - search : recherche textuelle libre (nom, prénom, raison sociale)
    - limit : nombre maximum de résultats (défaut: 100)
    - offset : pagination (défaut: 0)
    """
    try:
        filtering = ClientsAPI(request, SessionBdD())

        filtering.get_query() \
            .filter_part_pro() \
            .filter_by_dpt() \
            .filter_by_town() \
            .filter_has_phone() \
            .filter_has_email() \
            .filter_textual_search()

        # Validation des limites
        limit = min(filtering.limit, 500)  # Maximum 500 résultats

        # Application de la pagination
        total_count = filtering.query.count()
        clients = filtering.query.offset(filtering.offset).limit(limit).all()

        # Conversion en format JSON
        clients_data: List[Any] = []

        for client in clients:
            client_dict = client.to_dict()

            # Ajout des informations de contact
            client_dict['telephones'] = len(client.tels)
            client_dict['emails'] = len(client.mails)
            client_dict['has_phone'] = len(client.tels) > 0
            client_dict['has_email'] = len(client.mails) > 0

            # Ajout du département
            if client.adresses:
                for adresse in client.adresses:
                    if not adresse.is_inactive and len(adresse.code_postal) >= 2:
                        client_dict['departement'] = adresse.code_postal[:2]
                        break

            clients_data.append(client_dict)

        return jsonify({
            'success': True,
            'clients': clients_data,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': filtering.offset,
                'has_more': filtering.offset + limit < total_count
            },
            'filters_applied': {
                'type_client': filtering.type_client,
                'has_phone': filtering.has_phone,
                'has_email': filtering.has_email,
                'departement': filtering.departement,
                'ville': filtering.ville,
                'is_active': filtering.is_active,
                'search': filtering.search
            }
        })

    except KeyError as e:
        return jsonify({'success': False, 'error': f'Clé manquante : {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Valeur invalide : {str(e)}'}), 400
    except TypeError as e:
        return jsonify({'success': False, 'error': f'Type invalide : {str(e)}'}), 400
