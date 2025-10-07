import os
from functools import wraps

from flask import request, jsonify, make_response


def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = os.getenv("API_KEY")
        
        if not api_key:
            return f(*args, **kwargs)
        
        provided_key = request.headers.get("X-API-Key")
        if not provided_key or provided_key != api_key:
            return jsonify({"error": "Invalid or missing API key"}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def cors_headers(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Convert to Response object if it's a tuple (response, status_code)
        if not hasattr(response, 'headers'):
            response = make_response(response)
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key'
        
        return response
    return decorated_function
