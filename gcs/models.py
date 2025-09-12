from datetime import datetime
from . import db

class SensorData(db.Model):
    __tablename__ = "sensor_data"
    id = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    # Gas sensor readings (ppm)
    co_ppm = db.Column(db.Float)
    no2_ppm = db.Column(db.Float)
    nh3_ppm = db.Column(db.Float)
    # Environmental sensors
    light_lux = db.Column(db.Float)
    temp_c = db.Column(db.Float)
    pressure_hpa = db.Column(db.Float)
    humidity_pct = db.Column(db.Float)
    # Optional metadata
    source = db.Column(db.String(64))   # e.g., "payload-rpi5"

class TargetDetection(db.Model):
    __tablename__ = "target_detection"
    id = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    target_type = db.Column(db.String(32))  # "valve" | "gauge" | "aruco"
    details_json = db.Column(db.JSON)       # valve_state, gauge_value, aruco_id/pose {x,y,z}
    image_url = db.Column(db.String(256))   # optional snapshot path

class SystemLog(db.Model):
    __tablename__ = "system_log"
    id = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    level = db.Column(db.String(16))        # INFO/WARN/ERROR
    message = db.Column(db.String(512))
