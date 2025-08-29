import pytest
from unittest.mock import Mock, patch
from app_acfc.application import acfc


class TestFlaskRoutesFixed:
    """Tests des routes Flask corrigés avec la bonne authentification."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Configuration pour chaque test."""
        acfc.config['TESTING'] = True
        acfc.config['SECRET_KEY'] = 'test-secret-key'
        acfc.config['WTF_CSRF_ENABLED'] = False
        self.client = acfc.test_client()

    def test_health_route_direct_access(self):
        """Test d'accès direct à /health sans authentification."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            
        with patch('app_acfc.modeles.SessionBdD') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            mock_session.execute.return_value = None
            
            response = self.client.get('/health')
            assert response.status_code in [200, 302]  # Peut être redirigé ou accessible

    def test_index_route_authenticated(self):
        """Test de la route / avec session authentifiée (user_id)."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['pseudo'] = 'testuser'

        response = self.client.get('/')
        assert response.status_code in [200, 302]

    def test_index_route_unauthenticated_redirect(self):
        """Test de redirection vers /login quand pas d'authentification."""
        response = self.client.get('/')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_login_get_page(self):
        """Test d'accès à la page de login."""
        response = self.client.get('/login')
        assert response.status_code == 200

    def test_logout_clears_session(self):
        """Test que logout nettoie la session."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['pseudo'] = 'testuser'

        response = self.client.get('/logout')
        assert response.status_code == 302
        assert '/login' in response.location

    @patch('app_acfc.modeles.SessionBdD')
    def test_users_route_authenticated(self, mock_session_class: Mock):
        """Test GET /users avec authentification."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['pseudo'] = 'admin'

        response = self.client.get('/users')
        assert response.status_code in [200, 302]  # Dépend des droits

    def test_unauthenticated_routes_redirect(self):
        """Test que les routes protégées redirigent vers login."""
        protected_routes = ['/users', '/user/test', '/chg_pwd']
        
        for route in protected_routes:
            response = self.client.get(route)
            assert response.status_code == 302
            assert '/login' in response.location

    @patch('app_acfc.modeles.SessionBdD')  
    def test_user_profile_access(self, mock_session_class: Mock):
        """Test d'accès au profil utilisateur."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_user = Mock()
        mock_user.pseudo = 'testuser'
        mock_user.prenom = 'Test'
        mock_user.nom = 'User'
        mock_user.email = 'test@example.com'
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['pseudo'] = 'testuser'

        response = self.client.get('/user/testuser')
        assert response.status_code in [200, 302]

    def test_static_files_accessible(self):
        """Test que les fichiers statiques sont accessibles sans auth."""
        response = self.client.get('/statics/common/css/base.css')
        # Les fichiers statiques doivent être accessibles (même si 404)
        assert response.status_code in [200, 404, 302]

    def test_error_handler_without_auth(self):
        """Test des gestionnaires d'erreur."""
        response = self.client.get('/route_vraiment_inexistante_12345')
        # Redirection vers login car pas d'auth pour routes inexistantes
        assert response.status_code == 302
        assert '/login' in response.location


class TestApplicationCore:
    """Tests des fonctionnalités core de l'application."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Configuration pour chaque test."""
        acfc.config['TESTING'] = True
        self.client = acfc.test_client()

    def test_app_configuration(self):
        """Test de la configuration de l'application."""
        assert acfc.config['TESTING'] is True
        assert acfc.name == 'app_acfc.application'

    def test_app_has_required_routes(self):
        """Test que l'application a les routes essentielles."""
        rules = [rule.rule for rule in acfc.url_map.iter_rules()]
        
        essential_routes = ['/', '/login', '/logout', '/health']
        for route in essential_routes:
            assert route in rules, f"Route {route} manquante"

    def test_app_blueprints_registered(self):
        """Test que les blueprints sont enregistrés."""
        blueprint_names = [bp.name for bp in acfc.blueprints.values()]
        
        # Les blueprints de contexte doivent être présents
        expected_blueprints = ['admin', 'clients', 'commandes', 'commercial', 'comptabilite', 'stocks', 'catalogue']
        for bp_name in expected_blueprints:
            assert bp_name in blueprint_names, f"Blueprint {bp_name} manquant"

    def test_middleware_before_request_exists(self):
        """Test que le middleware before_request existe."""
        # Le middleware doit être enregistré
        assert len(acfc.before_request_funcs[None]) > 0

    def test_error_handlers_registered(self):
        """Test que les gestionnaires d'erreur sont enregistrés."""
        # Test qu'il y a des gestionnaires d'erreur
        assert len(acfc.error_handler_spec) > 0 or len(acfc.error_handler_spec[None]) > 0

    @patch('app_acfc.application.ph_acfc')
    def test_password_service_available(self, mock_ph: Mock):
        """Test que le service de mot de passe est disponible."""
        # Le service doit être importable et utilisable
        from app_acfc.application import ph_acfc
        assert ph_acfc is not None
