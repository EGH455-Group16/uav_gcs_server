from datetime import datetime

from . import db


class SensorData(db.Model):
    __tablename__ = "sensor_data"
    
    id = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    co_ppm = db.Column(db.Float)
    no2_ppm = db.Column(db.Float)
    nh3_ppm = db.Column(db.Float)
    light_lux = db.Column(db.Float)
    temp_c = db.Column(db.Float)
    pressure_hpa = db.Column(db.Float)
    humidity_pct = db.Column(db.Float)
    source = db.Column(db.String(64))


class TargetDetection(db.Model):
    __tablename__ = "target_detection"
    
    id = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    target_type = db.Column(db.String(32))
    details_json = db.Column(db.JSON)
    image_url = db.Column(db.String(256))


class SystemLog(db.Model):
    __tablename__ = "system_log"
    
    id = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    level = db.Column(db.String(16))
    message = db.Column(db.String(512))
