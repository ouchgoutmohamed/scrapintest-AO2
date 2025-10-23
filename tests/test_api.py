"""
Tests d'intégration pour l'API
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root():
    """Test du endpoint racine"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test du health check"""
    response = client.get("/health")
    # Peut échouer si la DB n'est pas disponible
    assert response.status_code in [200, 503]


def test_consultations_list():
    """Test de la liste des consultations"""
    response = client.get("/api/v1/consultations?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_consultations_filter():
    """Test des filtres"""
    response = client.get("/api/v1/consultations?statut=en_cours&limit=5")
    assert response.status_code == 200


def test_stats():
    """Test des statistiques"""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_consultations" in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
