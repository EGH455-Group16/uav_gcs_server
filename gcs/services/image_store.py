"""
Image storage service for handling target detection images.
Provides utilities for saving uploaded images and managing the targets directory.
"""
import os
import base64
import json
from datetime import datetime
from typing import Optional, Dict, Any


def ensure_targets_dir() -> str:
    """Ensure the static/targets directory exists and return its path."""
    targets_dir = os.path.join("gcs", "static", "targets")
    os.makedirs(targets_dir, exist_ok=True)
    return targets_dir


def save_image_bytes(img_bytes: bytes, fname: str = "latest.jpg") -> str:
    """Save image bytes to the targets directory and return the file path."""
    targets_dir = ensure_targets_dir()
    file_path = os.path.join(targets_dir, fname)
    
    with open(file_path, "wb") as f:
        f.write(img_bytes)
    
    return file_path


def decode_b64_image(image_b64: str) -> bytes:
    """
    Decode base64 image data, handling both raw base64 and data URL formats.
    
    Args:
        image_b64: Base64 encoded image data, optionally prefixed with data URL
        
    Returns:
        Decoded image bytes
        
    Raises:
        ValueError: If the base64 data is invalid or not an image
    """
    # Strip data URL prefix if present
    if image_b64.startswith("data:image/"):
        # Extract base64 part after comma
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]
        else:
            raise ValueError("Invalid data URL format")
    
    try:
        # Decode base64
        img_bytes = base64.b64decode(image_b64)
        
        # Basic validation - check if it looks like an image
        if len(img_bytes) < 100:  # Too small to be a real image
            raise ValueError("Image data too small")
            
        # Check for common image file signatures
        if not (img_bytes.startswith(b'\xff\xd8\xff') or  # JPEG
                img_bytes.startswith(b'\x89PNG') or       # PNG
                img_bytes.startswith(b'GIF8')):           # GIF
            raise ValueError("Invalid image format - must be JPEG, PNG, or GIF")
            
        return img_bytes
        
    except Exception as e:
        raise ValueError(f"Failed to decode base64 image: {str(e)}")


def parse_details(details: Any) -> Dict[str, Any]:
    """
    Parse details field, handling both JSON strings and dict objects.
    
    Args:
        details: Either a JSON string or a dict
        
    Returns:
        Parsed details as a dict
    """
    if details is None:
        return {}
    
    if isinstance(details, dict):
        return details
    
    if isinstance(details, str):
        try:
            return json.loads(details)
        except json.JSONDecodeError:
            # If it's not valid JSON, treat as a simple string value
            return {"value": details}
    
    # For other types, convert to string
    return {"value": str(details)}


def get_image_url() -> str:
    """Get the URL path for the latest detection image."""
    return "/static/targets/latest.jpg"
