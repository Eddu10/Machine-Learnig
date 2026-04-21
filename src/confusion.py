import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay
import pandas as pd
import urllib
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import textwrap  # <-- IMPORTAMOS LA HERRAMIENTA DE TEXTO
import warnings

warnings.filterwarnings('ignore')

print("--- VISOR DE RESULTADOS XGBOOST (AJUSTE VISUAL DEFINTIVO) ---")

# 1. CARGAMOS EL CEREBRO YA ENTRENADO (¡Nos ahorramos las horas de entrenamiento!)
print("Cargando la IA desde el disco duro...")
modelo_xgb = joblib.load('cerebro_xgboost.pkl')
codificador = joblib.load('traductor_etiquetas.pkl')
clases_detectadas = codificador.classes_

NOMBRE_SERVIDOR = 'localhost'
NOMBRE_BD = 'TestAnomalias'
USUARIO = 'sa'
CONTRASENA = 'root'
MINUTOS_PREVIOS = 20

COLUMNAS_SENSORES = [
    'ST18 Motor speed reference', 'ST18 Motor speed feedback', 'ST18 Motor torque feedback', 'ST18 Drive 01 Current Feedback Raw',
    'IS18_PGM.LPR_Height_Ref', 'IS18_PGM.LPR_Height_Fdbk', 'IS18_PGM.Reg_Fdbk_PDA', 'Stand Load 18', 'Looper HMD 18'
]

print('Conectando a SQL Server y reconstruyendo el examen...')
params = urllib.parse.quote_plus(
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    fr'SERVER={NOMBRE_SERVIDOR};'
    fr'DATABASE={NOMBRE_BD};'
    fr'UID={USUARIO};'
    fr'PWD={CONTRASENA};'
)
motor_sql = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

consulta = """ SELECT DISTINCT s.*, 0 as rn
            FROM Señal s
            INNER JOIN registro_fallas f
                ON s.fecha_hora >= DATEADD(minute, -20, f.Fecha)
                AND s.fecha_hora <= DATEADD(SECOND, 59, f.hora_fin)
            UNION
            SELECT sub.*
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER(
                        PARTITION BY CONVERT(smalldatetime, fecha_hora)
                        ORDER BY fecha_hora
                    ) as rn
                FROM Señal
            ) sub
            WHERE sub.rn = 1
        """
df_senal = pd.read_sql(consulta, con=motor_sql)
df_senal['fecha_hora'] = pd.to_datetime(df_senal['fecha_hora'])

df_fallas = pd.read_sql("SELECT * FROM registro_fallas ORDER BY Fecha ASC", con=motor_sql)
df_fallas['Fecha'] = pd.to_datetime(df_fallas['Fecha'])
df_fallas['hora_fin'] = pd.to_datetime(df_fallas['hora_fin'])

df_senal['estado_maquina'] = 'Normal'
fallas_reales = df_fallas[df_fallas['Planificacion'] == 'NO PLANIFICADA']
paras_planificadas = df_fallas[df_fallas['Planificacion'] == 'PLANIFICADA']

for indice, para in paras_planificadas.iterrows():
    h_inicio = para['Fecha'] - pd.Timedelta(minutes=MINUTOS_PREVIOS)
    h_fin = para['hora_fin']
    mascara_tiempo = (df_senal['fecha_hora'] >= h_inicio) & (df_senal['fecha_hora'] <= h_fin)
    df_senal.loc[mascara_tiempo, 'estado_maquina'] = 'IGNORAR'

for indice, falla in fallas_reales.iterrows():
    h_inicio = falla['Fecha'] - pd.Timedelta(minutes=MINUTOS_PREVIOS)
    h_fin = falla['hora_fin']
    mascara_tiempo = (df_senal['fecha_hora'] >= h_inicio) & (df_senal['fecha_hora'] <= h_fin)
    df_senal.loc[mascara_tiempo, 'estado_maquina'] = falla['Clase']

df_senal = df_senal[df_senal['estado_maquina'] != 'IGNORAR'].copy()
df_senal[COLUMNAS_SENSORES] = df_senal[COLUMNAS_SENSORES].astype('float32')

top_fallas = fallas_reales['Clase'].value_counts().nlargest(10).index.tolist()
clases_comunes = ['Normal'] + top_fallas
df_senal.loc[~df_senal['estado_maquina'].isin(clases_comunes), 'estado_maquina'] = 'OTRA_FALLA'

# Usamos transform() porque el LabelEncoder ya está entrenado
df_senal['target_numerico'] = codificador.transform(df_senal['estado_maquina'])

X = df_senal[COLUMNAS_SENSORES]
y = df_senal['target_numerico']

# Recreamos exactamente el mismo examen usando el random_state=42
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("\n Generando la Matriz de Confusión AMPLIFICADA Y AJUSTADA...")
# 2. USAMOS EL CEREBRO PARA PREDECIR DIRECTAMENTE (Saltamos el fit)
predicciones = modelo_xgb.predict(X_test)

# --- APLICAMOS LA MICRO-CIRUGÍA VISUAL AQUÍ ---
# 1. Ampliamos un poco el ancho a 15 para que no genere tantas líneas verticales
clases_formateadas = [textwrap.fill(texto, width=15) for texto in clases_detectadas]

# 2. Lienzo masivo y alta resolución
fig, ax = plt.subplots(figsize=(24, 14), dpi=100)

ConfusionMatrixDisplay.from_predictions(
    y_test,
    predicciones,
    display_labels=clases_formateadas,
    xticks_rotation=90,
    cmap='Blues',
    values_format=',',
    text_kw={'fontsize': 7, 'color': 'black'}, # Los números se mantienen perfectos
    ax=ax
)

plt.title('Matriz de Confusión: Aciertos vs Errores de XGBoost', fontsize=26, pad=40)
plt.xlabel('Predicción de la IA', fontsize=20, labelpad=25)
plt.ylabel('Falla Real (Etiquetada)', fontsize=20, labelpad=25)

# --- LA SOLUCIÓN A LAS LETRAS SOBREPUESTAS ---
# Reducimos el tamaño de la letra de las categorías a 8 (antes estaba en 12)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)

plt.tight_layout(pad=6.0)

print("Mostrando gráfica. Recuerda cerrar la ventana para finalizar el script.")
plt.show()