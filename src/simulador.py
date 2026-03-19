import pyodbc
import time
import random
from datetime import datetime

print("Iniciando simulador de plc")

NOMBRE_SERVIDOR = 'localhost'
NOMBRE_BD = 'TestAnomalias'
USUARIO = 'sa'
CONTRASENA = 'root'

try:
    conexion = pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        fr'SERVER={NOMBRE_SERVIDOR};'
        fr'DATABASE={NOMBRE_BD};'
        fr'UID={USUARIO};'
        fr'PWD={CONTRASENA};'
    )
    cursor = conexion.cursor()
    print("Conectado exitosamente a SQL Server")

except Exception as e:
    print(f"Error al conectar: {e}")
    exit()

print("Inyectando datos...\n")

try:
    contador = 0
    while True:
        hora = datetime.now()
        #datos simulados
        velocidad = random.uniform(1480, 1520)
        temperatura = random.uniform(58, 62)
        estado = "Normal"

        probabilidad = random.randint(1, 100)

        #fallas simuladas
        if probabilidad <= 5 :
            velocidad = random.uniform(800, 1100)
            tempartura = random.uniform(85, 105)
            estado = "Anomalia Simulada"

        query = """ INSERT INTO señal (fecha_hora, velocidad, temperatura) VALUES (?, ?, ?) """
        cursor.execute(query, hora, velocidad, temperatura)
        conexion.commit()

        contador += 1
        print(f"[{hora.strftime('%H:%M:%S')}] Registro {contador} | Vel: {velocidad:.2f} | Temp: {temperatura:.2f} -> {estado}")

        time.sleep(5)
except KeyboardInterrupt:
    print("Simulador detenido por el usuario")
    cursor.close()
    conexion.close()