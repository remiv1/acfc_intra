#!/usr/bin/env python3
"""
Configuration pytest pour les tests unitaires ACFC
==================================================

Configuration spécifique pour les tests unitaires qui doivent être complètement
isolés de la base de données et des services externes.

Fonctionnalités :
- Mocks automatiques de toutes les connexions base de données
- Mocks des services externes (MongoDB, logger)
- Configuration Flask pour tests isolés
- Fixtures communes pour tests unitaires

Auteur : ACFC Development Team
Version : 1.0
"""
from flask import Flask
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import os

# Configuration des variables d'environnement pour les tests
os.environ['TESTING'] = 'true'
os.environ['DB_HOST'] = 'test_host'
os.environ['DB_PORT'] = '3306'
os.environ['DB_NAME'] = 'test_db'
os.environ['DB_USER'] = 'test_user'
os.environ['DB_PASSWORD'] = 'test_pass'
os.environ['MONGO_URL'] = 'mongodb://test:27017/test'

MODELES = 'app_acfc.modeles'

# Stratégie: Remplacer le module AVANT tout import
def setup_module_mocking():
    """Configure le module mock avant tout import."""
    # Charger le module mock depuis tests/modeles_test.py
    test_dir = Path(__file__).parent.parent  # Dossier tests/
    modeles_test_path = test_dir / 'modeles_test.py'
    
    if modeles_test_path.exists():
        # Import dynamique du module test
        import importlib.util
        spec = importlib.util.spec_from_file_location("modeles_test", modeles_test_path)
        if spec and spec.loader:
            modeles_test = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modeles_test)
            
            # Remplacer le module modeles par la version test AVANT tout import
            sys.modules[MODELES] = modeles_test
            return modeles_test
    
    # Fallback si le fichier n'est pas trouvé
    from unittest.mock import MagicMock
    mock_module = MagicMock()
    # Ajouter les classes nécessaires
    mock_module.User = MagicMock
    mock_module.Client = MagicMock
    mock_module.Commande = MagicMock
    mock_module.SessionBdD = MagicMock()
    mock_module.engine = MagicMock()
    mock_module.verify_env = lambda: True
    mock_module.init_database = lambda *args, **kwargs: None    # type: ignore
    mock_module.Configuration = MagicMock
    sys.modules[MODELES] = mock_module
    return mock_module

# Exécuter le setup immédiatement au chargement du conftest
setup_module_mocking()

# Fixture pour accès au module mocké dans les tests
@pytest.fixture(scope='session')
def mock_database_module():
    """Accès au module mocké pour les tests."""
    return sys.modules.get(MODELES)

# Mocks globaux pour les tests unitaires
@pytest.fixture(scope="session", autouse=True)
def setup_unit_test_mocks():
    """Configure les mocks globaux pour tous les tests unitaires."""
    with patch('app_acfc.modeles.init_database') as mock_init_db, \
         patch('app_acfc.modeles.SessionBdD') as mock_session_class, \
         patch('app_acfc.modeles.engine') as mock_engine, \
         patch('app_acfc.modeles.verify_env') as mock_verify_env, \
         patch('app_acfc.modeles.create_engine') as mock_create_engine, \
         patch('logs.logger.acfc_log') as mock_logger:
        
        # Mock de l'initialisation de la base
        mock_init_db.return_value = None
        
        # Mock de verify_env
        mock_verify_env.return_value = True
        
        # Mock de create_engine
        mock_create_engine.return_value = Mock()
        
        # Mock de l'engine SQLAlchemy
        mock_engine.connect.return_value.__enter__ = Mock()
        mock_engine.connect.return_value.__exit__ = Mock(return_value=None)
        mock_engine.execute = Mock()
        
        # Mock de la session de base de données
        mock_session_instance = Mock()
        mock_session_instance.execute = Mock()
        mock_session_instance.commit = Mock()
        mock_session_instance.rollback = Mock()
        mock_session_instance.close = Mock()
        mock_session_instance.query = Mock()
        mock_session_class.return_value = mock_session_instance
        
        # Mock du logger
        mock_logger.log_to_file = Mock()
        mock_logger._log_to_db = Mock()
        
        yield


@pytest.fixture
def mock_db_session():
    """Fixture pour une session de base de données mockée."""
    session = Mock()
    session.execute = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    session.query = Mock()
    return session


@pytest.fixture
def flask_app():
    """Fixture Flask app pour les tests unitaires."""
    with patch('app_acfc.modeles.init_database'), \
         patch('app_acfc.modeles.SessionBdD'), \
         patch('app_acfc.modeles.engine'), \
         patch('app_acfc.modeles.verify_env', return_value=True):
        
        from app_acfc.application import acfc
        
        # Configuration de test
        acfc.config['TESTING'] = True
        acfc.config['WTF_CSRF_ENABLED'] = False
        acfc.config['SECRET_KEY'] = 'test-secret-key-for-unit-tests'
        
        return acfc


@pytest.fixture
def test_client(flask_app: Flask):
    """Client de test Flask pour les tests unitaires."""
    return flask_app.test_client()
