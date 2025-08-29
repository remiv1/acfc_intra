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
import pytest
from unittest.mock import Mock, patch
from werkzeug.security import generate_password_hash
from flask import Flask
from app_acfc.modeles import Client

# Configuration des variables d'environnement pour les tests
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '3306'
os.environ['DB_NAME'] = 'test_acfc'
os.environ['DB_USER'] = 'test_user'
os.environ['DB_PASSWORD'] = 'test_password'
os.environ['MONGO_URL'] = 'mongodb://localhost:27017/test'
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'true'

# Patch global des modules problématiques avant l'import
@pytest.fixture(scope="session", autouse=True)
def setup_global_mocks():
    """Configure les mocks globaux avant tous les tests."""
    with patch('app_acfc.modeles.init_database') as mock_init_db, \
         patch('app_acfc.modeles.SessionBdD') as mock_session, \
         patch('logs.logger.acfc_log') as mock_logger:
        
        # Mock de l'initialisation de la base
        mock_init_db.return_value = None
        
        # Mock de la session de base de données
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        
        # Mock du logger
        mock_logger.log_to_file = Mock()
        mock_logger._log_to_db = Mock()
        
        yield


@pytest.fixture(scope="session")
def app():
    """Fixture Flask app pour les tests."""
    # Import après configuration des mocks
    with patch('app_acfc.modeles.init_database'):
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
    user.mot_de_passe = generate_password_hash('testpassword')
    user.actif = True
    user.date_creation = Mock()
    user.derniere_connexion = Mock()
    return user


@pytest.fixture
def authenticated_session(client: Client, mock_user: Mock):
    """Session authentifiée pour les tests."""
    with client.session_transaction() as sess:
        sess['pseudo'] = mock_user.pseudo
        sess['authenticated'] = True
    return sess


@pytest.fixture
def mock_database():
    """Mock de la session de base de données."""
    with patch('app_acfc.application.SessionBdD') as mock:
        session = Mock()
        mock.return_value = session
        yield session
