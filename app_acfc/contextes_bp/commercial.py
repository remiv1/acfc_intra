from flask import Blueprint, jsonify, request, Request, render_template
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload, Session as SessionBdDType, Query
from app_acfc.modeles import SessionBdD, Client, Part, Pro, Telephone, Mail, Adresse
from logs.logger import acfc_log, DEBUG
from typing import Any, List

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
                         title='ACFC - Commercial',
                         context='commercial',
                         subcontext='filter_list')

class ClientsAPI:
    def __init__(self, req:Request, session: SessionBdDType):
        self.request = req
        self.type_client = req.args.get('type_client', type=int)
        self.has_phone = req.args.get('has_phone', type=int)
        self.has_email = req.args.get('has_email', type=int)
        self.departement = req.args.get('departement', '').strip()
        self.ville = req.args.get('ville', '').strip()
        self.is_active = req.args.get('is_active', type=int)
        self.search = req.args.get('search', '').strip()
        self.limit = req.args.get('limit', default=100, type=int)
        self.offset = req.args.get('offset', default=0, type=int)
        self.session = session

    def close_session(self):
        if self.session:
            self.session.close()

    def validate_limit(self):
        if self.limit < 1:
            self.limit = 1
        elif self.limit > 500:
            self.limit = 500

    def validate_offset(self):
        if self.offset < 0:
            self.offset = 0

    def filter_part_pro(self):
        if self.type_client in [1, 2]:
            self.query.filter(Client.type_client == self.type_client)
        return self
    
    def filter_has_phone(self):
        if self.has_phone is not None:
            if self.has_phone == 1:
                self.query.join(Telephone).filter(Telephone.id_client == Client.id)
            else:
                subquery = self.session.query(Telephone.id_client).distinct()
                self.query.filter(~Client.id.in_(subquery))
        return self

    def filter_has_email(self):
        if self.has_email is not None:
            if self.has_email == 1:
                self.query.join(Mail).filter(Mail.id_client == Client.id)
            else:
                subquery = self.session.query(Mail.id_client).distinct()
                self.query.filter(~Client.id.in_(subquery))
        return self

    def filter_by_dpt(self):
        if self.departement:
            self.query = self.query.join(Adresse).filter(
                Adresse.id_client == Client.id,
                Adresse.is_active == True,
                Adresse.code_postal.ilike(f"%{self.departement}%")
            )
        return self
    
    def filter_by_town(self):
        if self.ville:
            self.query = self.query.join(Adresse).filter(
                Adresse.id_client == Client.id,
                Adresse.is_active == True,
                Adresse.ville.ilike(f"%{self.ville}%")
            )
        return self

    def filter_textual_search(self):
        # Filtrage par recherche textuelle
        #TODO: Erreur sur les recherches textuelles à revoir.
        if self.search:
            # Pour les particuliers, recherche par nom et prénom
            # Pour les professionnels, recherche par raison sociale
            search_conditions: List[Any] = []

            if self.type_client != 2:
                search_conditions.append(
                    and_(
                        Client.type_client == 1,
                        or_(
                            Part.prenom.ilike(f"%{self.search}%"),
                            Part.nom.ilike(f"%{self.search}%")
                        )
                    )
                )
            if self.type_client != 1:
                search_conditions.append(
                    and_(
                        Client.type_client == 2,
                        or_(
                            Pro.raison_sociale.ilike(f"%{self.search}%"),
                            Pro.siren.ilike(f"%{self.search}%")
                        )
                    )
                )
            if search_conditions:
                # Joindre les tables appropriées selon le type de client
                self.query = self.query.outerjoin(Part).outerjoin(Pro)
                self.query = self.query.filter(or_(*search_conditions))

            # Tri par nom d'affichage
            self.query = self.query.outerjoin(Part).outerjoin(Pro).order_by(
                func.coalesce(
                    func.concat(Part.prenom, ' ', Part.nom),
                    func.concat(Pro.raison_sociale, ' ', Pro.siren)
                )
            )

        return self

    def get_query(self):
        self.validate_limit()
        self.validate_offset()
        self.query = self.session.query(Client).options(
            joinedload(Client.part),
            joinedload(Client.pro),
            joinedload(Client.tels),
            joinedload(Client.mails),
            joinedload(Client.adresses)
        )
        return self

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
            
    except Exception as e:
        acfc_log.log_to_file(DEBUG, f"Erreur lors de la recherche de clients : {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la recherche de clients'
        }), 500