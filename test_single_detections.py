#!/usr/bin/env python3
"""
Test single detections to verify they update the metadata box correctly
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

def send_single_detection(target_type, details, confidence=None):
    """Send a single detection"""
    img_bytes = make_test_image()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    # Build the detection object
    detection = {
        "target_type": target_type,
        "details": details
    }
    
    # Add confidence if provided
    if confidence is not None:
        detection["confidence"] = confidence
    
    payload = {
        "image_b64": f"data:image/jpeg;base64,{img_b64}",
        "details": detection,
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "device_id": "test_single_detections"
    }
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(API, headers=headers, data=json.dumps(payload))
    print(f"[SINGLE] {target_type}: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"  -> Saved {result['saved']} detection(s)")
        for det in result['detections']:
            print(f"     - {det['target_type']}: {json.dumps(det['details'])}")
    else:
        print(f"  -> Error: {response.text}")
    return response

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SINGLE DETECTION TEST - Metadata Box Update Verification")
    print("="*70)
    print("Testing each detection type individually...")
    print("Check your browser at http://localhost:5000")
    print("The metadata box should show:")
    print("  - All 3 slots visible (ArUco, Gauge, Valve)")
    print("  - Only the active detection shows real data")
    print("  - Other slots show placeholder labels with -- values")
    print("="*70)
    
    # Test 1: Single valve detection
    print("\n1. Sending single VALVE detection...")
    send_single_detection("valve", {
        "state": "open",
        "id": "V-101"
    }, confidence=0.95)
    
    print("\n   -> Check: Valve slot should show 'State: open | Confidence: 95.0%'")
    print("   -> Check: ArUco and Gauge slots should show placeholder -- values")
    time.sleep(3)
    
    # Test 2: Single gauge detection
    print("\n2. Sending single GAUGE detection...")
    send_single_detection("gauge", {
        "reading_bar": 2.85,
        "angle_deg": 180.0,
        "label": "Pressure Main"
    }, confidence=0.88)
    
    print("\n   -> Check: Gauge slot should show 'Reading: 2.85 bar | Confidence: 88.0%'")
    print("   -> Check: ArUco and Valve slots should show placeholder -- values")
    time.sleep(3)
    
    # Test 3: Single ArUco detection (no confidence)
    print("\n3. Sending single ARUCO detection (no confidence)...")
    send_single_detection("aruco", {
        "id": 42,
        "pose": [0.15, 0.22, 1.35],
        "rotation": [0.05, 0.98, -0.12]
    })
    
    print("\n   -> Check: ArUco slot should show 'ID: 42 | Position: [0.150, 0.220, 1.350] | Rotation: [0.050, 0.980, -0.120]'")
    print("   -> Check: Gauge and Valve slots should show placeholder -- values")
    time.sleep(3)
    
    # Test 4: Another valve with different state
    print("\n4. Sending another VALVE detection (closed state)...")
    send_single_detection("valve", {
        "state": "closed",
        "id": "V-102"
    }, confidence=0.92)
    
    print("\n   -> Check: Valve slot should now show 'State: closed | Confidence: 92.0%'")
    print("   -> Check: ArUco and Gauge slots should show placeholder -- values")
    time.sleep(3)
    
    # Test 5: Another ArUco with different ID
    print("\n5. Sending another ARUCO detection (different ID)...")
    send_single_detection("aruco", {
        "id": 23,
        "pose": [0.8, 0.1, 2.1],
        "rotation": [0.2, 0.9, 0.0]
    })
    
    print("\n   -> Check: ArUco slot should now show 'ID: 23 | Position: [0.800, 0.100, 2.100] | Rotation: [0.200, 0.900, 0.000]'")
    print("   -> Check: Gauge and Valve slots should show placeholder -- values")
    
    print("\n" + "="*70)
    print("TEST COMPLETE!")
    print("="*70)
    print("If everything worked correctly:")
    print("✅ Each single detection should update only its respective slot")
    print("✅ All three slots should always be visible with persistent labels")
    print("✅ ArUco detections should show position and rotation data")
    print("✅ Valve detections should show state and confidence")
    print("✅ Gauge detections should show reading and confidence")
    print("✅ Timestamps should be valid (not 'Invalid Date')")
    print("✅ No flickering between different label formats")
    print("="*70)
