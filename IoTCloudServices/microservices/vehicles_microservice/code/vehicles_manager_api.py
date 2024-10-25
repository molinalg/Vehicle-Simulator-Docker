import os,time
from flask import Flask, request
from flask_cors import CORS
from vehicles_db_manager import VehicleDBManager

app = Flask(__name__)
CORS(app)
@app.route('/vehicles/register/', methods=['POST'])
def register():
    global db_manager
    params = request.get_json()
    vehicle_id = params.get('device_id')

    plate = db_manager.register_new_vehicle(vehicle_id)

    if plate:
        return {"Plate": plate}, 201
    else:
        return {"result": "error inserting a new vehicle"}, 500
@app.route('/vehicles/retrieve/', methods=['GET'])
def get_active_vehicles():
    vehicles = db_manager.get_active_vehicles()
    return vehicles

if __name__ == '__main__':
    time.sleep(20)
    db_manager = VehicleDBManager()
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    app.run(host=HOST, port=PORT)