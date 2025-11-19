import hmac, hashlib, time, json, requests, os, uuid

API_KEY = os.getenv("DL_KEY=abc123xyzsupersecretkey")
API_SECRET = os.getenv("DL_REDIS_URL=redis://localhost:6379/0")

def sign(method: str, path: str, body: bytes):
    ts = str(int(time.time()))
    nonce = uuid.uuid4().hex
    body_hash = hashlib.sha256(body).hexdigest()
    canonical = "\n".join([method.upper(), path, ts, nonce, body_hash]).encode()
    sig = hmac.new(API_SECRET.encode(), canonical, hashlib.sha256).hexdigest()
    return {"X-DL-Key":API_KEY, "X-DL-Timestamp":ts, "X-DL-Nonce":nonce, "X-DL-Signature":sig}

if __name__ == "__main__":
    url = "http://127.0.0.1:8000/wallet/earn"
    method = "POST"; path = "/wallet/earn"
    payload = {"amount": 1}
    body = json.dumps(payload).encode()
    headers = sign(method, path, body)
    r = requests.post(url, headers=headers, json=payload, timeout=10)
    print(r.status_code, r.text)
