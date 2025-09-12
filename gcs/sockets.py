from flask import Blueprint, request
from . import socketio
from .services.logger import log_info, log_error

bp = Blueprint("sockets", __name__)

@socketio.on("connect", namespace="/stream")
def handle_connect():
    """Handle client connection to the stream namespace"""
    client_ip = request.remote_addr
    log_info(f"Client connected to /stream from {client_ip}")
    
    # Optionally emit last-known snapshot(s) here
    # For now, just acknowledge the connection
    socketio.emit("connected", {"status": "ok", "namespace": "/stream"}, namespace="/stream")

@socketio.on("disconnect", namespace="/stream")
def handle_disconnect():
    """Handle client disconnection from the stream namespace"""
    client_ip = request.remote_addr
    log_info(f"Client disconnected from /stream from {client_ip}")

@socketio.on("error", namespace="/stream")
def handle_error(error):
    """Handle Socket.IO errors"""
    log_error(f"Socket.IO error: {error}")

@socketio.on("ping", namespace="/stream")
def handle_ping():
    """Handle ping from client for connection health check"""
    socketio.emit("pong", {"timestamp": "now"}, namespace="/stream")
