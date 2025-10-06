# target_test.py
import base64, io, time, datetime, requests
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
    img_bytes = make_img(txt=label)
    r = requests.post(API, headers=H, json={
        "target_type": target_type,
        "details": details,
        "image_b64": data_url(img_bytes),
        "ts": iso_z()
    })
    print(target_type, details, r.status_code, r.text)

# 1) Valve appears (immediate card)
post("valve", {"state":"open","confidence":0.92}, "VALVE OPEN")
time.sleep(2)

# 2) Same valve within 4s (should NOT refresh recent card)
post("valve", {"state":"open","confidence":0.93}, "VALVE OPEN (2s)")
time.sleep(5)

# 3) Same valve after 5s (>=4s: should refresh)
post("valve", {"state":"open","confidence":0.91}, "VALVE OPEN (5s)")
time.sleep(1)

# 4) Switch object → immediate switch
post("gauge", {"reading_bar":4.14,"confidence":0.90}, "GAUGE 4.14")
time.sleep(5)

# 5) Small change after 5s (same object by ≤0.1 rule → refresh)
post("gauge", {"reading_bar":4.18,"confidence":0.90}, "GAUGE 4.18")
time.sleep(1)

# 6) New ArUco id (immediate switch)
post("aruco", {"id":17,"rvec":[-2.176,0.152,-1.285],"tvec":[0.12,0.03,0.88],"confidence":0.96}, "ARUCO 17")
