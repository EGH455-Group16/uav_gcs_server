from flask import Blueprint, request

from . import socketio
from .services.logger import log_info, log_error

bp = Blueprint("sockets", __name__)


@socketio.on("connect", namespace="/stream")
def handle_connect():
    client_ip = request.remote_addr
    log_info(f"Client connected to /stream from {client_ip}")
    socketio.emit("connected", {"status": "ok", "namespace": "/stream"}, namespace="/stream")


@socketio.on("disconnect", namespace="/stream")
def handle_disconnect():
    client_ip = request.remote_addr
    log_info(f"Client disconnected from /stream from {client_ip}")


@socketio.on("error", namespace="/stream")
def handle_error(error):
    log_error(f"Socket.IO error: {error}")


@socketio.on("ping", namespace="/stream")
def handle_ping():
    socketio.emit("pong", {"timestamp": "now"}, namespace="/stream")
