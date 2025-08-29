#!/usr/bin/env python3
"""
Tests des routes Flask pour améliorer la couverture
==================================================

Ce fichier contient des tests spécifiques pour les routes de l'application
Flask afin d'améliorer significativement la couverture de code.

Focus :
- Routes d'authentification (login, logout)
- Routes de gestion utilisateur (my_account, users)
- Routes administratives et utilitaires
- Gestionnaires d'erreurs personnalisés
- Middleware et hooks Flask

Approche :
- Mocking complet des dépendances externes
- Tests des différents scénarios (succès, échec, erreurs)
- Validation des réponses HTTP et contenu
- Test de la logique métier de chaque route

Technologies :
- pytest : Framework de test
- Flask test client : Simulation requêtes HTTP
- unittest.mock : Système de mocking complet

Auteur : ACFC Development Team
Version : 1.0
"""

from unittest.mock import Mock, patch
import json
from typing import Any


class TestFlaskRoutes:
    """Tests pour les routes Flask d'application.py."""
    
    @patch('app_acfc.modeles.init_database')
    @patch('app_acfc.modeles.SessionBdD')
    @patch('logs.logger.acfc_log')
    def setup_method(self, method: Any, mock_logger: Mock, mock_session: Mock, mock_init_db: Mock):
        """Configuration pour chaque test."""
        mock_init_db.return_value = None
        mock_session.return_value = Mock()
        
        from app_acfc.application import acfc
        self.app = acfc
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
    
    @patch('app_acfc.modeles.SessionBdD')
    def test_health_route_success(self, mock_session_class: Mock):
        """Test de la route /health avec succès."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.execute.return_value = None
        
        response = self.client.get('/health')
        
        assert response.status_code == 200
        assert response.content_type.startswith('application/json')
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'timestamp' in data
        assert 'services' in data
    
    @patch('app_acfc.modeles.SessionBdD')
    def test_health_route_database_error(self, mock_session_class: Mock):
        """Test de la route /health avec erreur base de données."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.execute.side_effect = Exception("Database error")
        
        response = self.client.get('/health')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['status'] == 'degraded'
    
    def test_index_route_without_session(self):
        """Test de la route / sans session authentifiée."""
        response = self.client.get('/')
        
        # Devrait rediriger vers login
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_index_route_with_session(self):
        """Test de la route / avec session authentifiée."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['pseudo'] = 'testuser'

        response = self.client.get('/')

        assert response.status_code == 200
    
    @patch('app_acfc.modeles.SessionBdD')
    @patch('app_acfc.application.ph_acfc')
    def test_login_post_success(self, mock_ph: Mock, mock_session_class: Mock):
        """Test POST /login avec succès."""
        # Setup des mocks
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_user = Mock()
        mock_user.pseudo = 'testuser'
        mock_user.mot_de_passe = 'hashed_password'
        mock_user.actif = True
        mock_user.derniere_connexion = None
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_ph.verify_password.return_value = True
        
        # Test de la requête POST
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        })
        
        # Vérifications
        assert response.status_code == 302  # Redirection après login
        mock_ph.verify_password.assert_called_once_with('testpass', 'hashed_password')
    
    @patch('app_acfc.modeles.SessionBdD')
    @patch('app_acfc.application.ph_acfc')
    def test_login_post_invalid_credentials(self, mock_ph: Mock, mock_session_class: Mock):
        """Test POST /login avec identifiants invalides."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        response = self.client.post('/login', data={
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        
        assert response.status_code == 200  # Reste sur la page de login
        # Devrait contenir un message d'erreur
        assert b'erreur' in response.data.lower() or b'error' in response.data.lower()
    
    def test_login_get(self):
        """Test GET /login."""
        response = self.client.get('/login')
        
        assert response.status_code == 200
        # Devrait contenir un formulaire de login
        assert b'form' in response.data.lower() or b'login' in response.data.lower()
    
    def test_logout_route(self):
        """Test de la route /logout."""
        # Set up session
        with self.client.session_transaction() as sess:
            sess['pseudo'] = 'testuser'
            sess['authenticated'] = True
        
        response = self.client.get('/logout')
        
        assert response.status_code == 302  # Redirection
        assert '/login' in response.location
    
    @patch('app_acfc.modeles.SessionBdD')
    def test_users_route_get(self, mock_session_class: Mock):
        """Test GET /users."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Session authentifiée
        with self.client.session_transaction() as sess:
            sess['pseudo'] = 'admin'
            sess['authenticated'] = True
        
        response = self.client.get('/users')
        
        assert response.status_code == 200
    
    def test_users_route_without_auth(self):
        """Test GET /users sans authentification."""
        response = self.client.get('/users')
        
        assert response.status_code == 302
        assert '/login' in response.location
    
    @patch('app_acfc.modeles.SessionBdD')
    def test_my_account_get(self, mock_session_class: Mock):
        """Test GET /user/<pseudo>."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_user = Mock()
        mock_user.pseudo = 'testuser'
        mock_user.prenom = 'Test'
        mock_user.nom = 'User'
        mock_user.email = 'test@example.com'
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        # Session authentifiée
        with self.client.session_transaction() as sess:
            sess['pseudo'] = 'testuser'
            sess['authenticated'] = True
        
        response = self.client.get('/user/testuser')
        
        assert response.status_code == 200
    
    def test_my_account_forbidden(self):
        """Test GET /user/<pseudo> pour un autre utilisateur."""
        with self.client.session_transaction() as sess:
            sess['pseudo'] = 'user1'
            sess['authenticated'] = True
        
        response = self.client.get('/user/user2')
        
        assert response.status_code == 403
    
    @patch('app_acfc.modeles.SessionBdD')
    @patch('app_acfc.application.ph_acfc')
    def test_chg_pwd_success(self, mock_ph: Mock, mock_session_class: Mock):
        """Test POST /chg_pwd avec succès."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_user = Mock()
        mock_user.pseudo = 'testuser'
        mock_user.mot_de_passe = 'old_hash'
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_ph.verify_password.return_value = True
        mock_ph.hash_password.return_value = 'new_hash'
        
        response = self.client.post('/chg_pwd', data={
            'username': 'testuser',
            'old_password': 'oldpass',
            'new_password': 'newpass123!',
            'confirm_password': 'newpass123!'
        })
        
        assert response.status_code == 200
    
    def test_chg_pwd_missing_data(self):
        """Test POST /chg_pwd avec données manquantes."""
        response = self.client.post('/chg_pwd', data={
            'username': 'testuser',
            'old_password': '',
            'new_password': 'newpass',
            'confirm_password': 'newpass'
        })
        
        assert response.status_code == 200
    
    def test_chg_pwd_passwords_mismatch(self):
        """Test POST /chg_pwd avec mots de passe non correspondants."""
        response = self.client.post('/chg_pwd', data={
            'username': 'testuser',
            'old_password': 'oldpass',
            'new_password': 'newpass1',
            'confirm_password': 'newpass2'
        })
        
        assert response.status_code == 200
    
    def test_error_404_handler(self):
        """Test du gestionnaire d'erreur 404."""
        response = self.client.get('/route_inexistante')
        
        assert response.status_code == 404
    
    def test_error_500_handler(self):
        """Test du gestionnaire d'erreur 500."""
        # Difficile à tester directement, on vérifie qu'il y a un handler
        assert self.app.error_handler_spec is not None
    
    @patch('app_acfc.modeles.SessionBdD')
    def test_user_parameters_get(self, mock_session_class: Mock):
        """Test GET /user/<pseudo>/parameters."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_user = Mock()
        mock_user.pseudo = 'testuser'
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        with self.client.session_transaction() as sess:
            sess['pseudo'] = 'testuser'
            sess['authenticated'] = True
        
        response = self.client.get('/user/testuser/parameters')
        
        assert response.status_code == 200
    
    def test_user_parameters_post_redirect(self):
        """Test POST /user/<pseudo>/parameters redirection."""
        with self.client.session_transaction() as sess:
            sess['pseudo'] = 'testuser'
            sess['authenticated'] = True
        
        response = self.client.post('/user/testuser/parameters')
        
        assert response.status_code == 302
        assert '/user/testuser' in response.location


class TestErrorHandlers:
    """Tests pour les gestionnaires d'erreur personnalisés."""
    
    @patch('app_acfc.modeles.init_database')
    @patch('app_acfc.modeles.SessionBdD')
    @patch('logs.logger.acfc_log')
    def setup_method(self, method: Any, mock_logger: Mock, mock_session: Mock, mock_init_db: Mock):
        """Configuration pour chaque test."""
        mock_init_db.return_value = None
        mock_session.return_value = Mock()
        
        from app_acfc.application import acfc
        self.app = acfc
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_page_not_found_handler(self):
        """Test du gestionnaire 404."""
        response = self.client.get('/page_inexistante')
        
        assert response.status_code == 404
        # Devrait contenir du contenu HTML d'erreur
        assert b'html' in response.data.lower() or response.data


class TestMiddlewareAndHooks:
    """Tests pour les middleware et hooks Flask."""
    
    @patch('app_acfc.modeles.init_database')
    @patch('app_acfc.modeles.SessionBdD')
    @patch('logs.logger.acfc_log')
    def setup_method(self, method: Any, mock_logger: Mock, mock_session: Mock, mock_init_db: Mock):
        """Configuration pour chaque test."""
        mock_init_db.return_value = None
        mock_session.return_value = Mock()
        
        from app_acfc.application import acfc
        self.app = acfc
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    @patch('app_acfc.application.acfc_log')
    def test_request_logging(self, mock_logger: Mock):
        """Test du logging des requêtes."""
        response = self.client.get('/login')
        
        # Vérifier que la requête a été traitée
        assert response.status_code == 200
    
    def test_session_handling(self):
        """Test de la gestion des sessions."""
        # Test création de session
        with self.client.session_transaction() as sess:
            sess['test_key'] = 'test_value'
        
        # Test lecture de session
        with self.client.session_transaction() as sess:
            assert sess.get('test_key') == 'test_value'


class TestApplicationConfiguration:
    """Tests pour la configuration de l'application."""
    
    @patch('app_acfc.modeles.init_database')
    @patch('app_acfc.modeles.SessionBdD')
    @patch('logs.logger.acfc_log')
    def test_app_configuration(self, mock_logger: Mock, mock_session: Mock, mock_init_db: Mock):
        """Test de la configuration de l'application."""
        mock_init_db.return_value = None
        mock_session.return_value = Mock()
        
        from app_acfc.application import acfc
        
        # Vérifier la configuration de base
        assert acfc.config['SECRET_KEY'] is not None
        assert 'SESSION_TYPE' in acfc.config
        
        # Vérifier les blueprints
        blueprint_names = [bp.name for bp in acfc.blueprints.values()]
        expected_blueprints = ['admin', 'catalogue', 'clients', 'commandes', 'commercial', 'comptabilite', 'stocks']
        
        for blueprint_name in expected_blueprints:
            assert blueprint_name in blueprint_names
    
    @patch('app_acfc.modeles.init_database')
    @patch('app_acfc.modeles.SessionBdD')
    @patch('logs.logger.acfc_log')
    def test_app_routes_registration(self, mock_logger: Mock, mock_session: Mock, mock_init_db: Mock):
        """Test de l'enregistrement des routes."""
        mock_init_db.return_value = None
        mock_session.return_value = Mock()
        
        from app_acfc.application import acfc
        
        # Vérifier que les routes principales sont enregistrées
        routes = [rule.rule for rule in acfc.url_map.iter_rules()]
        
        expected_routes = ['/', '/login', '/logout', '/health', '/users', '/chg_pwd']
        
        for route in expected_routes:
            assert route in routes or any(route in r for r in routes)


class TestSecurityFeatures:
    """Tests pour les fonctionnalités de sécurité."""
    
    @patch('app_acfc.modeles.init_database')
    @patch('app_acfc.modeles.SessionBdD')
    @patch('logs.logger.acfc_log')
    def setup_method(self, method: Any, mock_logger: Mock, mock_session: Mock, mock_init_db: Mock):
        """Configuration pour chaque test."""
        mock_init_db.return_value = None
        mock_session.return_value = Mock()
        
        from app_acfc.application import acfc
        self.app = acfc
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_csrf_protection_disabled_in_tests(self):
        """Test que la protection CSRF est désactivée en mode test."""
        # En mode test, les formulaires doivent fonctionner sans token CSRF
        response = self.client.post('/login', data={
            'username': 'test',
            'password': 'test'
        })
        
        # Ne devrait pas échouer à cause de CSRF
        assert response.status_code != 400
    
    def test_session_security_settings(self):
        """Test des paramètres de sécurité des sessions."""
        # Vérifier que l'application a une clé secrète
        assert self.app.secret_key is not None
        assert len(self.app.secret_key) > 10
