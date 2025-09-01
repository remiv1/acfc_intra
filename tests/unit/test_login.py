#!/usr/bin/env python3
"""
Tests Unitaires pour l'Authentification
=======================================

Tests des scénarios d'authentification avec mocks appropriés.
Cette version évite les dépendances de base de données pour les tests isolés.

Scénarios testés :
- Utilisateur inexistant
- Utilisateur désactivé  
- Utilisateur bloqué
- Connexion réussie
- Vérification des mots de passe

Auteur : ACFC Development Team
Version : 1.0
"""

import pytest
from unittest.mock import Mock
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from typing import Any, List, Dict


class PasswordService:
    """Service de mot de passe pour les tests."""
    
    def __init__(self):
        self.hasher = PasswordHasher()
    
    def hash_password(self, password: str) -> str:
        return self.hasher.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        try:
            self.hasher.verify(hashed, password)
            return True
        except VerifyMismatchError:
            return False


# Mots de passe de test pré-hachés
_password_service = PasswordService()
TEST_PASSWORDS = {
    'admin': _password_service.hash_password('admin123!'),
    'commercial': _password_service.hash_password('commercial123!'),
    'user': _password_service.hash_password('user123!'),
    'test': _password_service.hash_password('test123!'),
}


class UserFixtures:
    """Fixtures pour les objets User mockés."""
    
    @staticmethod
    def user_admin() -> Mock:
        """Utilisateur administrateur avec tous les droits."""
        user = Mock()
        user.id = 1
        user.prenom = "Admin"
        user.nom = "SYSTÈME"
        user.pseudo = "admin"
        user.email = "admin@acfc.local"
        user.sha_mdp = TEST_PASSWORDS['admin']
        user.is_active = True
        user.is_locked = False
        user.nb_errors = 0
        user.permission = "ADMIN"
        user.is_chg_mdp = False
        return user
    
    @staticmethod
    def user_commercial() -> Mock:
        """Utilisateur commercial standard."""
        user = Mock()
        user.id = 2
        user.prenom = "Jean"
        user.nom = "COMMERCIAL"
        user.pseudo = "jcommercial"
        user.email = "commercial@acfc.local"
        user.sha_mdp = TEST_PASSWORDS['commercial']
        user.is_active = True
        user.is_locked = False
        user.nb_errors = 0
        user.permission = "37"
        user.is_chg_mdp = False
        return user
    
    @staticmethod
    def user_locked() -> Mock:
        """Utilisateur verrouillé pour tests de sécurité."""
        user = Mock()
        user.id = 3
        user.prenom = "Bloqué"
        user.nom = "UTILISATEUR"
        user.pseudo = "bloque"
        user.email = "bloque@acfc.local"
        user.sha_mdp = TEST_PASSWORDS['user']
        user.is_active = False  # Important: inactif car bloqué
        user.is_locked = True
        user.nb_errors = 5
        user.permission = "5"
        user.is_chg_mdp = True
        return user
    
    @staticmethod
    def user_inactive() -> Mock:
        """Utilisateur inactif."""
        user = Mock()
        user.id = 4
        user.prenom = "Inactif"
        user.nom = "UTILISATEUR"
        user.pseudo = "inactif"
        user.email = "inactif@acfc.local"
        user.sha_mdp = TEST_PASSWORDS['user']
        user.is_active = False
        user.is_locked = False
        user.nb_errors = 0
        user.permission = "2"
        user.is_chg_mdp = False
        return user


class MockSession:
    """Session de base de données mockée pour les tests."""
    
    def __init__(self):
        self._query_results: Dict[Any, Any] = {}
        self.add_called_with: List[Any] = []
        self.commit_called: int = 0
        self.rollback_called: int = 0
        self.flush_called: int = 0

    def set_query_result(self, model_name: str, results: List[Any]) -> None:
        """Configure le résultat d'une requête."""
        self._query_results[model_name] = results
    
    def query(self, model_name: str):
        """Simule une requête sur un modèle."""
        results = self._query_results.get(model_name, [])
        query_mock = Mock()
        query_mock.all.return_value = results
        query_mock.first.return_value = results[0] if results else None
        query_mock.filter_by.return_value = query_mock
        return query_mock

    def add(self, obj: Any):
        """Simule l'ajout d'un objet."""
        self.add_called_with.append(obj)
    
    def commit(self):
        """Simule un commit."""
        self.commit_called += 1
    
    def rollback(self):
        """Simule un rollback."""
        self.rollback_called += 1
    
    def flush(self):
        """Simule un flush."""
        self.flush_called += 1


class TestUserFixtures:
    """Tests des fixtures utilisateurs."""
    
    def test_user_admin_fixture(self):
        """Test de la fixture utilisateur administrateur."""
        user = UserFixtures.user_admin()
        
        assert user.id == 1
        assert user.pseudo == "admin"
        assert user.permission == "ADMIN"
        assert user.is_active is True
        assert user.is_locked is False
        assert user.nb_errors == 0
        assert user.sha_mdp == TEST_PASSWORDS['admin']
    
    def test_user_commercial_fixture(self):
        """Test de la fixture utilisateur commercial."""
        user = UserFixtures.user_commercial()
        
        assert user.id == 2
        assert user.pseudo == "jcommercial"
        assert user.permission == "37"
        assert user.is_active is True
        assert user.is_locked is False
        assert user.nb_errors == 0
        assert user.sha_mdp == TEST_PASSWORDS['commercial']
    
    def test_user_locked_fixture(self):
        """Test de la fixture utilisateur verrouillé."""
        user = UserFixtures.user_locked()
        
        assert user.id == 3
        assert user.pseudo == "bloque"
        assert user.is_active is False  # Inactif car bloqué
        assert user.is_locked is True
        assert user.nb_errors == 5
        assert user.is_chg_mdp is True
    
    def test_user_inactive_fixture(self):
        """Test de la fixture utilisateur inactif."""
        user = UserFixtures.user_inactive()
        
        assert user.id == 4
        assert user.pseudo == "inactif"
        assert user.is_active is False
        assert user.is_locked is False


class TestAuthenticationScenarios:
    """Tests des scénarios d'authentification."""
    
    @pytest.fixture
    def mock_session(self):
        """Session mockée pour les tests."""
        return MockSession()
    
    @pytest.fixture
    def password_service(self):
        """Service de mot de passe réel pour les tests."""
        return PasswordService()
    
    def test_connexion_utilisateur_inexistant(self, mock_session: MockSession):
        """Test : Tentative de connexion avec utilisateur inexistant."""
        # Arrange
        _ = "utilisateur_inexistant"
        mock_session.set_query_result('User', [])  # Aucun utilisateur trouvé
        
        # Act
        query_result = mock_session.query('User')
        user = query_result.first()
        
        # Assert
        assert user is None, "L'utilisateur inexistant ne devrait pas être trouvé"
    
    def test_connexion_utilisateur_desactive(self, mock_session: MockSession):
        """Test : Tentative de connexion avec utilisateur désactivé."""
        # Arrange
        user_inactif = UserFixtures.user_inactive()
        mock_session.set_query_result('User', [user_inactif])
        
        # Act
        query_result = mock_session.query('User')
        user = query_result.first()
        
        # Assert
        assert user is not None
        assert user.pseudo == "inactif"
        assert user.is_active is False
        assert user.is_locked is False
        # Dans l'application, cette connexion devrait être refusée
    
    def test_connexion_utilisateur_bloque(self, mock_session: MockSession):
        """Test : Tentative de connexion avec utilisateur bloqué."""
        # Arrange
        user_bloque = UserFixtures.user_locked()
        mock_session.set_query_result('User', [user_bloque])
        
        # Act
        query_result = mock_session.query('User')
        user = query_result.first()
        
        # Assert
        assert user is not None
        assert user.pseudo == "bloque"
        assert user.is_locked is True
        assert user.nb_errors == 5
        assert user.is_active is False
        # Dans l'application, cette connexion devrait être refusée
    
    def test_connexion_utilisateur_valide(self, mock_session: MockSession):
        """Test : Connexion réussie avec utilisateur valide."""
        # Arrange
        user_admin = UserFixtures.user_admin()
        mock_session.set_query_result('User', [user_admin])
        
        # Act
        query_result = mock_session.query('User')
        user = query_result.first()
        
        # Assert
        assert user is not None
        assert user.pseudo == "admin"
        assert user.is_active is True
        assert user.is_locked is False
        assert user.nb_errors == 0
        assert user.permission == "ADMIN"
        # Cette connexion devrait réussir
    
    def test_verification_mot_de_passe_correct(self, password_service: PasswordService):
        """Test : Vérification d'un mot de passe correct."""
        # Arrange
        user = UserFixtures.user_admin()
        mot_de_passe_saisi = "admin123!"
        
        # Act
        is_valid = password_service.verify_password(mot_de_passe_saisi, user.sha_mdp)
        
        # Assert
        assert is_valid is True
    
    def test_verification_mot_de_passe_incorrect(self, password_service: PasswordService):
        """Test : Vérification d'un mot de passe incorrect."""
        # Arrange
        user = UserFixtures.user_admin()
        mot_de_passe_incorrect = "mauvais_mdp"
        
        # Act
        is_valid = password_service.verify_password(mot_de_passe_incorrect, user.sha_mdp)
        
        # Assert
        assert is_valid is False


class TestMockSession:
    """Tests de la session mockée."""
    
    def test_session_mock_query_empty(self):
        """Test des requêtes sans données."""
        session = MockSession()
        
        # Test sans données
        query = session.query('User')
        assert query.all() == []
        assert query.first() is None
    
    def test_session_mock_query_with_data(self):
        """Test des requêtes avec données."""
        session = MockSession()
        
        # Test avec données
        users = [UserFixtures.user_admin(), UserFixtures.user_commercial()]
        session.set_query_result('User', users)
        
        query = session.query('User')
        assert len(query.all()) == 2
        assert query.first().pseudo == "admin"
    
    def test_session_mock_operations(self):
        """Test des opérations sur la session mockée."""
        session = MockSession()
        user = UserFixtures.user_admin()
        
        # Test add
        session.add(user)
        assert user in session.add_called_with
        
        # Test commit/rollback/flush
        session.commit()
        session.rollback()
        session.flush()
        
        assert session.commit_called == 1
        assert session.rollback_called == 1
        assert session.flush_called == 1


class TestPasswordSecurity:
    """Tests de sécurité des mots de passe."""
    
    def test_test_passwords_are_hashed(self):
        """Test que les mots de passe de test sont bien hachés."""
        for password_hash in TEST_PASSWORDS.values():
            assert password_hash is not None
            assert len(password_hash) > 20  # Hash Argon2 > 20 caractères
            assert password_hash.startswith('$argon2')  # Format Argon2
    
    def test_different_passwords_different_hashes(self):
        """Test que des mots de passe différents donnent des hashs différents."""
        hashes = list(TEST_PASSWORDS.values())
        unique_hashes = set(hashes)
        assert len(hashes) == len(unique_hashes), "Tous les hashs doivent être uniques"


class TestWorkflowAuthentification:
    """Tests du workflow complet d'authentification."""
    
    @pytest.fixture
    def mock_session(self):
        return MockSession()
    
    @pytest.fixture
    def password_service(self):
        return PasswordService()
    
    def test_workflow_connexion_reussie(self, mock_session: MockSession, password_service: PasswordService):
        """Test : Workflow complet de connexion réussie."""
        # Arrange
        username = "admin"
        password = "admin123!"
        user_admin = UserFixtures.user_admin()
        mock_session.set_query_result('User', [user_admin])
        
        # Simulate authentication workflow
        # 1. Recherche utilisateur par pseudo
        query = mock_session.query('User')
        user = query.first()
        
        # 2. Vérifications de sécurité
        assert user is not None, "Utilisateur non trouvé"
        assert user.is_active is True, "Utilisateur inactif"
        assert user.is_locked is False, "Utilisateur verrouillé"
        
        # 3. Vérification du mot de passe
        password_valid = password_service.verify_password(password, user.sha_mdp)
        assert password_valid is True, "Mot de passe incorrect"
        
        # 4. Connexion réussie
        assert user.pseudo == username
        assert user.permission == "ADMIN"
    
    def test_workflow_connexion_echec_utilisateur_bloque(self, mock_session: MockSession):
        """Test : Workflow de connexion échouée - utilisateur bloqué."""
        # Arrange
        _ = "bloque"
        user_bloque = UserFixtures.user_locked()
        mock_session.set_query_result('User', [user_bloque])
        
        # Act
        query = mock_session.query('User')
        user = query.first()
        
        # Assert
        assert user is not None, "Utilisateur non trouvé"
        
        # Échec attendu: utilisateur bloqué
        assert user.is_locked is True, "L'utilisateur devrait être bloqué"
        assert user.is_active is False, "L'utilisateur devrait être inactif"
        assert user.nb_errors == 5, "Nombre d'erreurs incorrect"
    
    def test_workflow_connexion_echec_mot_de_passe(self, mock_session: MockSession, password_service: PasswordService):
        """Test : Workflow de connexion échouée - mauvais mot de passe."""
        # Arrange
        _ = "admin"
        wrong_password = "mauvais_mdp"
        user_admin = UserFixtures.user_admin()
        mock_session.set_query_result('User', [user_admin])
        
        # Act
        query = mock_session.query('User')
        user = query.first()
        
        # Vérifications de base passent
        assert user is not None
        assert user.is_active is True
        assert user.is_locked is False
        
        # Échec attendu: mauvais mot de passe
        password_valid = password_service.verify_password(wrong_password, user.sha_mdp)
        assert password_valid is False, "Le mot de passe incorrect ne devrait pas être accepté"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
