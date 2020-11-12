#!/usr/bin/env python3
import argparse
from datetime import timedelta
import requests
import random
import datetime
from pymongo import MongoClient
from credentials import cluster_url, password, username

parser = argparse.ArgumentParser()
parser.add_argument("command", help="'fill' to fill DB with dummy values, 'clean' to clean db", type=str, choices=["fill", "clean"])
args = parser.parse_args()

client = MongoClient(f"mongodb+srv://{username}:{password}@{cluster_url}/default?retryWrites=true&w=majority")

# Get database from client
db = client.db

if args.command == "clean":
    # Drop collections "devices", "measures" and "alerts"
    db.devices.drop()
    db.measures.drop()
    db.alerts.drop()

    # Close connection to MongoDB Server
    client.close()

    print("Database cleaned.")

elif args.command == "fill":
    # Add 3 devices and get their device_id's
    device_ids = []
    print("Adding device n°1...")
    device_ids.append(requests.post("https://82.64.33.131:5000/api/devices/", json={"name": "Salle 3R80", "color": "#FF0000"}, verify=False).json()["device_id"])

    print("Adding device n°2...")
    device_ids.append(requests.post("https://82.64.33.131:5000/api/devices/", json={"name": "Salle 3R82", "color": "#00FF00"}, verify=False).json()["device_id"])

    print("Adding device n°3...")
    device_ids.append(requests.post("https://82.64.33.131:5000/api/devices/", json={"name": "Salle réseau", "color": "#0000FF"}, verify=False).json()["device_id"])
    print("All devices added.")

    # Add points of data for each device
    print("Adding measures...")

    for device_id in device_ids:
        measures = []
        measure = {
            "temperature": 38.0,
            "pressure": 1002.0,
            "humidity": 29.0,
            "created": datetime.datetime(2020, 10, 25, 12, 0, 0),
            "device_id": device_id
        }

        # Add first value
        measures.append(measure.copy())

        # Add lots of values
        for i in range(200):
            # Randomize values
            measure["temperature"] += round(random.uniform(-0.2, 0.2), 1)
            measure["pressure"] += round(random.uniform(-0.4, 0.4), 1)
            measure["humidity"] += round(random.uniform(-0.1, 0.1), 1)

            # Add 5 seconds interval to measure time
            measure["created"] += datetime.timedelta(seconds=5)

            measures.append(measure.copy())

        # Once we have all values, add them all to our collection
        db.measures.insert_many(measures)

    print("Measures added.")

    print("Adding alerts...")
    requests.post("https://82.64.33.131:5000/api/alerts/", json={"code": 1, "message": "Temperature exceeds 30°C", "device_id": device_ids[0]}, verify=False)
    requests.post("https://82.64.33.131:5000/api/alerts/", json={"code": 2, "message": "Temperature sensor malfunction", "device_id": device_ids[1]}, verify=False)
    print("Alerts added.")
