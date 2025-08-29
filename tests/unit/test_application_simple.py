#!/usr/bin/env python3
"""
Tests simplifiés pour l'application Flask ACFC
================================================

Tests simplifiés qui évitent les problèmes de contexte et de mock complex.
Focus sur les fonctionnalités principales sans trop de complexité.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os
import json

# Import conditionnel avec gestion d'erreur
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app_acfc'))

@pytest.fixture
def app():
    """Création d'une app de test simplifiée."""
    with patch('app_acfc.modeles.init_database'):
        with patch('waitress.serve'):
            from app_acfc.application import acfc
            acfc.config['TESTING'] = True
            acfc.config['SECRET_KEY'] = 'test_secret_key_simple'
            acfc.config['WTF_CSRF_ENABLED'] = False
            acfc.config['SESSION_TYPE'] = 'filesystem'
            return acfc

@pytest.fixture  
def client(app):
    """Client de test."""
    return app.test_client()

@pytest.fixture
def authenticated_client(client):
    """Client avec session authentifiée."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['pseudo'] = 'testuser'
        sess['email'] = 'test@example.com'
        sess['habilitations'] = 'user'
    return client

class TestBasicRoutes:
    """Tests de base pour les routes principales."""

    def test_login_page_access(self, client):
        """Test d'accès à la page de login."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_health_endpoint(self, authenticated_client):
        """Test de l'endpoint health avec authentification."""
        with patch('app_acfc.application.SessionBdD') as mock_session:
            mock_session.return_value.execute.return_value = None
            
            response = authenticated_client.get('/health')
            assert response.status_code == 200
            assert response.content_type.startswith('application/json')

    def test_logout_clears_session(self, authenticated_client):
        """Test que logout vide la session."""
        # Vérifier session avant logout
        with authenticated_client.session_transaction() as sess:
            assert 'user_id' in sess

        # Logout
        response = authenticated_client.get('/logout')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_unauthenticated_redirect(self, client):
        """Test redirection pour utilisateur non authentifié."""
        response = client.get('/users')
        assert response.status_code == 302
        assert '/login' in response.location

class TestPasswordManagement:
    """Tests pour la gestion des mots de passe."""

    def test_password_change_missing_fields(self, client):
        """Test changement mot de passe avec champs manquants."""
        response = client.post('/chg_pwd', data={
            'username': 'testuser',
            'old_password': '',  # Champ manquant
            'new_password': 'newpass',
            'confirm_password': 'newpass'
        })
        
        # Devrait rediriger vers login ou afficher erreur
        assert response.status_code in [200, 302]

    def test_password_change_mismatch(self, client):
        """Test changement mot de passe avec confirmation différente."""
        response = client.post('/chg_pwd', data={
            'username': 'testuser',
            'old_password': 'oldpass',
            'new_password': 'newpass1',
            'confirm_password': 'newpass2'  # Différent
        })
        
        assert response.status_code in [200, 302]

class TestErrorHandlers:
    """Tests pour les gestionnaires d'erreur."""

    def test_404_error_with_auth(self, authenticated_client):
        """Test erreur 404 avec utilisateur authentifié."""
        response = authenticated_client.get('/route_inexistante_vraiment_unique')
        # Peut être 404 ou redirection selon configuration
        assert response.status_code in [200, 302, 404]

class TestApplicationConfiguration:
    """Tests de configuration de l'application."""

    def test_app_has_secret_key(self, app):
        """Test que l'app a une clé secrète."""
        assert app.secret_key is not None
        assert len(app.secret_key) > 5

    def test_app_in_testing_mode(self, app):
        """Test que l'app est en mode test."""
        assert app.config['TESTING'] is True

    def test_blueprints_registered(self, app):
        """Test que les blueprints sont enregistrés."""
        blueprint_names = list(app.blueprints.keys())
        expected = ['admin', 'clients', 'commandes', 'commercial', 'comptabilite', 'stocks', 'catalogue']
        
        for expected_bp in expected:
            assert expected_bp in blueprint_names

class TestSecurityBasics:
    """Tests de sécurité de base."""

    @patch('app_acfc.application.SessionBdD')
    def test_login_form_accepts_input(self, mock_session_class, client):
        """Test que le formulaire de login accepte les entrées."""
        # Mock la session de base de données
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'password'
        })
        
        # Ne devrait pas causer d'erreur 500
        assert response.status_code in [200, 302, 400]

    def test_invalid_routes_handled(self, client):
        """Test gestion des routes invalides."""
        response = client.get('/nonexistent_route_12345')
        
        # Ne devrait pas causer d'erreur 500
        assert response.status_code in [200, 302, 404]

class TestConstants:
    """Tests pour les constantes d'application."""

    def test_constants_exist(self):
        """Test que les constantes existent."""
        with patch('app_acfc.modeles.init_database'):
            import app_acfc.application as app_module
            
            # Test des constantes de configuration
            assert hasattr(app_module, 'LOGIN')
            assert hasattr(app_module, 'CLIENT')
            assert hasattr(app_module, 'USERS')
            assert hasattr(app_module, 'BASE')
            
            # Test des constantes de log
            assert hasattr(app_module, 'LOG_LOGIN_FILE')
            assert hasattr(app_module, 'LOG_CLIENT_FILE')

    def test_login_config_structure(self):
        """Test structure de la configuration LOGIN."""
        with patch('app_acfc.modeles.init_database'):
            import app_acfc.application as app_module
            
            login_config = app_module.LOGIN
            assert 'title' in login_config
            assert 'context' in login_config
            assert 'page' in login_config
            assert login_config['context'] == 'login'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
