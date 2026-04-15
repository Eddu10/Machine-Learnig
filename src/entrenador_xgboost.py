import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay
import pandas as pd
import urllib
from sqlalchemy import create_engine
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib
import warnings

warnings.filterwarnings('ignore')

print("Iniciando entrenamiento XGBOOST")
print("-" * 60)

NOMBRE_SERVIDOR = 'localhost'
NOMBRE_BD = 'TestAnomalias'
USUARIO = 'sa'
CONTRASENA = 'root'

MINUTOS_PREVIOS = 20

COLUMNAS_SENSORES = ['ST18 Motor speed reference', 'ST18 Motor speed feedback', 'ST18 Motor torque feedback', 'ST18 Drive 01 Current Feedback Raw',
                     'IS18_PGM.LPR_Height_Ref', 'IS18_PGM.LPR_Height_Fdbk', 'IS18_PGM.Reg_Fdbk_PDA', 'Stand Load 18', 'Looper HMD 18']

print('Conectando a SQL Server...')
params = urllib.parse.quote_plus(
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    fr'SERVER={NOMBRE_SERVIDOR};'
    fr'DATABASE={NOMBRE_BD};'
    fr'UID={USUARIO};'
    fr'PWD={CONTRASENA};'
)
motor_sql = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

print("Descargando historial de sensores continuos...")
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

print("Descargando historial de paras y fallas...")
df_fallas = pd.read_sql("SELECT * FROM registro_fallas ORDER BY Fecha ASC", con=motor_sql)
df_fallas['Fecha'] = pd.to_datetime(df_fallas['Fecha'])
df_fallas['hora_fin'] = pd.to_datetime(df_fallas['hora_fin'])

print(f"Etiquetando sintomas previos ({MINUTOS_PREVIOS} min antes de cada falla)...")
df_senal['estado_maquina'] = 'Normal'

fallas_reales = df_fallas[df_fallas['Planificacion'] == 'NO PLANIFICADA']
paras_planificadas = df_fallas[df_fallas['Planificacion'] == 'PLANIFICADA']

print(f"   -> Encontradas {len(fallas_reales)} fallas reales")
print(f"   -> Encontradas {len(paras_planificadas)} paras planificadas")

#ignorar fallas planiicadas
for indice, para in paras_planificadas.iterrows():
    h_inicio = para['Fecha'] - pd.Timedelta(minutes=MINUTOS_PREVIOS)
    h_fin = para['hora_fin']

    mascara_tiempo = (df_senal['fecha_hora'] >= h_inicio) & (df_senal['fecha_hora'] <= h_fin)
    df_senal.loc[mascara_tiempo, 'estado_maquina'] = 'IGNORAR'

#Por cada falla, regresamos un poco el tiempo
for indice, falla in fallas_reales.iterrows():
    h_inicio = falla['Fecha'] - pd.Timedelta(minutes=MINUTOS_PREVIOS)
    h_fin = falla['hora_fin']

    mascara_tiempo = (df_senal['fecha_hora'] >= h_inicio) & (df_senal['fecha_hora'] <= h_fin)
    df_senal.loc[mascara_tiempo, 'estado_maquina'] = falla['Causa']

#limpieza final
df_senal = df_senal[df_senal['estado_maquina'] != 'IGNORAR'].copy()
print("Se eliminaron registros contaminados por paras planificadas.")

df_senal[COLUMNAS_SENSORES] = df_senal[COLUMNAS_SENSORES].astype('float32')

print('\nDistribucion de estados aprendidos')
print(df_senal['estado_maquina'].value_counts())

#preparacion xgboost
print("\n Codificando diagnostico de texto a formato Numerico....")
codificador = LabelEncoder()
df_senal['target_numerico'] = codificador.fit_transform(df_senal['estado_maquina'])
clases_detectadas = codificador.classes_

if len(clases_detectadas) < 2:
    print("\n❌ ERROR CRÍTICO DE DATOS: La IA detectó que el 100% de los datos son 'Normales'.")
    print("No se encontraron fallas reales en los datos descargados.")
    print("Revisa que las fechas en 'registro_fallas' coincidan exactamente con las fechas en 'Señal'.")
    exit() # Detenemos el programa antes de que explote

print("\nCalculando Promedios de normalidad")
df_normal = df_senal[df_senal['estado_maquina'] == 'Normal']
promedios_normales = df_normal[COLUMNAS_SENSORES].mean().to_dict()
#print(f"Valores normales detectados: {promedios_normales}")
joblib.dump(promedios_normales, 'promedios_normales.pkl')

X = df_senal[COLUMNAS_SENSORES]
y = df_senal['target_numerico']
#80% para entrenar, 20% para examen final
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#entrenamiento xgboost
print(f"\n Entrenando red XGBOOST para reconocer {len(clases_detectadas)} estados...")
modelo_xgb = xgb.XGBClassifier(
    tree_method='hist',
    n_estimators=150,
    learning_rate=0.1,
    max_depth=6,
    random_state=42,
    eval_metric='mlogloss'
)
modelo_xgb.fit(X_train, y_train)

#evaluacion y exportacion
print("\n Evaluando precision del modelo...")
predicciones = modelo_xgb.predict(X_test)
precision = accuracy_score(y_test, predicciones)
print(f"Precision Global: {precision * 100:.2f}%\n")

print(classification_report(y_test, predicciones, target_names=clases_detectadas))

print(" Exportando la IA al disco duro...")
joblib.dump(modelo_xgb, 'cerebro_xgboost.pkl')
joblib.dump(codificador, 'traductor_etiquetas.pkl')

#graficos
print("\n Generando graficas de analisis...")
ax = xgb.plot_importance(modelo_xgb, importance_type='weight', max_num_features=10,
                         height=0.5, title='Ranking: Sensores Críticos'
                        )

fig_importancia = ax.figure
fig_importancia.set_size_inches(12, 6)
plt.tight_layout()
plt.show()

fig, ax = plt.subplots(figsize=(12, 8))
ConfusionMatrixDisplay.from_predictions(
    y_test,
    predicciones,
    display_labels=clases_detectadas,
    xticks_rotation=45,
    cmap='Blues',
    ax=ax
)
plt.title('Matriz de Confusion: Aciertos vs Errores de XGBoost', fontsize=16)
plt.xlabel('Lo que predijo la IA', fontsize=12)
plt.ylabel('La falla real', fontsize=12)
plt.tight_layout()
plt.show()

print("\nEntrenamiento completado esxitosamente")
print("los 3 archivos (.pkl) estan listos para se conectados al Monitor en vivo")