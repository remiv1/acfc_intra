"""
ACFC - Fixtures et Mocks pour le Système de Logging
===================================================

Module contenant les fixtures, mocks et factory functions pour les tests 
du système de logging hybride (fichiers + MongoDB/SQLite).

Ce module fournit des objets de test pour :
- CustomLogger et ses méthodes
- Base de données MongoDB simulée ou SQLite en mémoire
- Entrées de logs avec métadonnées
- Handlers de fichiers de logs
- Scenarios de tests pour le logging

Types d'objets fournis :
- Fixtures : Loggers et bases de données de test prédéfinies
- Mocks : Objets simulés pour isolation des tests
- Factories : Fonctions pour créer facilement des instances de test
- Test Data : Données de logs structurées pour les tests

Auteur : ACFC Development Team
Version : 1.0
"""

import sqlite3
import tempfile
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, patch

# Import du logger personnalisé
from logs.logger import CustomLogger, ERROR, WARNING, INFO, DEBUG

# ====================================================================
# CONSTANTES POUR LES TESTS DE LOGGING
# ====================================================================

# Niveaux de logging pour les tests
TEST_LOG_LEVELS = {
    'error': ERROR or 40,
    'warning': WARNING or 30,
    'info': INFO or 20,
    'debug': DEBUG or 10,
}

# Messages de test typiques
TEST_LOG_MESSAGES = {
    'error': "Erreur critique de test",
    'warning': "Avertissement de test", 
    'info': "Information de test",
    'debug': "Debug de test",
    'auth_error': "Échec d'authentification",
    'db_error': "Erreur de base de données",
    'api_info': "Appel API réussi",
    'session_warning': "Session expirée"
}

# Zones de logging pour les tests
TEST_LOG_ZONES = [
    "authentification",
    "base_donnees", 
    "api",
    "session",
    "commandes",
    "facturation",
    "debug",
    "comptabilité",
    "paiements",
    "stocks",
    "general"
]


# ====================================================================
# FIXTURES - BASE DE DONNÉES SQLITE POUR TESTS
# ====================================================================

class SQLiteLogDatabase:
    """
    Base de données SQLite en mémoire pour remplacer MongoDB dans les tests.
    Simule la structure de collection MongoDB avec une table SQL.
    """
    
    def __init__(self, db_path: str = ":memory:"):
        """
        Initialise la base SQLite en mémoire.
        
        Args:
            db_path: Chemin de la base (:memory: pour base en mémoire RAM)
        """
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self._setup_tables()
    
    def _setup_tables(self):
        """Crée la table des logs compatible avec la structure MongoDB."""
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level INTEGER NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                zone TEXT DEFAULT 'general',
                specific_logger TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.commit()
    
    def insert_one(self, log_entry: Dict[str, Any]) -> int:
        """
        Insère une entrée de log (compatible avec MongoDB insert_one).
        
        Args:
            log_entry: Dictionnaire contenant les données du log
            
        Returns:
            int: ID de l'entrée insérée
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO logs (level, message, timestamp, zone, specific_logger)
            VALUES (?, ?, ?, ?, ?)
        """, (
            log_entry.get('level'),
            log_entry.get('message'),
            log_entry.get('timestamp', datetime.now(timezone.utc)).isoformat(),
            log_entry.get('zone', 'general'),
            log_entry.get('specific_logger')
        ))
        self.connection.commit()
        return cursor.lastrowid or 0
    
    def find(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Recherche des entrées de logs (compatible avec MongoDB find).
        
        Args:
            query: Critères de recherche
            
        Returns:
            List[Dict]: Liste des entrées trouvées
        """
        cursor = self.connection.cursor()
        
        if query is None:
            cursor.execute("SELECT * FROM logs")
        else:
            # Construction basique de la requête (peut être étendue)
            conditions: List[str] = []
            params: List[Any] = []
            for key, value in query.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            cursor.execute(f"SELECT * FROM logs WHERE {where_clause}", params)
        
        columns = [desc[0] for desc in cursor.description]
        results: List[Dict[str, Any]] = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def count_documents(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Compte les documents correspondant à la requête."""
        cursor = self.connection.cursor()
        
        if query is None:
            cursor.execute("SELECT COUNT(*) FROM logs")
        else:
            conditions: List[str] = []
            params: List[Any] = []
            for key, value in query.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            cursor.execute(f"SELECT COUNT(*) FROM logs WHERE {where_clause}", params)
        
        return cursor.fetchone()[0]
    
    def drop(self):
        """Supprime toutes les données (équivalent MongoDB)."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM logs")
        self.connection.commit()
    
    def close(self):
        """Ferme la connexion à la base."""
        self.connection.close()


# ====================================================================
# FIXTURES - LOGGER PERSONNALISÉ
# ====================================================================

class LoggerFixtures:
    """Fixtures pour les objets CustomLogger et composants associés."""
    
    @staticmethod
    def create_test_logger_with_sqlite():
        """
        Crée un logger de test utilisant SQLite au lieu de MongoDB.
        
        Returns:
            tuple: (CustomLogger configuré, SQLiteLogDatabase)
        """
        # Crée une base SQLite temporaire
        temp_db = SQLiteLogDatabase()
        
        # Crée un mock du logger qui utilise SQLite
        with patch('logs.logger.MongoClient') as mock_client:
            # Configure le mock pour utiliser notre SQLite
            mock_collection = Mock()
            mock_collection.insert_one = temp_db.insert_one
            mock_collection.find = temp_db.find
            mock_collection.count_documents = temp_db.count_documents
            mock_collection.drop = temp_db.drop
            
            mock_db = Mock()
            mock_db.__getitem__ = Mock(return_value=mock_collection)
            
            mock_client.return_value.__getitem__ = Mock(return_value=mock_db)
            mock_client.return_value.admin.command = Mock(return_value=True)
            
            # Crée le logger avec configuration de test
            logger = CustomLogger(
                db_uri="sqlite://test",
                db_name="test_db", 
                collection_name="test_logs"
            )
            
            # Remplace la collection par notre SQLite
            logger.collection = mock_collection
            logger.mongodb_available = True
            
        return logger, temp_db
    
    @staticmethod
    def create_file_only_logger() -> CustomLogger:
        """
        Crée un logger qui écrit uniquement dans les fichiers (sans MongoDB).
        
        Returns:
            CustomLogger: Logger configuré pour fichiers uniquement
        """
        with patch('logs.logger.MongoClient', side_effect=Exception("No MongoDB")):
            logger = CustomLogger(
                db_uri="mongodb://fake:27017",
                db_name="fake_db",
                collection_name="fake_collection"
            )
        return logger
    
    @staticmethod
    def create_mock_logger() -> Mock:
        """
        Crée un mock complet du CustomLogger pour tests isolés.
        
        Returns:
            Mock: Logger simulé avec toutes les méthodes
        """
        mock_logger = Mock()
        mock_logger.log_to_file = Mock()
        mock_logger.log_to_db = Mock()
        mock_logger._log_to_db = Mock()
        mock_logger.error_logger = Mock()
        mock_logger.warning_logger = Mock()
        mock_logger.info_logger = Mock()
        mock_logger.debug_logger = Mock()
        mock_logger.mongodb_available = True
        
        return mock_logger


# ====================================================================
# FIXTURES - ENTRÉES DE LOGS
# ====================================================================

class LogEntryFixtures:
    """Fixtures pour les entrées de logs avec différents scénarios."""
    
    @staticmethod
    def error_entry() -> Dict[str, Any]:
        """Entrée de log d'erreur standard."""
        return {
            'level': ERROR or 40,
            'message': TEST_LOG_MESSAGES['error'],
            'timestamp': datetime.now(timezone.utc),
            'zone': 'general'
        }
    
    @staticmethod
    def warning_entry() -> Dict[str, Any]:
        """Entrée de log d'avertissement."""
        return {
            'level': WARNING or 30,
            'message': TEST_LOG_MESSAGES['warning'],
            'timestamp': datetime.now(timezone.utc),
            'zone': 'general'
        }
    
    @staticmethod
    def info_entry() -> Dict[str, Any]:
        """Entrée de log d'information."""
        return {
            'level': INFO or 20,
            'message': TEST_LOG_MESSAGES['info'],
            'timestamp': datetime.now(timezone.utc),
            'zone': 'api'
        }
    
    @staticmethod
    def debug_entry() -> Dict[str, Any]:
        """Entrée de log de débogage."""
        return {
            'level': DEBUG or 10,
            'message': TEST_LOG_MESSAGES['debug'],
            'timestamp': datetime.now(timezone.utc),
            'zone': 'debug'
        }
    
    @staticmethod
    def auth_error_entry() -> Dict[str, Any]:
        """Entrée de log d'erreur d'authentification."""
        return {
            'level': ERROR or 40,
            'message': TEST_LOG_MESSAGES['auth_error'],
            'timestamp': datetime.now(timezone.utc),
            'zone': 'authentification'
        }
    
    @staticmethod
    def db_error_entry() -> Dict[str, Any]:
        """Entrée de log d'erreur de base de données."""
        return {
            'level': ERROR or 40,
            'message': TEST_LOG_MESSAGES['db_error'],
            'timestamp': datetime.now(timezone.utc),
            'zone': 'base_donnees'
        }


# ====================================================================
# FACTORY FUNCTIONS
# ====================================================================

class LogEntryFactory:
    """Factory pour créer facilement des entrées de logs personnalisées."""
    
    @staticmethod
    def create_log_entry(
        level: int,
        message: str,
        zone: str = "general",
        timestamp: Optional[datetime] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Crée une entrée de log personnalisée.
        
        Args:
            level: Niveau de log (ERROR, WARNING, INFO, DEBUG)
            message: Message du log
            zone: Zone fonctionnelle
            timestamp: Horodatage (maintenant par défaut)
            **kwargs: Autres attributs
            
        Returns:
            Dict: Entrée de log structurée
        """
        entry: Dict[str, Any] = {
            'level': level,
            'message': message,
            'timestamp': timestamp or datetime.now(timezone.utc),
            'zone': zone
        }
        entry.update(kwargs)
        return entry
    
    @staticmethod
    def create_batch_entries(count: int, base_message: str = "Test log") -> List[Dict[str, Any]]:
        """
        Crée un lot d'entrées de logs pour tests de volume.
        
        Args:
            count: Nombre d'entrées à créer
            base_message: Message de base (sera suffixé par un numéro)
            
        Returns:
            List[Dict]: Liste d'entrées de logs
        """
        entries: List[Dict[str, Any]] = []
        levels = [ERROR or 40, WARNING or 30, INFO or 20, DEBUG or 10]
        zones = TEST_LOG_ZONES
        
        for i in range(count):
            entry = LogEntryFactory.create_log_entry(
                level=levels[i % len(levels)],
                message=f"{base_message} #{i+1}",
                zone=zones[i % len(zones)]
            )
            entries.append(entry)
        
        return entries


# ====================================================================
# MOCKS SPÉCIALISÉS
# ====================================================================

class DatabaseMocks:
    """Mocks spécialisés pour les interactions avec la base de données."""
    
    @staticmethod
    def create_mongo_collection_mock() -> Mock:
        """Crée un mock de collection MongoDB."""
        mock_collection = Mock()
        mock_collection.insert_one = Mock(return_value=Mock(inserted_id="fake_id"))
        mock_collection.find = Mock(return_value=[])
        mock_collection.count_documents = Mock(return_value=0)
        mock_collection.drop = Mock()
        return mock_collection
    
    @staticmethod
    def create_failing_mongo_mock() -> Mock:
        """Crée un mock de MongoDB qui échoue (pour tester la robustesse)."""
        mock_collection = Mock()
        mock_collection.insert_one.side_effect = Exception("Connection failed")
        mock_collection.find.side_effect = Exception("Connection failed")
        return mock_collection


class FileHandlerMocks:
    """Mocks pour les handlers de fichiers de logs."""
    
    @staticmethod
    def create_rotating_handler_mock() -> Mock:
        """Crée un mock de RotatingFileHandler."""
        mock_handler = Mock()
        mock_handler.emit = Mock()
        mock_handler.setFormatter = Mock()
        return mock_handler
    
    @staticmethod
    def create_temp_log_directory() -> str:
        """
        Crée un répertoire temporaire pour les fichiers de logs de test.
        
        Returns:
            str: Chemin du répertoire temporaire
        """
        temp_dir = tempfile.mkdtemp(prefix="acfc_test_logs_")
        return temp_dir


# ====================================================================
# FIXTURES DE SCÉNARIOS COMPLETS
# ====================================================================

class LoggingScenarioFixtures:
    """Fixtures pour des scénarios complets de logging."""
    
    @staticmethod
    def setup_complete_logging_environment() -> Dict[str, Any]:
        """
        Configure un environnement de logging complet pour tests.
        
        Returns:
            Dict: Environnement configuré avec logger, base, et répertoires
        """
        # Crée logger avec SQLite
        logger, sqlite_db = LoggerFixtures.create_test_logger_with_sqlite()
        
        # Crée répertoire temporaire pour fichiers
        temp_dir = FileHandlerMocks.create_temp_log_directory()
        
        # Pré-remplit avec quelques entrées de test
        test_entries = LogEntryFactory.create_batch_entries(5, "Setup test")
        for entry in test_entries:
            sqlite_db.insert_one(entry)
        
        return_value: Dict[str, Any] = {
            'logger': logger,
            'database': sqlite_db,
            'temp_directory': temp_dir,
            'test_entries': test_entries
        }
        return return_value
    
    @staticmethod
    def setup_error_handling_scenario() -> Dict[str, Any]:
        """
        Configure un scénario de test pour la gestion d'erreurs.
        
        Returns:
            Dict: Configuration avec logger défaillant et entrées d'erreur
        """
        # Logger avec MongoDB défaillant
        logger = LoggerFixtures.create_file_only_logger()
        
        # Collection qui échoue
        failing_collection = DatabaseMocks.create_failing_mongo_mock()
        
        # Entrées d'erreur variées
        error_entries = [
            LogEntryFixtures.error_entry(),
            LogEntryFixtures.auth_error_entry(),
            LogEntryFixtures.db_error_entry()
        ]
        
        return_values: Dict[str, Any] = {
            'logger': logger,
            'failing_collection': failing_collection,
            'error_entries': error_entries
        }
        return return_values


# ====================================================================
# UTILITAIRES DE TEST
# ====================================================================

class LogTestUtils:
    """Utilitaires pour faciliter les tests de logging."""
    
    @staticmethod
    def assert_log_entry_structure(entry: Dict[str, Any]):
        """
        Vérifie qu'une entrée de log a la structure attendue.
        
        Args:
            entry: Entrée de log à vérifier
            
        Raises:
            AssertionError: Si la structure est incorrecte
        """
        required_fields = ['level', 'message', 'timestamp', 'zone']
        for field in required_fields:
            assert field in entry, f"Champ manquant: {field}"
        
        assert isinstance(entry['level'], int), "Level doit être un entier"
        assert isinstance(entry['message'], str), "Message doit être une chaîne"
        assert entry['zone'] in TEST_LOG_ZONES + ['general'], f"Zone invalide: {entry['zone']}"
    
    @staticmethod
    def count_logs_by_level(database: SQLiteLogDatabase, level: int) -> int:
        """
        Compte les logs d'un niveau donné dans la base.
        
        Args:
            database: Base de données SQLite
            level: Niveau de log à compter
            
        Returns:
            int: Nombre de logs du niveau spécifié
        """
        return database.count_documents({'level': level})

    @staticmethod
    def get_latest_log(database: SQLiteLogDatabase) -> Optional[Dict[str, Any]]:
        """
        Récupère le log le plus récent.
        
        Args:
            database: Base de données SQLite
            
        Returns:
            Dict ou None: Dernière entrée de log
        """
        logs = database.find()
        return logs[-1] if logs else None


# ====================================================================
# EXEMPLE D'UTILISATION (POUR DOCUMENTATION)
# ====================================================================

def example_usage():
    """
    Exemple d'utilisation des fixtures de logging dans un test.
    Cette fonction sert de documentation et ne fait pas partie des tests.
    """
    # Création d'un environnement de test complet
    env = LoggingScenarioFixtures.setup_complete_logging_environment()
    logger = env['logger']
    database = env['database']
    
    # Test d'écriture de log
    logger.log_to_file(ERROR or 40, "Test error message", zone_log="test", db_log=True)
    
    # Vérification
    error_count = LogTestUtils.count_logs_by_level(database, ERROR or 40)
    latest_log = LogTestUtils.get_latest_log(database)
    
    print(f"Nombre d'erreurs: {error_count}")
    print(f"Dernier log: {latest_log}")
    
    # Nettoyage
    database.close()


if __name__ == "__main__":
    # Exécution de l'exemple si le script est lancé directement
    example_usage()
