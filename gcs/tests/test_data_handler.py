"""Tests for data_handler module"""

import pytest
from datetime import datetime
from gcs import create_app, db
from gcs.services.data_handler import ingest_sensor_json, ingest_target_json
from gcs.models import SensorData, TargetDetection


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


def test_ingest_sensor_json_valid_data(app):
    """Test sensor data ingestion with valid data"""
    with app.app_context():
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
        
        record = ingest_sensor_json(payload)
        
        assert record.id is not None
        assert record.co_ppm == 1.5
        assert record.no2_ppm == 0.8
        assert record.nh3_ppm == 0.3
        assert record.light_lux == 500
        assert record.temp_c == 22.5
        assert record.pressure_hpa == 1013.25
        assert record.humidity_pct == 60.0
        assert record.source == "test-payload"
        assert record.ts is not None


def test_ingest_sensor_json_minimal_data(app):
    """Test sensor data ingestion with minimal required data"""
    with app.app_context():
        payload = {
            "co_ppm": 1.0
        }
        
        record = ingest_sensor_json(payload)
        
        assert record.id is not None
        assert record.co_ppm == 1.0
        assert record.no2_ppm is None
        assert record.source == "payload"  # default value


def test_ingest_sensor_json_invalid_timestamp(app):
    """Test sensor data ingestion with invalid timestamp falls back to server time"""
    with app.app_context():
        payload = {
            "timestamp": "invalid-timestamp",
            "co_ppm": 1.0
        }
        
        record = ingest_sensor_json(payload)
        
        assert record.id is not None
        assert record.co_ppm == 1.0
        assert record.ts is not None  # Should use server time


def test_ingest_target_json_valid_data(app):
    """Test target detection ingestion with valid data"""
    with app.app_context():
        payload = {
            "timestamp": "2025-01-15T10:30:00Z",
            "target_type": "gauge",
            "details": {"value": 1.8, "unit": "bar"},
            "image_url": "http://example.com/image.jpg"
        }
        
        record = ingest_target_json(payload)
        
        assert record.id is not None
        assert record.target_type == "gauge"
        assert record.details_json == {"value": 1.8, "unit": "bar"}
        assert record.image_url == "http://example.com/image.jpg"
        assert record.ts is not None


def test_ingest_target_json_minimal_data(app):
    """Test target detection ingestion with minimal required data"""
    with app.app_context():
        payload = {
            "target_type": "valve"
        }
        
        record = ingest_target_json(payload)
        
        assert record.id is not None
        assert record.target_type == "valve"
        assert record.details_json == {}
        assert record.image_url is None


def test_ingest_target_json_invalid_timestamp(app):
    """Test target detection ingestion with invalid timestamp falls back to server time"""
    with app.app_context():
        payload = {
            "timestamp": "invalid-timestamp",
            "target_type": "aruco"
        }
        
        record = ingest_target_json(payload)
        
        assert record.id is not None
        assert record.target_type == "aruco"
        assert record.ts is not None  # Should use server time
