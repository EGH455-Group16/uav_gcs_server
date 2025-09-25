from datetime import datetime

from .. import db
from ..models import SensorData, TargetDetection


def ingest_sensor_json(payload: dict) -> SensorData:
    ts = datetime.utcnow()
    if "timestamp" in payload:
        try:
            ts = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    
    rec = SensorData(
        ts=ts,
        co_ppm=payload.get("co_ppm"),
        no2_ppm=payload.get("no2_ppm"),
        nh3_ppm=payload.get("nh3_ppm"),
        light_lux=payload.get("light_lux"),
        temp_c=payload.get("temp_c"),
        pressure_hpa=payload.get("pressure_hpa"),
        humidity_pct=payload.get("humidity_pct"),
        source=payload.get("source", "payload")
    )
    db.session.add(rec)
    db.session.commit()
    return rec


def ingest_target_json(payload: dict) -> TargetDetection:
    ts = datetime.utcnow()
    if "timestamp" in payload:
        try:
            ts = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    
    rec = TargetDetection(
        ts=ts,
        target_type=payload.get("target_type"),
        details_json=payload.get("details") or {},
        image_url=payload.get("image_url"),
    )
    db.session.add(rec)
    db.session.commit()
    return rec
