"""Tests for routes module"""

import pytest
import json
from gcs import create_app, db


@pytest.fixture
def app():
    """Create test app with in-memory SQLite database"""
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'uav-gcs'
    assert data['version'] == '1.0.0'


def test_dashboard_endpoint(client):
    """Test dashboard endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'UAV GCS' in response.data or b'Sensor Data' in response.data


def test_sensor_api_valid_data(client):
    """Test sensor API with valid data"""
    payload = {
        "timestamp": "2025-01-15T10:30:00Z",
        "co_ppm": 1.5,
        "no2_ppm": 0.8,
        "nh3_ppm": 0.3,
        "light_lux": 500,
        "temp_c": 22.5,
        "pressure_hpa": 1013.25,
        "humidity_pct": 60.0,
        "source": "test-payload"
    }
    
    response = client.post('/api/sensors', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert 'id' in data


def test_sensor_api_minimal_data(client):
    """Test sensor API with minimal data"""
    payload = {
        "co_ppm": 1.0
    }
    
    response = client.post('/api/sensors', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['status'] == 'ok'


def test_sensor_api_no_data(client):
    """Test sensor API with no sensor readings"""
    payload = {
        "source": "test"
    }
    
    response = client.post('/api/sensors', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'sensor reading' in data['error'].lower()


def test_sensor_api_invalid_content_type(client):
    """Test sensor API with invalid content type"""
    response = client.post('/api/sensors', data="not json")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Content-Type' in data['error']


def test_sensor_api_invalid_json(client):
    """Test sensor API with invalid JSON"""
    response = client.post('/api/sensors', 
                          data="invalid json",
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Invalid JSON' in data['error']


def test_sensor_api_invalid_numeric_value(client):
    """Test sensor API with invalid numeric value"""
    payload = {
        "co_ppm": "not a number"
    }
    
    response = client.post('/api/sensors', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Invalid value' in data['error']


def test_target_api_valid_data(client):
    """Test target API with valid data"""
    payload = {
        "timestamp": "2025-01-15T10:30:00Z",
        "target_type": "gauge",
        "details": {"value": 1.8, "unit": "bar"},
        "image_url": "http://example.com/image.jpg"
    }
    
    response = client.post('/api/targets', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert 'id' in data


def test_target_api_minimal_data(client):
    """Test target API with minimal data"""
    payload = {
        "target_type": "valve"
    }
    
    response = client.post('/api/targets', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['status'] == 'ok'


def test_target_api_missing_target_type(client):
    """Test target API with missing target_type"""
    payload = {
        "details": {"value": 1.8}
    }
    
    response = client.post('/api/targets', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'target_type is required' in data['error']


def test_target_api_invalid_target_type(client):
    """Test target API with invalid target_type"""
    payload = {
        "target_type": "invalid_type"
    }
    
    response = client.post('/api/targets', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'target_type must be one of' in data['error']


def test_target_api_invalid_details_type(client):
    """Test target API with invalid details type"""
    payload = {
        "target_type": "gauge",
        "details": "not an object"
    }
    
    response = client.post('/api/targets', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'details must be an object' in data['error']


def test_target_api_invalid_content_type(client):
    """Test target API with invalid content type"""
    response = client.post('/api/targets', data="not json")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Content-Type' in data['error']


def test_target_api_invalid_json(client):
    """Test target API with invalid JSON"""
    response = client.post('/api/targets', 
                          data="invalid json",
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Invalid JSON' in data['error']
