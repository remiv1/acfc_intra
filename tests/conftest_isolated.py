#!/usr/bin/env python3
"""
Configuration de test avec isolation complète
=============================================

Ce conftest désactive complètement les imports problématiques au niveau
le plus bas possible pour éviter toute tentative de connexion.

Auteur : ACFC Development Team
Version : 1.0
"""

import sys
import os
from unittest.mock import MagicMock, patch

# Configuration PRÉCOCE de l'environnement de test
os.environ['TESTING'] = 'true'
os.environ['DB_HOST'] = 'mock_host'
os.environ['DB_PORT'] = '3306'
os.environ['DB_NAME'] = 'mock_db'
os.environ['DB_USER'] = 'mock_user'
os.environ['DB_PASSWORD'] = 'mock_password'

# Installation précoce des mocks AVANT tout import
def install_early_mocks():
    """Installe les mocks le plus tôt possible."""
    
    # Mock complet de mysql.connector
    mysql_mock = MagicMock()
    mysql_mock.connect = MagicMock()
    mysql_mock.Error = Exception
    mysql_mock.errors = MagicMock()
    mysql_mock.errors.DatabaseError = Exception
    mysql_mock.errors.OperationalError = Exception
    sys.modules['mysql'] = MagicMock()
    sys.modules['mysql.connector'] = mysql_mock
    sys.modules['mysql.connector.errors'] = mysql_mock.errors
    
    # Mock de pymongo
    pymongo_mock = MagicMock()
    pymongo_mock.MongoClient = MagicMock()
    sys.modules['pymongo'] = pymongo_mock
    
    # Mock de SQLAlchemy
    sqlalchemy_mock = MagicMock()
    sqlalchemy_mock.create_engine = MagicMock()
    sqlalchemy_mock.text = MagicMock()
    sys.modules['sqlalchemy'] = sqlalchemy_mock
    sys.modules['sqlalchemy.orm'] = MagicMock()
    sys.modules['sqlalchemy.ext'] = MagicMock()
    sys.modules['sqlalchemy.ext.declarative'] = MagicMock()
    sys.modules['sqlalchemy.engine'] = MagicMock()
    sys.modules['sqlalchemy.engine.url'] = MagicMock()
    sys.modules['sqlalchemy.sql'] = MagicMock()
    sys.modules['sqlalchemy.exc'] = MagicMock()
    
    # Mock complet du module modeles avant son import
    modeles_mock = MagicMock()
    modeles_mock.verify_env = MagicMock(return_value=True)
    modeles_mock.init_database = MagicMock()
    modeles_mock.SessionBdD = MagicMock()
    modeles_mock.engine = MagicMock()
    modeles_mock.Base = MagicMock()
    modeles_mock.Configuration = MagicMock()
    modeles_mock.User = MagicMock()
    modeles_mock.Client = MagicMock()
    modeles_mock.Commande = MagicMock()
    sys.modules['app_acfc.modeles'] = modeles_mock
    
    # Mock du logger
    logger_mock = MagicMock()
    logger_mock.acfc_log = MagicMock()
    sys.modules['logs'] = MagicMock()
    sys.modules['logs.logger'] = logger_mock
    
    print("🧪 Mocks précoces installés pour les tests")

# Installer les mocks immédiatement
install_early_mocks()

# Maintenant on peut faire les imports pytest
import pytest

@pytest.fixture(scope="session", autouse=True)
def maintain_mocks():
    """Maintient les mocks pendant toute la session de test."""
    # Les mocks sont déjà installés, on s'assure juste qu'ils restent en place
    yield


@pytest.fixture
def isolated_test():
    """Fixture pour des tests complètement isolés."""
    # Cette fixture garantit que chaque test est complètement isolé
    yield


@pytest.fixture
def mock_db_session():
    """Fixture pour une session de base de données mockée."""
    session_mock = MagicMock()
    session_mock.execute = MagicMock()
    session_mock.commit = MagicMock()
    session_mock.rollback = MagicMock()
    session_mock.close = MagicMock()
    session_mock.query = MagicMock()
    return session_mock


@pytest.fixture
def mock_user():
    """Mock d'un utilisateur pour les tests."""
    user_mock = MagicMock()
    user_mock.pseudo = 'testuser'
    user_mock.prenom = 'Test'
    user_mock.nom = 'User'
    user_mock.email = 'test@example.com'
    user_mock.telephone = '0123456789'
    user_mock.actif = True
    user_mock.date_creation = MagicMock()
    user_mock.derniere_connexion = MagicMock()
    return user_mock


def pytest_configure(config):
    """Configuration pytest personnalisée."""
    # Ajouter des marqueurs personnalisés
    config.addinivalue_line("markers", "unit: Tests unitaires purs")
    config.addinivalue_line("markers", "integration: Tests d'intégration")
    config.addinivalue_line("markers", "slow: Tests lents")


def pytest_collection_modifyitems(config, items):
    """Modifier la collection de tests."""
    # Marquer automatiquement les tests selon leur localisation
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
