from flask import Flask, request, jsonify
import os
from datetime import datetime, timedelta

app = Flask(__name__)

DAILY_FILE = 'daily.txt'
LIFETIME_FILE = 'lifetime.txt'
USED_FILE = 'used_keys.txt'

def load_keys(filename):
    if not os.path.exists(filename):
        return set()
    with open(filename, 'r') as f:
        return {line.strip() for line in f if line.strip()}

def save_used_key(key, hwid):
    with open(USED_FILE, 'a') as f:
        f.write(f"{key}|{hwid}|{datetime.now().isoformat()}\n")

def is_key_used(key, hwid):
    if not os.path.exists(USED_FILE):
        return False
    with open(USED_FILE, 'r') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) < 3:
                continue
            k, h, t = parts
            if k == key:
                if key.startswith("WINT0X-DAILY"):
                    try:
                        old_time = datetime.fromisoformat(t)
                        if datetime.now() - old_time > timedelta(days=1):
                            return False
                    except:
                        pass
                if h != hwid:
                    return True
    return False

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    key = data.get('key', '').strip()
    hwid = data.get('hwid', '')

    if not key or not hwid:
        return jsonify({"status": "invalid", "message": "Invalid Request"})

    if is_key_used(key, hwid):
        return jsonify({"status": "invalid", "message": "Key already used on another device"})

    daily_keys = load_keys(DAILY_FILE)
    lifetime_keys = load_keys(LIFETIME_FILE)

    if key in lifetime_keys:
        save_used_key(key, hwid)
        return jsonify({"status": "valid", "message": "Lifetime Key Activated ✅", "type": "lifetime"})

    elif key in daily_keys:
        save_used_key(key, hwid)
        return jsonify({"status": "valid", "message": "Daily Key Activated (24 Hours) ✅", "type": "daily"})

    return jsonify({"status": "invalid", "message": "Key Invalid or Expired"})

# ROOT ROUTE - 404 Fix
@app.route('/')
def home():
    return """
    <h1>Wintox Tools Server</h1>
    <p><strong>Status:</strong> Running ✅</p>
    <p><strong>Endpoint:</strong> /verify (POST)</p>
    <p>Wintox Promo Checker Server is Live.</p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)