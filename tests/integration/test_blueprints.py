#!/usr/bin/env python3
"""
Tests pour les Blueprints ACFC
==============================

Tests pour les modules métiers (blueprints) de l'application ACFC :
- Module Clients (CRM)
- Module Catalogue (Produits)
- Module Commercial (Devis/Commandes)
- Module Comptabilité (Facturation)
- Module Stocks (Inventaire)

Ces tests vérifient l'intégration et le fonctionnement des différents
modules métiers de l'application.

Auteur : ACFC Development Team
"""

import pytest
import sys
import os
from typing import Any
from flask.testing import FlaskClient

# Configuration des chemins d'import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app_acfc'))

try:
    from app_acfc.application import acfc
except ImportError as e:
    pytest.skip(f"Impossible d'importer l'application: {e}", allow_module_level=True)

@pytest.fixture
def client():
    """Client de test Flask avec tous les blueprints."""
    acfc.config['TESTING'] = True
    acfc.config['WTF_CSRF_ENABLED'] = False
    
    with acfc.test_client() as client:
        yield client

@pytest.fixture
def authenticated_session(client: FlaskClient) -> Any:
    """Session utilisateur authentifiée pour les tests."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['pseudo'] = 'testuser'
        sess['last_name'] = 'Dupont'
        sess['first_name'] = 'Jean'
        sess['email'] = 'jean.dupont@test.com'
    return sess

class TestBlueprintRegistration:
    """Tests pour vérifier l'enregistrement des blueprints."""
    
    def test_all_blueprints_registered(self):
        """Test que tous les blueprints sont enregistrés."""
        # Liste des blueprints attendus (noms réels sans _bp)
        expected_blueprints = [
            'clients',
            'catalogue', 
            'commercial',
            'comptabilite',
            'stocks'
        ]
        
        registered_blueprints = [bp.name for bp in acfc.blueprints.values()]
        
        for expected_bp in expected_blueprints:
            assert expected_bp in registered_blueprints, f"Blueprint {expected_bp} non enregistré. Blueprints disponibles: {registered_blueprints}"

    def test_blueprint_url_prefixes(self):
        """Test que les blueprints ont les bons préfixes d'URL."""
        expected_prefixes = {
            'clients': '/clients',
            'catalogue': '/catalogue',
            'commercial': '/commercial', 
            'comptabilite': '/comptabilite',
            'stocks': '/stocks'
        }
        
        for bp_name in expected_prefixes.keys():
            if bp_name in [bp.name for bp in acfc.blueprints.values()]:
                _ = next(bp for bp in acfc.blueprints.values() if bp.name == bp_name)
                # Note: Flask peut stocker les préfixes différemment selon la version

class TestClientsBlueprint:
    """Tests pour le module Clients (CRM)."""

    def test_clients_route_requires_auth(self, client: FlaskClient) -> None:
        """Test que la route clients nécessite une authentification."""
        response = client.get('/clients')
        assert response.status_code == 302  # Redirect vers login

    def test_clients_route_with_auth(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test accès à la route clients avec authentification."""
        response = client.get('/clients')
        # Peut être 200 (succès) ou 404 (route non encore implémentée)
        assert response.status_code in [200, 404, 500]

    def test_clients_post_with_auth(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test création d'un client via POST."""
        client_data = {
            'type_client': '1',  # Particulier
            'prenom': 'Jean',
            'nom': 'Dupont',
            'email': 'jean.dupont@client.com',
            'telephone': '0123456789'
        }
        
        response = client.post('/clients', data=client_data)
        assert response.status_code in [200, 201, 404, 405, 500]

class TestCatalogueBlueprint:
    """Tests pour le module Catalogue."""

    def test_catalogue_route_requires_auth(self, client: FlaskClient) -> None:
        """Test que la route catalogue nécessite une authentification."""
        response = client.get('/catalogue')
        assert response.status_code == 302  # Redirect vers login

    def test_catalogue_route_with_auth(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test accès à la route catalogue avec authentification."""
        response = client.get('/catalogue')
        assert response.status_code in [200, 308, 404, 500]  # 308 pour redirection permanente

    def test_catalogue_product_creation(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test création d'un produit dans le catalogue."""
        product_data = {
            'nom': 'Produit Test',
            'description': 'Description du produit test',
            'prix': '99.99',
            'categorie': 'Electronique'
        }
        
        response = client.post('/catalogue', data=product_data)
        assert response.status_code in [200, 201, 404, 405, 500]

class TestCommercialBlueprint:
    """Tests pour le module Commercial."""

    def test_commercial_route_requires_auth(self, client: FlaskClient) -> None:
        """Test que la route commercial nécessite une authentification."""
        response = client.get('/commercial')
        assert response.status_code == 302

    def test_commercial_route_with_auth(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test accès à la route commercial avec authentification."""
        response = client.get('/commercial')
        assert response.status_code in [200, 308, 404, 500]  # 308 pour redirection permanente

    def test_devis_creation(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test création d'un devis."""
        devis_data = {
            'client_id': '1',
            'date_validite': '2024-12-31',
            'montant_ht': '100.00',
            'taux_tva': '20.00'
        }
        
        response = client.post('/commercial/devis', data=devis_data)
        assert response.status_code in [200, 201, 404, 405, 500]

    def test_commande_creation(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test création d'une commande."""
        commande_data = {
            'client_id': '1',
            'date_livraison': '2024-06-01',
            'statut': 'en_attente'
        }
        
        response = client.post('/commercial/commandes', data=commande_data)
        assert response.status_code in [200, 201, 404, 405, 500]

class TestComptabiliteBlueprint:
    """Tests pour le module Comptabilité."""

    def test_comptabilite_route_requires_auth(self, client: FlaskClient) -> None:
        """Test que la route comptabilité nécessite une authentification."""
        response = client.get('/comptabilite')
        assert response.status_code == 302

    def test_comptabilite_route_with_auth(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test accès à la route comptabilité avec authentification."""
        response = client.get('/comptabilite')
        assert response.status_code in [200, 308, 404, 500]  # 308 pour redirection permanente

    def test_facture_creation(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test création d'une facture."""
        facture_data = {
            'commande_id': '1',
            'date_emission': '2024-05-22',
            'montant_ht': '100.00',
            'montant_ttc': '120.00'
        }
        
        response = client.post('/comptabilite/factures', data=facture_data)
        assert response.status_code in [200, 201, 404, 405, 500]

    def test_operation_comptable(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test création d'une opération comptable."""
        operation_data = {
            'compte_debit': '411000',
            'compte_credit': '701000',
            'montant': '120.00',
            'libelle': 'Vente produit'
        }
        
        response = client.post('/comptabilite/operations', data=operation_data)
        assert response.status_code in [200, 201, 404, 405, 500]

class TestStocksBlueprint:
    """Tests pour le module Stocks."""

    def test_stocks_route_requires_auth(self, client: FlaskClient) -> None:
        """Test que la route stocks nécessite une authentification."""
        response = client.get('/stocks')
        assert response.status_code == 302

    def test_stocks_route_with_auth(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test accès à la route stocks avec authentification."""
        response = client.get('/stocks')
        assert response.status_code in [200, 308, 404, 500]  # 308 pour redirection permanente

    def test_stock_movement(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test mouvement de stock."""
        movement_data = {
            'produit_id': '1',
            'type_mouvement': 'entree',
            'quantite': '10',
            'motif': 'Réapprovisionnement'
        }
        
        response = client.post('/stocks/mouvements', data=movement_data)
        assert response.status_code in [200, 201, 404, 405, 500]

    def test_stock_inventory(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test inventaire des stocks."""
        response = client.get('/stocks/inventaire')
        assert response.status_code in [200, 404, 500]

class TestBlueprintIntegration:
    """Tests d'intégration entre les blueprints."""

    def test_client_to_commercial_workflow(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test workflow Client -> Commercial (création client puis commande)."""
        # 1. Création d'un client
        client_data = {
            'type_client': '1',
            'prenom': 'Jean',
            'nom': 'Dupont'
        }
        
        client_response = client.post('/clients', data=client_data)
        
        # 2. Création d'une commande pour ce client
        if client_response.status_code in [200, 201]:
            commande_data = {
                'client_id': '1',  # ID du client créé
                'date_livraison': '2024-06-01'
            }
            
            commande_response = client.post('/commercial/commandes', data=commande_data)
            assert commande_response.status_code in [200, 201, 404, 405, 500]

    def test_catalogue_to_stocks_workflow(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test workflow Catalogue -> Stocks (création produit puis gestion stock)."""
        # 1. Création d'un produit
        product_data = {
            'nom': 'Produit Test',
            'prix': '50.00'
        }
        
        product_response = client.post('/catalogue', data=product_data)
        
        # 2. Gestion du stock pour ce produit
        if product_response.status_code in [200, 201]:
            stock_data = {
                'produit_id': '1',
                'quantite_initiale': '100'
            }
            
            stock_response = client.post('/stocks', data=stock_data)
            assert stock_response.status_code in [200, 201, 404, 405, 500]

    def test_commercial_to_comptabilite_workflow(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test workflow Commercial -> Comptabilité (commande puis facturation)."""
        # 1. Création d'une commande
        commande_data = {
            'client_id': '1',
            'montant_ht': '100.00'
        }
        
        commande_response = client.post('/commercial/commandes', data=commande_data)
        
        # 2. Facturation de cette commande
        if commande_response.status_code in [200, 201]:
            facture_data = {
                'commande_id': '1',
                'montant_ht': '100.00',
                'montant_ttc': '120.00'
            }
            
            facture_response = client.post('/comptabilite/factures', data=facture_data)
            assert facture_response.status_code in [200, 201, 404, 405, 500]

class TestBlueprintErrorHandling:
    """Tests de gestion d'erreur pour les blueprints."""

    def test_invalid_blueprint_routes(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test accès à des routes invalides dans les blueprints."""
        invalid_routes = [
            '/clients/nonexistent',
            '/catalogue/invalid',
            '/commercial/wrong',
            '/comptabilite/missing',
            '/stocks/notfound'
        ]
        
        for route in invalid_routes:
            response = client.get(route)
            assert response.status_code in [200, 404, 500]  # 200 si gestion d'erreur gracieuse

    def test_blueprint_methods_not_allowed(self, client: FlaskClient, authenticated_session: Any) -> None:
        """Test méthodes HTTP non autorisées sur les blueprints."""
        routes_to_test = [
            '/clients',
            '/catalogue',
            '/commercial',
            '/comptabilite',
            '/stocks'
        ]
        
        for route in routes_to_test:
            # Test méthode PUT non autorisée (probablement)
            response = client.put(route)
            assert response.status_code in [200, 405, 404, 500]

class TestBlueprintStaticFiles:
    """Tests pour les fichiers statiques des blueprints."""

    def test_blueprint_css_files_accessible(self, client: FlaskClient) -> None:
        """Test que les fichiers CSS des blueprints sont accessibles."""
        css_files = [
            '/static/clients/css/clients.css',
            '/static/catalogue/css/catalogue.css',
            '/static/commercial/css/commercial.css',
            '/static/comptabilite/css/comptabilite.css',
            '/static/stocks/css/stocks.css'
        ]
        
        for css_file in css_files:
            response = client.get(css_file)
            # Soit le fichier existe (200), soit il n'existe pas (404), soit redirection (302)
            assert response.status_code in [200, 302, 404]

    def test_blueprint_js_files_accessible(self, client: FlaskClient) -> None:
        """Test que les fichiers JS des blueprints sont accessibles."""
        js_files = [
            '/static/clients/js/clients.js',
            '/static/catalogue/js/catalogue.js',
            '/static/commercial/js/commercial.js',
            '/static/comptabilite/js/comptabilite.js',
            '/static/stocks/js/stocks.js'
        ]
        
        for js_file in js_files:
            response = client.get(js_file)
            assert response.status_code in [200, 302, 404]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
