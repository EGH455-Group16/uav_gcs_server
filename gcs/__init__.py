import os
import time

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from dotenv import load_dotenv

from .services.throughput import ThroughputMeter

db = SQLAlchemy()
migrate = Migrate()

socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")
throughput_meter = ThroughputMeter(4.0)


def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object("config.Config")

    @app.before_request
    def before_request():
        request.start_time = time.time()

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    from threading import Thread
    from time import sleep

    def _emit_throughput():
        while True:
            socketio.emit("throughput_update", throughput_meter.snapshot(), namespace="/")
            sleep(4)

    socketio.start_background_task(_emit_throughput)

    from .models import SensorData, TargetDetection, SystemLog  # noqa: F401
    from .routes import bp as routes_bp
    from .sockets import bp as sockets_bp

    app.register_blueprint(routes_bp)
    app.register_blueprint(sockets_bp)

    with app.app_context():
        db.create_all()

    return app
