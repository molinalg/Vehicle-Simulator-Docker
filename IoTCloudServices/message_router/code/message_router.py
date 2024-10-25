import os, json, time, random, threading
import paho.mqtt.client as mqtt

from telemetry_register_interface import register_telemetry
from vehicle_register_interface import register_vehicle


MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))

EVENTS_TOPIC, STATE_TOPIC, INIT_TOPIC = "/fic/vehicles/+/events", "/fic/vehicles/+/telemetry", "/fic/vehicles/+/request_plate"

index_vehicle = 0
connected_vehicles = {}
available_plates = ["0001BBB", "0002BBB", "0003BBB", "0004BBB","0005BBB",
                    "0006BBB", "0007BBB", "0008BBB", "0009BBB","0010BBB"]

pois = ["Ayuntamiento de Leganes", "Ayuntamiento de Getafe",
        "Ayuntamiento de Alcorcón", "Ayuntamiento de Móstoles",
        "Universidad Carlos III de Madrid - Campus de Leganés",
        "Universidad Carlos III de Madrid - Campus de Getafe",
        "Universidad Carlos III de Madrid - Campus de Puerta de Toledo",
        "Universidad Carlos III de Madrid - Campus de Colmenarejo",
        "Ayuntamiento de Navalcarnero", "Ayuntamiento de Arroyomolinos",
        "Ayuntamiento de Carranque", "Ayuntamiento de Alcalá de Henares",
        "Ayuntamiento de Guadarrama", "Ayuntamiento de la Cabrera",
        "Ayuntamiento de Aranjuez"]

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

def update_json_telemetry(json_file, new_telemetry):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    # Actualiza el diccionario de datos con la nueva telemetría
    new_telemetry = json.loads(new_telemetry)
    data.update(new_telemetry)

    # Guarda los datos actualizados en el archivo JSON
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)


def on_connect(client, userdata, flags, rc):
    print("Connected o subscriber with code ", rc)

    if rc == 0:
        client.subscribe(INIT_TOPIC)
        print("Subscribed to ", INIT_TOPIC)
        client.subscribe(STATE_TOPIC)
        print("Subscribed to ", STATE_TOPIC)
        client.subscribe(EVENTS_TOPIC)
        print("Subscribed to ", EVENTS_TOPIC)


def on_message(client, userdata, msg):
    global index_vehicle, connected_vehicles, available_plates

    topic = msg.topic.split('/')
    if topic[-1] == "request_plate":
        input_data = msg.payload.decode()
        request_data = {"device_id": input_data}
        vehicle_plate = register_vehicle(request_data)

        if vehicle_plate.status_code == 201:
            print("Registro exitoso: {}".format(vehicle_plate.json()))
        elif vehicle_plate.status_code == 500:
            print("Error al insertar un nuevo vehículo: {}".format(vehicle_plate.json()))
        else:
            print("Error: Desconocido ({})".format(vehicle_plate.status_code))

        if vehicle_plate.status_code == 201:
            plate_json = json.dumps({"Plate": vehicle_plate.json()["Plate"]})
            time.sleep(1)
            client.publish("/fic/vehicles/" + msg.payload.decode() +
                           "/config", payload=plate_json, qos=1, retain=False)
            vehicle_plate = vehicle_plate.json()["Plate"]
            print("Publicado", vehicle_plate, "en TOPIC", msg.topic)
            requested_id = connected_vehicles.get(msg.payload.decode())
            if requested_id is None:
                # Comprobando si se han conectado menos de 10 vehículos
                if len(connected_vehicles) < len(available_plates):
                    connected_vehicles[msg.payload.decode()] = {}
                    connected_vehicles[msg.payload.decode()]["Plate"] = vehicle_plate
                    # Inicializamos la ruta como None
                    connected_vehicles[msg.payload.decode()]["Route"] = {}
                    connected_vehicles[msg.payload.decode()]["Route"]["Origin"] = None
                    connected_vehicles[msg.payload.decode()]["Route"]["Destination"] = None
                    index_vehicle += 1
                else:
                    # Publicando un mensaje de error cuando se alcanza el límite de vehículos
                    print("La flota de vehículos ya está totalmente asignada")
                    client.publish("/fic/vehicles/" + msg.payload.decode() + "/config",
                                   payload='{"Plate":"Not Available"}', qos=1, retain=False)

    elif topic[-1] == "telemetry":
        str_received_telemetry = json.loads(msg.payload.decode())
        print("Recibidas telemetrías")
        result = register_telemetry(str_received_telemetry["telemetry"])

        if result.status_code == 201:
            print("Telemetría registrada con éxito: {}".format(result.json()))
        elif result.status_code == 500:
            print("Error al registrar una nueva telemetría: {}".format(result.json()))
        else:
            print("Error: Desconocido ({})".format(result.status_code))

    elif topic[-1] == "events":
        mensaje = msg.payload.decode('utf-8')
        mensaje = json.loads(mensaje)
        if mensaje["Event"] == "Route Completed":
            for id, datos_vehiculo in connected_vehicles.items():
                if datos_vehiculo["Plate"] == mensaje["Plate"]:
                    connected_vehicles[id]["Route"]["Origin"] = None
                    connected_vehicles[id]["Route"]["Destination"] = None
                    break
            print("El vehículo con matrícula {} ha completado una ruta".format(mensaje["Plate"]))


def assign_route():
    """Función para asignar rutas a los vehículos"""
    global connected_vehicles

    while True:
        if len(connected_vehicles) > 0:
            # Se escoge uno de los vehículos conectados
            vehiculos = list(connected_vehicles.keys())
            vehiculo_seleccionado = random.choice(vehiculos)

            # Se sigue buscando si el seleccionado ya tiene una ruta
            while connected_vehicles[vehiculo_seleccionado]["Route"]["Origin"] != None and len(vehiculos) > 0:
                vehiculo_seleccionado = random.choice(vehiculos)
                vehiculos.remove(vehiculo_seleccionado)

            # Se escoge una ruta aleatoriamente si se ha encontrado un vehiculo apto
            if connected_vehicles[vehiculo_seleccionado]["Route"]["Origin"] == None:
                # Primero origen de ruta
                origen = random.choice(pois)
                # Después el destino
                destino = random.choice(pois)
                # Se buscan nuevos destinos hasta que uno no es igual al origen
                while destino == origen:
                    destino = random.choice(pois)

                # Creamos el json y enviamos la ruta al vehículo
                route = {"Origin": origen, "Destination": destino}
                ROUTES_TOPIC = "/fic/vehicles/" + vehiculo_seleccionado + "/routes"
                client.publish(ROUTES_TOPIC, payload=json.dumps(route), qos=1, retain=False)

                # Se actualiza la lista de vehículos con la ruta nueva
                connected_vehicles[vehiculo_seleccionado]["Route"]["Origin"] = origen
                connected_vehicles[vehiculo_seleccionado]["Route"]["Destination"] = destino

                print("Ruta asignada al vehículo con matrícula {plate}: {route}".format(plate=connected_vehicles[vehiculo_seleccionado]["Plate"],route=route))
                # Se espera 60 segundos antes de asignar otra
                time.sleep(60)

def establecer_cliente():
    global client

    client.username_pw_set(username="fic_server", password="fic_password")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT, 60)

    client.loop_forever()

if __name__ == "__main__":
    t0 = threading.Thread(target=establecer_cliente, daemon=True)
    t0.start()
    t1 = threading.Thread(target=assign_route, daemon=True)
    t1.start()
    t0.join()
    t1.join()