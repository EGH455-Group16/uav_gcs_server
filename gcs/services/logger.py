import logging
import time

from flask import request

from .. import socketio

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('uav_gcs')


def log_request(req, status_code):
    duration_ms = int((time.time() - req.start_time) * 1000) if hasattr(req, 'start_time') else 0
    logger.info(f"{req.method} {req.path} - {status_code} - {duration_ms}ms")


def log_error(message):
    logger.error(message)


def log_info(message):
    logger.info(message)


def log_warning(message):
    logger.warning(message)


def push_sensor_update(record_dict: dict):
    try:
        socketio.emit("sensor_update", record_dict, namespace="/stream")
        log_info(f"Sensor update emitted: {record_dict.get('ts', 'unknown')}")
    except Exception as e:
        log_error(f"Failed to emit sensor update: {str(e)}")


def push_target_detected(event_dict: dict):
    try:
        socketio.emit("target_detected", event_dict, namespace="/stream")
        log_info(f"Target detection emitted: {event_dict.get('target_type', 'unknown')}")
    except Exception as e:
        log_error(f"Failed to emit target detection: {str(e)}")
