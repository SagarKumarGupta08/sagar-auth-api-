from flask import Flask, request, jsonify, render_template, session, redirect, url_for import requests from datetime import datetime import os

app = Flask(name) app.secret_key = os.urandom(24)

Admin credentials

ADMIN_USERNAME = "RTX" ADMIN_PASSWORD = "3050"

JSONBin Config

JSONBIN_API_KEY = "$2a$10$vm/bHfwrLhw7wBCU4c/WeuiaKZy8mbLZt06WK3x6HpnEI9IPqyQFO" BIN_ID = "6856f4d78a456b7966b2c840"

HEADERS = { "Content-Type": "application/json", "X-Master-Key": JSONBIN_API_KEY }

---------------------------- Utility ----------------------------

def load_data(): try: res = requests.get(f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest", headers=HEADERS) if res.status_code == 200: return res.json().get("record", {}) return {} except Exception as e: print("Load Error:", e) return {}

def save_data(data): try: res = requests.put(f"https://api.jsonbin.io/v3/b/{BIN_ID}", headers=HEADERS, json=data) return res.status_code == 200 except Exception as e: print("Save Error:", e) return False

---------------------------- Routes ----------------------------

@app.route("/") def home(): if session.get("logged_in"): return render_template("index.html") return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"]) def login(): if request.method == "POST": username = request.form.get("username") password = request.form.get("password") if username == ADMIN_USERNAME and password == ADMIN_PASSWORD: session["logged_in"] = True return redirect(url_for("home")) else: return render_template("login.html", error="Invalid credentials") return render_template("login.html")

@app.route("/logout") def logout(): session.pop("logged_in", None) return redirect(url_for("login"))

@app.route("/add_user", methods=["POST"]) def add_user(): data = load_data() category = request.form["category"] username = request.form["username"] password = request.form["password"] expiry = request.form["expiry"]

if category not in data:
    data[category] = []

if any(u["Username"] == username for u in data[category]):
    return jsonify({"status": "error", "message": "Username already exists"})

data[category].append({
    "Username": username,
    "Password": password,
    "HWID": None,
    "Status": "Active",
    "Expiry": expiry,
    "CreatedAt": datetime.today().strftime("%Y-%m-%d")
})

if save_data(data):
    return jsonify({"status": "success", "message": "User added successfully"})
return jsonify({"status": "error", "message": "Failed to add user"})

@app.route("/delete_user", methods=["POST"]) def delete_user(): data = load_data() category = request.form["category"] username = request.form["username"]

if category not in data:
    return jsonify({"status": "error", "message": "Invalid application"})

original_len = len(data[category])
data[category] = [u for u in data[category] if u["Username"] != username]

if len(data[category]) == original_len:
    return jsonify({"status": "error", "message": "User not found"})

if save_data(data):
    return jsonify({"status": "success", "message": "User deleted"})
return jsonify({"status": "error", "message": "Failed to update data"})

@app.route("/pause_user", methods=["POST"]) def pause_user(): data = load_data() category = request.form["category"] username = request.form["username"] action = request.form["action"]

if category not in data:
    return jsonify({"status": "error", "message": "Invalid application"})

for user in data[category]:
    if user["Username"] == username:
        user["HWID"] = None if action == "pause" else ""
        user["Status"] = "Paused" if action == "pause" else "Active"
        if save_data(data):
            return jsonify({"status": "success", "message": f"User {action}d"})
        return jsonify({"status": "error", "message": "Failed to update user"})

return jsonify({"status": "error", "message": "User not found"})

@app.route("/reset_hwid", methods=["POST"]) def reset_hwid(): data = load_data() category = request.form["category"] username = request.form["username"]

if category not in data:
    return jsonify({"status": "error", "message": "Invalid application"})

for user in data[category]:
    if user["Username"] == username:
        user["HWID"] = ""
        if save_data(data):
            return jsonify({"status": "success", "message": f"HWID reset for {username}"})
        return jsonify({"status": "error", "message": "Failed to reset HWID"})

return jsonify({"status": "error", "message": "User not found"})

@app.route("/info_user", methods=["POST"]) def info_user(): data = load_data() category = request.form["category"] username = request.form["username"]

if category not in data:
    return jsonify({"status": "error", "message": "Invalid application"})

for user in data[category]:
    if user["Username"] == username:
        return jsonify({"status": "success", "data": user})

return jsonify({"status": "error", "message": "User not found"})

@app.route("/get_users", methods=["POST"]) def get_users(): data = load_data() category = request.form["category"] return jsonify(data.get(category, []))

@app.route("/send_message", methods=["POST"]) def send_message(): data = load_data() category = request.form["category"] username = request.form["username"] message = request.form["message"]

if category not in data:
    return jsonify({"status": "error", "message": "Invalid application"})

for user in data[category]:
    if user["Username"] == username:
        user["Message"] = message
        if save_data(data):
            return jsonify({"status": "success", "message": f"Message sent to {username}"})
        return jsonify({"status": "error", "message": "Failed to send message"})

return jsonify({"status": "error", "message": "User not found"})

@app.route("/client_login", methods=["POST"]) def client_login(): data = load_data() category = request.form["category"] username = request.form["username"] password = request.form["password"] hwid = request.form["hwid"]

if category not in data:
    return jsonify({"status": "error", "message": "Invalid application"})

for user in data[category]:
    if user["Username"] == username and user["Password"] == password:
        if user["Status"] != "Active":
            return jsonify({"status": "error", "message": "Account paused"})

        if user["HWID"] in [None, ""]:
            user["HWID"] = hwid
            save_data(data)
        elif user["HWID"] != hwid:
            return jsonify({"status": "error", "message": "HWID mismatch"})

        msg = user.get("Message", "")
        user["Message"] = ""
        save_data(data)

        return jsonify({"status": "success", "message": "Login success", "popup": msg})

return jsonify({"status": "error", "message": "Invalid credentials"})

---------------------------- Main ----------------------------

if name == "main": app.run(host="0.0.0.0", port=5000, debug=True)

