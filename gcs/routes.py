from flask import Blueprint, request, jsonify, render_template
from .services.data_handler import ingest_sensor_json, ingest_target_json
from .services.notifier import push_sensor_update, push_target_detected
from .services.logger import log_request, log_error
from .middleware import api_key_required, cors_headers
import logging

bp = Blueprint("routes", __name__)

@bp.route("/")
def index():
    return render_template("dashboard.html")

@bp.route("/health")
def health():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "service": "uav-gcs",
        "version": "1.0.0"
    }), 200

@bp.route("/api/sensors", methods=["POST"])
@api_key_required
@cors_headers
def api_sensors():
    try:
        # Validate JSON content type
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json(silent=False)
        if data is None:
            return jsonify({"error": "Invalid JSON payload"}), 400
        
        # Validate required fields (at least one sensor reading)
        sensor_fields = ["co_ppm", "no2_ppm", "nh3_ppm", "light_lux", "temp_c", "pressure_hpa", "humidity_pct"]
        if not any(field in data for field in sensor_fields):
            return jsonify({"error": "At least one sensor reading is required"}), 400
        
        # Validate data types
        for field in sensor_fields:
            if field in data and data[field] is not None:
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    return jsonify({"error": f"Invalid value for {field}: must be numeric"}), 400
        
        rec = ingest_sensor_json(data)
        log_request(request, 201)
        
        # Emit sensor update via Socket.IO
        push_sensor_update({
            "ts": rec.ts.isoformat(),
            "co_ppm": rec.co_ppm,
            "no2_ppm": rec.no2_ppm,
            "nh3_ppm": rec.nh3_ppm,
            "light_lux": rec.light_lux,
            "temp_c": rec.temp_c,
            "pressure_hpa": rec.pressure_hpa,
            "humidity_pct": rec.humidity_pct,
            "source": rec.source
        })
        
        return jsonify({"status": "ok", "id": rec.id}), 201
        
    except Exception as e:
        log_error(f"Sensor API error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route("/api/targets", methods=["POST"])
@api_key_required
@cors_headers
def api_targets():
    try:
        # Validate JSON content type
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json(silent=False)
        if data is None:
            return jsonify({"error": "Invalid JSON payload"}), 400
        
        # Validate required fields
        if "target_type" not in data:
            return jsonify({"error": "target_type is required"}), 400
        
        # Validate target_type enum
        valid_types = {"valve", "gauge", "aruco"}
        if data["target_type"] not in valid_types:
            return jsonify({"error": f"target_type must be one of: {', '.join(valid_types)}"}), 400
        
        # Validate details is object if provided
        if "details" in data and not isinstance(data["details"], dict):
            return jsonify({"error": "details must be an object"}), 400
        
        rec = ingest_target_json(data)
        log_request(request, 201)
        
        # Emit target detection via Socket.IO
        push_target_detected({
            "ts": rec.ts.isoformat(),
            "target_type": rec.target_type,
            "details": rec.details_json,
            "image_url": rec.image_url
        })
        
        return jsonify({"status": "ok", "id": rec.id}), 201
        
    except Exception as e:
        log_error(f"Target API error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
