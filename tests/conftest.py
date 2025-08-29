#!/usr/bin/env python3
"""
Configuration pytest pour les tests ACFC
========================================

Ce fichier configure l'environnement de test global pour l'application ACFC.
Il configure les mocks appropriés, les fixtures communes et l'isolation
des tests de la base de données et des services externes.

Features :
- Mock automatique de la base de données
- Mock des services externes (MongoDB)
- Configuration de l'application Flask pour les tests
- Isolation complète des tests

Technologies :
- pytest : Framework de test
- unittest.mock : Système de mocking
- Flask testing : Client de test Flask

Auteur : ACFC Development Team
Version : 2.0
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch
from werkzeug.security import generate_password_hash
from flask import Flask
from pathlib import Path

MODELES: str = 'app_acfc.modeles'

# === ÉTAPE CRITIQUE : MOCK DE LA BASE DE DONNÉES AVANT TOUT IMPORT ===
def setup_database_mock():
    """Configure le module mock AVANT tout import de l'application."""
    # Variables d'environnement de test AVANT tout
    os.environ['TESTING'] = 'true'
    os.environ['DB_HOST'] = 'mock_host'
    os.environ['SESSION_TYPE'] = 'filesystem'  # Fix pour Flask-Session
    
    # Mock de flask_session pour éviter les problèmes de configuration
    mock_session = Mock()
    mock_session.Session = Mock()
    sys.modules['flask_session'] = mock_session
    os.environ['DB_PORT'] = '3306'
    os.environ['DB_NAME'] = 'mock_db'
    os.environ['DB_USER'] = 'mock_user'
    os.environ['DB_PASSWORD'] = 'mock_password'
    os.environ['MONGO_URL'] = 'mongodb://localhost:27017/test'
    os.environ['FLASK_ENV'] = 'testing'
    
    # Charger le module mock depuis tests/modeles_test.py
    test_dir = Path(__file__).parent  # Dossier tests/
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
            print("🧪 Mock database configuré depuis tests/modeles_test.py")
            
            # Mock de ph_acfc pour Argon2
            mock_ph_acfc = Mock()
            mock_ph_acfc.verify_password.return_value = True
            mock_ph_acfc.hash_password.return_value = '$argon2id$v=19$m=65536,t=3,p=4$test$newhash'
            mock_ph_acfc.needs_rehash.return_value = False
            
            # Mock du module services complet
            mock_services = Mock()
            mock_services.ph_acfc = mock_ph_acfc
            # Mock des services de sécurité 
            mock_services.SecureSessionService = Mock()
            mock_services.SecureSessionService.return_value = Mock()
            
            sys.modules['app_acfc.services'] = mock_services
            print("🧪 Mock ph_acfc et services configuré")
            
            return modeles_test
    
    # Fallback si le fichier n'est pas trouvé
    from unittest.mock import MagicMock
    mock_module = MagicMock()
    # Ajouter les classes et fonctions nécessaires
    mock_module.User = MagicMock
    mock_module.Client = MagicMock
    mock_module.Commande = MagicMock
    mock_module.SessionBdD = MagicMock()
    mock_module.engine = MagicMock()
    mock_module.verify_env = lambda: True
    mock_module.init_database = lambda *args, **kwargs: None    # type: ignore
    mock_module.Configuration = MagicMock
    sys.modules[MODELES] = mock_module
    print("🧪 Mock database configuré avec fallback MagicMock")
    return mock_module

# EXÉCUTER LE MOCK IMMÉDIATEMENT - AVANT TOUT IMPORT
setup_database_mock()

from typing import Any

# Ajouter le répertoire racine au PYTHONPATH pour les imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# MAINTENANT on peut importer l'application - le mock est déjà en place !
try:
    from app_acfc.application import acfc   # type: ignore
    # Configuration pour les tests
    if acfc:
        acfc.config['SECRET_KEY'] = 'test_secret_key_for_testing'
        acfc.config['TESTING'] = True
        acfc.config['WTF_CSRF_ENABLED'] = False  # Désactiver CSRF pour les tests
    flask_app = True
    print("✅ Application importée avec succès avec le mock database !")
except ImportError as e:
    # Fallback si l'import échoue
    acfc = None
    flask_app = False
    print(f"❌ Échec d'import de l'application: {e}")

FLASK_APP_AVAILABLE = flask_app

# Patch global des modules problématiques avant l'import
@pytest.fixture(scope="session", autouse=True)
def setup_global_mocks():
    """Configure les mocks globaux avant tous les tests."""
    # Utiliser patch.dict pour éviter les problèmes d'import
    from unittest.mock import MagicMock
    
    # Mock complet des modules avant qu'ils soient importés
    mock_modeles = MagicMock()
    mock_modeles.init_database = MagicMock()
    mock_modeles.SessionBdD = MagicMock()
    mock_modeles.engine = MagicMock()
    mock_modeles.verify_env = MagicMock(return_value=True)
    mock_modeles.create_engine = MagicMock()
    mock_modeles.sessionmaker = MagicMock()
    mock_modeles.Base = MagicMock()
    mock_modeles.Configuration = MagicMock()
    
    # Mock des classes de modèles
    mock_modeles.User = MagicMock()
    mock_modeles.Client = MagicMock()
    mock_modeles.Commande = MagicMock()
    
    mock_logger = MagicMock()
    mock_logger.acfc_log = MagicMock()
    
    # Mock du module MySQL connector pour éviter les connexions réelles
    mock_mysql = MagicMock()
    mock_mysql.connect = MagicMock()
    mock_mysql.Error = Exception
    mock_mysql.errors = MagicMock()
    mock_mysql.errors.DatabaseError = Exception
    
    # Mock de PyMongo pour éviter les connexions MongoDB
    mock_pymongo = MagicMock()
    mock_pymongo.MongoClient = MagicMock()
    
    # Ajouter les mocks dans sys.modules
    with patch.dict('sys.modules', {
        MODELES: mock_modeles,
        'logs.logger': mock_logger,
        'mysql.connector': mock_mysql,
        'pymongo': mock_pymongo
    }):
        yield


@pytest.fixture
def app():
    """Fixture Flask app pour les tests."""
    # Mock complet pour éviter toute connexion à la base
    with patch('app_acfc.modeles.init_database'), \
         patch('app_acfc.modeles.SessionBdD'), \
         patch('app_acfc.modeles.engine'), \
         patch('app_acfc.modeles.verify_env', return_value=True):
        
        from app_acfc.application import acfc
        
        # Configuration de test
        acfc.config['TESTING'] = True
        acfc.config['WTF_CSRF_ENABLED'] = False
        acfc.config['SECRET_KEY'] = 'test-secret-key'
        
        yield acfc


@pytest.fixture
def client(app: Flask):
    """Client de test Flask."""
    return app.test_client()


@pytest.fixture
def mock_user():
    """Mock d'un utilisateur pour les tests."""
    user = Mock()
    user.pseudo = 'testuser'
    user.prenom = 'Test'
    user.nom = 'User'
    user.email = 'test@example.com'
    user.telephone = '0123456789'
    # Utilise un mot de passe généré aléatoirement pour les tests
    import secrets
    import string
    test_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    user.mot_de_passe = generate_password_hash(test_password)
    user.actif = True
    user.date_creation = Mock()
    user.derniere_connexion = Mock()
    return user


@pytest.fixture
def authenticated_session(client: Any, mock_user: Mock):
    """Session authentifiée pour les tests."""
    with client.session_transaction() as sess:
        sess['pseudo'] = mock_user.pseudo
        sess['authenticated'] = True
    return sess

from tests.modeles_test import Client

@pytest.fixture
def authenticated_client(client: Client):
    """Client Flask avec session utilisateur authentifiée pré-configurée."""
    with client.session_transaction() as sess:  # type: ignore
        # Configurer toutes les données de session nécessaires comme dans l'application
        sess['user_id'] = 1
        sess['pseudo'] = 'testuser'
        sess['last_name'] = 'User'
        sess['first_name'] = 'Test'
        sess['email'] = 'test@example.com'
        sess['habilitations'] = 'user'  # ou 'admin' selon les besoins
        sess['telephone'] = '0123456789'
        sess['authenticated'] = True
    
    return client


@pytest.fixture
def admin_client(client: Client):
    """Client Flask avec session administrateur pré-configurée."""
    with client.session_transaction() as sess:  # type: ignore
        sess['user_id'] = 1
        sess['pseudo'] = 'admin'
        sess['last_name'] = 'Admin'
        sess['first_name'] = 'Super'
        sess['email'] = 'admin@example.com'
        sess['habilitations'] = 'admin'
        sess['telephone'] = '0123456789'
        sess['authenticated'] = True
    
    return client


@pytest.fixture
def mock_database():
    """Mock de la session de base de données."""
    with patch('app_acfc.modeles.SessionBdD') as mock_session_class, \
         patch('app_acfc.application.SessionBdD') as mock_app_session:
        
        # Mock des instances de session
        session = Mock()
        session.execute = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        session.query = Mock()
        
        # Configuration des mocks
        mock_session_class.return_value = session
        mock_app_session.return_value = session
        
        yield session
