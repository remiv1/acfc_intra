"""
Tests de base pour vérifier le fonctionnement de l'infrastructure de test
=======================================================================

Ce module contient des tests simples pour valider que l'infrastructure
de test fonctionne correctement sans dépendre de l'application Flask.
"""

from typing import Any, Union, List, Dict
import pytest
import os
from unittest.mock import Mock, patch

# Test basique pour valider pytest
def test_pytest_works() -> None:
    """Test basique pour vérifier que pytest fonctionne"""
    assert True


def test_environment_variables() -> None:
    """Test pour vérifier les variables d'environnement de test"""
    assert os.environ.get('TESTING') == 'true'
    assert os.environ.get('FLASK_ENV') == 'testing'


@pytest.mark.unit
def test_unit_marker() -> None:
    """Test avec marqueur unit"""
    assert 1 + 1 == 2


@pytest.mark.integration
def test_integration_marker() -> None:
    """Test avec marqueur integration"""
    data = {'key': 'value'}
    assert data['key'] == 'value'


class TestBasicFunctionality:
    """Classe de tests pour les fonctionnalités de base"""
    
    def test_string_operations(self) -> None:
        """Test des opérations sur les chaînes"""
        text = "Hello, ACFC!"
        assert text.upper() == "HELLO, ACFC!"
        assert text.lower() == "hello, acfc!"
        assert "ACFC" in text

    def test_list_operations(self) -> None:
        """Test des opérations sur les listes"""
        data = [1, 2, 3, 4, 5]
        assert len(data) == 5
        assert max(data) == 5
        assert min(data) == 1
    
    def test_dict_operations(self) -> None:
        """Test des opérations sur les dictionnaires"""
        user_data = {
            'nom': 'Test',
            'prenom': 'User',
            'email': 'test@example.com'
        }
        assert user_data['nom'] == 'Test'
        assert 'email' in user_data
        assert len(user_data.keys()) == 3


class TestMockFunctionality:
    """Classe de tests pour les fonctionnalités de mock"""
    
    def test_mock_basic(self):
        """Test basique avec mock"""
        mock_object = Mock()
        mock_object.method.return_value = "mocked result"
        
        result = mock_object.method()
        assert result == "mocked result"
        mock_object.method.assert_called_once()
    
    @patch('builtins.print')
    def test_patch_decorator(self, mock_print: Mock) -> None:
        """Test avec décorateur patch"""
        print("Hello, World!")
        mock_print.assert_called_once_with("Hello, World!")

    def test_mock_side_effect(self) -> None:
        """Test avec side_effect"""
        mock_function = Mock()
        mock_function.side_effect = [1, 2, 3]
        
        assert mock_function() == 1
        assert mock_function() == 2
        assert mock_function() == 3


@pytest.mark.slow
class TestSlowOperations:
    """Tests marqués comme lents"""
    
    def test_large_computation(self):
        """Test d'une opération potentiellement lente"""
        # Simulation d'un calcul
        result = sum(range(1000))
        expected = 999 * 1000 // 2
        assert result == expected


class TestParametrizedTests:
    """Tests paramétrés"""
    
    @pytest.mark.parametrize("input_value,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
        (5, 10)
    ])
    def test_multiply_by_two(self, input_value: int, expected: int) -> None:
        """Test paramétré pour multiplication par 2"""
        result = input_value * 2
        assert result == expected
    
    @pytest.mark.parametrize("email", [
        "test@example.com",
        "user@domain.org",
        "admin@company.fr"
    ])
    def test_email_format(self, email: str) -> None:
        """Test paramétré pour validation d'email"""
        assert "@" in email
        assert "." in email
        assert len(email) > 5


class TestFixtures:
    """Tests utilisant des fixtures"""
    
    @pytest.fixture
    def sample_data(self) -> Dict[str, List[Dict[str, int | str]] | int]:
        """Fixture avec des données d'exemple"""
        return {
            'users': [
                {'id': 1, 'name': 'Alice'},
                {'id': 2, 'name': 'Bob'},
                {'id': 3, 'name': 'Charlie'}
            ],
            'total': 3
        }
    
    def test_fixture_usage(self, sample_data: Dict[str, List[Dict[str, int | str]]] | int) -> None:
        """Test utilisant la fixture sample_data"""
        users: List[Dict[str, int | str]] = sample_data['users']    # type: ignore
        assert sample_data['total'] == 3    # type: ignore
        assert len(users) == 3  # type: ignore
        assert users[0]['name'] == 'Alice'  # type: ignore

    def test_fixture_modification(self, sample_data: Dict[str, List[Dict[str, int | str]]] | int) -> None:
        """Test modifiant les données de la fixture"""
        if isinstance(sample_data, dict):
            sample_data['users'].append({'id': 4, 'name': 'David'})
            assert len(sample_data['users']) == 4


class TestExceptionHandling:
    """Tests pour la gestion des exceptions"""
    
    def test_exception_raised(self) -> None:
        """Test vérifiant qu'une exception est levée"""
        with pytest.raises(ValueError):
            int("not a number")

    def test_exception_message(self) -> None:
        """Test vérifiant le message d'exception"""
        with pytest.raises(ZeroDivisionError, match="division by zero"):
            1 / 0  # type: ignore

    def test_exception_with_custom_message(self) -> None:
        """Test avec message d'exception personnalisé"""
        def divide_positive(a: int, b: int) -> Any:
            if b == 0:
                raise ValueError("Cannot divide by zero")
            if a < 0 or b < 0:
                raise ValueError("Only positive numbers allowed")
            return a / b
        
        with pytest.raises(ValueError, match="Only positive numbers"):
            divide_positive(-1, 2)


@pytest.mark.auth
class TestAuthenticationMocks:
    """Tests mockés pour l'authentification"""
    
    def test_user_authentication_success(self):
        """Test d'authentification réussie"""
        # Mock d'un service d'authentification
        auth_service = Mock()
        auth_service.authenticate.return_value = {
            'success': True,
            'user_id': 1,
            'username': 'testuser'
        }
        
        result = auth_service.authenticate('testuser', 'password')
        assert result['success'] is True
        assert result['user_id'] == 1
    
    def test_user_authentication_failure(self):
        """Test d'authentification échouée"""
        auth_service = Mock()
        auth_service.authenticate.return_value = {
            'success': False,
            'error': 'Invalid credentials'
        }
        
        result = auth_service.authenticate('wronguser', 'wrongpass')
        assert result['success'] is False
        assert 'error' in result


@pytest.mark.security
class TestSecurityValidation:
    """Tests de validation de sécurité"""
    
    def test_password_strength(self):
        """Test de validation de force de mot de passe"""
        def validate_password(password: str) -> tuple[bool, str]:
            if len(password) < 8:
                return False, "Password too short"
            if not any(c.isupper() for c in password):
                return False, "Password must contain uppercase"
            if not any(c.islower() for c in password):
                return False, "Password must contain lowercase"
            if not any(c.isdigit() for c in password):
                return False, "Password must contain digits"
            return True, "Password valid"
        
        # Mot de passe valide
        valid, msg = validate_password("StrongPass123")
        assert valid is True
        
        # Mot de passe trop court
        valid, msg = validate_password("Short1")
        assert valid is False
        assert "too short" in msg
    
    def test_input_sanitization(self):
        """Test de validation d'entrée"""
        def sanitize_input(text: str) -> Union[str, None]:
            dangerous_chars = ['<', '>', '"', "'", '&']
            for char in dangerous_chars:
                if char in text:
                    return None
            return text.strip()
        
        # Entrée valide
        assert sanitize_input("Hello World") == "Hello World"
        
        # Entrée dangereuse
        assert sanitize_input("<script>alert('xss')</script>") is None
        assert sanitize_input("Hello & World") is None


# Fonction utilitaire pour les tests
def setup_test_environment() -> Dict[str, Any]:
    """Configuration de l'environnement de test"""
    test_config: Dict[str, Any] = {
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'DATABASE_URL': 'sqlite:///:memory:'
    }
    return test_config


# Tests de performance basiques
@pytest.mark.benchmark
def test_performance_basic():
    """Test de performance basique"""
    import time
    start = time.time()
    
    # Opération à mesurer
    result = sum(range(10000))
    
    end = time.time()
    duration = end - start
    
    # Vérifier que l'opération prend moins d'une seconde
    assert duration < 1.0
    assert result > 0
