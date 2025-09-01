from flask import Blueprint, jsonify, request, render_template
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_, func
from app_acfc.modeles import SessionBdD, Client, Part, Pro, Telephone, Mail, Adresse
from logs.logger import acfc_log, DEBUG

commercial_bp = Blueprint('commercial',
                          __name__,
                          url_prefix='/commercial',
                          static_folder='statics/commercial')


@commercial_bp.route('/')
def commercial_index():
    """Page d'accueil du module commercial."""
    return render_template('base.html', 
                         title='ACFC - Module Commercial',
                         context='commercial')


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
    return render_template('base.html', 
                         title='ACFC - Liste des Clients',
                         context='commercial',
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
        # Récupération des paramètres de filtrage
        type_client = request.args.get('type_client', type=int)
        has_phone = request.args.get('has_phone', type=int)
        has_email = request.args.get('has_email', type=int)
        departement = request.args.get('departement', '').strip()
        ville = request.args.get('ville', '').strip()
        is_active = request.args.get('is_active', type=int)
        search = request.args.get('search', '').strip()
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # Validation des limites
        limit = min(limit, 500)  # Maximum 500 résultats
        
        with SessionBdD() as db_session:
            # Construction de la requête de base avec jointures optimisées
            query = db_session.query(Client).options(
                joinedload(Client.part),
                joinedload(Client.pro),
                joinedload(Client.tels),
                joinedload(Client.mails),
                joinedload(Client.adresses)
            )
            
            # Filtre par type de client
            if type_client in [1, 2]:
                query = query.filter(Client.type_client == type_client)
            
            # Filtre par statut actif/inactif
            if is_active is not None:
                query = query.filter(Client.is_active == bool(is_active))
            
            # Filtre par présence de téléphone
            if has_phone is not None:
                if has_phone == 1:
                    query = query.join(Telephone).filter(Telephone.id_client == Client.id)
                else:
                    subquery = db_session.query(Telephone.id_client).distinct()
                    query = query.filter(~Client.id.in_(subquery))
            
            # Filtre par présence d'email
            if has_email is not None:
                if has_email == 1:
                    query = query.join(Mail).filter(Mail.id_client == Client.id)
                else:
                    subquery = db_session.query(Mail.id_client).distinct()
                    query = query.filter(~Client.id.in_(subquery))
            
            # Filtre par département
            if departement:
                query = query.join(Adresse).filter(
                    Adresse.id_client == Client.id,
                    Adresse.is_active == True,
                    Adresse.code_postal.like(f"{departement}%")
                )
            
            # Filtre par ville
            if ville:
                query = query.join(Adresse).filter(
                    Adresse.id_client == Client.id,
                    Adresse.is_active == True,
                    Adresse.ville.ilike(f"%{ville}%")
                )
            
            # Recherche textuelle libre
            if search:
                # Pour les particuliers : recherche dans prénom et nom
                # Pour les professionnels : recherche dans raison sociale
                search_conditions = []
                
                if type_client != 2:  # Inclure les particuliers
                    search_conditions.append(
                        and_(
                            Client.type_client == 1,
                            or_(
                                Part.prenom.ilike(f"%{search}%"),
                                Part.nom.ilike(f"%{search}%")
                            )
                        )
                    )
                
                if type_client != 1:  # Inclure les professionnels
                    search_conditions.append(
                        and_(
                            Client.type_client == 2,
                            Pro.raison_sociale.ilike(f"%{search}%")
                        )
                    )
                
                if search_conditions:
                    # Joindre les tables appropriées selon le type de client
                    query = query.outerjoin(Part).outerjoin(Pro)
                    query = query.filter(or_(*search_conditions))
            
            # Tri par nom d'affichage
            query = query.outerjoin(Part).outerjoin(Pro).order_by(
                func.coalesce(
                    func.concat(Part.prenom, ' ', Part.nom),
                    Pro.raison_sociale
                )
            )
            
            # Application de la pagination
            total_count = query.count()
            clients = query.offset(offset).limit(limit).all()
            
            # Conversion en format JSON
            clients_data = []
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
                        if adresse.is_active and len(adresse.code_postal) >= 2:
                            client_dict['departement'] = adresse.code_postal[:2]
                            break
                
                clients_data.append(client_dict)
            
            return jsonify({
                'success': True,
                'clients': clients_data,
                'pagination': {
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_count
                },
                'filters_applied': {
                    'type_client': type_client,
                    'has_phone': has_phone,
                    'has_email': has_email,
                    'departement': departement,
                    'ville': ville,
                    'is_active': is_active,
                    'search': search
                }
            })
            
    except Exception as e:
        acfc_log(DEBUG, f"Erreur lors de la recherche de clients : {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la recherche de clients'
        }), 500