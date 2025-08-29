#!/usr/bin/env python3
"""
Test simple sans aucun import de l'application
==============================================

Ce test ne fait aucun import de l'application et ne devrait pas échouer.
"""


def test_simple_python():
    """Test simple sans aucune dépendance."""
    assert 1 + 1 == 2


def test_basic_data_structures():
    """Test des structures de données de base."""
    # Test de liste
    my_list = [1, 2, 3, 4, 5]
    assert len(my_list) == 5
    assert my_list[0] == 1
    
    # Test de dictionnaire
    my_dict = {'a': 1, 'b': 2, 'c': 3}
    assert my_dict['a'] == 1
    assert len(my_dict) == 3
    
    # Test de string
    my_string = "Hello World"
    assert my_string.upper() == "HELLO WORLD"
    assert len(my_string) == 11


def test_basic_functions():
    """Test de fonctions simples."""
    def add_numbers(a: int, b: int) -> int:
        return a + b
    
    def multiply_numbers(a: int, b: int) -> int:
        return a * b
    
    assert add_numbers(2, 3) == 5
    assert multiply_numbers(4, 5) == 20


def test_environment_variables():
    """Test que les variables d'environnement de test sont présentes."""
    import os
    
    # Ces variables devraient être définies par le conftest
    assert os.environ.get('TESTING') == 'true'
    # Note: on ne teste pas les autres variables car elles pourraient ne pas être définies
    # dans un environnement de test simple


def test_mock_system():
    """Test que le système de mocking fonctionne."""
    from unittest.mock import Mock, MagicMock
    
    # Créer des mocks simples
    mock_obj = Mock()
    mock_obj.method.return_value = "test_result"
    
    result = mock_obj.method()
    assert result == "test_result"
    
    # Test avec MagicMock
    magic_mock = MagicMock()
    magic_mock.attribute = "test_attribute"
    
    assert magic_mock.attribute == "test_attribute"


class TestBasicClass:
    """Classe de test simple."""
    
    def test_class_method(self):
        """Test d'une méthode de classe."""
        ok = True
        assert ok is True
    
    def test_setup_and_teardown(self):
        """Test de setup et teardown."""
        # Setup
        test_data = {"key": "value"}
        
        # Test
        assert test_data["key"] == "value"
        
        # Teardown (automatique)


def test_string_operations():
    """Test d'opérations sur les chaînes."""
    text = "hello test"
    
    assert text.startswith("hello")
    assert text.endswith("test")
    assert "test" in text
    assert text.replace("test", "example") == "hello example"


def test_list_operations():
    """Test d'opérations sur les listes."""
    numbers = [1, 2, 3, 4, 5]
    
    # Filtrage
    even_numbers = [x for x in numbers if x % 2 == 0]
    assert even_numbers == [2, 4]
    
    # Mapping
    squared_numbers = [x**2 for x in numbers]
    assert squared_numbers == [1, 4, 9, 16, 25]
    
    # Réduction
    total = sum(numbers)
    assert total == 15


def test_exception_handling():
    """Test de gestion des exceptions."""
    import pytest
    
    def divide_by_zero():
        return 1 / 0
    
    with pytest.raises(ZeroDivisionError):
        divide_by_zero()


def test_parametrized_simple():
    """Test simple avec paramètres."""
    test_cases = [
        (1, 2, 3),
        (0, 5, 5),
        (-1, 1, 0),
        (10, -3, 7)
    ]
    
    for a, b, expected in test_cases:
        result = a + b
        assert result == expected, f"Failed for {a} + {b}, expected {expected}, got {result}"
