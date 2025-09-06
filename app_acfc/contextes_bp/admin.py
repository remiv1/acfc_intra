'''
Blueprint d'administration pour l'application ACFC.
Ce module définit les routes et la logique associée à l'administration, incluant :
- La page d'accueil de l'administration avec statistiques générales.
- Le dashboard des logs avec filtrage et pagination côté serveur.
- L'export des logs filtrés au format CSV.
Fonctionnalités principales :
- Statistiques sur les utilisateurs et les logs (MongoDB).
- Filtrage avancé et pagination des logs.
- Export des logs filtrés.
- Sécurisation des routes par habilitation (ADMINISTRATEUR).
Routes :
- `/admin/` : Page d'accueil de l'administration.
- `/admin/logs` : Dashboard des logs avec filtres.
- `/admin/logs/export` : Export des logs filtrés en CSV.
: TODO :
- *A développer* :
  - *Réactivation client*
  - *Gestion des utilisateurs*
  - *Suppression de masses à double validation (1 administrateur et 1 gestionnaire)*
Dépendances :
- Flask (Blueprint, request, session, make_response)
- MongoDB (pymongo)
- SQLAlchemy (gestion des utilisateurs)
- Modules internes : habilitations, modèles, templates, logs
Sécurité :
Toutes les routes sont protégées par le décorateur `validate_habilitation(ADMINISTRATEUR)`.

'''
# TODO : Réalisations des routes dans *A développer*

from flask import Blueprint, request, make_response
from app_acfc.habilitations import (
    validate_habilitation, ADMINISTRATEUR
    )
from pymongo import MongoClient
from flask import session
from datetime import datetime, timedelta
from logs.logger import acfc_log, DB_URI, DB_NAME, COLLECTION_NAME, QueryLogs
from app_acfc.modeles import Constants, PrepareTemplates, get_db_session, User
from sqlalchemy.orm import Session as SessionBdDType
from typing import Any, Dict

admin_bp = Blueprint('admin',
                     __name__,
                     url_prefix='/admin',
                     static_folder='statics/admin')

@validate_habilitation(ADMINISTRATEUR)
@admin_bp.route('/')
def admin_list():
    """
    Page d'accueil de l'administration avec statistiques générales.
    """
    try:
        # Connexion à MongoDB pour les statistiques des logs
        client: MongoClient[Any] = MongoClient(DB_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Statistiques des dernières 24h
        yesterday = datetime.now() - timedelta(days=1)
        stats_query = {'timestamp': {'$gte': yesterday}}

        # Récupération du nombre total d'utilisateurs
        db_session: SessionBdDType = get_db_session()
        total_users: int = db_session.query(User).count()
        
        # Compilation des statistiques
        stats: Dict[str, Any] = {
            'total_logs': collection.count_documents(stats_query),
            'total_errors': collection.count_documents({**stats_query, 'level': 'ERROR'}),
            'total_warnings': collection.count_documents({**stats_query, 'level': 'WARNING'}),
            'total_users': total_users,
            'system_status': True
        }
        
        return PrepareTemplates.admin(subcontext='dashboard', stats=stats)
                             
    except Exception as e:
        message = Constants.messages('error_500', 'default') \
                    + '\ncode erreur : 500' \
                    + f'\ndétail erreur : {str(e)}'
        return PrepareTemplates.error_5xx(status_code=500, status_message=message,
                                          log=True, specific_log=Constants.log_files('security'))

@validate_habilitation(ADMINISTRATEUR)
@admin_bp.route('/logs')
def logs_dashboard():
    """
    Dashboard principal des logs avec filtrage côté serveur.
    Utilise MongoDB pour récupérer et filtrer les logs.
    """
    try:
        # Instanciation de la classe de requête des logs
        query_logs = QueryLogs(request)

        # Construction de la requête MongoDB
        query_logs.get_log_form_filter() \
            .construct_query() \
            .construct_pagination() \
            .construct_stats() \
            .get_filters()
        
        # Pagination simple
        pagination: Dict[str, Any] = {
            'page': query_logs.page,
            'pages': query_logs.total_pages,
            'has_prev': query_logs.has_previous,
            'has_next': query_logs.has_next,
            'prev_num': query_logs.page - 1 if query_logs.has_previous else None,
            'next_num': query_logs.page + 1 if query_logs.has_next else None,
            'iter_pages': lambda: range(max(1, query_logs.page - 2), min(query_logs.total_pages + 1, query_logs.page + 3))
        }
        # Rendu du template avec les logs et les filtres
        return PrepareTemplates.admin(logs=query_logs.logs,
                                      total_logs=query_logs.total_logs,
                                      stats=query_logs.stats,
                                      pagination=pagination,
                                      available_zones=sorted(query_logs.available_zones),   # type: ignore
                                      available_users=sorted(query_logs.available_users),   # type: ignore
                                      log=True)

    except Exception as e:
        message = Constants.messages('error_500', 'default') \
                    + '\ncode erreur : 500' \
                    + f'\ndétail erreur : {str(e)}'
        return PrepareTemplates.error_5xx(status_code=500, status_message=message,
                                          log=True, specific_log=Constants.log_files('security'))

@validate_habilitation(ADMINISTRATEUR)
@admin_bp.route('/logs/export', methods=['POST'])
def logs_export():
    """
    Export des logs filtrés en CSV.
    Utilise les mêmes filtres que le dashboard.
    """
    try:
        # Instanciation de la classe de requête des logs
        query_logs = QueryLogs(request)
        
        # Opérations de filtrage de données
        query_logs.get_log_form_filter() \
            .construct_query() \
            .construct_list() \
            .build_csv()

        # Nom du fichier avec timestamp
        filename = f"logs_acfc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Création de la réponse HTTP
        response = make_response(query_logs.output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        acfc_log.log(40, f"Erreur export logs: {str(e)}", 
                    specific_logger=Constants.log_files('security'), db_log=True, user=session.get('pseudo', 'N/A'))
        return "Erreur lors de l'export des logs", 500
