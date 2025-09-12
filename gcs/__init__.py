from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os
import time

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins=os.getenv("SOCKETIO_CORS_ORIGINS", "*"))

def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object("config.Config")

    # Request timing middleware
    @app.before_request
    def before_request():
        request.start_time = time.time()

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    from .models import SensorData, TargetDetection, SystemLog  # noqa: F401
    from .routes import bp as routes_bp
    from .sockets import bp as sockets_bp

    app.register_blueprint(routes_bp)
    app.register_blueprint(sockets_bp)
    return app
