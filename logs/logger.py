import logging
from logging.handlers import RotatingFileHandler
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Any, Dict, List
from datetime import datetime, timezone
from os.path import dirname, join as join_os, abspath
from flask import Request
from datetime import datetime, timedelta

"""
ACFC - Système de Logging Hybride
=================================

Module de gestion des logs pour l'application ACFC, offrant un système hybride
combinant le logging traditionnel en fichiers et le stockage NoSQL MongoDB.

Fonctionnalités principales :
- Logging multi-niveaux (ERROR, WARNING, INFO, DEBUG)
- Rotation automatique des fichiers de logs
- Stockage des logs en base MongoDB avec métadonnées
- Création de loggers spécifiques par zone fonctionnelle
- Gestion des zones de logging pour catégoriser les événements

Architecture :
- Fichiers de logs rotatifs (5MB max, 3 sauvegardes)
- Base de données MongoDB pour recherche et analyse
- Horodatage UTC pour cohérence multi-timezone
- Formatage standardisé des messages

Utilisation :
```python
logger = CustomLogger("mongodb://localhost:27017", "acfc_logs", "application")
logger.log_to_file(ERROR, "Message d'erreur", zone_log="authentification")
logger.log_to_db(INFO, "Connexion utilisateur", zone_log="session")
```

Technologies :
- logging : Module Python standard pour les logs
- RotatingFileHandler : Rotation automatique des fichiers
- PyMongo : Client MongoDB pour Python
- datetime : Gestion des horodatages UTC

Auteur : ACFC Development Team
Version : 1.0
"""

# Constantes de niveaux de logging pour faciliter l'utilisation
ERROR = logging.ERROR       # Niveau 40 - Erreurs critiques
WARNING = logging.WARNING   # Niveau 30 - Avertissements
INFO = logging.INFO         # Niveau 20 - Informations générales
DEBUG = logging.DEBUG       # Niveau 10 - Informations de débogage


class CustomLogger:
    """
    Gestionnaire de logs hybride combinant fichiers locaux et base MongoDB.
    
    Cette classe permet de gérer les logs de l'application ACFC avec :
    - Stockage local en fichiers rotatifs par niveau de criticité
    - Stockage centralisé en base MongoDB avec métadonnées
    - Support des loggers spécifiques par zone fonctionnelle
    
    Attributes:
        client (MongoClient): Client de connexion à MongoDB
        db: Base de données MongoDB pour les logs
        collection: Collection MongoDB pour stocker les entrées de log
        error_logger (Logger): Logger dédié aux erreurs
        warning_logger (Logger): Logger dédié aux avertissements
        info_logger (Logger): Logger dédié aux informations
        debug_logger (Logger): Logger dédié au débogage
    """
    
    def __init__(self, db_uri: str, db_name: str, collection_name: str):
        """
        Initialise le système de logging hybride.
        
        Args:
            db_uri (str): URI de connexion à MongoDB (ex: "mongodb://localhost:27017")
            db_name (str): Nom de la base de données MongoDB
            collection_name (str): Nom de la collection pour stocker les logs
            
        Raises:
            ConnectionError: En cas d'échec de connexion à MongoDB
        """
        # Initialisation de la connexion à la base de données NoSQL
        try:
            self.client: MongoClient[Any] | None = MongoClient(
                db_uri, 
                serverSelectionTimeoutMS=5000,  # Timeout de 5 secondes
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            # Test de la connexion
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            self.mongodb_available = True
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            print(f"Avertissement: Impossible de se connecter à MongoDB: {e}")
            print("Le logging sera effectué uniquement dans les fichiers.")
            self.mongodb_available = False
            self.client = None
            self.db = None
            self.collection = None
        
        # Création des loggers pour Error, Warning, Info, Debug
        self.error_logger = self._create_file_logger('error.log', ERROR)
        self.warning_logger = self._create_file_logger('warning.log', WARNING)
        self.info_logger = self._create_file_logger('info.log', INFO)
        self.debug_logger = self._create_file_logger('debug.log', DEBUG)

    def _create_specific_logger(self, filepath: str, level: int = DEBUG):
        """
        Crée un logger spécifique pour une zone fonctionnelle donnée.
        
        Args:
            filepath (str): Chemin du fichier de log spécifique
            level (int): Niveau de logging (DEBUG par défaut)
            
        Returns:
            Logger: Instance de logger configurée pour le fichier spécifié
        """
        return self._create_file_logger(filepath, level)

    def _create_file_logger(self, filename: str, level: int):
        """
        Crée et configure un logger pour écriture en fichier avec rotation.
        
        Configuration :
        - Rotation automatique : 5MB max par fichier, 3 sauvegardes
        - Format : [timestamp] --niveau-- message
        - Handler : RotatingFileHandler pour gestion de l'espace disque
        
        Args:
            filename (str): Nom du fichier de log
            level (int): Niveau minimum de logging pour ce logger
            
        Returns:
            Logger: Instance de logger configurée et prête à l'emploi
        """
        path_logs = join_os(dirname(abspath(__file__)), 'fichiers_logs', filename)
        logger = logging.getLogger(filename)
        logger.setLevel(level)
        handler = RotatingFileHandler(path_logs, maxBytes=5*1024*1024, backupCount=3)
        formatter = logging.Formatter('[%(asctime)s] --%(levelname)s-- %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _log_to_db(self, level: int, message: str, zone_log: str = "general", user: str = "N/A"):
        """
        Enregistre un log dans la base de données MongoDB avec métadonnées.
        
        Crée une entrée structurée avec horodatage UTC et informations contextuelles
        pour faciliter la recherche et l'analyse des logs.
        
        Args:
            level (int): Niveau de criticité du log (ERROR, WARNING, INFO, DEBUG)
            message (str): Message de log à enregistrer
            specific_logger (str | None): Nom du logger spécifique (optionnel)
            zone_log (str): Zone fonctionnelle d'origine du log (défaut: "general")
            
        Note:
            Si specific_logger est fourni, crée également un fichier de log dédié
            Si MongoDB n'est pas disponible, l'opération est ignorée silencieusement
        """
        if not self.mongodb_available or self.collection is None:
            # MongoDB non disponible, on ignore silencieusement
            return
            
        try:
            log_entry: dict[str, Any] = {
                "level": logging.getLevelName(level),  # Convertit le niveau numérique en nom (ERROR, WARNING, etc.)
                "message": message,
                "timestamp": datetime.now(timezone.utc),
                "zone_log": zone_log,  # Zone fonctionnelle (admin, security, client, etc.)
                "user": user
            }
            self.collection.insert_one(log_entry)
        except Exception as e:
            # En cas d'erreur MongoDB, on continue sans interrompre l'application
            print(f"Erreur lors de l'écriture du log en base: {e}")

    def log(self, level: int, message: str, specific_logger: str='general.log', zone_log: str | None = None, db_log: bool = False, user: str = "N/A"):
        """
        Enregistre un log dans les fichiers appropriés selon le niveau de criticité.
        
        Distribue automatiquement le message vers le fichier de log correspondant
        au niveau de criticité. Optionnellement, peut aussi enregistrer en base.
        
        Args:
            level (int): Niveau de criticité (ERROR, WARNING, INFO, DEBUG)
            message (str): Message à enregistrer
            specific_logger (str): Nom du fichier de log spécifique (défaut: 'general.log')
            zone_log (str): Zone fonctionnelle (défaut: specific_logger sans extension)
            db_log (bool): Si True, enregistre aussi en base MongoDB (défaut: False)
            user (str): Utilisateur associé au log (défaut: "N/A")
            
        Comportement :
        - ERROR : Écrit dans error.log
        - WARNING : Écrit dans warning.log  
        - INFO : Écrit dans info.log
        - DEBUG : Écrit dans debug.log
        - Si specific_logger fourni : Écrit aussi dans le fichier spécifique
        """
        # Log dans la base de données si demandé
        if db_log:
            if zone_log is None:
                zone_log = specific_logger.split('.')[0]
            self._log_to_db(level=level, message=message, zone_log=zone_log, user=user)
        
        # Distribution vers les fichiers de logs par niveau
        if level == logging.ERROR:
            self.error_logger.error(message)
        elif level == logging.WARNING:
            self.warning_logger.warning(message)
        elif level == logging.INFO:
            self.info_logger.info(message)
        elif level == logging.DEBUG:
            self.debug_logger.debug(message)

        # Log additionnel dans un fichier spécifique
        self._create_specific_logger(specific_logger)

class QueryLogs:
    """
    Classe pour la construction de requêtes de recherche de logs.
    
    Cette classe fournit des méthodes pour construire des requêtes complexes
    basées sur divers critères tels que le niveau de log, la zone fonctionnelle,
    l'utilisateur, les mots-clés, et les plages de dates.
    
    Attributes:
        None
    """
    def __init__(self, request: Request):
        """
        Initialise la classe QueryLogs.
        """
        self.request = request
        self.client: MongoClient[Any] = MongoClient(DB_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]

    def get_log_form_filter(self):
        """
        Extrait les paramètres de filtrage des logs depuis la requête.
        """
        # Extraction des paramètres de filtrage
        self.page = int(self.request.args.get('page', 1))
        self.limit = int(self.request.args.get('limit', 25))
        self.level = self.request.args.get('level', '')
        self.zone_log = self.request.args.get('zone_log', '')
        self.user = self.request.args.get('user', '')
        self.search = self.request.args.get('search', '')
        self.date_from = self.request.args.get('date_from', '')
        self.date_to = self.request.args.get('date_to', '')

        return self

    def construct_query(self):
        """
        Construit une requête MongoDB basée sur les paramètres extraits.
        """
        self.query: Dict[str, Any] = {}

        if self.level:
            self.query['level'] = self.level

        if self.zone_log:
            self.query['zone_log'] = self.zone_log

        if self.user and self.user != 'N/A':
            self.query['user'] = self.user

        if self.search:
            self.query['message'] = {'$regex': self.search, '$options': 'i'}

        # Filtrage par date
        if self.date_from or self.date_to:
            date_query = {}
            if self.date_from:
                date_query['$gte'] = datetime.strptime(self.date_from, '%Y-%m-%d')
            if self.date_to:
                # Ajouter 23:59:59 pour inclure toute la journée
                end_date = datetime.strptime(self.date_to, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
                date_query['$lte'] = end_date
            self.query['timestamp'] = date_query

        return self

    def construct_list(self):
        """
        Construit la liste des logs selon la requête et la pagination.
        """
        logs_cursor = self.collection.find(self.query).sort('timestamp', DESCENDING).limit(10000)
        self.logs = list(logs_cursor)
        return self
    
    def build_csv(self):
        """
        Construit un CSV des logs selon la requête.
        """
        import csv
        from io import StringIO

        self.output = StringIO()
        writer = csv.writer(self.output)
        writer.writerow(['Timestamp', 'Niveau', 'Zone', 'Utilisateur', 'Message'])

        for log in self.logs:
            writer.writerow([
                log.get('timestamp', '').isoformat() if log.get('timestamp') else '',
                log.get('level', ''),
                log.get('zone_log', ''),
                log.get('user', ''),
                log.get('message', '')
            ])
        
        # Préparation de la réponse
        self.output.seek(0)
        return self

    def construct_pagination(self):
        """
        Construit les paramètres de pagination pour la requête MongoDB.
        """
        # Calcul du total de pagination
        self.total_logs = self.collection.count_documents(self.query)
        skip = (self.page - 1) * self.limit

        # Récupération des logs avec pagination
        logs_cursor = self.collection.find(self.query).sort('timestamp', DESCENDING) \
                            .skip(skip).limit(self.limit)
        self.logs = list(logs_cursor)

        # Calcul des pages
        self.total_pages = (self.total_logs + self.limit - 1) // self.limit
        self.has_previous = self.page > 1
        self.has_next = self.page < self.total_pages

        return self
    
    def construct_stats(self):
        """
        Construit les statistiques des logs par niveau.
        """
        yesterday = datetime.now() - timedelta(days=1)
        stats_query = {'timestamp': {'$gte': yesterday}}
        self.stats: Dict[str, int] = {
            'total_errors': self.collection.count_documents({**stats_query, 'level': 'ERROR'}),
            'total_warnings': self.collection.count_documents({**stats_query, 'level': 'WARNING'}),
            'total_info': self.collection.count_documents({**stats_query, 'level': 'INFO'}),
        }
        return self
    
    def get_filters(self):
        """
        Retourne les filtres actuels sous forme de dictionnaire.
        """
        self.available_zones: List[Any] = self.collection.distinct('zone_log')  # type: ignore
        self.available_users: List[Any] = self.collection.distinct('user')  # type: ignore
        return self


DB_URI = "mongodb://acfc-logs:27017/"
DB_NAME = "logDB"
COLLECTION_NAME = "traces"

# Création du logger personnalisé
acfc_log = CustomLogger(
    db_uri=DB_URI,
    db_name=DB_NAME,
    collection_name=COLLECTION_NAME
)