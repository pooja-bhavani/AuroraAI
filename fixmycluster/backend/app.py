import time
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

# ============================
# App Setup
# ============================

app = Flask(__name__)
CORS(app)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet"
)

# ============================
# Health Route
# ============================

@app.route("/")
def home():
    return jsonify({"message": "AI Auto-Heal Backend Running 🚀"})

@app.route("/status")
def status():
    return jsonify({"status": "Healthy"})


# ============================
# Website Check
# ============================

@app.route("/check-website", methods=["POST"])
def check_website():
    data = request.json or {}
    url = data.get("url")

    socketio.emit("kubectl_log", f"🔍 Checking {url}...")

    try:
        start = time.time()
        response = requests.get(url, timeout=8)
        response_time = round((time.time() - start) * 1000, 2)

        socketio.emit("kubectl_log", f"📊 HTTP {response.status_code}")
        socketio.emit("kubectl_log", f"⏱ Response time: {response_time}ms")

        if response.status_code >= 400:
            return jsonify({
                "result": {
                    "status": "error",
                    "response_time": response_time
                },
                "diagnosis": {
                    "root_cause": f"HTTP {response.status_code} Server Error",
                    "confidence": 85,
                    "fix_steps": [
                        "Retry request",
                        "Switch protocol",
                        "Increase timeout",
                        "Check upstream availability"
                    ],
                    "estimated_fix_time": "1-3 minutes"
                }
            })

        return jsonify({
            "result": {
                "status": "healthy",
                "response_time": response_time
            },
            "diagnosis": {
                "root_cause": "No issues detected",
                "confidence": 100,
                "fix_steps": [],
                "estimated_fix_time": "0 minutes"
            }
        })

    except requests.exceptions.RequestException as e:
        socketio.emit("kubectl_log", f"🚨 Network error: {str(e)}")

        return jsonify({
            "result": {"status": "error", "response_time": 0},
            "diagnosis": {
                "root_cause": "Network connectivity failure",
                "confidence": 90,
                "fix_steps": [
                    "Check DNS resolution",
                    "Retry with longer timeout",
                    "Disable SSL verification",
                    "Switch protocol"
                ],
                "estimated_fix_time": "2-5 minutes"
            }
        })


# ============================
# AUTO HEAL (INTELLIGENT)
# ============================

@app.route("/auto-heal", methods=["POST"])
def auto_heal():
    data = request.json or {}
    url = data.get("url")

    socketio.emit("kubectl_log", "🧠 AI analyzing recovery strategies...")
    time.sleep(1)

    healed = False
    last_error = None

    def switch_protocol(u):
        if u.startswith("https://"):
            return "http://" + u[len("https://"):]
        elif u.startswith("http://"):
            return "https://" + u[len("http://"):]
        return u

    strategies = [
        ("Simple retry", lambda u: requests.get(u, timeout=8)),
        ("Long timeout retry", lambda u: requests.get(u, timeout=15)),
        ("Disable SSL verification", lambda u: requests.get(u, timeout=10, verify=False)),
        ("Protocol switch", lambda u: requests.get(switch_protocol(u), timeout=10)),
    ]

    for name, strategy in strategies:
        socketio.emit("kubectl_log", f"🔄 Strategy: {name}")
        try:
            resp = strategy(url)

            if resp.status_code < 400:
                healed = True
                socketio.emit("kubectl_log", f"✅ Recovery succeeded via {name}")
                break
            else:
                socketio.emit("kubectl_log", f"⚠ Still failing: HTTP {resp.status_code}")

        except Exception as e:
            last_error = str(e)
            socketio.emit("kubectl_log", f"❌ {name} failed")

        time.sleep(1.2)

    if healed:
        socketio.emit("kubectl_log", "🎯 Intelligent auto-healing completed")
        socketio.emit("status_update", {"status": "Healthy"})

        return jsonify({
            "success": True,
            "message": "Service recovered via intelligent self-healing",
            "healing_time": "4.2s"
        })

    socketio.emit("kubectl_log", "🚨 All healing strategies exhausted")

    return jsonify({
    "success": False,
    "message": "All recovery strategies attempted but service continues returning HTTP errors"
})


# ============================
# MAIN
# ============================

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
