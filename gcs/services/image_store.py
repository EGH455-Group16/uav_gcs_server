import base64
import json
import os
from typing import Any, Dict


def ensure_targets_dir() -> str:
    targets_dir = os.path.join("gcs", "static", "targets")
    os.makedirs(targets_dir, exist_ok=True)
    return targets_dir


def save_image_bytes(img_bytes: bytes, fname: str = "latest.jpg") -> str:
    targets_dir = ensure_targets_dir()
    file_path = os.path.join(targets_dir, fname)
    
    with open(file_path, "wb") as f:
        f.write(img_bytes)
    
    return file_path


def decode_b64_image(image_b64: str) -> bytes:
    if image_b64.startswith("data:image/"):
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]
        else:
            raise ValueError("Invalid data URL format")
    
    try:
        img_bytes = base64.b64decode(image_b64)
        
        if len(img_bytes) < 100:
            raise ValueError("Image data too small")
            
        if not (img_bytes.startswith(b'\xff\xd8\xff') or
                img_bytes.startswith(b'\x89PNG') or
                img_bytes.startswith(b'GIF8')):
            raise ValueError("Invalid image format - must be JPEG, PNG, or GIF")
            
        return img_bytes
        
    except Exception as e:
        raise ValueError(f"Failed to decode base64 image: {str(e)}")


def parse_details(details: Any) -> Dict[str, Any]:
    if details is None:
        return {}
    
    if isinstance(details, dict):
        return details
    
    if isinstance(details, str):
        try:
            return json.loads(details)
        except json.JSONDecodeError:
            return {"value": details}
    
    return {"value": str(details)}


def get_image_url() -> str:
    return "/static/targets/latest.jpg"
