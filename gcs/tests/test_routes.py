import base64
import io
import json
import os
import tempfile

import pytest

from gcs import create_app, db


@pytest.fixture
def app():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'uav-gcs'
    assert data['version'] == '1.0.0'


def test_dashboard_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'UAV GCS' in response.data or b'Sensor Data' in response.data


def test_sensor_api_valid_data(client):
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
    response = client.post('/api/sensors', data="not json")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Content-Type' in data['error']


def test_sensor_api_invalid_json(client):
    response = client.post('/api/sensors', 
                          data="invalid json",
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Invalid JSON' in data['error']


def test_sensor_api_invalid_numeric_value(client):
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
    response = client.post('/api/targets', data="not json")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'Content-Type' in data['error']


def test_target_api_invalid_json(client):
    response = client.post('/api/targets', 
                          data="invalid json",
                          content_type='application/json')
    assert response.status_code == 400


def test_target_api_multipart_upload(client):
    # Create a small test image
    test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    
    data = {
        'file': (io.BytesIO(test_image_data), 'test.jpg', 'image/jpeg'),
        'target_type': 'valve',
        'details': '{"state": "open"}',
        'ts': '2025-01-15T10:30:00Z'
    }
    
    response = client.post('/api/targets', 
                          data=data,
                          content_type='multipart/form-data')
    assert response.status_code == 201
    
    result = json.loads(response.data)
    assert result['url'] == '/static/targets/latest.jpg'
    assert result['target_type'] == 'valve'
    assert result['details']['state'] == 'open'
    assert 'ts' in result


def test_target_api_json_base64_upload(client):
    # Create a small test image and encode as base64
    test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    image_b64 = base64.b64encode(test_image_data).decode('utf-8')
    
    payload = {
        'image_b64': image_b64,
        'target_type': 'gauge',
        'details': {'value': 42.5, 'unit': 'psi'},
        'ts': '2025-01-15T10:30:00Z'
    }
    
    response = client.post('/api/targets', 
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 201
    
    result = json.loads(response.data)
    assert result['url'] == '/static/targets/latest.jpg'
    assert result['target_type'] == 'gauge'
    assert result['details']['value'] == 42.5
    assert 'ts' in result


def test_target_api_missing_file(client):
    data = {
        'target_type': 'valve',
        'details': '{"state": "open"}'
    }
    
    response = client.post('/api/targets', 
                          data=data,
                          content_type='multipart/form-data')
    assert response.status_code == 400
    
    result = json.loads(response.data)
    assert 'No file provided' in result['error']


def test_target_api_invalid_base64(client):
    payload = {
        'image_b64': 'invalid_base64_data',
        'target_type': 'valve'
    }
    
    response = client.post('/api/targets', 
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 400
    
    result = json.loads(response.data)
    assert 'Failed to decode base64 image' in result['error']


def test_target_api_missing_image_b64(client):
    payload = {
        'target_type': 'valve',
        'details': {'state': 'open'}
    }
    
    response = client.post('/api/targets', 
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 400
    
    result = json.loads(response.data)
    assert 'image_b64 is required' in result['error']
