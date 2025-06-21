from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# JSONBin API Config
JSONBIN_API_KEY = "$2a$10$vm/bHfwrLhw7wBCU4c/WeuiaKZy8mbLZt06WK3x6HpnEI9IPqyQFO"
BIN_ID = "68567a118960c979a5ae5135"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

def load_data():
    try:
        res = requests.get(f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest", headers=HEADERS)
        if res.status_code == 200:
            return res.json().get("record", {})
        return {}
    except Exception as e:
        print("Load Error:", e)
        return {}

def save_data(data):
    try:
        res = requests.put(f"https://api.jsonbin.io/v3/b/{BIN_ID}", headers=HEADERS, json=data)
        return res.status_code == 200
    except Exception as e:
        print("Save Error:", e)
        return False

@app.route("/client_login", methods=["POST"])
def client_login():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    password = request.form["password"]
    client_hwid = request.form["hwid"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    for user in data[category]:
        if user["Username"] == username and user["Password"] == password:
            if user["Status"] != "Active":
                return jsonify({"status": "error", "message": "Account paused"})

            # HWID bind logic
            if user["HWID"] in [None, ""]:
                user["HWID"] = client_hwid
                if save_data(data):
                    return jsonify({"status": "success", "message": "HWID bound successfully. Login success"})
                else:
                    return jsonify({"status": "error", "message": "Failed to bind HWID"})

            if user["HWID"] != client_hwid:
                return jsonify({"status": "error", "message": "HWID mismatch. Access denied"})

            return jsonify({"status": "success", "message": "Login success"})

    return jsonify({"status": "error", "message": "Invalid username or password"})

# For testing user creation from here
@app.route("/add_user", methods=["POST"])
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
        "Status": "Active",
        "Expiry": expiry,
        "CreatedAt": datetime.today().strftime("%Y-%m-%d")
    })

    if save_data(data):
        return jsonify({"status": "success", "message": "User added successfully"})
    return jsonify({"status": "error", "message": "Failed to add user"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
