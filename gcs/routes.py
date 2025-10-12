from datetime import datetime
import json

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
    # Filter out "livedata" type (not a real detection)
    return jsonify([{
        "ts": target.ts.isoformat(),
        "target_type": target.target_type,
        "details": target.details_json,
        "image_url": target.image_url
    } for target in recent if target.target_type != "livedata"])

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
        # Filter out "livedata" type (not a real detection)
        recent = TargetDetection.query.filter(
            TargetDetection.target_type != "livedata"
        ).order_by(TargetDetection.ts.desc()).limit(limit).all()
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
    
    # Filter out "livedata" type (not a real detection)
    target_data = TargetDetection.query.filter(
        TargetDetection.target_type != "livedata"
    ).order_by(TargetDetection.ts.desc()).paginate(
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
    POST /api/targets
    Accepts:
      - multipart/form-data with:
          file: JPEG/PNG
          details: JSON (object OR array of detection items)
          ts: ISO string (optional fallback timestamp)
          device_id: optional
          target_type: optional (back-compat; ignored if details is array with per-item target_type)
      - application/json with:
          image_b64: data URL OR raw base64
          details: object OR array of detection items
          ts, device_id: optional

    Behavior:
      - Saves/archives image ONCE, reuses same URLs for all detection rows
      - Creates one TargetDetection row per detection item
      - Emits push + recent_detections per detection
      - Responds with batch summary
    """
    try:
        # 1) TAIP metering
        nbytes = request.content_length or len(request.get_data(cache=True) or b"")
        throughput_meter.add("TAIP", nbytes)

        # 2) Defaults
        server_ts = datetime.utcnow()
        image_url_latest = get_image_url()
        archived_url = None
        thumb_url = None
        device_id = None

        raw_details = None
        top_ts = None

        # 3) Branch by content-type
        if request.content_type and "multipart/form-data" in request.content_type:
            if "file" not in request.files:
                return jsonify({"error": "No file provided"}), 400

            file = request.files["file"]
            if not file.filename or not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
                return jsonify({"error": "File must be JPEG or PNG"}), 400

            device_id = request.form.get("device_id")
            top_ts_str = request.form.get("ts")
            if top_ts_str:
                try:
                    top_ts = datetime.fromisoformat(top_ts_str.replace("Z", "+00:00"))
                except Exception:
                    top_ts = None

            # details can be a JSON object or JSON array (string)
            raw_details = request.form.get("details")

            # save/archive image once
            img_bytes = file.read()
            save_image_bytes(img_bytes, "latest.jpg")
            archived_url = archive_image_bytes(img_bytes, request.form.get("target_type") or "batch")
            # If your archiver also creates a thumb, expose it (optional)
            if isinstance(archived_url, dict):
                thumb_url = archived_url.get("thumb_url")
                archived_url = archived_url.get("image_url")

        elif request.is_json:
            data = request.get_json(silent=False)
            if data is None:
                return jsonify({"error": "Invalid JSON payload"}), 400

            device_id = data.get("device_id")
            top_ts_str = data.get("ts")
            if top_ts_str:
                try:
                    top_ts = datetime.fromisoformat(top_ts_str.replace("Z", "+00:00"))
                except Exception:
                    top_ts = None

            raw_details = data.get("details")
            if "image_b64" not in data:
                # allow image-less event (e.g., livedata heartbeat), but still need details
                if raw_details is None:
                    return jsonify({"error": "image_b64 or details required"}), 400
                img_bytes = None
            else:
                try:
                    img_bytes = decode_b64_image(data["image_b64"])
                except ValueError as e:
                    return jsonify({"error": str(e)}), 400

            if img_bytes:
                save_image_bytes(img_bytes, "latest.jpg")
                archived_url = archive_image_bytes(img_bytes, data.get("target_type") or "batch")
                if isinstance(archived_url, dict):
                    thumb_url = archived_url.get("thumb_url")
                    archived_url = archived_url.get("image_url")
        else:
            return jsonify({"error": "Content-Type must be multipart/form-data or application/json"}), 400

        # 4) Normalize `details` to a Python list of detection items
        def _to_list(obj):
            if obj is None:
                return []
            if isinstance(obj, list):
                return obj
            if isinstance(obj, dict):
                # Check if this dict has the batch detection schema (target_type + details fields)
                # If not, it's probably just a details object from the old API
                if "target_type" in obj and "details" in obj:
                    return [obj]  # This is a single detection item
                else:
                    return []  # This is just a details dict, not a detection item
            if isinstance(obj, str):
                # stringified JSON -> parse then recurse
                try:
                    parsed = json.loads(obj)
                except Exception:
                    return []
                return _to_list(parsed)
            return []

        detections = _to_list(raw_details)

        # Back-compat: if client sent only top-level `target_type/details` style (single detection)
        # Check if we have a top-level target_type field
        legacy_target_type = (request.form.get("target_type") if request.form else None) or \
                             (request.json.get("target_type") if request.is_json else None)
        legacy_confidence = (request.form.get("confidence") if request.form else None) or \
                           (request.json.get("confidence") if request.is_json else None)
        
        if not detections and legacy_target_type:
            # Old-style API: target_type at top level, details is just the details object
            legacy_details = parse_details(raw_details if raw_details is not None else {})
            
            # Add top-level confidence to details if present
            if legacy_confidence is not None:
                legacy_details["confidence"] = float(legacy_confidence)
            
            detections = [{
                "target_type": legacy_target_type,
                "details": legacy_details
            }]
        elif not detections and raw_details is not None:
            # Have details but no target_type - use "unknown"
            legacy_details = parse_details(raw_details)
            # Accept even empty details
            detections = [{
                "target_type": "unknown",
                "details": legacy_details
            }]

        if not detections:
            return jsonify({"error": "No detections found in 'details'"}), 400

        # 5) Persist each detection as a row
        from .models import TargetDetection
        from . import db
        saved = []
        created = 0

        # fallback image URL fields
        final_image_url = archived_url or image_url_latest
        final_thumb_url = thumb_url

        for det in detections:
            # Validate/normalize one item
            if not isinstance(det, dict):
                continue
            target_type = det.get("target_type") or "unknown"
            details_obj = parse_details(det.get("details", {}))
            
            # Merge top-level confidence into details if present
            if "confidence" in det:
                details_obj["confidence"] = det["confidence"]
            
            det_ts = det.get("ts")
            try:
                ts = datetime.fromisoformat(det_ts.replace("Z", "+00:00")) if det_ts else (top_ts or server_ts)
            except Exception:
                ts = top_ts or server_ts

            rec = TargetDetection(
                ts=ts,
                target_type=target_type,
                details_json=details_obj,
                image_url=final_image_url
            )
            db.session.add(rec)
            saved.append({
                "target_type": target_type,
                "ts": ts.isoformat(),
                "details": details_obj
            })
            created += 1

        db.session.commit()
        log_request(request, 201)

        # 6) Broadcast per detection & feed "recent_detections"
        accepted_detections = []
        is_batch = (created > 1)  # Flag to suppress individual socket events for batches
        
        for s in saved:
            # Still call push_target_detected for logging, but skip socket emission for batches
            # We'll emit a batch event instead
            if not is_batch:
                push_target_detected({
                    "ts": s["ts"],
                    "target_type": s["target_type"],
                    "details": s["details"],
                    "image_url": final_image_url,
                    "thumb_url": final_thumb_url,
                    "device_id": device_id
                })
            try:
                # Use server timestamp seconds for de-dupe windowing
                accepted = recent_detections.consider(
                    s["target_type"],
                    s["details"],
                    final_image_url,
                    server_ts=server_ts.timestamp(),
                )
                if accepted:
                    accepted_detections.append({
                        "ts": accepted.ts,
                        "type": accepted.type,
                        "details": accepted.details,
                        "image_url": accepted.image_url,
                        "thumb_url": accepted.thumb_url
                    })
            except Exception:
                # non-fatal
                pass

        # Emit events based on ORIGINAL detection count (not filtered count)
        # This prevents flickering when multiple detections arrive together
        try:
            from . import socketio
            if created == 1 and len(accepted_detections) == 1:
                # Single detection - emit individual event
                socketio.emit("recent_detection", accepted_detections[0], namespace="/stream")
            elif created > 1 and len(accepted_detections) > 0:
                # Multiple detections sent together - always emit batch event
                # Even if some were filtered by deduplication
                socketio.emit("target_batch", {
                    "count": len(accepted_detections),
                    "image_url": final_image_url,
                    "thumb_url": final_thumb_url,
                    "device_id": device_id,
                    "detections": accepted_detections
                }, namespace="/stream")
            # If all detections were filtered (len(accepted_detections) == 0), emit nothing
        except Exception:
            pass

        return jsonify({
            "ok": True,
            "saved": created,
            "image_url": final_image_url,
            "thumb_url": final_thumb_url,
            "detections": saved
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
