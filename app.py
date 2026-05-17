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

def get_key_expiry(key):
    """Daily key ka expiry time return karega"""
    if not os.path.exists(USED_FILE):
        return None
    with open(USED_FILE, 'r') as f:
        for line in f:
            if key in line:
                parts = line.strip().split('|')
                if len(parts) >= 3:
                    try:
                        return datetime.fromisoformat(parts[2])
                    except:
                        return None
    return None

def save_used_key(key, hwid):
    """Daily key ka expiry 24 hours set karega"""
    expiry_time = (datetime.now() + timedelta(hours=24)).isoformat()
    with open(USED_FILE, 'a') as f:
        f.write(f"{key}|{hwid}|{expiry_time}\n")

def is_key_valid(key, hwid):
    if not os.path.exists(USED_FILE):
        return True  # Pehli baar valid

    with open(USED_FILE, 'r') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) < 3:
                continue
            k, h, exp = parts
            if k == key:
                try:
                    expiry = datetime.fromisoformat(exp)
                    if datetime.now() > expiry:
                        return False  # Expired
                    if h != hwid:
                        return False  # Different device
                    return True
                except:
                    return False
    return True

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    key = data.get('key', '').strip()
    hwid = data.get('hwid', '')

    if not key or not hwid:
        return jsonify({"status": "invalid", "message": "Invalid Request"})

    daily_keys = load_keys(DAILY_FILE)
    lifetime_keys = load_keys(LIFETIME_FILE)

    # Lifetime Key
    if key in lifetime_keys:
        return jsonify({"status": "valid", "message": "Lifetime Key Activated ✅", "type": "lifetime"})

    # Daily Key
    if key in daily_keys:
        if is_key_valid(key, hwid):
            # Agar pehli baar hai to expiry set kar do
            if not any(key in line for line in open(USED_FILE, 'r')) if os.path.exists(USED_FILE) else True:
                save_used_key(key, hwid)
            return jsonify({"status": "valid", "message": "Daily Key Activated (24 Hours) ✅", "type": "daily"})
        else:
            return jsonify({"status": "invalid", "message": "Daily Key Expired or Used on Another Device"})

    return jsonify({"status": "invalid", "message": "Key Invalid or Expired"})


@app.route('/')
def home():
    return """
    <h1>Wintox Tools Server</h1>
    <p><strong>Status:</strong> Running ✅</p>
    <p><strong>Endpoint:</strong> /verify</p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)