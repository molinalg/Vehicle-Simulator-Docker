import os,time
from flask import Flask, request
from flask_cors import CORS
from telemetry_db_manager import TelemetryDBManager

app = Flask(__name__)
CORS(app)
@app.route('/telemetry/register/', methods=['POST'])
def register():
    global db_manager
    params = request.get_json()

    completed = db_manager.register_new_telemetry(params)

    if type(completed) == bool:
        return {"result": "Telemetry registered"}, 201
    else:
        return completed, 500
@app.route('/telemetry/vehicle/detailed_info/', methods=['GET'])
def vehicle_detailed_info():
    result = db_manager.get_vehicle_detailed_info(request.args.get)

    if result["Error Message"] is None:
        return result, 201
    else:
        return result, 500
    return vehicles

@app.route('/telemetry/vehicle/positions/', methods=['GET'])
def vehicle_positions():
    result = db_manager.get_vehicles_last_position()

    if result["Error Message"] is None:
        return result, 201
    else:
        return result, 500

if __name__ == '__main__':
    time.sleep(20)
    db_manager = TelemetryDBManager()
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    app.run(host=HOST, port=PORT)