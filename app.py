from flask import Flask, request, jsonify
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# ==================== ALL TOOLS FILES ====================
FILES = {
    "promochecker": "promochecker.txt",
    "tokenhumanizer": "tokenhumanizer.txt",
    "tokenchecker": "tokenchecker.txt",
    "multitokenmanager": "multitokenmanager.txt"
}

USED_FILE = "used_keys.txt"

def load_keys(tool):
    filename = FILES.get(tool.lower())
    if not filename or not os.path.exists(filename):
        return set()
    with open(filename, "r") as f:
        return {line.strip() for line in f if line.strip()}

def is_key_valid(key, hwid, tool):
    if not os.path.exists(USED_FILE):
        return True

    with open(USED_FILE, "r") as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) < 4:
                continue
            k, h, exp, t = parts
            if k == key:
                try:
                    if t == "daily":
                        expiry = datetime.fromisoformat(exp)
                        if datetime.now() > expiry:
                            return False
                    if h != hwid:
                        return False
                    return True
                except:
                    return False
    return True

def save_used_key(key, hwid, key_type):
    expiry = (datetime.now() + timedelta(hours=24)).isoformat() if key_type == "daily" else "lifetime"
    with open(USED_FILE, "a") as f:
        f.write(f"{key}|{hwid}|{expiry}|{key_type}\n")

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    key = data.get('key', '').strip()
    hwid = data.get('hwid', '')
    tool = data.get('tool', '').lower()

    if not key or not hwid or tool not in FILES:
        return jsonify({"status": "invalid", "message": "Invalid Request"})

    all_keys = load_keys(tool)
    if not all_keys:
        return jsonify({"status": "invalid", "message": "No keys configured for this tool"})

    key_type = "lifetime" if "life" in key.lower() else "daily"

    if key not in all_keys:
        return jsonify({"status": "invalid", "message": "Key Invalid or Expired"})

    if not is_key_valid(key, hwid, tool):
        return jsonify({"status": "invalid", "message": "Key Expired or Used on Another Device"})

    # First time HWID lock
    if not any(key in line for line in open(USED_FILE, 'r')) if os.path.exists(USED_FILE) else True:
        save_used_key(key, hwid, key_type)

    return jsonify({
        "status": "valid", 
        "message": f"{key_type.capitalize()} Key Activated ✅",
        "type": key_type
    })

@app.route('/')
def home():
    return "<h1>Wintox Tools Server Running ✅ | Multi Tool Support</h1>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)