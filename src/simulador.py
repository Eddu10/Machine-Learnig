import pyodbc
import time
import random
from datetime import datetime

print("--- INICIANDO SIMULADOR ---")

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
    print("✅ Conectado exitosamente a SQL Server")

except Exception as e:
    print(f"❌ Error al conectar: {e}")
    exit()

print("Inyectando telemetría en tiempo real...\n")

try:
    contador = 0
    while True:
        hora = datetime.now()
        probabilidad = random.randint(1, 100)

        if probabilidad <= 10:
            estado = "⚠️ ANOMALÍA SIMULADA"
            speed_ref = 52.335
            speed_fdbk = random.uniform(10.0, 25.0)       # Cae drásticamente
            torque = random.uniform(1200.0, 1500.0)       # Se dispara por el esfuerzo
            current = random.uniform(1800.0, 2200.0)      # Sobrecorriente

            # Sensores secundarios (variaciones bruscas)
            lpr_height_ref = 15.5
            lpr_height_fdbk = random.uniform(5.0, 8.0)
            reg_fdbk_pda = random.uniform(10.0, 15.0)
            stand_load = random.uniform(800.0, 950.0)
            looper_hmd = random.uniform(5.0, 10.0)

        else:
            estado = "Normal"
            speed_ref = 52.335
            speed_fdbk = random.uniform(52.30, 52.34)     # Sigue muy de cerca a la referencia
            torque = random.uniform(495.0, 515.0)         # Estable alrededor de 500
            current = random.uniform(600.0, 770.0)        # Estable alrededor de 700

            # Sensores secundarios (valores estables de relleno)
            lpr_height_ref = 15.5
            lpr_height_fdbk = random.uniform(15.3, 15.6)
            reg_fdbk_pda = random.uniform(1.0, 1.5)
            stand_load = random.uniform(310.0, 330.0)
            looper_hmd = random.uniform(44.0, 46.0)

        # Usamos corchetes [ ] en SQL porque los nombres de tus columnas tienen espacios
        query = """
            INSERT INTO Simulador (
                fecha_hora,
                [ST18 Motor speed reference],
                [ST18 Motor speed feedback],
                [ST18 Motor torque feedback],
                [ST18 Drive 01 Current Feedback Raw],
                [IS18_PGM.LPR_Height_Ref],
                [IS18_PGM.LPR_Height_Fdbk],
                [IS18_PGM.Reg_Fdbk_PDA],
                [Stand Load 18],
                [Looper HMD 18]
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(query,
                       hora,
                       speed_ref,
                       speed_fdbk,
                       torque,
                       current,
                       lpr_height_ref,
                       lpr_height_fdbk,
                       reg_fdbk_pda,
                       stand_load,
                       looper_hmd)
        conexion.commit()

        contador += 1
        print(f"[{hora.strftime('%H:%M:%S')}] #{contador} | Vel: {speed_fdbk:.2f} | Torq: {torque:.2f} | Amp: {current:.2f} -> {estado}")

        time.sleep(2) # Inyecta un dato cada 2 segundos

except KeyboardInterrupt:
    print("\n⏹️ Simulador detenido por el usuario.")
    cursor.close()
    conexion.close()