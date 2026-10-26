from flask import Flask, request, jsonify

from backend.database import (
    init_database,
    save_telemetry,
    get_latest_telemetry,
    get_history,
    get_alerts
)

from backend.alerts import check_occupancy_alert


app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/")
def home():
    return jsonify({
        "message": "API Parqueadero IoT funcionando"
    })


@app.route("/api/v1/telemetry", methods=["POST"])
def receive_telemetry():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No se recibió JSON"
        }), 400

    required_fields = [
        "device_id",
        "timestamp",
        "measurements"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Falta el campo: {field}"
            }), 400

    measurements = data["measurements"]

    required_measurements = [
        "space_id",
        "occupied",
        "distance",
        "parking_duration"
    ]

    for field in required_measurements:
        if field not in measurements:
            return jsonify({
                "error": f"Falta la medición: {field}"
            }), 400

    try:

        save_telemetry(data)

        alert = check_occupancy_alert(data)

        response = {
            "message": "Telemetría recibida correctamente"
        }

        if alert:
            response["alert"] = alert

        return jsonify(response), 201

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


@app.route("/api/v1/parking", methods=["GET"])
def get_parking():

    data = get_latest_telemetry()

    return jsonify(data), 200


@app.route("/api/v1/history", methods=["GET"])
def get_history_data():

    data = get_history()

    return jsonify(data), 200


@app.route("/api/v1/alerts", methods=["GET"])
def get_alerts_data():

    data = get_alerts()

    return jsonify(data), 200


if __name__ == "__main__":

    init_database()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )