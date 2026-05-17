from flask import Flask, request, jsonify
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Files
DAILY_FILE = 'daily.txt'
LIFETIME_FILE = 'lifetime.txt'
USED_FILE = 'used_keys.txt'   # HWID lock ke liye

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
            k, h, t = line.strip().split('|')
            if k == key:
                # Daily key hai to expiry check
                if key.startswith("WINT0X-DAILY"):
                    try:
                        old_time = datetime.fromisoformat(t)
                        if datetime.now() - old_time > timedelta(days=1):
                            return False  # expired, allow new use? (optional)
                    except:
                        pass
                if h != hwid:
                    return True  # dusre device pe locked
    return False

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    key = data.get('key', '').strip()
    hwid = data.get('hwid', '')

    if not key or not hwid:
        return jsonify({"status": "invalid", "message": "Invalid Request"})

    # Check if already used on another device
    if is_key_used(key, hwid):
        return jsonify({"status": "invalid", "message": "Key already used on another device"})

    daily_keys = load_keys(DAILY_FILE)
    lifetime_keys = load_keys(LIFETIME_FILE)

    if key in lifetime_keys:
        # First time use lock
        save_used_key(key, hwid)
        return jsonify({"status": "valid", "message": "Lifetime Key Activated ✅", "type": "lifetime"})

    elif key in daily_keys:
        save_used_key(key, hwid)
        return jsonify({"status": "valid", "message": "Daily Key Activated (24 Hours) ✅", "type": "daily"})

    return jsonify({"status": "invalid", "message": "Key Invalid or Expired"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)