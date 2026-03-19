
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import urllib
from sqlalchemy import create_engine
from sklearn.ensemble import IsolationForest

print("Iniciando detector")

#conf conexion
NOMBRE_BD = 'TestAnomalias'
NOMBRE_SERVIDOR = 'localhost'
USUARIO = 'sa'
CONTRASENA = 'root'

def detector_anomalias_sql():
    print("Conectando a la BD...")

    try:
        #conexion sql server
        params = urllib.parse.quote_plus(
            r'Driver={ODBC Driver 17 for SQL Server};'
            fr'Server={NOMBRE_SERVIDOR};'
            fr'Database={NOMBRE_BD};'
            fr'UID={USUARIO};'
            fr'PWD={CONTRASENA};'
        )
        motor_sql = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

        #descarga de datos
        print("leyendo las señales...")
        query = "SELECT * FROM Señal ORDER BY fecha_hora ASC"
        df = pd.read_sql(query, con=motor_sql)

        if len(df) == 0:
            print("La tabla esta vacia")
            return None

        print(f"Se cargaron {len(df)} registros correctamente")

        df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])

        #preparacion de la ia
        print("Preparando datos para IA...")
        columnas_sensores = df.columns.drop('fecha_hora')
        df_sensores = df[columnas_sensores].dropna()

        #entrenamiento del modelo
        print("Entrenando algoritmo IF...")
        modelo = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)

        #analiza datos
        df['anomalia_detectada'] = modelo.fit_predict(df_sensores)

        normales = len(df[df['anomalia_detectada'] == 1])
        anomalos = len(df[df['anomalia_detectada'] == -1])
        print(f"Normales: {normales} | Anomalías: {anomalos}")

        #grafica
        print("Generando grafica...")
        df_normal = df[df['anomalia_detectada'] == 1]
        df_peligro = df[df['anomalia_detectada'] == -1]

        plt.figure(figsize=(25, 10))

        for sensor in columnas_sensores:
            plt.plot(df_normal['fecha_hora'], df_normal[sensor], linestyle='-', marker='', alpha=0.5, label=f'Normal {sensor}')
            plt.plot(df_peligro['fecha_hora'], df_peligro[sensor], linestyle='none', marker='o', color='red', markersize=6)

        plt.title('Detector de IA: Anomalias en todos los sensores')
        plt.xlabel('Hora', fontsize=14)
        plt.ylabel('Valor', fontsize=14)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.xticks(rotation=75, ha='right')
        plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        return df
    except Exception as e:
        print(f"Error de conexion o proceso: {e}")
        return None

if __name__ == "__main__":
    datos_analizados = detector_anomalias_sql()
