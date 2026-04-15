import pandas as pd
import urllib
from sqlalchemy import create_engine
import joblib
import time
import warnings
import os

warnings.filterwarnings('ignore')

os.system('cls' if os.name == 'nt' else 'clear')

#base de datos
NOMBRE_SERVIDOR = 'localhost'
NOMBRE_BD = 'TestAnomalias'
USUARIO = 'sa'
CONTRASENA = 'root'

COLUMNAS_SENSORES = ['ST18 Motor speed reference', 'ST18 Motor speed feedback', 'ST18 Motor torque feedback', 'ST18 Drive 01 Current Feedback Raw',
                     'IS18_PGM.LPR_Height_Ref', 'IS18_PGM.LPR_Height_Fdbk', 'IS18_PGM.Reg_Fdbk_PDA', 'Stand Load 18', 'Looper HMD 18'
                    ]

#cargar ia
print("\n[1/3] Cargando Cerebro XGBoost...")
modelo_xgb = joblib.load('cerebro_xgboost.pkl')

print("\n[2/3] Cargando Traductor de etiquetas...")
codificador = joblib.load('traductor_etiquetas.pkl')

print("\n[3/3] Cargando Promedios de Normaidad...")
promedios_normales = joblib.load('promedios_normales.pkl')

#conexion bd
params = urllib.parse.quote_plus(
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    fr'SERVER={NOMBRE_SERVIDOR};'
    fr'DATABASE={NOMBRE_BD};'
    fr'UID={USUARIO};'
    fr'PWD={CONTRASENA};'
)
motor_sql = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

print("\n Ssistema en linea, Iniciando Moitoreo...\n")
print("-" * 60)

#Monitoreo
while True:
    try:
        consulta_envivo = "SELECT TOP 1 * FROM Señal ORDER BY fecha_hora DESC"
        df_envivo = pd.read_sql(consulta_envivo, con=motor_sql)

        if df_envivo.empty:
            print("Espereando conexion de Sensores")
            time.sleep(2)
            continue

        timepo_actual = df_envivo['fecha_hora'].iloc[0].strftime('%Y-%m-%d %H:%M:%S')
        X_envivo = df_envivo[COLUMNAS_SENSORES]

        #prediccion ia
        prediccion_numerica = modelo_xgb.predict(X_envivo)[0]
        probabilidades = modelo_xgb.predict_probabilidad(X_envivo)[0]
        confianza = max(probabilidades) * 100

        causa_detectada = codificador.inverse_transform([prediccion_numerica])[0]

        if causa_detectada == 'Normal':
            print(f"[{timepo_actual}] Estado Normal | Velocidad: {X_envivo['ST18 Motor speed feedback'].iloc[0]:.0f} | Corriente: {X_envivo['ST18 Drive 01 Current Feedback Raw'].iloc[0]:.0f}")
        else:
            print("\n" + "!" * 60)
            print(f"ALERTA CRITICA DETECTADA: {causa_detectada.upper()}")
            print(f"Tiempo: {timepo_actual} | Confianza de la IA: {confianza: .1f}%")

            print("Analisis de Cuasa: ")
            mayor_desviacion = 0
            sensor_culpable = ""

            for sensor in COLUMNAS_SENSORES:
                valor_envivo = float(X_envivo[sensor].iloc[0])
                valor_normal = promedios_normales[sensor]

                if valor_normal != 0:
                    desviacion_pct = abs((valor_envivo - valor_normal) / valor_normal) *100
                    if desviacion_pct > 10: #si varia mas de un 10%
                        indicador = "ALTO" if valor_envivo > valor_normal else "BAJO"
                        print (f"  -{sensor}: {valor_envivo:.2f} ({indicador}, Normal es ~{valor_normal:.2f})")

                    if desviacion_pct > mayor_desviacion:
                        mayor_desviacion = desviacion_pct
                        sensor_culpable = sensor

            # Sistema Prescriptivo
            print("\n Prescripcion Recomendada para el Operador:")
            try:
                # se busca la ultima vez que ocurrio una falla igual
                consulta_solucion = f"SELECT TOP 1 Solucion FROM registro_fallas WHERE Causa = '{causa_detectada}' ORDER BY Fecha DESC"
                df_solucion = pd.read_sql(consulta_solucion, con=motor_sql)
                if not df_solucion.empty:
                    print(f"  >> ACCIÓN: {df_solucion['Solucion'].iloc[0]}")
                else:
                    print("  >>(No hay solucion registrada en la base de datos para esta falla)")
            except Exception as e:
                print("  >> Error consultando la bitácora de soluciones", e)

            print("!" * 60 + "\n")

            time.sleep(5)

        time.sleep(2)
    except Exception as error_general:
        print(f"Error de lectura: {error_general}")
        time.sleep(5)