import time, sys, json, threading, math, random, os, subprocess
from datetime import datetime
import requests
import paho.mqtt.client as mqtt

vehicleControlCommands = None                                       # Comandos extraidos del JSON
currentRouteDetailedSteps = None                                    # Variable para los pasos actuales de una ruta

current_steering, current_speed, current_duration = 0, 0, 0.0       # Valores del comando actual del servomotor
current_light, current_obstacle_distance = 0.0, 0.0                 # Valores de las últimas mediciones de luz y distancia tomadas
current_position = {"latitude": 0.0, "longitude": 0.0}

slowing_down = 0                                                 # Variable para controlar las luces de frenado (0 = deben mantenerse apagadas,
                                                                    # 1 = deben activarse, 2 = deben mantenerse encendidas, 3 = deben desactivarse)

lights_on = None                                                    # Valor que indica si las luces de posicion están encendidas
previous_blinker = False                                            # Valor que indica si el comando anterior encendía intermitentes

# Manejo del estado del botón y del sistema
keep_reading = False                                                # Variable para controlar parones ajenos al botón
sys_state_lock = threading.Lock()                                   # Garantiza el cambio de estado del sistema

google_maps_api_key = "NONE"     # IMPORTANT TO ADD YOU OWN KEY HERE

routes = []                                                         # Variable para almacenar las rutas
frenar = False                                                      # Variable para almacenar si se debe frenar o no

current_leds = json.loads('[{"Color": "White", "Intensity": 0.0, "Blinking": 0},'
                        '{"Color": "White", "Intensity": 0.0, "Blinking": 0},'
                        '{"Color": "Red", "Intensity": 0.0, "Blinking": 0},'
                        '{"Color": "Red", "Intensity": 0.0, "Blinking": 0}]')

count = 100                                                           # Varible para controlar los momentos en los que se hace print de comandos
vehicle_plate = ""                                                    # Variable global para la matrícula del vehículo
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)                # Cliente a utilizar
terminate = False                                                     # Variable para terminar con el hilo de conexión
event_message = ""                                                    # Variable para registrar un nuevo evento

recibida = False                                                      # Variable global para controlar si se debe establecer el evento como completado
enviado = False                                                       # Variable global para no cambiar constantemente la variable evento

def signal_handler() -> None:
    """Función que limpia los puertos y termina el proceso"""
    print("Saliendo")
    sys.exit(0)


def execute_command(command, step) -> None:
    global current_steering, current_speed, current_position
    global slowing_down
    global lights_on
    global previous_blinker
    global count

    if count >= 100:
        #print("Ejecutando el comando: {}".format(command))
        #print("Step: {}".format(step))
        count = 0
    else:
        count += 1

    # Primero se mira si se está frenando
    if current_speed > command["Speed"]:
        # Si lo está se mira si va a activar intermitentes para reiniciar variables en ese caso
        if command["SteeringAngle"] >= 80 and command["SteeringAngle"] <= 100:
            # Se pone de color rojo para frenado o posicion si corresponde
            current_leds[2]["Color"] = "Red"
            current_leds[3]["Color"] = "Red"

            # Se pide que se activen las luces de frenado
            if slowing_down == 0:
                slowing_down = 1
                previous_blinker = False
        else:
            # Se reinician variables
            lights_on = False
            slowing_down = 0
            current_leds[0]["Intensity"] = 0.0
            current_leds[1]["Intensity"] = 0.0
            current_leds[2]["Intensity"] = 0.0
            current_leds[3]["Intensity"] = 0.0
            # Se ponen de color amarillo para el intermitente
            current_leds[2]["Color"] = "Yellow"
            current_leds[3]["Color"] = "Yellow"
            previous_blinker = True

    else:
        if command["SteeringAngle"] >= 80 and command["SteeringAngle"] <= 100:
            # Se pone de color rojo para frenado o posicion si corresponde
            current_leds[2]["Color"] = "Red"
            current_leds[3]["Color"] = "Red"
            # Se pide que se desactiven las luces de frenado si estaban activadas
            if not previous_blinker:
                if slowing_down == 2:
                    slowing_down = 3
        else:
            # Se reinician variables
            lights_on = False
            slowing_down = 0
            current_leds[0]["Intensity"] = 0.0
            current_leds[1]["Intensity"] = 0.0
            current_leds[2]["Intensity"] = 0.0
            current_leds[3]["Intensity"] = 0.0
            # Se ponen de color amarillo para el intermitente
            current_leds[2]["Color"] = "Yellow"
            current_leds[3]["Color"] = "Yellow"
            previous_blinker = True

    current_steering, current_speed = command["SteeringAngle"], command["Speed"]
    time.sleep(command["Time"])
    current_position = step["Destination"]


def vehicle_controller() -> None:
    """Función para controlar la velocidad del motor"""
    global vehicleControlCommands
    global currentRouteDetailedSteps
    global routes
    global event_message
    global recibida
    global enviado

    while True:
        if len(routes) > 0:
            print("Comienzo a ejecutar una ruta")
            origin_address = routes[0]["Origin"]
            destination_address = routes[0]["Destination"]
            routes_manager(origin_address, destination_address)
            #print("Los comandos del vehiculo son: {}".format(vehicleControlCommands))
            i = 0
            while len(vehicleControlCommands) > 0:
                execute_command(vehicleControlCommands[0], currentRouteDetailedSteps[i])
                i += 1
                del vehicleControlCommands[0]
            if len(routes) > 0:
                del routes[0]
        elif len(routes) == 0 and recibida and not enviado:
            event_message = "Route Completed"
            print("Ruta completada")
            enviado = True


def vehicle_stop():
    global vehicleControlCommands
    global currentRouteDetailedSteps
    global current_steering
    global current_speed
    global current_leds
    global current_light
    global current_obstacle_distance
    global lights_on
    global slowing_down
    global terminate

    vehicleControlCommands = []
    currentRouteDetailedSteps = []
    current_steering = 90.0
    current_speed = 0

    current_leds = json.loads('[{"Color": "White", "Intensity": 0.0, "Blinking": 0},'
                              '{"Color": "White", "Intensity": 0.0, "Blinking": 0},'
                              '{"Color": "Red", "Intensity": 0.0, "Blinking": 0},'
                              '{"Color": "Red", "Intensity": 0.0, "Blinking": 0}]')

    current_light = 0.0
    current_obstacle_distance = 0.0
    lights_on = False
    slowing_down = 0

    # Cerramos el programa y desconectamos al cliente
    terminate = True
    client.disconnect()
    signal_handler()


def led_controller() -> None:
    global slowing_down
    global lights_on
    global current_leds
    lights_on = False

    # Tiempo que pasa el intermitente en cada estado del parpadeo
    freq_intermitente = 1/6

    while True:
        # Primero comprobamos si se debe encender un intermitente
        if current_steering > 100:
            # Encendemos intermitente izquierdo
            #print("----------Enciendo intermitente izquierdo----------")
            current_leds[0]["Intensity"] = 0.0
            current_leds[1]["Intensity"] = 0.0
            current_leds[3]["Intensity"] = 0.0
            current_leds[2]["Intensity"] = 100.0
            current_leds[2]["Blinking"] = 1
            time.sleep(1)
            #print("----------Apago intermitente izquierdo----------")
            current_leds[2]["Intensity"] = 0.0
            current_leds[2]["Blinking"] = 0

        elif current_steering < 80:
            # Encendemos el intermitente derecho
            #print("----------Enciendo intermitente derecho----------")
            current_leds[0]["Intensity"] = 0.0
            current_leds[1]["Intensity"] = 0.0
            current_leds[2]["Intensity"] = 0.0
            current_leds[3]["Intensity"] = 100.0
            current_leds[3]["Blinking"] = 1
            time.sleep(1)
            #print("----------Apago intermitente derecho----------")
            current_leds[3]["Intensity"] = 0.0
            current_leds[3]["Blinking"] = 0

        else:
            # Si la iluminación es baja y las luces de posición están apagadas, se aumenta intensidad al 50 en rojo
            if current_light > 2000 and not lights_on:
                #print("----------Enciendo luces de posición----------")
                current_leds[0]["Intensity"] = current_leds[0]["Intensity"] + 100
                current_leds[1]["Intensity"] = current_leds[1]["Intensity"] + 100
                current_leds[2]["Intensity"] = current_leds[2]["Intensity"] + 50
                current_leds[3]["Intensity"] = current_leds[3]["Intensity"] + 50
                lights_on = True

            # Si la iluminación es alta y las luces de posición están encendidas, se disminuye intensidad al 50 en rojo
            elif current_light <= 2000 and lights_on:
                #print("----------Apago luces de posición----------")
                current_leds[0]["Intensity"] = current_leds[0]["Intensity"] - 100
                current_leds[1]["Intensity"] = current_leds[1]["Intensity"] - 100
                current_leds[2]["Intensity"] = current_leds[2]["Intensity"] - 50
                current_leds[3]["Intensity"] = current_leds[3]["Intensity"] - 50
                lights_on = False

            if slowing_down == 1:
                # Si está frenando se aumenta un 50 la actual luz roja trasera
                #print("----------Enciendo luz de frenado----------")
                current_leds[2]["Intensity"] = current_leds[2]["Intensity"] + 50
                current_leds[3]["Intensity"] = current_leds[3]["Intensity"] + 50
                slowing_down = 2

            elif slowing_down == 3:
                # Si no está frenando y antes lo estaba se disminuye un 50 la actual luz roja trasera
                #print("----------Apago luz de frenado----------")
                current_leds[2]["Intensity"] = current_leds[2]["Intensity"] - 50
                current_leds[3]["Intensity"] = current_leds[3]["Intensity"] - 50
                slowing_down = 0

        time.sleep(0.5)


def simulate_ldr():
    global current_light
    # print("Simulando la luz del entorno")
    if current_light > 0.0:
        current_light += random.uniform(-300.0, 300.0)
        if current_light < 0.0:
            current_light = 0.0
    else:
        current_light = random.uniform(0.0, 3000.0)


def simulate_obstacle():
    global current_obstacle_distance
    # print("Simulando la distancia de obstaculos")
    if current_obstacle_distance > 0.0:
        current_obstacle_distance += random.uniform(-5.0, 5.0)
        if current_obstacle_distance < 0.0:
            current_obstacle_distance = 0.0
    else:
        current_obstacle_distance = random.uniform(0.0, 50.0)


def environment_simulator():
    global frenar

    while True:
        simulate_ldr()
        simulate_obstacle()
        if current_obstacle_distance < 10:
            frenar = True
            #print("----------Frenando----------")
        else:
            frenar = False
        #print("La distancia al obstáculo es: {}".format(current_obstacle_distance))
        #print("La luz del entorno es: {}".format(current_light))


def routes_manager(origin_address="Toronto", destination_address="Montreal"):
    global currentRouteDetailedSteps
    global vehicleControlCommands

    # print("Asignando una ruta al vehículo")
    url = "https://maps.googleapis.com/maps/api/directions/json?origin=" + origin_address + "&destination=" + destination_address + "&key=" + google_maps_api_key
    # print("URL: {}".format(url))
    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    current_route = response.text
    #print("La ruta es: {}".format(response.text))
    steps = response.json()["routes"][0]["legs"][0]["steps"]
    # print(steps)
    currentRouteDetailedSteps = get_detailed_steps(steps)
    getCommands()
    #print("He acabado de asignar los comandos al vehículo")


def decode_polyline(polyline_str):
    '''Pass a Google Maps encoded polyline string; returns list of lat/lon pairs'''
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    # Coordinates have variable length when encoded, so just keep
    # track of whether we've hit the end of the string. In each
    # while loop iteration, a single coordinate is decoded.
    while index < len(polyline_str):
        # Gather lat/lon changes, store them in a dictionary to apply them later
        for unit in ['latitude', 'longitude']:
            shift, result = 0, 0

            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break
            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append((lat / 100000.0, lng / 100000.0))

    return coordinates


def distance(p1, p2):
    p1Latitude = p1["latitude"]
    p1Longitude = p1["longitude"]
    p2Latitude = p2["latitude"]
    p2Longitude = p2["longitude"]

    #print("Calculando la distancia entre ({},{}) y ({},{})".format(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"]))
    earth_radius = {"km": 6371.0087714, "mile": 3959}
    result = earth_radius["km"] * math.acos(math.cos((math.radians(p1Latitude))) * math.cos(math.radians(p2Latitude)) * math.cos(math.radians(p2Longitude) - math.radians(p1Longitude)) + math.sin(math.radians(p1Latitude)) * math.sin(math.radians(p2Latitude)))
    #print ("La distancia calculada es:{}".format(result))

    return result


def getCommands():
    global currentRouteDetailedSteps
    global vehicleControlCommands
    steeringAngle: float = 90.0

    vehicleControlCommands = []
    index = 0
    for detailedStep in currentRouteDetailedSteps:
        index += 1
        # print("Generando el comando {} para el paso {}".format(index, detailedStep))
        if (detailedStep["Maneuver"].upper() == "STRAIGHT" or
                    detailedStep["Maneuver"].upper() == "RAMP_LEFT" or
                    detailedStep["Maneuver"].upper() == "RAMP_RIGHT" or
                    detailedStep["Maneuver"].upper() == "MERGE" or
                    detailedStep["Maneuver"].upper() == "MANEUVER_UNSPECIFIED"):
            steeringAngle = 90.0
        if detailedStep["Maneuver"].upper() == "TURN_LEFT":
            steeringAngle = 45.0
        if detailedStep["Maneuver"].upper() == "UTURN_LEFT":
            steeringAngle = 0.0
        if detailedStep["Maneuver"].upper() == "TURN_SHARP_LEFT":
            steeringAngle = 15.0
        if detailedStep["Maneuver"].upper() == "TURN_SLIGHT_LEFT":
            steeringAngle = 60.0
        if detailedStep["Maneuver"].upper() == "TURN_RIGHT":
            steeringAngle = 135.0
        if detailedStep["Maneuver"].upper() == "UTURN_RIGHT":
            steeringAngle = 180.0
        if detailedStep["Maneuver"].upper() == "TURN_SHARP_RIGHT":
            steeringAngle = 105.0
        if detailedStep["Maneuver"].upper() == "TURN_SLIGHT_RIGHT":
            steeringAngle = 150.0

        newCommand = {"SteeringAngle": steeringAngle, "Speed": detailedStep["Speed"], "Time": detailedStep["Time"]}
        vehicleControlCommands.append(newCommand)


def routes_loader(required_route):
    global routes
    global recibida
    route_to_process = json.loads(required_route)
    routes.append(route_to_process)
    recibida = True


def get_detailed_steps(route_steps):
    # print("Detallando la ruta")
    detailedSteps = []
    for step  in route_steps:
        index = 0
        step_distance = step["distance"]["value"]
        # MIRAR LO DE DIVIDIR ENTRE 0
        stepTime = step["duration"]["value"]
        if step_distance == 0 or stepTime == 0:
            continue
        stepSpeed = (step_distance / 1000) / (stepTime / 3600)

        try:
            stepManeuver = step["maneuver"]
        except:
            stepManeuver = "Straight"
        # print("El paso {} de la ruta empieza en {}, termina en {} con Distancia: {}; Tiempo: {}; Duración: {}; Maniobra: {
        # print("La secuencia de puntos codificados es: {}; con una longitud de {} caracteres".format(step["polyline"]["p

        substeps = decode_polyline(step["polyline"]["points"])
        # print("La secuencia de puntos detallados es: {}".format(substeps"))
        for substep in substeps:
            if index < len(substeps):
                p1 = {"latitude": substeps[index][0], "longitude": substeps[index][1]}
                p2 = {"latitude": substeps[index + 1][0], "longitude": substeps[index + 1][1]}
                # print("Voy a calcular la distancia entre {} y {}".format(p1, p2))
                points_distance = distance(p1, p2)
                if points_distance > 0.001:
                    subStepDuration = points_distance / stepSpeed
                    new_detailed_step = {"Origin": p1, "Destination": p2, "Speed": stepSpeed, "Time": subStepDuration,
                                         "Distance": points_distance, "Maneuver": stepManeuver}
                    # print("Se ha añadido el paso: {}".format(new_detailed_step))
                    detailedSteps.append(new_detailed_step)
                    # print("La ruta tiene {} pasos".format(len(detailedSteps)))

    return detailedSteps


def mqtt_communications():
    global client
    global event_message
    STATE_TOPIC = "/fic/vehicles/" + get_host_name() + "/telemetry"

    client.username_pw_set(username="g07",
                           password="g07pw")

    client.on_connect = on_connect
    client.on_message = on_message

    connection_dict = {"vehicle_plate": vehicle_plate, "status": "Off - Irregular Disconnection",
                       "timestamp": str(datetime.now())}
    connection_str = json.dumps(connection_dict)
    client.will_set(STATE_TOPIC, connection_str)

    MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
    MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))
    client.connect(MQTT_SERVER, MQTT_PORT, 60)
    client.loop_start()

    while not terminate:
        if vehicle_plate != "":
            if event_message != "":
                publish_event(client)
                event_message = ""

            publish_telemetry(client)
            time.sleep(10)


def getVehicleStatus():
    vehicle_status = {"id": get_host_name(), "vehicle_plate":
        vehicle_plate, "telemetry": {"id": get_host_name(),
                                     "current_steering": current_steering,
                                     "current_speed": current_speed,
                                     "latitude": current_position["latitude"],
                                     "longitude": current_position["longitude"],
                                     "current_ldr": current_light,
                                     "current_obstacle_distance": current_obstacle_distance,
                                     "front_left_led_intensity": current_leds[0]["Intensity"],
                                     "front_right_led_intensity": current_leds[1]["Intensity"],
                                     "rear_left_led_intensity": current_leds[2]["Intensity"],
                                     "rear_right_led_intensity": current_leds[3]["Intensity"],
                                     "front_left_led_color": current_leds[0]["Color"],
                                     "front_right_led_color": current_leds[1]["Color"],
                                     "rear_left_led_color": current_leds[2]["Color"],
                                     "rear_right_led_color": current_leds[3]["Color"],
                                     "front_left_led_blinking": current_leds[0]["Blinking"],
                                     "front_right_led_blinking": current_leds[1]["Blinking"],
                                     "rear_left_led_blinking": current_leds[2]["Blinking"],
                                     "rear_right_led_blinking": current_leds[3]["Blinking"],
                                     "time_stamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}

    return vehicle_status


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        PLATE_REQUEST_TOPIC = "/fic/vehicles/" + get_host_name() + "/request_plate"
        client.publish(PLATE_REQUEST_TOPIC, payload=get_host_name(),
                       qos=1, retain=False)

        CONFIG_TOPIC = "/fic/vehicles/" + get_host_name() + "/config"
        client.subscribe(CONFIG_TOPIC)
        print("Suscrito a {}".format(CONFIG_TOPIC))

        ROUTES_TOPIC = "/fic/vehicles/" + get_host_name() + "/routes"
        client.subscribe(ROUTES_TOPIC)
        print("Suscrito a {}".format(ROUTES_TOPIC))

def get_host_name():
    bashCommandName = 'echo $HOSTNAME'
    host = subprocess \
               .check_output(['bash', '-c', bashCommandName]) \
               .decode("utf-8")[0:-1]
    return host


def on_message(client, userdata, msg):
    global vehicle_plate

    topic = (msg.topic).split('/')
    if topic[-1] == "config":
        config_received = msg.payload.decode()
        json_config_received = json.loads(config_received)
        if json_config_received["Plate"] != "Not Available":
            vehicle_plate = json_config_received["Plate"]
            print("Matrícula: {}".format(vehicle_plate))

    elif topic[-1] == "routes":
        required_route = msg.payload.decode("utf-8")
        print("Se ha asignado la ruta: {}".format(required_route))
        routes_loader(required_route)


def publish_telemetry(client):
    STATE_TOPIC = "/fic/vehicles/" + get_host_name() + "/telemetry"
    vehicle_status = getVehicleStatus()
    json_telemetry = json.dumps(vehicle_status)
    client.publish(STATE_TOPIC, payload=json_telemetry,qos=1, retain=False)
    print("Telemetrías enviadas a: {}".format(STATE_TOPIC))


def publish_event(client):
    global recibida
    global enviado
    event_to_send = {"Plate": vehicle_plate, "Event": event_message,
                     "Timestamp": str(datetime.timestamp(datetime.now()))}
    json_event = json.dumps(event_to_send)
    EVENTS_TOPIC = "/fic/vehicles/" + get_host_name() + "/events"
    client.publish(EVENTS_TOPIC, payload=json_event, qos=1,
                   retain=False)
    recibida = False
    enviado = False
    print("Enviado mensaje de ruta completada")

if __name__ == '__main__':
    try:
        t1 = threading.Thread(target=mqtt_communications, daemon=True)
        t1.start()
        t2 = threading.Thread(target=environment_simulator, daemon=True)
        t2.start()
        t3 = threading.Thread(target=vehicle_controller, daemon=True)
        t3.start()
        t4 = threading.Thread(target=led_controller, daemon=True)
        t4.start()
        t1.join()
        t2.join()
        t3.join()
        t4.join()
    except Exception as e:
        print(e)
        vehicle_stop()
    except KeyboardInterrupt:
        print("Parando el programa...")
        vehicle_stop()