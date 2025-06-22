from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import requests
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Configuration ---
ADMIN_USERNAME = "RTX"
ADMIN_PASSWORD = "3050"

JSONBIN_API_KEY = "$2a$10$vm/bHfwrLhw7wBCU4c/WeuiaKZy8mbLZt06WK3x6HpnEI9IPqyQFO"
BIN_ID = "685791978a456b7966b31c51"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY,
    "X-Bin-Versioning": "false"
}

# --- JSONBin Helpers ---
def load_data():
    try:
        r = requests.get(f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest", headers=HEADERS)
        if r.status_code == 200:
            return r.json().get('record', {})
        print("Load error:", r.status_code, r.text)
    except Exception as e:
        print("Error loading:", e)
    return {}

def save_data(data):
    try:
        r = requests.put(
            f"https://api.jsonbin.io/v3/b/{BIN_ID}",
            headers=HEADERS,
            json={"record": data}  # Important for JSONBin v3
        )
        if r.status_code == 200:
            return True
        print("Save error:", r.status_code, r.text)
    except Exception as e:
        print("Error saving:", e)
    return False

# --- Routes ---
@app.route("/")
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect("/")
        return render_template("login.html", error="Invalid Credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect("/")

# --- App Management ---
@app.route("/create_app", methods=["POST"])
def create_app():
    name = request.form["name"]
    data = load_data()
    if name in data:
        return jsonify({"message": "App already exists"})
    data[name] = []
    if save_data(data):
        return jsonify({"message": "App created"})
    return jsonify({"message": "Error creating app"})

@app.route("/get_apps")
def get_apps():
    data = load_data()
    return jsonify([key for key in data if key != "messages"])

# --- User Operations ---
@app.route("/add_user", methods=["POST"])
def add_user():
    category = request.form["category"]
    username = request.form["username"]
    password = request.form["password"]
    expiry = request.form["expiry"]
    data = load_data()
    if category not in data:
        return jsonify({"message": "App not found"})

    if any(u["Username"] == username for u in data[category]):
        return jsonify({"message": "User already exists"})

    data[category].append({
        "Username": username,
        "Password": password,
        "HWID": None,
        "Status": "Active",
        "Expiry": expiry,
        "CreatedAt": datetime.today().strftime("%Y-%m-%d")
    })

    if save_data(data):
        return jsonify({"message": "User created"})
    return jsonify({"message": "Error saving user"})

@app.route("/delete_user", methods=["POST"])
def delete_user():
    category = request.form["category"]
    username = request.form["username"]
    data = load_data()
    if category not in data:
        return jsonify({"message": "App not found"})

    data[category] = [u for u in data[category] if u["Username"] != username]

    if save_data(data):
        return jsonify({"message": "User deleted"})
    return jsonify({"message": "Error deleting user"})

@app.route("/pause_user", methods=["POST"])
def pause_user():
    category = request.form["category"]
    username = request.form["username"]
    action = request.form["action"]
    data = load_data()
    for user in data.get(category, []):
        if user["Username"] == username:
            user["Status"] = "Paused" if action == "pause" else "Active"
            if save_data(data):
                return jsonify({"message": f"User {action}d"})
            return jsonify({"message": "Error saving status"})
    return jsonify({"message": "User not found"})

@app.route("/reset_hwid", methods=["POST"])
def reset_hwid():
    category = request.form["category"]
    username = request.form["username"]
    data = load_data()
    for user in data.get(category, []):
        if user["Username"] == username:
            user["HWID"] = None
            if save_data(data):
                return jsonify({"message": "HWID reset"})
            return jsonify({"message": "Error saving HWID"})
    return jsonify({"message": "User not found"})

@app.route("/info_user", methods=["POST"])
def info_user():
    category = request.form["category"]
    username = request.form["username"]
    data = load_data()
    for user in data.get(category, []):
        if user["Username"] == username:
            return jsonify({"status": "success", "data": user})
    return jsonify({"status": "error", "message": "User not found"})

@app.route("/get_users", methods=["POST"])
def get_users():
    category = request.form["category"]
    data = load_data()
    return jsonify(data.get(category, []))

# --- Messaging ---
@app.route("/send_message", methods=["POST"])
def send_message():
    category = request.form["category"]
    username = request.form["username"]
    message = request.form["message"]
    data = load_data()

    if "messages" not in data:
        data["messages"] = {}

    data["messages"][f"{category}:{username}"] = message

    if save_data(data):
        return jsonify({"message": "Message sent"})
    return jsonify({"message": "Error sending message"})

@app.route("/get_message", methods=["POST"])
def get_message():
    category = request.form["category"]
    username = request.form["username"]
    data = load_data()
    msg = data.get("messages", {}).get(f"{category}:{username}", "")
    return jsonify({"message": msg})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
