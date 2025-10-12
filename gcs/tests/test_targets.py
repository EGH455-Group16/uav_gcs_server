# target_test.py
import base64, io, time, datetime, requests, json
try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("Install Pillow first: pip install pillow")

API = "http://localhost:5000/api/targets"
API_KEY = "YOUR_API_KEY"   # <-- change me
H = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def make_img(w=320, h=240, txt="TEST"):
    img = Image.new("RGB", (w, h), (220, 230, 240))
    d = ImageDraw.Draw(img)
    d.rectangle((10, 10, w-10, h-10), outline=(0,120,255), width=3)
    d.text((20, 20), txt, fill=(0,0,0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()

def data_url(jpeg_bytes: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(jpeg_bytes).decode()

def iso_z():
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"

def post(target_type, details, label):
    """Send single detection (backward compatible)"""
    img_bytes = make_img(txt=label)
    r = requests.post(API, headers=H, json={
        "target_type": target_type,
        "details": details,
        "image_b64": data_url(img_bytes),
        "ts": iso_z()
    })
    print(f"[SINGLE] {target_type}: {r.status_code}")
    if r.status_code == 201:
        result = r.json()
        print(f"  -> Saved {result.get('saved', 1)} detection(s)")
    else:
        print(f"  -> Error: {r.text}")
    return r

def post_batch(detections, label):
    """Send batch of detections"""
    img_bytes = make_img(txt=label)
    r = requests.post(API, headers=H, json={
        "image_b64": data_url(img_bytes),
        "details": detections,
        "ts": iso_z(),
        "device_id": "test_device_001"
    })
    print(f"[BATCH] {len(detections)} detections: {r.status_code}")
    if r.status_code == 201:
        result = r.json()
        print(f"  -> Saved {result['saved']} detection(s)")
        for det in result['detections']:
            print(f"     - {det['target_type']}: {json.dumps(det['details'])}")
    else:
        print(f"  -> Error: {r.text}")
    return r

print("\n" + "="*60)
print("BATCH DETECTION TEST - Multiple detections per frame")
print("="*60 + "\n")

# 1) BATCH: Complete inspection frame with valve + gauge + aruco
print("Test 1: Full inspection - Valve + Gauge + ArUco marker")
post_batch([
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
], "BATCH 1")
time.sleep(3)

# 2) BATCH: Multiple gauges in same frame
print("\nTest 2: Multiple gauges detected")
post_batch([
    {
        "target_type": "gauge",
        "confidence": 0.90,
        "details": {"reading_bar": 4.14, "angle_deg": 180.0, "label": "Pressure A"}
    },
    {
        "target_type": "gauge",
        "confidence": 0.87,
        "details": {"reading_bar": 2.5, "angle_deg": 120.0, "label": "Pressure B"}
    },
    {
        "target_type": "gauge",
        "confidence": 0.85,
        "details": {"reading_bar": 3.2, "angle_deg": 150.0, "label": "Pressure C"}
    }
], "BATCH 2")
time.sleep(3)

# 3) BATCH: Multiple valves and one aruco
print("\nTest 3: Multiple valves + ArUco localization")
post_batch([
    {
        "target_type": "valve",
        "confidence": 0.91,
        "details": {"state": "closed", "id": "V1"}
    },
    {
        "target_type": "valve",
        "confidence": 0.89,
        "details": {"state": "open", "id": "V2"}
    },
    {
        "target_type": "aruco",
        "confidence": 0.96,
        "details": {"id": 17, "rvec": [-2.176, 0.152, -1.285], "tvec": [0.12, 0.03, 0.88]}
    }
], "BATCH 3")
time.sleep(2)

print("\n" + "="*60)
print("SINGLE DETECTION TEST - Backward compatibility")
print("="*60 + "\n")

# 4) SINGLE: Valve appears (immediate card)
print("Test 4: Single valve detection (old API format)")
post("valve", {"state":"open","confidence":0.92}, "VALVE OPEN")
time.sleep(2)

# 5) SINGLE: Same valve within 4s (should NOT refresh recent card)
print("\nTest 5: Same valve within 4s (no refresh)")
post("valve", {"state":"open","confidence":0.93}, "VALVE OPEN (2s)")
time.sleep(5)

# 6) SINGLE: Same valve after 5s (>=4s: should refresh)
print("\nTest 6: Same valve after 5s (should refresh)")
post("valve", {"state":"open","confidence":0.91}, "VALVE OPEN (5s)")
time.sleep(1)

# 7) SINGLE: Switch object → immediate switch
print("\nTest 7: Switch to gauge (immediate)")
post("gauge", {"reading_bar":4.14,"confidence":0.90}, "GAUGE 4.14")
time.sleep(5)

# 8) SINGLE: Small change after 5s (same object by ≤0.1 rule → refresh)
print("\nTest 8: Gauge reading changed (refresh)")
post("gauge", {"reading_bar":4.18,"confidence":0.90}, "GAUGE 4.18")
time.sleep(1)

# 9) SINGLE: New ArUco id (immediate switch)
print("\nTest 9: New ArUco marker (immediate)")
post("aruco", {"id":17,"rvec":[-2.176,0.152,-1.285],"tvec":[0.12,0.03,0.88],"confidence":0.96}, "ARUCO 17")

print("\n" + "="*60)
print("MIXED TEST - Batch with varied detection counts")
print("="*60 + "\n")

# 10) BATCH: Single detection in batch format (should work)
print("Test 10: Single detection in batch array format")
post_batch([
    {
        "target_type": "livedata",
        "confidence": 1.0,
        "details": {"id": "livedata", "status": "heartbeat"}
    }
], "BATCH 4")
time.sleep(2)

# 11) BATCH: Large batch with all types
print("\nTest 11: Large batch - All detection types")
post_batch([
    {"target_type": "valve", "confidence": 0.92, "details": {"state": "open", "id": "V1"}},
    {"target_type": "valve", "confidence": 0.88, "details": {"state": "closed", "id": "V2"}},
    {"target_type": "valve", "confidence": 0.85, "details": {"state": "open", "id": "V3"}},
    {"target_type": "gauge", "confidence": 0.90, "details": {"reading_bar": 2.1, "angle_deg": 90.0}},
    {"target_type": "gauge", "confidence": 0.87, "details": {"reading_bar": 3.5, "angle_deg": 150.0}},
    {"target_type": "aruco", "confidence": 0.96, "details": {"id": 42, "pose": [0.2, 0.3, 1.2]}},
], "BATCH 5")

print("\n" + "="*60)
print("ALL TESTS COMPLETED!")
print("="*60)
