#!/usr/bin/env python3
"""
Test ArUco marker detections only
"""
import requests
import json
import base64
import time
from datetime import datetime, timezone

API = "http://localhost:5000/api/targets"
API_KEY = "test_key_123"

def make_test_image():
    """Create a minimal valid JPEG image"""
    return base64.b64decode(
        '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAIBAQIBAQICAgICAgICAwUDAwMDAwYEBAMFBwYHBwcGBwcICQsJCAgKCAcHCg0KCgsMDAwMBwkODw0MDgsMDAz/'
        '2wBDAQICAgMDAwYDAwYMCAcIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAz/'
        'wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAr/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/'
        '8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k='
    )

def send_aruco_detection(aruco_id, pose, rotation):
    """Send a single ArUco detection"""
    img_bytes = make_test_image()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    detection = {
        "target_type": "aruco",
        "details": {
            "id": aruco_id,
            "pose": pose,
            "rotation": rotation
        }
    }
    
    payload = {
        "image_b64": f"data:image/jpeg;base64,{img_b64}",
        "details": detection,
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "device_id": "test_aruco_only"
    }
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(API, headers=headers, data=json.dumps(payload))
    print(f"[ARUCO] ID {aruco_id}: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"  -> Saved {result['saved']} detection(s)")
        for det in result['detections']:
            print(f"     - {det['target_type']}: {json.dumps(det['details'])}")
    else:
        print(f"  -> Error: {response.text}")
    return response

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ARUCO MARKER DETECTION TEST")
    print("="*60)
    print("Testing ArUco marker detections only...")
    print("Check your browser at http://localhost:5000")
    print("The metadata box should show:")
    print("  - ArUco slot with real data")
    print("  - Gauge and Valve slots with placeholder -- values")
    print("="*60)
    
    # Test 1: ArUco marker ID 42
    print("\n1. Sending ArUco marker ID 42...")
    send_aruco_detection(42, [0.15, 0.22, 1.35], [0.05, 0.98, -0.12])
    
    print("\n   -> Check: ArUco slot should show 'ID: 42 | Position: [0.150, 0.220, 1.350] | Rotation: [0.050, 0.980, -0.120]'")
    print("   -> Check: Gauge and Valve slots should show placeholder -- values")
    time.sleep(3)
    
    # Test 2: ArUco marker ID 23 (different position)
    print("\n2. Sending ArUco marker ID 23...")
    send_aruco_detection(23, [0.8, 0.1, 2.1], [0.2, 0.9, 0.0])
    
    print("\n   -> Check: ArUco slot should now show 'ID: 23 | Position: [0.800, 0.100, 2.100] | Rotation: [0.200, 0.900, 0.000]'")
    print("   -> Check: Gauge and Valve slots should show placeholder -- values")
    time.sleep(3)
    
    # Test 3: ArUco marker ID 7 (moving position)
    print("\n3. Sending ArUco marker ID 7...")
    send_aruco_detection(7, [1.2, 0.5, 0.8], [-0.1, 0.8, 0.3])
    
    print("\n   -> Check: ArUco slot should now show 'ID: 7 | Position: [1.200, 0.500, 0.800] | Rotation: [-0.100, 0.800, 0.300]'")
    print("   -> Check: Gauge and Valve slots should show placeholder -- values")
    time.sleep(3)
    
    # Test 4: ArUco marker ID 42 again (same ID, different position)
    print("\n4. Sending ArUco marker ID 42 again (moved)...")
    send_aruco_detection(42, [0.3, 0.7, 1.8], [0.15, 0.95, -0.05])
    
    print("\n   -> Check: ArUco slot should show 'ID: 42 | Position: [0.300, 0.700, 1.800] | Rotation: [0.150, 0.950, -0.050]'")
    print("   -> Check: Gauge and Valve slots should show placeholder -- values")
    
    print("\n" + "="*60)
    print("ARUCO TEST COMPLETE!")
    print("="*60)
    print("If everything worked correctly:")
    print("  - ArUco slot should show each marker's ID, position, and rotation")
    print("  - Position and rotation values should update correctly")
    print("  - Gauge and Valve slots should remain as placeholders")
    print("  - No confidence values should be shown (ArUco doesn't use confidence)")
    print("  - Timestamps should be valid")
    print("="*60)
