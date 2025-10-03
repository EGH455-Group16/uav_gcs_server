from flask import Blueprint, request
from flask_socketio import join_room

from . import socketio
from .services.logger import log_info, log_error

bp = Blueprint("sockets", __name__)


# Default namespace handlers
@socketio.on("connect")
def handle_connect():
    client_ip = request.remote_addr
    log_info(f"Client connected from {client_ip}")


@socketio.on("disconnect")
def handle_disconnect():
    client_ip = request.remote_addr
    log_info(f"Client disconnected from {client_ip}")


@socketio.on("register_device")
def register_device(data):
    """Handle device registration and room joining"""
    device_id = data.get("device_id")
    if device_id:
        join_room(device_id)
        log_info(f"Device {device_id} registered and joined room")
        socketio.emit("ack", {"ok": True, "room": device_id})
    else:
        log_error("Device registration failed: no device_id provided")
        socketio.emit("ack", {"ok": False, "error": "device_id required"})


@socketio.on("join_room")
def handle_join_room(data):
    """Handle explicit room joining"""
    device_id = data.get("device_id")
    if device_id:
        join_room(device_id)
        log_info(f"Device {device_id} joined room")
        socketio.emit("ack", {"ok": True, "room": device_id})
    else:
        log_error("Join room failed: no device_id provided")
        socketio.emit("ack", {"ok": False, "error": "device_id required"})


@socketio.on("ping")
def handle_ping():
    socketio.emit("pong", {"timestamp": "now"})


def send_display_command(device_id, mode):
    """Send display mode command to a specific device"""
    log_info(f"Sending display command to device {device_id}: mode={mode}")
    socketio.emit("set_display", {"mode": mode}, room=device_id)


# Stream namespace handlers (existing)
@socketio.on("connect", namespace="/stream")
def handle_connect_stream():
    client_ip = request.remote_addr
    log_info(f"Client connected to /stream from {client_ip}")
    socketio.emit("connected", {"status": "ok", "namespace": "/stream"}, namespace="/stream")


@socketio.on("disconnect", namespace="/stream")
def handle_disconnect_stream():
    client_ip = request.remote_addr
    log_info(f"Client disconnected from /stream from {client_ip}")


@socketio.on("error", namespace="/stream")
def handle_error_stream(error):
    log_error(f"Socket.IO error: {error}")


@socketio.on("ping", namespace="/stream")
def handle_ping_stream():
    socketio.emit("pong", {"timestamp": "now"}, namespace="/stream")
