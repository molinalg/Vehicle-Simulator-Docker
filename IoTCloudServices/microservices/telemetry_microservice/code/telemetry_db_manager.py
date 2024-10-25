import os,json
import mysql.connector

class TelemetryDBManager:
    def __init__(self):
        self.mydb = self.connect_database()
    def connect_database(self):
        mydb = mysql.connector.connect(
            host=os.getenv('DBHOST'),
            user=os.getenv('DBUSER'),
            password=os.getenv('DBPASSWORD'),
            database=os.getenv('DBDATABASE')
        )
        return mydb

    def register_new_telemetry(self,params):
        sql = """
            INSERT INTO vehicles_telemetry (
                vehicle_id, current_steering, current_speed, latitude, longitude,
                current_ldr, current_obstacle_distance, front_left_led_intensity,
                front_right_led_intensity, rear_left_led_intensity, rear_right_led_intensity,
                front_left_led_color, front_right_led_color, rear_left_led_color, rear_right_led_color,
                front_left_led_blinking, front_right_led_blinking, rear_left_led_blinking, rear_right_led_blinking,
                time_stamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        lista = []
        for key in params:
            lista.append(params[key])

        with self.mydb.cursor() as mycursor:
            try:
                mycursor.execute(sql,lista)
                self.mydb.commit()
                return True


            except Exception as e:
                print("Error: {}".format(e))
                return json.dumps({"Error Message": str(e)})

    def get_vehicle_detailed_info(self,params):
        sql = """
            SELECT vehicle_id, current_steering, current_speed, current_ldr,
                   current_obstacle_distance, front_left_led_intensity,
                   front_right_led_intensity, rear_left_led_intensity,
                   rear_right_led_intensity, front_left_led_color,
                   front_right_led_color, rear_left_led_color, rear_right_led_color,
                   front_left_led_blinking, front_right_led_blinking,
                   rear_left_led_blinking, rear_right_led_blinking, time_stamp
            FROM vehicles_telemetry
            WHERE vehicle_id = %s
            ORDER BY time_stamp DESC
            LIMIT 20;
        """
        with self.mydb.cursor() as mycursor:
            try:
                vehicle_id = params["vehicle_id"]
                query_params = (vehicle_id,)

                mycursor.execute(sql, query_params)
                my_result = mycursor.fetchall()

                result = []
                for vehicle_id, current_steering, current_speed, current_ldr, current_obstacle_distance, front_left_led_intensity, front_right_led_intensity, rear_left_led_intensity, rear_right_led_intensity, front_left_led_color, front_right_led_color, rear_left_led_color, rear_right_led_color, front_left_led_blinking, front_right_led_blinking, rear_left_led_blinking, rear_right_led_blinking, time_stamp in my_result:

                    item = {"Vehicle_id": vehicle_id,
                            "Current Steering": current_steering,
                            "Current Speed": current_speed,
                            "Current LDR": current_ldr,
                            "Obstacle Distance":current_obstacle_distance,
                            "Front Left Led Intensity": front_left_led_intensity,
                            "Front Right Led Intensity": front_right_led_intensity,
                            "Rear Left Led Intensity": rear_left_led_intensity,
                            "Rear Right Led Intensity": rear_right_led_intensity,
                            "Front Left Led Color": front_left_led_color,
                            "Front Right Led Color": front_right_led_color,
                            "Rear Left Led Color": rear_left_led_color,
                            "Rear Right Led Color": rear_right_led_color,
                            "Front Left Led Blinking": front_left_led_blinking,
                            "Front Right Led Blinking": front_right_led_blinking,
                            "Rear Left Led Blinking": rear_left_led_blinking,
                            "Rear Right Led Blinking": rear_right_led_blinking,
                            "Time Stamp": time_stamp}

                    result.append(item)

                return json.dumps(result)

            except Exception as e:
                print("Error: {}".format(e))
                return json.dumps({"Error Message": str(e)})

    def get_vehicles_last_position(self):
        sql = """
            SELECT vehicles.vehicle_id, plate, latitude, longitude, time_stamp
            FROM vehicles
            INNER JOIN vehicles_telemetry ON vehicles.vehicle_id = vehicles_telemetry.vehicle_id
            WHERE status = 1
            ORDER BY time_stamp DESC
            LIMIT 1;
        """

        with self.mydb.cursor() as mycursor:
            try:
                mycursor.execute(sql)
                my_result = mycursor.fetchall()

                result = []
                for vehicle_id, plate, latitude, longitude, time_stamp in my_result:
                    item = {"Vehicle_id": vehicle_id, "Plate": plate, "Latitude":latitude, "Longitude": longitude, "Time Stamp": time_stamp}
                    result.append(item)

                return json.dumps(result)

            except Exception as e:
                print("Error: {}".format(e))
                return json.dumps({"Error Message": str(e)})
