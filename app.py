from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import requests
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Config ---
ADMIN_USERNAME = "RTX"
ADMIN_PASSWORD = "3050"

JSONBIN_API_KEY = "$2a$10$qpbJqpXhVrqPgWBQgq4Rmu7BWx/WcNLkrObn5UUfpYk1/eibVKDFq"
BIN_ID = "685791978a456b7966b31c51"
HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

# --- JSONBin Helpers ---
def load_data():
    try:
        r = requests.get(f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest", headers=HEADERS)
        return r.json()['record'] if r.status_code == 200 else {}
    except Exception as e:
        print("Load Error:", e)
        return {}

def save_data(data):
    try:
        r = requests.put(f"https://api.jsonbin.io/v3/b/{BIN_ID}", headers=HEADERS, json=data)
        return r.status_code == 200
    except Exception as e:
        print("Save Error:", e)
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

@app.route("/get_users", methods=["POST"])
def get_users():
    data = load_data()
    category = request.form["category"]
    return jsonify(data.get(category, []))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
