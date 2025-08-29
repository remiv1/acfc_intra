#!/usr/bin/env python3
"""
Version test du fichier modeles.py - Complètement mockée
========================================================

Cette version remplace complètement les connexions réelles par des mocks
pour éviter toute tentative de connexion à la base de données pendant les tests.

Auteur : ACFC Development Team  
Version : 1.0
"""

import os
from unittest.mock import MagicMock
from typing import Any

# En mode test, tout est mocké - aucun import de SQLAlchemy ou MySQL
print("🧪 Mode test activé - Toutes les connexions base de données sont mockées")

# Mock de la configuration
class Configuration:
    def __init__(self):
        self.db_port = 3306
        self.db_name = 'test_db'
        self.db_user = 'test_user'
        self.db_password = 'test_password'
        self.db_host = 'localhost'

def verify_env() -> bool:
    """Mock de verify_env - retourne toujours True en test."""
    return True

def init_database(*args: Any, **kwargs: Any) -> None:
    """Mock de init_database - ne fait rien en test."""
    print("✅ Base de données mockée pour les tests")
    return None

# Tous les objets SQLAlchemy sont mockés
engine = MagicMock()

# Déclarations forward des classes pour éviter les erreurs d'ordre
User = None
Client = None
Commande = None

# Mock de SessionBdD plus réaliste
class MockSession:
    """Session de base de données mockée pour les tests."""
    
    def __init__(self):
        self._users = {}
        self._clients = {}
        self._commandes = {}
        self._last_id = 1
        
    def _init_test_data(self):
        """Initialise les données de test après que les classes soient définies."""
        global User
        if User is not None:
            # Ajouter quelques données de test par défaut
            test_user = User(
                id=1, 
                pseudo='testuser', 
                email='test@example.com',
                sha_mdp='$argon2id$v=19$m=65536,t=3,p=4$test$validhash',
                nb_errors=0,
                permission='admin',  # Ajouter permission
                prenom='Test',       # Ajouter prenom  
                nom='User',          # Ajouter nom
                last_name='User',    # Alias pour nom
                first_name='Test'    # Alias pour prenom
            )
            self._users[1] = test_user
            self._users['testuser'] = test_user
        
    def query(self, model_class):
        """Mock de la méthode query."""
        mock_query = MagicMock()
        
        if model_class.__name__ == 'User':
            mock_query.filter_by = lambda **kwargs: self._filter_users(**kwargs)
            mock_query.filter = lambda condition: self._filter_users_advanced(condition)
            mock_query.all = lambda: list(self._users.values())
            mock_query.first = lambda: list(self._users.values())[0] if self._users else None
            
        elif model_class.__name__ == 'Client':
            mock_query.filter_by = lambda **kwargs: self._filter_clients(**kwargs)
            mock_query.all = lambda: list(self._clients.values())
            mock_query.first = lambda: list(self._clients.values())[0] if self._clients else None
            
        elif model_class.__name__ == 'Commande':
            mock_query.filter_by = lambda **kwargs: self._filter_commandes(**kwargs)
            mock_query.all = lambda: list(self._commandes.values())
            mock_query.first = lambda: list(self._commandes.values())[0] if self._commandes else None
            
        return mock_query
    
    def _filter_users(self, **kwargs):
        """Filtre les utilisateurs selon les critères."""
        mock_query = MagicMock()
        
        if 'pseudo' in kwargs:
            user = self._users.get(kwargs['pseudo'])
            mock_query.first = lambda u=user: u
            mock_query.all = lambda u=user: [u] if u else []
        elif 'email' in kwargs:
            # Chercher par email
            for user in self._users.values():
                if hasattr(user, 'email') and user.email == kwargs['email']:
                    mock_query.first = lambda u=user: u
                    mock_query.all = lambda u=user: [u]
                    return mock_query
            mock_query.first = lambda: None
            mock_query.all = lambda: []
        else:
            mock_query.first = lambda: None
            mock_query.all = lambda: []
            
        return mock_query
    
    def _filter_users_advanced(self, condition):
        """Filtre avancé pour les utilisateurs."""
        mock_query = MagicMock()
        mock_query.first = lambda: list(self._users.values())[0] if self._users else None
        mock_query.all = lambda: list(self._users.values())
        return mock_query
    
    def _filter_clients(self, **kwargs):
        """Filtre les clients selon les critères."""
        mock_query = MagicMock()
        mock_query.first = lambda: None
        mock_query.all = lambda: []
        return mock_query
    
    def _filter_commandes(self, **kwargs):
        """Filtre les commandes selon les critères."""
        mock_query = MagicMock()
        mock_query.first = lambda: None
        mock_query.all = lambda: []
        return mock_query
    
    def add(self, obj):
        """Mock de la méthode add."""
        pass
    
    def execute(self, statement):
        """Mock de la méthode execute pour les requêtes SQL directes."""
        # Simule l'exécution d'une requête SQL (comme SELECT 1 pour health check)
        return MagicMock()  # Retourne un résultat mock
    
    def commit(self):
        """Mock de la méthode commit."""
        pass
    
    def rollback(self):
        """Mock de la méthode rollback."""
        pass
    
    def close(self):
        """Mock de la méthode close."""
        pass
    
    def flush(self):
        """Mock de la méthode flush."""
        pass
    
    def refresh(self, obj):
        """Mock de la méthode refresh."""
        pass
    
    def __call__(self):
        """Permet d'utiliser SessionBdD() comme un callable."""
        return self

# Instance globale de la session mockée
SessionBdD = MockSession()
Base = MagicMock()

# Mock des classes de modèles avec des attributs de base
class User:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.pseudo = kwargs.get('pseudo', 'testuser')
        self.prenom = kwargs.get('prenom', 'Test')
        self.nom = kwargs.get('nom', 'User')
        self.email = kwargs.get('email', 'test@example.com')
        self.telephone = kwargs.get('telephone', '0123456789')
        self.actif = kwargs.get('actif', True)
        # Attributs manquants qui causent les erreurs TypeError
        self.nb_errors = kwargs.get('nb_errors', 0)  # Pour user.nb_errors > 0
        self.sha_mdp = kwargs.get('sha_mdp', '$argon2id$v=19$m=65536,t=3,p=4$test$hash')  # Hash mock
        self.mot_de_passe = kwargs.get('mot_de_passe', 'hashed_password')  # Pour login
        self.role = kwargs.get('role', 'user')
        self.permission = kwargs.get('permission', 'user')  # AJOUT : pour session['habilitations']
        self.is_chg_mdp = kwargs.get('is_chg_mdp', False)  # AJOUT : pour changement mdp forcé
        self.last_login = kwargs.get('last_login', None)
        self.derniere_connexion = kwargs.get('derniere_connexion', None)  # AJOUT : pour login
        self.created_at = kwargs.get('created_at', None)
        self.updated_at = kwargs.get('updated_at', None)
        self.is_admin = kwargs.get('is_admin', False)
        self.is_active = kwargs.get('is_active', True)
        
        # Alias pour compatibilité avec les templates
        self.last_name = self.nom
        self.first_name = self.prenom
        
    def __str__(self):
        return f"User(id={self.id}, pseudo='{self.pseudo}')"
    
    def __repr__(self):
        return self.__str__()

class Client:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.nom = kwargs.get('nom', 'Test Client')
        self.email = kwargs.get('email', 'client@example.com')
        self.telephone = kwargs.get('telephone', '0123456789')
        self.actif = kwargs.get('actif', True)
        self.adresse = kwargs.get('adresse', 'Test Address')
        self.code_postal = kwargs.get('code_postal', '12345')
        self.ville = kwargs.get('ville', 'Test City')
        
    def __str__(self):
        return f"Client(id={self.id}, nom='{self.nom}')"
    
    def __repr__(self):
        return self.__str__()

class Commande:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.numero = kwargs.get('numero', 'CMD-001')
        self.client_id = kwargs.get('client_id', 1)
        self.date_creation = kwargs.get('date_creation', None)
        self.statut = kwargs.get('statut', 'en_cours')
        self.montant = kwargs.get('montant', 0.0)
        
    def __str__(self):
        return f"Commande(id={self.id}, numero='{self.numero}')"
    
    def __repr__(self):
        return self.__str__()

# Toutes les autres classes mockées pour éviter les erreurs d'import
class Part:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Pro:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Telephone:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Mail:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Facture:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Adresse:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class DevisesFactures:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Expeditions:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Catalogue:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class PCG:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Operations:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Ventilations:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Documents:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Stock:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Villes:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class IndicatifsTel:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

class Moi:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        for key, value in kwargs.items():
            setattr(self, key, value)

# Initialiser les données de test maintenant que toutes les classes sont définies
SessionBdD._init_test_data()
print("✅ Données de test mockées initialisées")
