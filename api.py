from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import bcrypt
import os

app = Flask(__name__)

# Load Firebase Admin SDK JSON key (keep this file private & server-only!)
cred_path = os.environ.get("FIREBASE_CRED", "parkingpulse-c143b-firebase-adminsdk-fbsvc-72445d5bb9.json")
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

# ----------- ROUTES -----------

@app.route("/api/create-user", methods=["POST"])
def create_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "User")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    db.collection("users").add({
        "username": username,
        "password": hashed_pw,
        "role": role.capitalize()
    })
    return jsonify({"message": "User created"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user_docs = db.collection("users").where("username", "==", username).get()
    if not user_docs:
        return jsonify({"error": "Invalid credentials"}), 401

    user_data = user_docs[0].to_dict()
    if bcrypt.checkpw(password.encode(), user_data["password"].encode()):
        return jsonify({
            "username": username,
            "role": user_data["role"]
        }), 200
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/log-vehicle", methods=["POST"])
def log_vehicle():
    data = request.json
    vehicle_id = str(data.get("vehicle_id"))
    features = data.get("features", [])

    if not vehicle_id or not features:
        return jsonify({"error": "Missing vehicle_id or features"}), 400

    db.collection("vehicles").document(vehicle_id).set({
        "vehicle_id": vehicle_id,
        "timestamp": datetime.now().isoformat(),
        "feature_vector": features
    })
    return jsonify({"message": "Vehicle logged"}), 201


@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    vehicles = db.collection("vehicles").order_by("timestamp", direction="DESCENDING").stream()
    vehicle_data = [{
        "vehicle_id": doc.to_dict().get("vehicle_id"),
        "timestamp": doc.to_dict().get("timestamp")
    } for doc in vehicles]
    return jsonify(vehicle_data), 200


@app.route("/api/vehicles", methods=["DELETE"])
def delete_vehicles():
    docs = db.collection("vehicles").stream()
    for doc in docs:
        db.collection("vehicles").document(doc.id).delete()
    return jsonify({"message": "All vehicles deleted"}), 200

# ----------- START -----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
