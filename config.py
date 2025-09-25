import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///uav_gcs.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_UI_DATA_LATENCY_S = 4
    API_KEY = os.getenv("API_KEY", None)
    SOCKETIO_CORS_ORIGINS = os.getenv("SOCKETIO_CORS_ORIGINS", "*")