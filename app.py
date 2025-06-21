from flask import Flask, request, jsonify, render_template, redirect, session, url_for
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey123"  # Replace in real app or move to env

# ✅ Hardcoded credentials (for testing only)
JSONBIN_API_KEY = "$2a$10$vm/bHfwrLhw7wBCU4c/WeuiaKZy8mbLZt06WK3x6HpnEI9IPqyQFO"
BIN_ID = "68567a118960c979a5ae5135"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

def load_data():
    try:
        url = f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest"
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            return res.json().get("record", {})
        return {}
    except Exception as e:
        print("Error loading:", e)
        return {}

def save_data(data):
    try:
        url = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
        res = requests.put(url, headers=HEADERS, json=data)
        print("Save status:", res.status_code, res.text)
        return res.status_code == 200
    except Exception as e:
        print("Save error:", e)
        return False

def login_required(func):
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET"])
@login_required
def home():
    return render_template("index.html")

@app.route("/add_user", methods=["POST"])
@login_required
def add_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    password = request.form["password"]
    expiry = request.form["expiry"]

    if category not in data:
        data[category] = []

    if any(u["Username"] == username for u in data[category]):
        return jsonify({"status": "error", "message": "Username already exists"})

    data[category].append({
        "Username": username,
        "Password": password,
        "HWID": None,
        "Expiry": expiry,
        "CreatedAt": datetime.today().strftime("%Y-%m-%d")
    })

    if save_data(data):
        return jsonify({"status": "success", "message": "User added"})
    return jsonify({"status": "error", "message": "Failed to save user"})

@app.route("/delete_user", methods=["POST"])
@login_required
def delete_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    users = data[category]
    updated_users = [u for u in users if u["Username"] != username]

    if len(users) == len(updated_users):
        return jsonify({"status": "error", "message": "User not found"})

    data[category] = updated_users
    if save_data(data):
        return jsonify({"status": "success", "message": "User deleted"})
    return jsonify({"status": "error", "message": "Failed to update data"})

@app.route("/pause_user", methods=["POST"])
@login_required
def pause_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    action = request.form["action"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    for u in data[category]:
        if u["Username"] == username:
            u["HWID"] = None if action == "pause" else ""
            if save_data(data):
                return jsonify({"status": "success", "message": f"User {action}d"})
            return jsonify({"status": "error", "message": "Failed to update user"})

    return jsonify({"status": "error", "message": "User not found"})

@app.route("/info_user", methods=["POST"])
@login_required
def info_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    for u in data[category]:
        if u["Username"] == username:
            return jsonify({"status": "success", "data": u})

    return jsonify({"status": "error", "message": "User not found"})

@app.route("/get_users", methods=["POST"])
@login_required
def get_users():
    data = load_data()
    category = request.form["category"]
    return jsonify(data.get(category, []))

@app.route("/reset_hwid", methods=["POST"])
@login_required
def reset_hwid():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    for u in data[category]:
        if u["Username"] == username:
            u["HWID"] = ""
            if save_data(data):
                return jsonify({"status": "success", "message": f"HWID reset for {username}"})
            return jsonify({"status": "error", "message": "Failed to update data"})

    return jsonify({"status": "error", "message": "User not found"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
