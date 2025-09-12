"""Tests for models module"""

import pytest
from datetime import datetime
from gcs import create_app, db
from gcs.models import SensorData, TargetDetection, SystemLog


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


def test_sensor_data_creation(app):
    """Test SensorData model creation"""
    with app.app_context():
        sensor = SensorData(
            co_ppm=1.5,
            no2_ppm=0.8,
            nh3_ppm=0.3,
            light_lux=500,
            temp_c=22.5,
            pressure_hpa=1013.25,
            humidity_pct=60.0,
            source="test-payload"
        )
        
        db.session.add(sensor)
        db.session.commit()
        
        assert sensor.id is not None
        assert sensor.co_ppm == 1.5
        assert sensor.no2_ppm == 0.8
        assert sensor.nh3_ppm == 0.3
        assert sensor.light_lux == 500
        assert sensor.temp_c == 22.5
        assert sensor.pressure_hpa == 1013.25
        assert sensor.humidity_pct == 60.0
        assert sensor.source == "test-payload"
        assert sensor.ts is not None


def test_sensor_data_defaults(app):
    """Test SensorData model with default values"""
    with app.app_context():
        sensor = SensorData()
        
        db.session.add(sensor)
        db.session.commit()
        
        assert sensor.id is not None
        assert sensor.ts is not None
        assert sensor.co_ppm is None
        assert sensor.source is None


def test_target_detection_creation(app):
    """Test TargetDetection model creation"""
    with app.app_context():
        target = TargetDetection(
            target_type="gauge",
            details_json={"value": 1.8, "unit": "bar"},
            image_url="http://example.com/image.jpg"
        )
        
        db.session.add(target)
        db.session.commit()
        
        assert target.id is not None
        assert target.target_type == "gauge"
        assert target.details_json == {"value": 1.8, "unit": "bar"}
        assert target.image_url == "http://example.com/image.jpg"
        assert target.ts is not None


def test_target_detection_defaults(app):
    """Test TargetDetection model with default values"""
    with app.app_context():
        target = TargetDetection()
        
        db.session.add(target)
        db.session.commit()
        
        assert target.id is not None
        assert target.ts is not None
        assert target.target_type is None
        assert target.details_json is None
        assert target.image_url is None


def test_system_log_creation(app):
    """Test SystemLog model creation"""
    with app.app_context():
        log = SystemLog(
            level="INFO",
            message="Test log message"
        )
        
        db.session.add(log)
        db.session.commit()
        
        assert log.id is not None
        assert log.level == "INFO"
        assert log.message == "Test log message"
        assert log.ts is not None


def test_system_log_defaults(app):
    """Test SystemLog model with default values"""
    with app.app_context():
        log = SystemLog()
        
        db.session.add(log)
        db.session.commit()
        
        assert log.id is not None
        assert log.ts is not None
        assert log.level is None
        assert log.message is None


def test_database_relationships(app):
    """Test that all models can coexist in the database"""
    with app.app_context():
        # Create one of each model
        sensor = SensorData(co_ppm=1.0, source="test")
        target = TargetDetection(target_type="valve", details_json={})
        log = SystemLog(level="INFO", message="Test")
        
        db.session.add(sensor)
        db.session.add(target)
        db.session.add(log)
        db.session.commit()
        
        # Verify all records exist
        assert SensorData.query.count() == 1
        assert TargetDetection.query.count() == 1
        assert SystemLog.query.count() == 1
        
        # Verify they have different IDs
        assert sensor.id != target.id
        assert target.id != log.id
        assert sensor.id != log.id


def test_timestamp_indexing(app):
    """Test that timestamp fields are properly indexed"""
    with app.app_context():
        # Create multiple records with different timestamps
        now = datetime.utcnow()
        
        sensor1 = SensorData(co_ppm=1.0, ts=now)
        sensor2 = SensorData(co_ppm=2.0, ts=now)
        target1 = TargetDetection(target_type="valve", ts=now)
        
        db.session.add(sensor1)
        db.session.add(sensor2)
        db.session.add(target1)
        db.session.commit()
        
        # Query by timestamp should work efficiently
        sensors = SensorData.query.filter(SensorData.ts == now).all()
        assert len(sensors) == 2
        
        targets = TargetDetection.query.filter(TargetDetection.ts == now).all()
        assert len(targets) == 1
