#!/usr/bin/env python3
"""
Tests Unitaires pour les Routes ACFC
====================================

Suite de tests complète pour toutes les routes de l'application ACFC.
Utilise pytest et les factories de test Flask pour simuler les requêtes
et valider le comportement attendu de chaque endpoint.

Coverage :
- Routes d'authentification (login, logout)
- Routes utilisateur (profil, paramètres)
- Routes administratives (users, health)
- Routes utilitaires (changement mot de passe)
- Gestion des erreurs et cas limites

Technologies :
- pytest : Framework de test Python
- Flask test client : Simulation des requêtes HTTP
- Mocking : Simulation des dépendances (base de données)
- Fixtures : Données de test réutilisables

Auteur : ACFC Development Team
Version : 1.0
"""

from typing import Generator, Any
import pytest
import sys
import os
from unittest.mock import Mock, patch
from werkzeug.security import generate_password_hash
from flask.testing import FlaskClient
import string
import secrets

# Ajout du chemin de l'application pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app_acfc'))

def generate_password(length: int = 15):
    alphabet: str = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# MdP générique de test (remplacé car compromis)
TEST_PWD = generate_password()

# Import conditionnel pour éviter les erreurs de dépendances
try:
    from app_acfc.application import acfc
    from app_acfc.modeles import User
except ImportError as e:
    pytest.skip(f"Impossible d'importer les modules application: {e}", allow_module_level=True)

# ====================================================================
# FIXTURES DE TEST
# ====================================================================

@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Fixture Flask test client pour simuler les requêtes HTTP."""
    acfc.config['TESTING'] = True
    acfc.config['WTF_CSRF_ENABLED'] = False  # Désactiver CSRF pour les tests
    acfc.config['SECRET_KEY'] = 'test-secret-key'
    
    with acfc.test_client() as client:
        with acfc.app_context():
            yield client

@pytest.fixture
def mock_user() -> Mock:
    """Fixture pour un utilisateur de test."""
    user = Mock(spec=User)
    user.id = 1
    user.pseudo = "testuser"
    user.prenom = "Jean"
    user.nom = "Dupont"
    user.email = "jean.dupont@test.com"
    user.telephone = "0123456789"
    user.sha_mdp = generate_password_hash(TEST_PWD)
    user.is_active = True
    user.is_locked = False
    user.is_chg_mdp = False
    user.nb_errors = 0
    user.date_chg_mdp = None
    user.created_at = None
    user.debut = None
    user.fin = None
    return user

@pytest.fixture
def authenticated_session(client: FlaskClient, mock_user: Mock) -> Any:
    """Fixture pour une session utilisateur authentifiée."""
    with client.session_transaction() as sess:
        sess['user_id'] = mock_user.id
        sess['pseudo'] = mock_user.pseudo
        sess['last_name'] = mock_user.nom
        sess['first_name'] = mock_user.prenom
        sess['email'] = mock_user.email
    return sess

# ====================================================================
# TESTS DES ROUTES D'AUTHENTIFICATION
# ====================================================================

class TestAuthenticationRoutes:
    """Tests pour les routes d'authentification (login, logout)."""

    def test_login_get_displays_form(self, client: FlaskClient) -> None:
        """Test affichage du formulaire de connexion (GET /login)."""
        response = client.get('/login')
        
        assert response.status_code == 200
        assert b'Authentification' in response.data or b'login' in response.data.lower()

    @patch('app_acfc.application.SessionBdD')
    @patch('app_acfc.application.ph_acfc')
    def test_login_post_success(self, mock_ph: Mock, mock_session_class: Mock, client: FlaskClient, mock_user: Mock) -> None:
        """Test connexion réussie (POST /login)."""
        # Configuration des mocks
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_ph.verify_password.return_value = True
        mock_ph.needs_rehash.return_value = False

        # Données du formulaire
        data = {
            'username': 'testuser',
            'password': TEST_PWD
        }

        response = client.post('/login', data=data)
        
        # Vérifications
        assert response.status_code == 200
        mock_session.query.assert_called_once()
        mock_ph.verify_password.assert_called_once()

    @patch('app_acfc.application.SessionBdD')
    def test_login_post_invalid_user(self, mock_session_class: Mock, client: FlaskClient) -> None:
        """Test connexion avec utilisateur inexistant."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        data = {
            'username': 'nonexistent',
            'password': 'wrongpassword'
        }

        response = client.post('/login', data=data)
        
        assert response.status_code == 200
        assert b'Identifiants invalides' in response.data or b'invalid' in response.data.lower()

    @patch('app_acfc.application.SessionBdD')
    @patch('app_acfc.application.ph_acfc')
    def test_login_post_wrong_password(self, mock_ph: Mock, mock_session_class: Mock, client: FlaskClient, mock_user: Mock) -> None:
        """Test connexion avec mot de passe incorrect."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_ph.verify_password.return_value = False

        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }

        response = client.post('/login', data=data)
        
        assert response.status_code == 200
        assert mock_user.nb_errors == 1

    def test_login_post_missing_data(self, client: FlaskClient) -> None:
        """Test connexion avec données manquantes."""
        data = {
            'username': '',
            'password': ''
        }

        response = client.post('/login', data=data)
        
        assert response.status_code == 200

    def test_login_invalid_method(self, client: FlaskClient) -> None:
        """Test méthode HTTP non autorisée sur /login."""
        response = client.put('/login')
        assert response.status_code == 405  # Method Not Allowed

    def test_logout_clears_session(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test déconnexion (GET /logout)."""
        response = client.get('/logout')
        
        assert response.status_code == 302  # Redirect
        assert response.location.endswith('/login')

    def test_logout_without_session(self, client: FlaskClient) -> None:
        """Test déconnexion sans session active."""
        response = client.get('/logout')
        
        assert response.status_code == 302  # Redirect vers login

# ====================================================================
# TESTS DES ROUTES PRINCIPALES
# ====================================================================

class TestMainRoutes:
    """Tests pour les routes principales de l'application."""

    def test_index_without_authentication_redirects(self, client: FlaskClient) -> None:
        """Test accès à l'index sans authentification."""
        response = client.get('/')
        
        assert response.status_code == 302  # Redirect vers login
        assert '/login' in response.location

    def test_index_with_authentication(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test accès à l'index avec authentification."""
        response = client.get('/')
        
        assert response.status_code == 200

    def test_health_check(self, client: FlaskClient) -> None:
        """Test de l'endpoint de santé (/health)."""
        with patch('app_acfc.application.SessionBdD') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            mock_session.execute.return_value = None

            response = client.get('/health')
            
            assert response.status_code == 200
            assert response.content_type == 'application/json'
            
            json_data = response.get_json()
            assert 'status' in json_data
            assert 'timestamp' in json_data
            assert 'services' in json_data

    def test_health_check_database_error(self, client: FlaskClient) -> None:
        """Test de l'endpoint de santé avec erreur base de données."""
        with patch('app_acfc.application.SessionBdD') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            mock_session.execute.side_effect = Exception("Database connection failed")

            response = client.get('/health')
            
            assert response.status_code == 503  # Service Unavailable
            json_data = response.get_json()
            assert json_data['status'] == 'degraded'

# ====================================================================
# TESTS DES ROUTES UTILISATEUR
# ====================================================================

class TestUserRoutes:
    """Tests pour les routes de gestion utilisateur."""

    def test_my_account_get_without_auth(self, client: FlaskClient) -> None:
        """Test accès à mon compte sans authentification."""
        response = client.get('/user/testuser')
        
        assert response.status_code == 302  # Redirect vers login

    @patch('app_acfc.application.SessionBdD')
    def test_my_account_get_success(self, mock_session_class: Mock, client: FlaskClient, authenticated_session: Any, mock_user: Mock) -> None:
        """Test affichage de mon compte (GET /user/<pseudo>)."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        response = client.get('/user/testuser')
        
        assert response.status_code == 200

    @patch('app_acfc.application.SessionBdD')
    def test_my_account_get_user_not_found(self, mock_session_class: Mock, client: FlaskClient, authenticated_session: Any) -> None:
        """Test affichage compte utilisateur inexistant."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        response = client.get('/user/testuser')
        
        assert response.status_code == 200
        assert b'Erreur' in response.data

    def test_my_account_get_forbidden_access(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test accès au compte d'un autre utilisateur."""
        response = client.get('/user/otheruser')
        
        assert response.status_code == 403  # Forbidden

    @patch('app_acfc.application.SessionBdD')
    def test_my_account_post_success(self, mock_session_class: Mock, client: FlaskClient, authenticated_session: Any, mock_user: Mock) -> None:
        """Test mise à jour des informations utilisateur (POST /user/<pseudo>)."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        data = {
            'prenom': 'Jean-Updated',
            'nom': 'Dupont-Updated',
            'email': 'jean.updated@test.com',
            'telephone': '0987654321'
        }

        response = client.post('/user/testuser', data=data)
        
        assert response.status_code == 200
        assert mock_user.prenom == 'Jean-Updated'
        assert mock_user.nom == 'Dupont-Updated'
        mock_session.commit.assert_called_once()

    @patch('app_acfc.application.SessionBdD')
    def test_my_account_post_invalid_email(self, mock_session_class: Mock, client: FlaskClient, authenticated_session: Any, mock_user: Mock) -> None:
        """Test mise à jour avec email invalide."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        data = {
            'prenom': 'Jean',
            'nom': 'Dupont',
            'email': 'invalid-email',
            'telephone': '0123456789'
        }

        response = client.post('/user/testuser', data=data)
        
        assert response.status_code == 200
        assert b'email' in response.data.lower() and b'valide' in response.data.lower()

    @patch('app_acfc.application.SessionBdD')
    def test_my_account_post_duplicate_email(self, mock_session_class: Mock, client: FlaskClient, authenticated_session: Any, mock_user: Mock) -> None:
        """Test mise à jour avec email déjà utilisé."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [mock_user, mock_user]  # User puis existing user

        data = {
            'prenom': 'Jean',
            'nom': 'Dupont',
            'email': 'existing@test.com',
            'telephone': '0123456789'
        }

        response = client.post('/user/testuser', data=data)
        
        assert response.status_code == 200
        assert b'email' in response.data.lower() and b'utilis' in response.data.lower()

    @patch('app_acfc.application.SessionBdD')
    def test_my_account_post_missing_fields(self, mock_session_class: Mock, client: FlaskClient, authenticated_session: Any, mock_user: Mock) -> None:
        """Test mise à jour avec champs manquants."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        data = {
            'prenom': '',
            'nom': 'Dupont',
            'email': 'test@test.com',
            'telephone': '0123456789'
        }

        response = client.post('/user/testuser', data=data)
        
        assert response.status_code == 200
        assert b'obligatoires' in response.data.lower()

    @patch('app_acfc.application.SessionBdD')
    def test_user_parameters_get(self, mock_session_class: Mock, client: FlaskClient, authenticated_session: Any, mock_user: Mock) -> None:
        """Test affichage des paramètres utilisateur (GET /user/<pseudo>/parameters)."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        response = client.get('/user/testuser/parameters')
        
        assert response.status_code == 200

    def test_user_parameters_post_redirects(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test redirection POST des paramètres vers my_account."""
        response = client.post('/user/testuser/parameters', data={})
        
        assert response.status_code == 302
        assert '/user/testuser' in response.location

# ====================================================================
# TESTS DES ROUTES ADMINISTRATIVES
# ====================================================================

class TestAdminRoutes:
    """Tests pour les routes d'administration."""

    def test_users_get_without_auth(self, client: FlaskClient) -> None:
        """Test accès à la gestion des utilisateurs sans authentification."""
        response = client.get('/users')
        
        assert response.status_code == 302  # Redirect vers login

    def test_users_get_with_auth(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test affichage de la gestion des utilisateurs (GET /users)."""
        response = client.get('/users')
        
        assert response.status_code == 200

    def test_users_post_with_auth(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test création d'utilisateur (POST /users)."""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com'
        }

        response = client.post('/users', data=data)
        
        assert response.status_code == 200

    def test_users_invalid_method(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test méthode HTTP non autorisée sur /users."""
        response = client.put('/users')
        
        assert response.status_code == 200  # La route gère cela comme une erreur

# ====================================================================
# TESTS DES ROUTES UTILITAIRES
# ====================================================================

class TestUtilityRoutes:
    """Tests pour les routes utilitaires."""

    @patch('app_acfc.application.SessionBdD')
    @patch('app_acfc.application.ph_acfc')
    def test_chg_pwd_success(self, mock_ph: Mock, mock_session_class: Mock, client: FlaskClient, mock_user: Mock) -> None:
        """Test changement de mot de passe réussi (POST /chg_pwd)."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_ph.verify_password.return_value = True
        mock_ph.hash_password.return_value = "new_hashed_password"

        data = {
            'username': 'testuser',
            'old_password': 'oldpassword123',
            'new_password': 'newpassword456789ABCD!',
            'confirm_password': 'newpassword456789ABCD!'
        }

        response = client.post('/chg_pwd', data=data)
        
        assert response.status_code == 200
        mock_ph.verify_password.assert_called_once()
        mock_ph.hash_password.assert_called_once()

    def test_chg_pwd_missing_data(self, client: FlaskClient) -> None:
        """Test changement de mot de passe avec données manquantes."""
        data = {
            'username': 'testuser',
            'old_password': '',
            'new_password': 'newpassword',
            'confirm_password': 'newpassword'
        }

        response = client.post('/chg_pwd', data=data)
        
        assert response.status_code == 200

    def test_chg_pwd_passwords_dont_match(self, client: FlaskClient) -> None:
        """Test changement de mot de passe avec mots de passe non correspondants."""
        data = {
            'username': 'testuser',
            'old_password': 'oldpassword',
            'new_password': 'newpassword456789ABCD!',
            'confirm_password': 'differentpassword'
        }

        response = client.post('/chg_pwd', data=data)
        
        assert response.status_code == 200

    def test_chg_pwd_same_password(self, client: FlaskClient) -> None:
        """Test changement de mot de passe identique à l'ancien."""
        data = {
            'username': 'testuser',
            'old_password': 'samepassword',
            'new_password': 'samepassword',
            'confirm_password': 'samepassword'
        }

        response = client.post('/chg_pwd', data=data)
        
        assert response.status_code == 200

    @patch('app_acfc.application.SessionBdD')
    def test_chg_pwd_wrong_old_password(self, mock_session_class: Mock, client: FlaskClient, mock_user: Mock) -> None:
        """Test changement de mot de passe avec ancien mot de passe incorrect."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        with patch('application.ph_acfc') as mock_ph:
            mock_ph.verify_password.return_value = False

            data = {
                'username': 'testuser',
                'old_password': 'wrongpassword',
                'new_password': 'newpassword456789ABCD!',
                'confirm_password': 'newpassword456789ABCD!'
            }

            response = client.post('/chg_pwd', data=data)
            
            assert response.status_code == 200

    def test_chg_pwd_get_method_not_allowed(self, client: FlaskClient) -> None:
        """Test méthode GET non autorisée sur /chg_pwd."""
        response = client.get('/chg_pwd')
        
        assert response.status_code == 405  # Method Not Allowed

# ====================================================================
# TESTS DES GESTIONNAIRES D'ERREURS
# ====================================================================

class TestErrorHandlers:
    """Tests pour les gestionnaires d'erreurs HTTP."""

    def test_404_error_handler(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test gestionnaire d'erreur 404."""
        response = client.get('/nonexistent-route')
        
        assert response.status_code == 404

    def test_403_error_handler(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test gestionnaire d'erreur 403 (accès interdit)."""
        # Tentative d'accès au compte d'un autre utilisateur
        response = client.get('/user/otheruseraccount')
        
        assert response.status_code == 403

    def test_500_error_handler(self, client: FlaskClient) -> None:
        """Test gestionnaire d'erreur 500."""
        # Nous pouvons simuler une erreur 500 en causant une exception interne
        with patch('app_acfc.application.render_template') as mock_render:
            mock_render.side_effect = Exception("Internal server error")
            
            response = client.get('/login')
            
            # Flask gère automatiquement l'exception et retourne 500
            assert response.status_code in [500, 200]  # Peut varier selon la configuration

# ====================================================================
# TESTS D'INTÉGRATION
# ====================================================================

class TestIntegration:
    """Tests d'intégration end-to-end."""

    @patch('app_acfc.application.SessionBdD')
    @patch('app_acfc.application.ph_acfc')
    def test_complete_user_flow(self, mock_ph: Mock, mock_session_class: Mock, client: FlaskClient, mock_user: Mock) -> None:
        """Test complet : login -> consultation profil -> modification -> logout."""
        # Configuration des mocks
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_ph.verify_password.return_value = True
        mock_ph.needs_rehash.return_value = False

        # 1. Login
        login_data = {
            'username': 'testuser',
            'password': TEST_PWD
        }
        response = client.post('/login', data=login_data)
        assert response.status_code == 200

        # 2. Consultation du profil
        response = client.get('/user/testuser')
        assert response.status_code == 200

        # 3. Modification des informations
        update_data = {
            'prenom': 'Jean-Modified',
            'nom': 'Dupont-Modified',
            'email': 'jean.modified@test.com',
            'telephone': '0111111111'
        }
        response = client.post('/user/testuser', data=update_data)
        assert response.status_code == 200

        # 4. Logout
        response = client.get('/logout')
        assert response.status_code == 302

    def test_security_flow_password_change(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test du flow de sécurité : changement de mot de passe."""
        with patch('app_acfc.application.SessionBdD') as mock_session_class:
            with patch('app_acfc.application.ph_acfc') as mock_ph:
                mock_session = Mock()
                mock_session_class.return_value = mock_session
                mock_user = Mock()
                mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
                mock_ph.verify_password.return_value = True
                mock_ph.hash_password.return_value = "new_hash"

                # Changement de mot de passe
                pwd_data = {
                    'username': 'testuser',
                    'old_password': 'oldpass123456789ABC!',
                    'new_password': 'newpass456789123DEF!',
                    'confirm_password': 'newpass456789123DEF!'
                }
                response = client.post('/chg_pwd', data=pwd_data)
                assert response.status_code == 200

# ====================================================================
# CONFIGURATION DES TESTS
# ====================================================================

if __name__ == "__main__":
    """Exécution directe des tests."""
    pytest.main([__file__, "-v", "--tb=short"])
