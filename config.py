import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///uav_gcs.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Meets ≤4s availability (REQ-M-19): client polls fallback every 2–3s; websockets push instantly.
    MAX_UI_DATA_LATENCY_S = 4
    
    # Optional API key for security (disabled by default)
    API_KEY = os.getenv("API_KEY", None)
    
    # Socket.IO CORS settings
    SOCKETIO_CORS_ORIGINS = os.getenv("SOCKETIO_CORS_ORIGINS", "*")