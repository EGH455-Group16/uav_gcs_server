from datetime import datetime

from flask import Blueprint, request, jsonify, render_template

from .middleware import api_key_required, cors_headers
from .services.data_handler import ingest_sensor_json, ingest_target_json
from .services.image_store import ensure_targets_dir, save_image_bytes, decode_b64_image, parse_details, get_image_url, archive_image_bytes
from .services.logger import log_request, log_error, push_sensor_update, push_target_detected
from . import throughput_meter, recent_detections

bp = Blueprint("routes", __name__)

@bp.route("/")
def index():
    return render_template("dashboard.html")

@bp.route("/air-quality")
def air_quality():
    """Air Quality monitoring page"""
    return render_template("air_quality.html")

@bp.route("/graphs")
def graphs():
    """Real-time and historical sensor graphs page"""
    return render_template("graphs.html")

@bp.route("/targets")
def targets():
    """Targets and Images page"""
    return render_template("targets.html")

@bp.route("/live-feed")
def live_feed():
    """Live Feed and Device Control page"""
    return render_template("live_feed.html")

@bp.route("/logs")
def logs():
    """System Logs page"""
    return render_template("logs.html")

@bp.route("/api/latest-sensor")
def latest_sensor():
    """Get the latest sensor data for dashboard initialization"""
    from .models import SensorData
    latest = SensorData.query.order_by(SensorData.ts.desc()).first()
    if latest:
        return jsonify({
            "ts": latest.ts.isoformat(),
            "co_ppm": latest.co_ppm,
            "no2_ppm": latest.no2_ppm,
            "nh3_ppm": latest.nh3_ppm,
            "light_lux": latest.light_lux,
            "temp_c": latest.temp_c,
            "pressure_hpa": latest.pressure_hpa,
            "humidity_pct": latest.humidity_pct,
            "source": latest.source
        })
    return jsonify(None)

@bp.route("/api/sensor-history")
def sensor_history():
    """Get historical sensor data for graphs (chronological order)"""
    from .models import SensorData
    from sqlalchemy import select
    limit = request.args.get('limit', 100, type=int)
    
    # Limit to reasonable values
    if limit > 500:
        limit = 500
    
    # Optimized query: use subquery to get most recent IDs, then order chronologically
    # This avoids loading all records into memory and then reversing
    subquery = select(SensorData.id).order_by(SensorData.ts.desc()).limit(limit).scalar_subquery()
    records = SensorData.query.filter(SensorData.id.in_(subquery)).order_by(SensorData.ts.asc()).all()
    
    return jsonify([{
        "ts": record.ts.isoformat(),
        "co_ppm": record.co_ppm,
        "no2_ppm": record.no2_ppm,
        "nh3_ppm": record.nh3_ppm,
        "light_lux": record.light_lux,
        "temp_c": record.temp_c,
        "pressure_hpa": record.pressure_hpa,
        "humidity_pct": record.humidity_pct,
        "source": record.source
    } for record in records])

@bp.route("/api/recent-targets")
def recent_targets():
    """Get recent target detections for dashboard initialization"""
    from .models import TargetDetection
    recent = TargetDetection.query.order_by(TargetDetection.ts.desc()).limit(20).all()
    return jsonify([{
        "ts": target.ts.isoformat(),
        "target_type": target.target_type,
        "details": target.details_json,
        "image_url": target.image_url
    } for target in recent])

@bp.route("/api/recent-detections")
def api_recent_detections():
    """Get recent detections with archive and de-duplication logic"""
    limit = request.args.get("limit", 40, type=int)
    
    # Get from in-memory service first
    detections = recent_detections.list(limit=limit)
    
    # If no detections in memory, fall back to database
    if not detections:
        from .models import TargetDetection
        # Get the most recent records and reverse them to show earliest to latest
        recent = TargetDetection.query.order_by(TargetDetection.ts.desc()).limit(limit).all()
        recent.reverse()  # Reverse to show earliest to latest
        detections = [{
            "ts": target.ts.timestamp(),  # Convert to epoch seconds for consistency
            "type": target.target_type,
            "details": target.details_json or {},
            "image_url": target.image_url or "/static/targets/latest.jpg",
            "thumb_url": target.image_url or "/static/targets/latest.jpg"
        } for target in recent]
    
    return jsonify(detections)

@bp.route("/database-viewer")
def database_viewer():
    """Database viewer page"""
    return render_template("database_viewer.html")

@bp.route("/api/sensor-data")
def api_sensor_data():
    """Get all sensor data for database viewer"""
    from .models import SensorData
    from flask import request
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    sensor_data = SensorData.query.order_by(SensorData.ts.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        "data": [{
            "id": record.id,
            "ts": record.ts.isoformat(),
            "co_ppm": record.co_ppm,
            "no2_ppm": record.no2_ppm,
            "nh3_ppm": record.nh3_ppm,
            "light_lux": record.light_lux,
            "temp_c": record.temp_c,
            "pressure_hpa": record.pressure_hpa,
            "humidity_pct": record.humidity_pct,
            "source": record.source
        } for record in sensor_data.items],
        "total": sensor_data.total,
        "pages": sensor_data.pages,
        "current_page": sensor_data.page,
        "per_page": sensor_data.per_page
    })

@bp.route("/api/target-data")
def api_target_data():
    """Get all target detection data for database viewer"""
    from .models import TargetDetection
    from flask import request
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    target_data = TargetDetection.query.order_by(TargetDetection.ts.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        "data": [{
            "id": record.id,
            "ts": record.ts.isoformat(),
            "target_type": record.target_type,
            "details": record.details_json,
            "image_url": record.image_url
        } for record in target_data.items],
        "total": target_data.total,
        "pages": target_data.pages,
        "current_page": target_data.page,
        "per_page": target_data.per_page
    })

@bp.route("/health")
def health():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "service": "uav-gcs",
        "version": "1.0.0"
    }), 200

@bp.route("/api/telemetry/throughput")
def api_throughput():
    from . import throughput_meter
    return jsonify(throughput_meter.snapshot())

@bp.route("/api/sensors", methods=["POST"])
@api_key_required
@cors_headers
def api_sensors():
    try:
        # Validate JSON content type
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        # Measure payload size for AQSA
        nbytes = request.content_length or len(request.get_data(cache=True) or b"")
        throughput_meter.add("AQSA", nbytes)
        
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
    """
    Robust POST /api/targets endpoint that accepts either:
    - multipart/form-data with file (JPEG/PNG) + form fields
    - application/json with image_b64 (data URL or raw base64) + fields
    """
    try:
        # Measure payload size for TAIP
        nbytes = request.content_length or len(request.get_data(cache=True) or b"")
        throughput_meter.add("TAIP", nbytes)
        
        # Get current timestamp
        ts = datetime.utcnow()
        target_type = None
        details = {}
        image_url = get_image_url()
        
        # Branch by Content-Type
        if request.content_type and "multipart/form-data" in request.content_type:
            # Handle multipart/form-data
            if "file" not in request.files:
                return jsonify({"error": "No file provided"}), 400
            
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400
            
            # Validate file type
            if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                return jsonify({"error": "File must be JPEG or PNG"}), 400
            
            # Get form fields
            target_type = request.form.get("target_type", "unknown")
            details_str = request.form.get("details", "{}")
            ts_str = request.form.get("ts")
            
            # Parse timestamp if provided
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass  # Use server time if parsing fails
            
            # Parse details
            details = parse_details(details_str)
            
            # Save file
            img_bytes = file.read()
            save_image_bytes(img_bytes, "latest.jpg")
            
            # Archive a snapshot for recent detections
            archived_url = archive_image_bytes(img_bytes, target_type)
            
        elif request.is_json:
            # Handle application/json
            data = request.get_json(silent=False)
            if data is None:
                return jsonify({"error": "Invalid JSON payload"}), 400
            
            # Validate required fields
            if "image_b64" not in data:
                return jsonify({"error": "image_b64 is required"}), 400
            
            target_type = data.get("target_type", "unknown")
            details = parse_details(data.get("details", {}))
            ts_str = data.get("ts")
            
            # Parse timestamp if provided
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass  # Use server time if parsing fails
            
            # Decode and save image
            try:
                img_bytes = decode_b64_image(data["image_b64"])
                save_image_bytes(img_bytes, "latest.jpg")
                
                # Archive a snapshot for recent detections
                archived_url = archive_image_bytes(img_bytes, target_type)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
                
        else:
            return jsonify({"error": "Content-Type must be multipart/form-data or application/json"}), 400
        
        # # Check if this is just a live feed frame (no actual detection)
        # if target_type == "livedata":
        #     # Just update latest.jpg, don't create database record
        #     log_request(request, 200)
        #     return jsonify({
        #         "status": "ok",
        #         "message": "Live feed frame updated",
        #         "url": image_url,
        #         "ts": ts.isoformat()
        #     }), 200
        
        # Create target detection record for actual detections
        from .models import TargetDetection
        rec = TargetDetection(
            ts=ts,
            target_type=target_type,
            details_json=details,
            image_url=archived_url  # Use the archived URL instead of latest.jpg
        )
        
        from . import db
        db.session.add(rec)
        db.session.commit()
        
        log_request(request, 201)
        
        # Emit target detection via Socket.IO
        push_target_detected({
            "ts": rec.ts.isoformat(),
            "target_type": rec.target_type,
            "details": rec.details_json,
            "image_url": rec.image_url
        })
        
        # Consider for Recent Detections (confidence, de-dupe, 4s refresh)
        accepted = recent_detections.consider(target_type, details, archived_url, server_ts=ts.timestamp())
        if accepted:
            # Broadcast a dedicated recent-detection event (in addition to existing push_target_detected)
            from . import socketio
            socketio.emit("recent_detection", {
                "ts": accepted.ts,
                "type": accepted.type,
                "details": accepted.details,
                "image_url": accepted.image_url,
                "thumb_url": accepted.thumb_url
            }, namespace="/stream")
        
        return jsonify({
            "url": image_url,
            "ts": rec.ts.isoformat(),
            "target_type": rec.target_type,
            "details": rec.details_json
        }), 201
        
    except Exception as e:
        log_error(f"Target API error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/device/<device_id>/display", methods=["POST"])
@api_key_required
@cors_headers
def api_set_display_mode(device_id):
    """Set display mode for a specific device"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json(silent=False)
        if data is None:
            return jsonify({"error": "Invalid JSON payload"}), 400
        
        mode = data.get("mode")
        if not mode:
            return jsonify({"error": "mode is required"}), 400
        
        # Validate mode
        valid_modes = ["default", "ip", "targets", "temp", "sensors"]
        if mode not in valid_modes:
            return jsonify({"error": f"Invalid mode. Must be one of: {', '.join(valid_modes)}"}), 400
        
        # Import here to avoid circular imports
        from .sockets import send_display_command
        send_display_command(device_id, mode)
        
        log_request(request, 200)
        return jsonify({"status": "ok", "device_id": device_id, "mode": mode}), 200
        
    except Exception as e:
        log_error(f"Display control API error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/api/clear-history", methods=["POST"])
def api_clear_history():
    """Clear all history including database records and stored images"""
    try:
        import os
        import shutil
        from pathlib import Path
        from .models import SensorData, TargetDetection, SystemLog
        from . import db
        
        # Clear database tables
        TargetDetection.query.delete()
        SensorData.query.delete()
        SystemLog.query.delete()
        db.session.commit()
        
        # Clear archived images
        archive_dir = Path("gcs/static/targets/archive")
        if archive_dir.exists():
            for file in archive_dir.iterdir():
                if file.is_file():
                    file.unlink()
        
        # Clear latest.jpg (optional - replace with placeholder or delete)
        latest_jpg = Path("gcs/static/targets/latest.jpg")
        if latest_jpg.exists():
            latest_jpg.unlink()
        
        # Clear in-memory services
        recent_detections.clear()
        throughput_meter.reset()
        
        log_request(request, 200)
        return jsonify({
            "status": "ok",
            "message": "History cleared successfully",
            "cleared": {
                "database_records": True,
                "archived_images": True,
                "latest_image": True,
                "memory_cache": True,
                "throughput": True
            }
        }), 200
        
    except Exception as e:
        log_error(f"Clear history API error: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
