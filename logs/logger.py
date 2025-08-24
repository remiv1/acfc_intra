import logging
from logging.handlers import RotatingFileHandler
from pymongo import MongoClient
from pymongo.mongo_client import MongoClient
from typing import Any
from datetime import datetime, timezone

class CustomLogger:
    def __init__(self, db_uri: str, db_name: str, collection_name: str):
        # Initialisation de la connexion à la base de données NoSQL
        self.client: MongoClient[Any] = MongoClient(db_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        
        # Création des loggers pour Error, Warning, Info
        self.error_logger = self._create_file_logger('error.log', logging.ERROR)
        self.warning_logger = self._create_file_logger('warning.log', logging.WARNING)
        self.info_logger = self._create_file_logger('info.log', logging.INFO)
        self.debug_logger = self._create_file_logger('debug.log', logging.DEBUG)

    def _create_specific_logger(self, filepath: str):
        return self._create_file_logger(filepath, logging.DEBUG)

    def _create_file_logger(self, filename: str, level: int):
        logger = logging.getLogger(filename)
        logger.setLevel(level)
        handler = RotatingFileHandler(filename, maxBytes=5*1024*1024, backupCount=3)
        formatter = logging.Formatter('[%(asctime)s] --%(levelname)s-- %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def log_to_db(self, level: int, message: str, specific_logger: str | None = None, zone_log: str = "general"):
        log_entry: dict[str, Any] = {
            "level": level,
            "message": message,
            "timestamp": datetime.now(timezone.utc),
            "zone": zone_log
        }
        if specific_logger:
            self._create_specific_logger(specific_logger).log(level, message)
        self.collection.insert_one(log_entry)

    def log_to_file(self, level: int, message: str, specific_logger: str | None = None,
                    zone_log: str = "general", db_log: bool = False):
        # Log dans la base de données
        if db_log: self.log_to_db(level, message, zone_log)
        
        # Log dans les fichiers appropriés
        if level == logging.ERROR:
            self.error_logger.error(message)
        elif level == logging.WARNING:
            self.warning_logger.warning(message)
        elif level == logging.INFO:
            self.info_logger.info(message)
        elif level == logging.DEBUG:
            self.debug_logger.debug(message)

        if specific_logger:
            self._create_specific_logger(specific_logger).log(level, message)
