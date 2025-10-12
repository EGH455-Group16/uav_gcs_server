#!/usr/bin/env python3
"""
Live test for multiple detections - sends to running GCS server
so you can see all detections displayed in the dashboard metadata box
"""
import requests
import json
import base64
import time

API = "http://localhost:5000/api/targets"
API_KEY = "test_key_123"

def make_test_image():
    """Create a minimal valid JPEG image"""
    # Minimal valid JPEG (1x1 pixel)
    return base64.b64decode(
        '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAIBAQIBAQICAgICAgICAwUDAwMDAwYEBAMFBwYHBwcGBwcICQsJCAgKCAcHCg0KCgsMDAwMBwkODw0MDgsMDAz/'
        '2wBDAQICAgMDAwYDAwYMCAcIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAz/'
        'wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAr/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/'
        '8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k='
    )

def send_batch_detections():
    """Send multiple detections in one request to see them all in dashboard"""
    
    print("\n" + "="*70)
    print("SENDING BATCH OF 3 DETECTIONS TO GCS DASHBOARD")
    print("="*70)
    print("\nCheck your browser at http://localhost:5000")
    print("You should see all 3 detections in the metadata box!\n")
    
    # Create test image
    img_bytes = make_test_image()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    # Payload with 3 different detection types
    payload = {
        "image_b64": f"data:image/jpeg;base64,{img_b64}",
        "details": [
            {
                "target_type": "valve",
                "confidence": 0.92,
                "details": {
                    "state": "open",
                    "id": "V-101"
                }
            },
            {
                "target_type": "gauge",
                "confidence": 0.88,
                "details": {
                    "reading_bar": 2.45,
                    "angle_deg": 245.0,
                    "label": "Pressure Main"
                }
            },
            {
                "target_type": "aruco",
                "details": {
                    "id": 42,
                    "pose": [0.15, 0.22, 1.35],
                    "rotation": [0.05, 0.98, -0.12]
                }
            }
        ],
        "device_id": "test_pi_001"
    }
    
    # Send request
    response = requests.post(
        API,
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        data=json.dumps(payload)
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print(f"\n>> Successfully sent {result['saved']} detections!")
        print(f"\nDetections sent:")
        for i, det in enumerate(result['detections'], 1):
            print(f"  {i}. {det['target_type'].upper()}")
            print(f"     Details: {json.dumps(det['details'], indent=10)}")
        
        print(f"\n>> Image URL: {result['image_url']}")
        print("\n" + "="*70)
        print("GO TO YOUR DASHBOARD NOW!")
        print("The metadata box should show all 3 detections without flickering:")
        print("  - VALVE: State: open | Confidence: 92.0%")
        print("  - GAUGE: Reading: 2.45 bar | Confidence: 88.0%")
        print("  - ARUCO: ID: 42 | Position: [...] | Rotation: [...]")
        print("="*70)
    else:
        print(f"\n>> Error: {response.text}")

if __name__ == "__main__":
    print("\n>> Starting live multiple detections test...")
    print(">> Make sure your GCS server is running on http://localhost:5000")
    time.sleep(1)
    
    send_batch_detections()
    
    print("\n\n>> TIP: Run this script multiple times to see fresh detections!")
    print("      Each run will create a new entry in the recent detections list.\n")

