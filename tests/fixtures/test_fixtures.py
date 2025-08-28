"""
Fixtures de Test - Système de Bon de Commande
=============================================

Ce module contient les fixtures et données de test
pour le système de génération de bons de commande.

Auteur : Développement ACFC
Version : 1.0
"""

import pytest
import sys
import os
from datetime import datetime, date
from unittest.mock import Mock, MagicMock

# Ajouter le chemin du projet pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))


@pytest.fixture
def sample_client():
    """Fixture pour un client de test"""
    return {
        'id': 1,
        'nom': 'Entreprise Dupont',
        'adresse': '123 Rue de la Paix',
        'ville': 'Paris',
        'code_postal': '75001',
        'telephone': '01.23.45.67.89',
        'email': 'contact@dupont.fr',
        'siret': '12345678901234',
        'tva': 'FR12345678901'
    }


@pytest.fixture
def sample_articles():
    """Fixture pour des articles de test"""
    return [
        {
            'id': 1,
            'nom': 'Article Premium A',
            'description': 'Article de haute qualité',
            'quantite': 2,
            'prix_unitaire': 50.0,
            'tva': 20.0,
            'total_ht': 100.0,
            'total_ttc': 120.0
        },
        {
            'id': 2,
            'nom': 'Article Standard B',
            'description': 'Article standard',
            'quantite': 1,
            'prix_unitaire': 75.0,
            'tva': 20.0,
            'total_ht': 75.0,
            'total_ttc': 90.0
        },
        {
            'id': 3,
            'nom': 'Article Économique C',
            'description': 'Article économique',
            'quantite': 3,
            'prix_unitaire': 25.0,
            'tva': 20.0,
            'total_ht': 75.0,
            'total_ttc': 90.0
        }
    ]


@pytest.fixture
def sample_commande(sample_client, sample_articles):
    """Fixture pour une commande de test complète"""
    return {
        'id': 1,
        'numero': 'CMD-2024-001',
        'client_id': sample_client['id'],
        'client': sample_client,
        'date_creation': datetime(2024, 1, 15, 10, 30, 0),
        'date_livraison': date(2024, 1, 25),
        'statut': 'En préparation',
        'articles': sample_articles,
        'total_ht': 250.0,
        'total_tva': 50.0,
        'total_ttc': 300.0,
        'commentaires': 'Commande prioritaire',
        'facturation': {
            'facturee': False,
            'date_facture': None,
            'numero_facture': None
        },
        'expedition': {
            'expediee': False,
            'date_expedition': None,
            'transporteur': None,
            'numero_suivi': None
        }
    }


@pytest.fixture
def sample_commande_facturee(sample_commande):
    """Fixture pour une commande facturée"""
    commande = sample_commande.copy()
    commande['facturation'] = {
        'facturee': True,
        'date_facture': datetime(2024, 1, 20, 14, 0, 0),
        'numero_facture': 'FACT-2024-001'
    }
    commande['statut'] = 'Facturée'
    return commande


@pytest.fixture
def sample_commande_expediee(sample_commande_facturee):
    """Fixture pour une commande expédiée"""
    commande = sample_commande_facturee.copy()
    commande['expedition'] = {
        'expediee': True,
        'date_expedition': datetime(2024, 1, 22, 9, 15, 0),
        'transporteur': 'Colissimo',
        'numero_suivi': '3S12345678901'
    }
    commande['statut'] = 'Expédiée'
    return commande


@pytest.fixture
def mock_flask_app():
    """Fixture pour une application Flask mockée"""
    app = Mock()
    app.config = {
        'SECRET_KEY': 'test-secret-key',
        'TESTING': True,
        'DATABASE_URL': 'sqlite:///:memory:'
    }
    
    # Mock du contexte Flask
    app_context = Mock()
    app_context.__enter__ = Mock(return_value=app_context)
    app_context.__exit__ = Mock(return_value=None)
    app.app_context = Mock(return_value=app_context)
    
    return app


@pytest.fixture
def mock_qr_code():
    """Fixture pour un QR Code mocké"""
    mock_qr = Mock()
    mock_qr.add_data = Mock()
    mock_qr.make = Mock()
    
    # Mock de l'image générée
    mock_img = Mock()
    mock_img.size = (90, 90)
    mock_img.save = Mock()
    mock_qr.make_image = Mock(return_value=mock_img)
    
    return mock_qr


@pytest.fixture
def sample_qr_code_base64():
    """Fixture pour un QR Code en base64"""
    # QR Code minimal en base64 (image 1x1 pixel PNG)
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


@pytest.fixture
def sample_urls():
    """Fixture pour des URLs de test"""
    return {
        'base_url': 'http://localhost:5000',
        'details_url': '/commandes/client/1/commandes/1/details',
        'bon_url': '/commandes/client/1/commandes/1/bon-impression',
        'auto_print_url': '/commandes/client/1/commandes/1/bon-impression?auto_print=true',
        'print_close_url': '/commandes/client/1/commandes/1/bon-impression?auto_print=close',
        'fast_print_url': '/commandes/client/1/commandes/1/bon-impression?auto_print=true&delay=500',
        'test_mode_url': '/commandes/client/1/commandes/1/bon-impression?click_print=true'
    }


@pytest.fixture
def mock_template_context():
    """Fixture pour un contexte de template mocké"""
    return {
        'commande': None,  # Sera remplacé par une fixture de commande
        'client': None,    # Sera remplacé par une fixture de client
        'qr_code': None,   # Sera remplacé par une fixture de QR code
        'auto_print': False,
        'delay': 1500,
        'click_print': False,
        'current_user': {
            'id': 1,
            'nom': 'Utilisateur Test',
            'role': 'commercial'
        }
    }


@pytest.fixture
def sample_print_parameters():
    """Fixture pour les paramètres d'impression"""
    return [
        {'params': '', 'auto_print': False, 'delay': None, 'close_after': False},
        {'params': 'auto_print=true', 'auto_print': True, 'delay': 1500, 'close_after': False},
        {'params': 'auto_print=close', 'auto_print': True, 'delay': 1500, 'close_after': True},
        {'params': 'auto_print=true&delay=500', 'auto_print': True, 'delay': 500, 'close_after': False},
        {'params': 'click_print=true', 'auto_print': False, 'delay': None, 'close_after': False}
    ]


@pytest.fixture
def mock_database():
    """Fixture pour une base de données mockée"""
    db = Mock()
    
    # Mock des opérations de base
    db.session = Mock()
    db.session.query = Mock()
    db.session.add = Mock()
    db.session.commit = Mock()
    db.session.rollback = Mock()
    
    return db


@pytest.fixture
def mock_request():
    """Fixture pour un objet request Flask mocké"""
    request = Mock()
    request.method = 'GET'
    request.args = {}
    request.form = {}
    request.json = None
    request.headers = {}
    request.url = 'http://localhost:5000/test'
    request.base_url = 'http://localhost:5000'
    
    return request


@pytest.fixture
def error_scenarios():
    """Fixture pour les scénarios d'erreur"""
    return [
        {
            'name': 'Client ID invalide',
            'client_id': 'abc',
            'commande_id': '123',
            'expected_error': 'Client ID non numérique'
        },
        {
            'name': 'Commande ID invalide',
            'client_id': '123',
            'commande_id': 'xyz',
            'expected_error': 'Commande ID non numérique'
        },
        {
            'name': 'Client ID négatif',
            'client_id': '-1',
            'commande_id': '123',
            'expected_error': 'Client ID négatif'
        },
        {
            'name': 'Commande ID zéro',
            'client_id': '123',
            'commande_id': '0',
            'expected_error': 'Commande ID zéro'
        },
        {
            'name': 'Commande inexistante',
            'client_id': '123',
            'commande_id': '999999',
            'expected_error': 'Commande non trouvée'
        }
    ]


@pytest.fixture
def performance_test_data():
    """Fixture pour les tests de performance"""
    return {
        'small_commande': {
            'articles_count': 3,
            'expected_time_ms': 100
        },
        'medium_commande': {
            'articles_count': 50,
            'expected_time_ms': 500
        },
        'large_commande': {
            'articles_count': 200,
            'expected_time_ms': 1000
        }
    }


@pytest.fixture
def browser_compatibility():
    """Fixture pour les tests de compatibilité navigateur"""
    return {
        'chrome': {
            'auto_print': True,
            'auto_close': True,
            'pdf_viewer': True,
            'javascript': True
        },
        'firefox': {
            'auto_print': True,
            'auto_close': False,
            'pdf_viewer': True,
            'javascript': True
        },
        'safari': {
            'auto_print': True,
            'auto_close': False,
            'pdf_viewer': True,
            'javascript': True
        },
        'edge': {
            'auto_print': True,
            'auto_close': True,
            'pdf_viewer': True,
            'javascript': True
        },
        'ie11': {
            'auto_print': False,
            'auto_close': False,
            'pdf_viewer': False,
            'javascript': True
        },
        'mobile_chrome': {
            'auto_print': False,
            'auto_close': False,
            'pdf_viewer': True,
            'javascript': True
        }
    }


@pytest.fixture
def sample_test_scenarios():
    """Fixture pour différents scénarios de test"""
    return [
        {
            'name': 'Commande simple',
            'commande_id': 1,
            'client_id': 1,
            'articles_count': 3,
            'total': 300.0,
            'statut': 'En préparation'
        },
        {
            'name': 'Commande complexe',
            'commande_id': 999,
            'client_id': 888,
            'articles_count': 15,
            'total': 9999.99,
            'statut': 'Facturée'
        },
        {
            'name': 'Commande vide',
            'commande_id': 2,
            'client_id': 2,
            'articles_count': 0,
            'total': 0.0,
            'statut': 'Brouillon'
        },
        {
            'name': 'Commande expédiée',
            'commande_id': 3,
            'client_id': 3,
            'articles_count': 7,
            'total': 1234.56,
            'statut': 'Expédiée'
        }
    ]


# Utilitaires pour les tests

class TestDataBuilder:
    """Constructeur de données de test"""
    
    @staticmethod
    def build_commande(commande_id=1, client_id=1, articles_count=3):
        """Construit une commande de test avec le nombre d'articles spécifié"""
        articles = []
        total_ht = 0
        
        for i in range(articles_count):
            prix = 50.0 + (i * 10)
            quantite = i + 1
            total_article = prix * quantite
            
            articles.append({
                'id': i + 1,
                'nom': f'Article Test {i + 1}',
                'quantite': quantite,
                'prix_unitaire': prix,
                'total_ht': total_article
            })
            
            total_ht += total_article
        
        return {
            'id': commande_id,
            'client_id': client_id,
            'articles': articles,
            'total_ht': total_ht,
            'total_ttc': total_ht * 1.2,  # TVA 20%
            'date_creation': datetime.now(),
            'statut': 'En préparation'
        }
    
    @staticmethod
    def build_qr_url(client_id, commande_id, base_url='http://localhost:5000'):
        """Construit une URL pour QR Code"""
        return f"{base_url}/commandes/client/{client_id}/commandes/{commande_id}/details"
    
    @staticmethod
    def build_print_url(client_id, commande_id, **params):
        """Construit une URL d'impression avec paramètres"""
        base_url = f"/commandes/client/{client_id}/commandes/{commande_id}/bon-impression"
        
        if params:
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            return f"{base_url}?{param_string}"
        
        return base_url


# Configuration globale des fixtures

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Configuration automatique de l'environnement de test"""
    # Configuration du logging pour les tests
    import logging
    logging.getLogger().setLevel(logging.WARNING)
    
    # Configuration des variables d'environnement de test
    os.environ['TESTING'] = 'True'
    os.environ['FLASK_ENV'] = 'testing'
    
    yield
    
    # Nettoyage après les tests
    if 'TESTING' in os.environ:
        del os.environ['TESTING']
    if 'FLASK_ENV' in os.environ:
        del os.environ['FLASK_ENV']
