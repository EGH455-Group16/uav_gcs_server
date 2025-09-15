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

- Python 3.8+ (tested with Python 3.11.9)
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd uav_gcs_server
```

2. **Set up a virtual environment (recommended):**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (Command Prompt):
venv\Scripts\activate
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# You should see (venv) in your command prompt when activated
```

**Note**: If you get an execution policy error in PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables (optional):**
```bash
# Copy the example environment file
copy env.example .env
# Edit .env with your configuration (optional - defaults work fine)
```

5. **Initialize the database:**
```bash
# Set Flask app environment variable (Windows)
set FLASK_APP=app.py

# Set Flask app environment variable (macOS/Linux)
export FLASK_APP=app.py

# Initialize database migrations (only needed once)
python -m flask db init

# Create initial migration (only needed once)
python -m flask db migrate -m "Initial migration"

# Apply migrations
python -m flask db upgrade
```

6. **Run the application:**
```bash
python app.py
```

The server will start on `http://0.0.0.0:5000` and be accessible from any device on the LAN.

### Quick Start for Windows Users

If you're on Windows and want to get started quickly:

1. Open PowerShell as Administrator
2. Navigate to the project folder: `cd C:\path\to\uav_gcs_server`
3. Create and activate virtual environment:
   ```powershell
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```
4. Install dependencies: `pip install -r requirements.txt`
5. Set Flask app: `$env:FLASK_APP="app.py"`
6. Initialize database: `python -m flask db upgrade`
7. Run server: `python app.py`
8. Open browser to: http://localhost:5000

### Accessing the Dashboard

Once the server is running, you can access:
- **Main Dashboard**: http://localhost:5000/ or http://your-ip:5000/
- **Health Check**: http://localhost:5000/health
- **API Endpoints**: http://localhost:5000/api/sensors and http://localhost:5000/api/targets

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

1. **"Dead Link" or Connection Issues**:
   - Ensure the server is running: `python app.py`
   - Check if port 5000 is available: `netstat -an | findstr :5000`
   - Try accessing http://localhost:5000/health first
   - Check Windows Firewall settings if accessing from another device

2. **Database Connection Errors**:
   - Ensure database is initialized: `python -m flask db upgrade`
   - Check your `SQLALCHEMY_DATABASE_URI` configuration
   - Verify the `instance/` directory exists and is writable

3. **Socket.IO Connection Issues**:
   - Check browser console for WebSocket connection errors
   - Verify CORS settings in your `.env` file
   - Ensure firewall allows WebSocket connections on port 5000
   - Try refreshing the page if connection status shows "Disconnected"

4. **Dependencies Not Found**:
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`
   - Check Python version: `python --version` (should be 3.8+)

5. **TTS Not Working**:
   - Ensure browser supports `speechSynthesis` API
   - Check if TTS is enabled in the dashboard controls
   - Try in a different browser (Chrome/Firefox recommended)

6. **Migration Errors**:
   - If migrations fail, try: `python -m flask db stamp head`
   - Then: `python -m flask db upgrade`
   - For fresh start: delete `instance/uav_gcs.db` and run migrations again

### Verification Steps

To verify everything is working:

1. **Start the server**: `python app.py`
2. **Check health endpoint**: Visit http://localhost:5000/health
3. **Check main dashboard**: Visit http://localhost:5000/
4. **Check browser console**: Look for "Connected to GCS stream" message
5. **Test API**: Send a POST request to http://localhost:5000/api/sensors with sample data

### Sample API Test

Test the sensor API with curl:
```bash
curl -X POST http://localhost:5000/api/sensors \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-01-15T10:30:00Z",
    "co_ppm": 1.5,
    "no2_ppm": 0.8,
    "temp_c": 22.5,
    "humidity_pct": 60.0,
    "source": "test"
  }'
```

### Logs

Application logs are written to stdout. Check the console output for error messages and request logs. The dashboard also shows connection status in the top-right corner.

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
