#!/usr/bin/env python3
from os import device_encoding
from types import MethodDescriptorType
from pymongo import MongoClient
from credentials import username, password, cluster_url
from datetime import datetime
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS

# Connect to database
client = MongoClient(f"mongodb+srv://{username}:{password}@{cluster_url}/default?retryWrites=true&w=majority")

# Get database from client
db = client.db

# Create Flask app
app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "The API is online. Contact via /api/(devices|measures|alerts|stats)/"

# Route that manages devices
@app.route("/api/devices/", methods=["GET", "POST"])
def api_devices():
    if request.method == "GET":
        return jsonify(list(db.devices.find(projection={"_id": False})))
    else: # POST
        try:
            # Get json from request
            request_json = request.get_json(force=True)
            print(f"Request received : {request_json}")

            # Extract info from json
            device = {
                "name": request_json["name"],
                "color": request_json["color"],
                "device_id": str(uuid.uuid4()), # Generate UUID for the device
                "created": datetime.today()
            }

            # Insert device to "devices" collection
            db.devices.insert_one(device)

            # Return JSON with UUID
            return jsonify({"device_id": device["device_id"]})
        except KeyError:
            return jsonify({"message": "Missing key in JSON : Need fields 'name' and 'color'", "success": False}), 400
        except ValueError:
            return jsonify({"message": "Invalid JSON format", "success": False}), 400

# Function that returns a dict containing all devices, in which their measures can be found (in devices[x]["measures"])
def get_devices_with_measures():
    # Get list of all devices without ObjectId
    devices = list(db.devices.find(projection={"_id": False}))

    # Get list of all measures without ObjectId
    measures = list(db.measures.find(projection={"_id": False}))

    # For each device, create an empty array of measures
    for device in devices:
        device["measures"] = []

    # For each measure, put it in the corresponding device
    for measure in measures:
        next(device for device in devices if device["device_id"] == measure["device_id"])["measures"].append(
            # Append "measure" dict, without the key "device_id" as it would be redundant
            {key:measure[key] for key in measure if key != "device_id"}
        )

    return devices

# Route that manages device-specific measures
@app.route("/api/measures/<device_id>", methods=["GET"])
def api_measures_device_id(device_id):
    # Get all devices with corresponding measures
    devices = get_devices_with_measures()

    # Get only the specified device
    device = next(device for device in devices if device["device_id"] == device_id)

    # Calculate stats
    average_temperature = 0
    average_humidity = 0
    average_pressure = 0

    for measure in device["measures"]:
        average_temperature += measure["temperature"]
        average_humidity += measure["humidity"]
        average_pressure += measure["pressure"]

    average_temperature /= len(device["measures"])
    average_humidity /= len(device["measures"])
    average_pressure /= len(device["measures"])

    # Add stats to JSON
    device["average_temperature"] = average_temperature
    device["average_humidity"] = average_humidity
    device["average_pressure"] = average_pressure

    # Only get measures of our device_id
    try:
        return device
    except StopIteration:
        return jsonify({"message": "Device does not exist", "success": False}), 400

# Route that manages measures
@app.route("/api/measures/", methods=["GET", "POST"])
def api_measures():
    if request.method == "GET":
        # Get number of "last x measures"
        last = request.args.get("last", type=int)

        # Get dates "from" and "to"
        date_from = request.args.get("from", type=str)
        date_to = request.args.get("to", type=str)

        # Get all measures
        devices = get_devices_with_measures()

        # If the "last" argument is specified, keep only the last n measures of each device
        if last:
            for device in devices:
                device["measures"] = device["measures"][-last:]

        # If the "from" and "to" arguments are supplied
        elif date_from and date_to:
            try:
                # Convert to Python datetime
                date_from = datetime.fromisoformat(date_from)
                date_to = datetime.fromisoformat(date_to)
            except ValueError:
                return jsonify({"message": "Invalid date format for arguments 'from' and 'to' (ISO expected)", "success": False}), 400

            # For each measure, remove it if it is not between "date_from" and "date_to"
            for device in devices:
                device["measures"] = [measure for measure in device["measures"] if date_from < measure["created"] < date_to]

        return jsonify({"devices": devices})
    else: # POST
        try:
            # Get json from request
            request_json = request.get_json(force=True)
            print(f"Request received : {request_json}")

            # Check if device actually exists
            # TODO Delete line to optimize
            if db.devices.find_one({"device_id": request_json["device_id"]}) is None:
                print("Error : Device with that device_id does not exist, register with POST /api/devices/")
                return jsonify({"message": "Error : Device with that device_id does not exist, register with POST /api/devices/", "success": False}), 400

            # Extract info from json
            measure = {
                "temperature": request_json["temperature"],
                "pressure": request_json["pressure"],
                "humidity": request_json["humidity"],
                "created": datetime.today(),
                "device_id": request_json["device_id"]
            }

            # Insert measure to "measures" collection
            db.measures.insert_one(measure)

            # Return message + status code 200
            return jsonify({"message": "Measure added successfully", "success": True})
        except KeyError:
            print("JSON needs fields 'temperature', 'pressure', 'humidity', 'device_id'", "success")
            return jsonify({"message": "JSON needs fields 'temperature', 'pressure', 'humidity', 'device_id'", "success": False}), 400
        except ValueError:
            print("Invalid JSON format")
            return jsonify({"message": "Invalid JSON format", "success": False}), 400

# Route that manages alerts
@app.route("/api/alerts/", methods=["GET", "POST"])
def api_alerts():
    if request.method == "GET":
        # Get list of all alerts without ObjectId
        alerts = list(db.alerts.find(projection={"_id": False}))

        # Get list of all devices without ObjectId
        devices = list(db.devices.find(projection={"_id": False}))

        # For each alert, get corresponding device's name
        for alert in alerts:
            alert["device_name"] = next(device["name"] for device in devices if device["device_id"] == alert["device_id"])

        return jsonify({"alerts": alerts})
    else: # POST
        try:
            # Get json from request
            request_json = request.get_json(force=True)
            print(f"Request received : {request_json}")

            # Check if device actually exists
            # TODO Delete line to optimize
            if db.devices.find_one({"device_id": request_json["device_id"]}) is None:
                return "Error : Device with that device_id does not exist, register with POST /api/devices/", 400

            # Extract info from json
            alert = {
                "device_id": request_json["device_id"],
                "code": request_json["code"],
                "message": request_json["message"]
            }

            # Insert alert to "alerts" collection
            db.alerts.insert_one(alert)

            # Return message + status code 200
            return jsonify({"message": "Alert added successfully", "success": True})
        except KeyError:
            return jsonify({"message": "JSON needs fields 'device_id', 'code', 'message'", "success": False}), 400
        except ValueError:
            return jsonify({"message": "Invalid JSON format", "success": False}), 400

# Route that manages global stats
@app.route("/api/stats/", methods=["GET", "POST"])
def api_stats():
    # Get list of all measures without ObjectId
    measures = list(db.measures.find(projection={"_id": False}))

    # Get list of all devices without ObjectId
    devices = list(db.devices.find(projection={"_id": False}))

    average_temperature = 0
    average_humidity = 0
    average_pressure = 0

    for measure in measures:
        average_temperature += measure["temperature"]
        average_humidity += measure["humidity"]
        average_pressure += measure["pressure"]

    average_temperature /= len(measures)
    average_humidity /= len(measures)
    average_pressure /= len(measures)

    stats = {
        "total_devices": len(devices),
        "average_temperature": average_temperature,
        "average_humidity": average_humidity,
        "average_pressure": average_pressure
    }

    return jsonify(stats)


# Route that returns "database" formatted list of measures
@app.route("/api/database/", methods=["GET"])
def api_database():
    # List of all measures
    database = []

    # Get all devices with associated measures
    devices = get_devices_with_measures()

    # Get measures of devices, with name of message
    for device in devices:
        for measure in device["measures"]:
            database.append({**measure, "name": device["name"]})

    return jsonify(database)

app.run("0.0.0.0", 5000, ssl_context=("cert.pem", "key.pem"))
# app.run("127.0.0.1", 80, debug=True)
