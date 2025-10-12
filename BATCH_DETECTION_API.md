# Batch Detection API Documentation

## Overview

The `/api/targets` endpoint has been enhanced to support **batch detections** while maintaining full backward compatibility with the existing single-detection API.

## Key Features

✅ **Batch Processing**: Submit multiple detections from a single frame  
✅ **Single Image Archive**: All detections share the same archived image  
✅ **Backward Compatible**: Existing clients continue to work without changes  
✅ **Flexible Input**: Supports both `multipart/form-data` and `application/json`  
✅ **Per-Detection Events**: Each detection triggers individual socket events  
✅ **Batch Event**: Optional batch summary event for UI optimization  

## API Changes

### New Response Format

```json
{
  "ok": true,
  "saved": 3,
  "image_url": "/static/targets/archive/20251012T063527_batch.jpg",
  "thumb_url": "/static/targets/archive/20251012T063527_batch_thumb.jpg",
  "detections": [
    {
      "target_type": "valve",
      "ts": "2025-10-12T06:35:27Z",
      "details": {"state": "open"}
    },
    {
      "target_type": "gauge",
      "ts": "2025-10-12T06:35:27Z",
      "details": {"reading_bar": 1.8, "angle_deg": 271.0}
    },
    {
      "target_type": "aruco",
      "ts": "2025-10-12T06:35:27Z",
      "details": {"id": 23, "pose": [0.1, 0.2, 1.5]}
    }
  ]
}
```

### Detection Item Schema

Each detection item in the batch should follow this schema:

```json
{
  "target_type": "valve|gauge|aruco|livedata",
  "confidence": 0.92,               // optional
  "details": { ... },               // required (object)
  "ts": "2025-10-12T06:10:27Z"      // optional per-detection timestamp
}
```

## Usage Examples

### 1. Batch Detection (JSON with base64 image)

```python
import base64
import json
import requests

# Encode image
with open("frame.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

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
            "details": {"id": 23, "pose": [0.1, 0.2, 1.5]}
        }
    ],
    "ts": "2025-10-12T06:10:27Z",
    "device_id": "pi_device_001"
}

response = requests.post(
    "http://localhost:5000/api/targets",
    headers={
        "X-API-Key": "YOUR_API_KEY",
        "Content-Type": "application/json"
    },
    json=payload
)

print(response.json())
```

### 2. Batch Detection (Multipart Form)

```bash
curl -X POST http://localhost:5000/api/targets \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@frame.jpg" \
  -F 'details=[
    {"target_type":"valve","confidence":0.92,"details":{"state":"open"}},
    {"target_type":"gauge","confidence":0.88,"details":{"reading_bar":1.8,"angle_deg":271.0}},
    {"target_type":"aruco","confidence":0.95,"details":{"id":23,"pose":[0.1,0.2,1.5]}}
  ]' \
  -F "ts=2025-10-12T06:10:27Z" \
  -F "device_id=pi_device_001"
```

### 3. Single Detection (Backward Compatible)

**Old API format still works:**

```python
payload = {
    "image_b64": img_b64,
    "target_type": "valve",
    "details": {"state": "open"},
    "ts": "2025-10-12T06:10:27Z"
}

response = requests.post(
    "http://localhost:5000/api/targets",
    headers={
        "X-API-Key": "YOUR_API_KEY",
        "Content-Type": "application/json"
    },
    json=payload
)
```

**Multipart form (backward compatible):**

```bash
curl -X POST http://localhost:5000/api/targets \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@frame.jpg" \
  -F "target_type=valve" \
  -F 'details={"state":"open"}' \
  -F "ts=2025-10-12T06:10:27Z"
```

### 4. Image-less Event (e.g., LiveData Heartbeat)

```python
payload = {
    "target_type": "livedata",
    "details": {"id": "livedata", "status": "alive"},
    "device_id": "pi_device_001"
}

response = requests.post(
    "http://localhost:5000/api/targets",
    headers={
        "X-API-Key": "YOUR_API_KEY",
        "Content-Type": "application/json"
    },
    json=payload
)
```

## Socket.IO Events

### Per-Detection Events

Each detection in the batch triggers:

**Event: `target_detected`** (existing event, maintains compatibility)

```json
{
  "ts": "2025-10-12T06:35:27Z",
  "target_type": "valve",
  "details": {"state": "open"},
  "image_url": "/static/targets/archive/20251012T063527_batch.jpg",
  "thumb_url": "/static/targets/archive/20251012T063527_batch_thumb.jpg",
  "device_id": "pi_device_001"
}
```

**Event: `recent_detection`** (if accepted by de-dupe logic)

```json
{
  "ts": 1728721527.5,
  "type": "valve",
  "details": {"state": "open"},
  "image_url": "/static/targets/archive/20251012T063527_batch.jpg",
  "thumb_url": "/static/targets/archive/20251012T063527_batch_thumb.jpg"
}
```

### Batch Summary Event (New)

**Event: `target_batch`** (new event for batch operations)

```json
{
  "count": 3,
  "image_url": "/static/targets/archive/20251012T063527_batch.jpg",
  "thumb_url": "/static/targets/archive/20251012T063527_batch_thumb.jpg",
  "device_id": "pi_device_001",
  "detections": [
    {
      "target_type": "valve",
      "ts": "2025-10-12T06:35:27Z",
      "details": {"state": "open"}
    },
    {
      "target_type": "gauge",
      "ts": "2025-10-12T06:35:27Z",
      "details": {"reading_bar": 1.8, "angle_deg": 271.0}
    },
    {
      "target_type": "aruco",
      "ts": "2025-10-12T06:35:27Z",
      "details": {"id": 23, "pose": [0.1, 0.2, 1.5]}
    }
  ]
}
```

## Database

Each detection creates a separate row in the `TargetDetection` table:

| id | ts | target_type | details_json | image_url |
|----|-------|-------------|--------------|-----------|
| 1 | 2025-10-12 06:35:27 | valve | {"state":"open"} | /static/targets/archive/20251012T063527_batch.jpg |
| 2 | 2025-10-12 06:35:27 | gauge | {"reading_bar":1.8,"angle_deg":271.0} | /static/targets/archive/20251012T063527_batch.jpg |
| 3 | 2025-10-12 06:35:27 | aruco | {"id":23,"pose":[0.1,0.2,1.5]} | /static/targets/archive/20251012T063527_batch.jpg |

All rows share the same `image_url` since they were detected in the same frame.

## Implementation Details

### Image Handling

1. Image is saved once to `latest.jpg`
2. Image is archived once with a timestamp
3. All detection records reference the same archived image URL
4. Thumbnail is generated once (if your archiver supports it)

### Backward Compatibility

The API automatically detects whether the payload is:
- **Old format**: Top-level `target_type` and `details` as a simple object
- **New format**: `details` as an array of detection items

```python
# Old format detection logic
if top_level_has_target_type and details_is_not_array:
    # Treat as single detection (backward compatible)
    detections = [{
        "target_type": payload["target_type"],
        "details": payload["details"]
    }]
```

### Timestamp Handling

- **Top-level `ts`**: Fallback timestamp for all detections
- **Per-detection `ts`**: Overrides the top-level timestamp for that specific detection
- **Server timestamp**: Used if neither is provided

Priority: `per-detection ts` > `top-level ts` > `server timestamp`

## Testing

Run the test suite:

```bash
# Run all tests
pytest gcs/tests/test_routes.py -v

# Run only batch detection tests
pytest gcs/tests/test_routes.py::test_target_api_batch_detections_json -v
pytest gcs/tests/test_routes.py::test_target_api_batch_detections_multipart -v

# Run backward compatibility tests
pytest gcs/tests/test_routes.py -k "target_api" -v
```

Run the interactive test script:

```bash
# Edit API_KEY in test_batch_api.py first
python test_batch_api.py
```

## Migration Guide

### For RPi Clients

**No changes required** - existing clients continue to work. To use batch detection:

```python
# Old way (still works)
send_detection(image, target_type, details)

# New way (batched)
detections = [
    {"target_type": "valve", "details": {...}},
    {"target_type": "gauge", "details": {...}},
]
send_batch_detection(image, detections)
```

### For Frontend/UI

**Existing listeners continue to work** - you'll just receive multiple `target_detected` events when a batch is submitted.

**Optional optimization** - listen for the new `target_batch` event:

```javascript
socket.on('target_batch', (data) => {
  console.log(`Received batch of ${data.count} detections`);
  // Update UI atomically with all detections
  data.detections.forEach(detection => {
    addDetectionCard(detection, data.image_url);
  });
});
```

## Error Handling

### Invalid Batch

```json
{
  "error": "No detections found in 'details'"
}
```

### Missing Required Fields

```json
{
  "error": "image_b64 or details required"
}
```

### Invalid Image

```json
{
  "error": "Failed to decode base64 image"
}
```

## Performance Considerations

- **Single DB transaction**: All detections are committed in one transaction
- **Single image operation**: Image is saved/archived only once
- **Multiple socket events**: Each detection triggers socket events (consider rate limiting for large batches)
- **Throughput metering**: Batch payloads are measured as a single TAIP metric

## Future Enhancements

- [ ] Batch size limits (configurable max detections per batch)
- [ ] Bulk insert optimization for very large batches
- [ ] Compressed batch payloads
- [ ] Batch validation before processing
- [ ] Confidence-based filtering at API level

## Support

For issues or questions, check:
- Test suite: `gcs/tests/test_routes.py`
- Implementation: `gcs/routes.py` (line 261+)
- Example script: `test_batch_api.py`

