# UAV Ground Control Station (GCS)

A Flask-based web server for the EGH455 UAVPayloadTAQ-25 project that provides real-time monitoring and data collection for UAV sensor data and target detections.

## Features

- **Real-time Data Collection**: Accepts JSON POST requests from UAV payloads
- **Live Dashboard**: Web-based interface showing sensor readings and target detections
- **Text-to-Speech**: Vocalizes target detections using browser TTS
- **WebSocket Updates**: Real-time data streaming via Socket.IO
- **Database Storage**: Persistent storage with SQLAlchemy and Flask-Migrate
- **API Security**: Optional API key authentication (disabled by default)
- **Health Monitoring**: Built-in health check endpoint

## Requirements Coverage

- ✅ **REQ-F-08**: Server accessible on LAN, logs sensor/target data with timestamps
- ✅ **REQ-F-06/07**: Live display for sensors & targets (dashboard)
- ✅ **REQ-F-05**: Vocalize target detections (browser TTS)
- ✅ **REQ-M-19**: Push updates to keep ≤4s latency

## Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd uav_gcs_server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional):
```bash
# Copy the example environment file
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
# Set Flask app environment variable
set FLASK_APP=app.py

# Initialize database migrations
python -m flask db init

# Create initial migration
python -m flask db migrate -m "Initial migration"

# Apply migrations
python -m flask db upgrade
```

5. Run the application:
```bash
python app.py
```

The server will start on `http://0.0.0.0:5000` and be accessible from any device on the LAN.

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Database Configuration
SQLALCHEMY_DATABASE_URI=sqlite:///uav_gcs.db

# Security (optional)
API_KEY=your-secret-api-key-here

# Socket.IO Configuration
SOCKETIO_CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO
```

### Database Options

- **SQLite** (default): `sqlite:///uav_gcs.db`
- **PostgreSQL**: `postgresql://user:password@localhost/dbname`
- **MySQL**: `mysql://user:password@localhost/dbname`

## API Endpoints

### Health Check
```
GET /health
```
Returns service status and version information.

### Sensor Data
```
POST /api/sensors
Content-Type: application/json

{
  "timestamp": "2025-01-15T10:30:00Z",
  "co_ppm": 1.5,
  "no2_ppm": 0.8,
  "nh3_ppm": 0.3,
  "light_lux": 500,
  "temp_c": 22.5,
  "pressure_hpa": 1013.25,
  "humidity_pct": 60.0,
  "source": "payload-rpi5"
}
```

### Target Detection
```
POST /api/targets
Content-Type: application/json

{
  "timestamp": "2025-01-15T10:30:00Z",
  "target_type": "gauge",
  "details": {
    "value": 1.8,
    "unit": "bar"
  },
  "image_url": "http://example.com/image.jpg"
}
```

**Target Types:**
- `valve`: Valve detection with state information
- `gauge`: Pressure/temperature gauge with value and unit
- `aruco`: ArUco marker detection with ID and pose

## Testing

Run the test suite:
```bash
python -m pytest gcs/tests/ -v
```

## Development

### Project Structure

```
uav_gcs_server/
├── app.py                 # Main application entry point
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── pytest.ini           # Test configuration
├── gcs/                  # Main application package
│   ├── __init__.py       # Flask app factory
│   ├── models.py         # Database models
│   ├── routes.py         # API routes
│   ├── sockets.py        # Socket.IO handlers
│   ├── middleware.py     # Security middleware
│   ├── services/         # Business logic
│   │   ├── data_handler.py
│   │   ├── logger.py
│   │   └── notifier.py
│   ├── static/           # Static assets
│   │   └── js/
│   │       └── dashboard.js
│   ├── templates/        # HTML templates
│   │   ├── base.html
│   │   └── dashboard.html
│   └── tests/            # Unit tests
│       ├── test_data_handler.py
│       ├── test_models.py
│       └── test_routes.py
└── migrations/           # Database migrations
```

### Database Migrations

Create a new migration:
```bash
python -m flask db migrate -m "Description of changes"
```

Apply migrations:
```bash
python -m flask db upgrade
```

### Adding New Features

1. **New API Endpoints**: Add routes in `gcs/routes.py`
2. **Database Changes**: Update models in `gcs/models.py` and create migration
3. **Frontend Updates**: Modify templates in `gcs/templates/` and JS in `gcs/static/js/`
4. **Business Logic**: Add services in `gcs/services/`

## Deployment

### Production Considerations

1. **Database**: Use PostgreSQL or MySQL for production
2. **Security**: Enable API key authentication
3. **Logging**: Configure structured logging
4. **Monitoring**: Set up health check monitoring
5. **SSL**: Use HTTPS in production

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**: Check your `SQLALCHEMY_DATABASE_URI` configuration
2. **Socket.IO Connection Issues**: Verify CORS settings and firewall configuration
3. **TTS Not Working**: Ensure browser supports `speechSynthesis` API

### Logs

Application logs are written to stdout. Check the console output for error messages and request logs.

## License

This project is part of the EGH455 UAVPayloadTAQ-25 course at QUT.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For issues and questions, please contact the development team or create an issue in the repository.
