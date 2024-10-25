import os
import mysql.connector

class VehicleDBManager:
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

    @property
    def __class__(self):
        return super().__class__

    def get_active_vehicles(self):
        sql = "SELECT plate FROM vehicles WHERE status = 1;"
        plates = []
        with self.mydb.cursor() as mycursor:
            mycursor.execute(sql)
            myresult = mycursor.fetchall()
            for plate in myresult:
                data = {"Plate": plate}
                plates.append(data)
        return plates

    def register_new_vehicle(self, vehicle_id):
        sql_1 = "SELECT plate FROM vehicles WHERE vehicle_id = %s ORDER BY plate ASC LIMIT 1;"
        sql_2 = "SELECT plate, is_assigned FROM available_plates WHERE is_assigned = 0 ORDER BY plate ASC LIMIT 1;"

        with self.mydb.cursor() as mycursor:
            mycursor.execute(sql_1, (vehicle_id,))
            plate = mycursor.fetchone()

            if plate:
                return plate[0]
            else:
                mycursor.execute(sql_2)
                plate = mycursor.fetchone()

                if plate:
                    sql_insert = "INSERT INTO vehicles (vehicle_id, plate) VALUES (%s, %s);"
                    mycursor.execute(sql_insert, (vehicle_id, plate[0]))

                    sql_update = "UPDATE available_plates SET is_assigned = 1 WHERE plate = %s;"
                    mycursor.execute(sql_update, (plate[0],))

                    self.mydb.commit()

                    return plate[0]
                else:
                    return ""

