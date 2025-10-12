#!/usr/bin/env python3
"""
Test script for batch detection API

This script demonstrates:
1. Single detection (backward compatible)
2. Batch detection with JSON array
3. Multipart form with batch detections
"""

import base64
import io
import json
import requests
from PIL import Image, ImageDraw

# Configuration
API_URL = "http://localhost:5000/api/targets"
API_KEY = "YOUR_API_KEY"  # Change this to your actual API key

def create_test_image(width=320, height=240, text="TEST"):
    """Create a test JPEG image"""
    img = Image.new("RGB", (width, height), (220, 230, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle((10, 10, width-10, height-10), outline=(0, 120, 255), width=3)
    draw.text((20, 20), text, fill=(0, 0, 0))
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()

def test_single_detection():
    """Test backward-compatible single detection"""
    print("\n" + "="*60)
    print("TEST 1: Single Detection (Backward Compatible)")
    print("="*60)
    
    img_bytes = create_test_image(text="SINGLE")
    img_b64 = base64.b64encode(img_bytes).decode()
    
    payload = {
        "image_b64": img_b64,
        "target_type": "valve",
        "details": {"state": "open", "confidence": 0.92},
        "ts": "2025-10-12T10:30:00Z",
        "device_id": "test_device_001"
    }
    
    response = requests.post(
        API_URL,
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
def test_batch_detection_json():
    """Test batch detection with JSON array"""
    print("\n" + "="*60)
    print("TEST 2: Batch Detection (JSON Array)")
    print("="*60)
    
    img_bytes = create_test_image(text="BATCH")
    img_b64 = base64.b64encode(img_bytes).decode()
    
    payload = {
        "image_b64": img_b64,
        "details": [
            {
                "target_type": "valve",
                "confidence": 0.92,
                "details": {"state": "open"}
            },
            {
                "target_type": "gauge",
                "confidence": 0.88,
                "details": {"reading_bar": 1.8, "angle_deg": 271.0}
            },
            {
                "target_type": "aruco",
                "confidence": 0.95,
                "details": {"id": 23, "pose": [0.1, 0.2, 1.5], "rotation": [0.0, 1.0, 0.0]}
            }
        ],
        "ts": "2025-10-12T10:35:00Z",
        "device_id": "test_device_001"
    }
    
    response = requests.post(
        API_URL,
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_batch_detection_multipart():
    """Test batch detection with multipart/form-data"""
    print("\n" + "="*60)
    print("TEST 3: Batch Detection (Multipart Form)")
    print("="*60)
    
    img_bytes = create_test_image(text="MULTIPART")
    
    # Batch detections as JSON string
    details_json = json.dumps([
        {
            "target_type": "valve",
            "confidence": 0.91,
            "details": {"state": "closed"}
        },
        {
            "target_type": "gauge",
            "confidence": 0.86,
            "details": {"reading_bar": 2.5, "angle_deg": 180.0}
        }
    ])
    
    files = {
        'file': ('frame.jpg', io.BytesIO(img_bytes), 'image/jpeg')
    }
    
    data = {
        'details': details_json,
        'ts': '2025-10-12T10:40:00Z',
        'device_id': 'test_device_001'
    }
    
    response = requests.post(
        API_URL,
        headers={"X-API-Key": API_KEY},
        files=files,
        data=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def main():
    print("\n" + "="*60)
    print("Batch Detection API Test Suite")
    print("="*60)
    print(f"API URL: {API_URL}")
    print(f"API Key: {'*' * (len(API_KEY) - 4) + API_KEY[-4:]}")
    
    try:
        test_single_detection()
        test_batch_detection_json()
        test_batch_detection_multipart()
        
        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the server.")
        print("   Make sure the server is running on http://localhost:5000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    main()

