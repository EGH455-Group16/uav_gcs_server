"""
Optional API key middleware for security.
Disabled by default - set API_KEY environment variable to enable.
"""
import os
from flask import request, jsonify
from functools import wraps

def api_key_required(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = os.getenv("API_KEY")
        
        # If no API key is set, skip authentication
        if not api_key:
            return f(*args, **kwargs)
        
        # Check for API key in headers
        provided_key = request.headers.get("X-API-Key")
        if not provided_key or provided_key != api_key:
            return jsonify({"error": "Invalid or missing API key"}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def cors_headers(f):
    """Add CORS headers for LAN access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Add CORS headers for LAN access
        if hasattr(response, 'headers'):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key'
        
        return response
    return decorated_function
