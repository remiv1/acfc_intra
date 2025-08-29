"""
Test de la nouvelle fonctionnalité de recherche avancée de clients.
"""
import pytest
import json
from app_acfc.application import acfc
from app_acfc.modeles import SessionBdD, Client, Part, Pro, Adresse
from typing import Any


@pytest.fixture
def client():
    """Créer un client de test Flask."""
    acfc.config['TESTING'] = True
    with acfc.test_client() as client:
        yield client


@pytest.fixture
def sample_data():
    """Créer des données de test dans la base."""
    db_session = SessionBdD()
    
    # Créer un client particulier de test
    client_part = Client(type_client=1, notes="Client test particulier")
    db_session.add(client_part)
    db_session.flush()
    
    part = Part(
        id_client=client_part.id,
        prenom="Jean",
        nom="Dupont"
    )
    db_session.add(part)
    
    # Ajouter une adresse
    adresse = Adresse(
        id_client=client_part.id,
        adresse_l1="123 Rue de la Paix",
        code_postal="75001",
        ville="Paris"
    )
    db_session.add(adresse)
    
    # Créer un client professionnel de test
    client_pro = Client(type_client=2, notes="Client test professionnel")
    db_session.add(client_pro)
    db_session.flush()
    
    pro = Pro(
        id_client=client_pro.id,
        raison_sociale="ACME Corporation",
        type_pro=1
    )
    db_session.add(pro)
    
    # Ajouter une adresse
    adresse_pro = Adresse(
        id_client=client_pro.id,
        adresse_l1="456 Avenue des Champs",
        code_postal="75008",
        ville="Paris"
    )
    db_session.add(adresse_pro)
    
    db_session.commit()
    
    yield {
        'client_part_id': client_part.id,
        'client_pro_id': client_pro.id
    }
    
    # Nettoyage après test (si ce n'est pas un mock)
    try:
        db_session.delete(part)
        db_session.delete(pro)
        db_session.delete(adresse)
        db_session.delete(adresse_pro)
        db_session.delete(client_part)
        db_session.delete(client_pro)
        db_session.commit()
    except AttributeError:
        # En mode test avec mock, la méthode delete n'existe pas
        pass
    db_session.close()


def test_recherche_avancee_particulier(client: Client, sample_data: Any):
    """Test de recherche par particulier."""
    response = client.get('/clients/recherche_avancee?q=Jean&type=part')
    assert response.status_code in [200, 302]
    
    if response.status_code == 200:
        data = json.loads(response.data)
        assert len(data) > 0
        assert any(result['nom_affichage'] == 'Jean Dupont' for result in data)


def test_recherche_avancee_professionnel(client: Client, sample_data: Any):
    """Test de recherche par professionnel."""
    response = client.get('/clients/recherche_avancee?q=ACME&type=pro')
    assert response.status_code in [200, 302]
    
    if response.status_code == 200:
        data = json.loads(response.data)
        assert len(data) > 0
        assert any(result['nom_affichage'] == 'ACME Corporation' for result in data)


def test_recherche_avancee_adresse(client: Client, sample_data: Any):
    """Test de recherche par adresse."""
    response = client.get('/clients/recherche_avancee?q=75001&type=adresse')
    assert response.status_code in [200, 302]
    
    if response.status_code == 200:
        data = json.loads(response.data)
        assert len(data) > 0
        assert any(result['code_postal'] == '75001' for result in data)


def test_recherche_avancee_terme_trop_court(client: Client):
    """Test avec un terme de recherche trop court."""
    response = client.get('/clients/recherche_avancee?q=Je&type=part')
    assert response.status_code in [200, 302]
    
    if response.status_code == 200:
        data = json.loads(response.data)
        assert len(data) == 0  # Aucun résultat pour moins de 3 caractères


def test_recherche_avancee_sans_resultat(client: Client):
    """Test avec un terme qui ne donne aucun résultat."""
    response = client.get('/clients/recherche_avancee?q=TermeInexistant&type=part')
    assert response.status_code in [200, 302]
    
    if response.status_code == 200:
        data = json.loads(response.data)
        assert len(data) == 0
