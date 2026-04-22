import streamlit as st
import pandas as pd
import urllib
from sqlalchemy import create_engine
import joblib
import time
import warnings

warnings.filterwarnings('ignore')

#interfaz
st.set_page_config(page_title="Monitor IA", page_icon="🏭", layout="wide")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>""", unsafe_allow_html=True)

st.title("Panel de Monitoreo Prescriptivo con IA")
st.markdown("---")

@st.cache_resource
def cargar_inteligencia():
    motor_sql = create_engine(f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(r'DRIVER={ODBC Driver 17 for SQL Server}; SERVER=localhost;DATABASE=TestAnomalias;UID=sa;PWD=root;')}")
    modelo = joblib.load('cerebro_xgboost.pkl')
    codificador = joblib.load('traductor_etiquetas.pkl')
    promedios = joblib.load('promedios_normales.pkl')
    return motor_sql, modelo, codificador, promedios

motor_sql, modelo_xgb, codificador, promedios_normales = cargar_inteligencia()

COLUMNAS_SENSORES = ['ST18 Motor speed reference', 'ST18 Motor speed feedback', 'ST18 Motor torque feedback', 'ST18 Drive 01 Current Feedback Raw',
                     'IS18_PGM.LPR_Height_Ref', 'IS18_PGM.LPR_Height_Fdbk', 'IS18_PGM.Reg_Fdbk_PDA', 'Stand Load 18', 'Looper HMD 18'
                    ]

#visualizacion
panel_estado = st.empty()
col1, col2, col3 = st.columns(3)
con_velocidad = col1.empty()
con_corriente = col2. empty()
con_carga = col3.empty()

panel_alerta = st.empty()
panel_diagnostico = st.empty()
panel_solucion = st.empty()

while True:
    try:
        df_live = pd.read_sql("SELECT TOP 1 * FROM Simulador ORDER BY fecha_hora DESC", con=motor_sql)

        if df_live.empty:
            panel_estado.warning("Esperando datos...")
            time.sleep(2)
            continue

        X_live = df_live[COLUMNAS_SENSORES]
        tiempo_actual = df_live['fecha_hora'].iloc[0].strftime('%H:%M:%S')

        prediccion = modelo_xgb.predict(X_live)[0]
        probabilidades = modelo_xgb.predict_proba(X_live)[0]
        confianza = max(probabilidades) * 100
        causa_detectada = codificador.inverse_transform([prediccion])[0]

        velocidad = float(X_live['ST18 Motor speed feedback'].iloc[0])
        corriente = float(X_live['ST18 Drive 01 Current Feedback Raw'].iloc[0])
        carga = float(X_live['Stand Load 18'].iloc[0])

        if causa_detectada == 'Normal':
            panel_estado.success(f"**ESTADO: OPERACIÓN NORMAL** (Última lectura: {tiempo_actual})")

            con_velocidad.metric(label="Velocidad (RPM)", value=f"{velocidad:.0f}")
            con_corriente.metric(label="Corriente (Amp)", value=f"{corriente:.0f}")
            con_carga.metric(label="Carga (Load)", value=f"{carga:.0f}")

            panel_alerta.empty()
            panel_diagnostico.empty()
            panel_solucion.empty()

        else:
            panel_estado.error(f"**ALERTA CRÍTICA DETECTADA** (Última lectura: {tiempo_actual})")

            con_velocidad.metric(label="Velocidad (RPM)", value=f"{velocidad:.0f}", delta="- Anomalía", delta_color="inverse")
            con_corriente.metric(label="Corriente (Amp)", value=f"{corriente:.0f}")
            con_carga.metric(label="Carga (Load)", value=f"{carga:.0f}")

            panel_alerta.error(f"**Avería Inminente:** {causa_detectada.upper()} (Certeza: {confianza:.1f}%)")

            texto_diagnostico = "### Análisis de Causa\nLos sensores más desviados de la normalidad son:\n"
            for sensor in COLUMNAS_SENSORES:
                val_vivo = float(X_live[sensor].iloc[0])
                val_norm = promedios_normales[sensor]
                if val_norm != 0:
                    desv = abs((val_vivo - val_norm) / val_norm) * 100
                    if desv > 10:
                        flecha = "⬆️" if val_vivo > val_norm else "⬇️"
                        texto_diagnostico += f"* **{sensor}:** {val_vivo:.1f} ({flecha} *Normal: ~{val_norm:.1f}*)\n"

            panel_diagnostico.warning(texto_diagnostico)

            # Buscar Solución
            try:
                df_solucion = pd.read_sql(f"SELECT TOP 1 Solucion FROM registro_fallas WHERE Causa = '{causa_detectada}' ORDER BY Fecha DESC", con=motor_sql)
                if not df_solucion.empty:
                    panel_solucion.info(f"**ACCIÓN PRESCRIPTIVA:**\n\n{df_solucion['Solucion'].iloc[0]}")
                else:
                    panel_solucion.info("**ACCIÓN PRESCRIPTIVA:** No hay solución registrada previa para este evento.")
            except:
                pass

        time.sleep(2)

    except Exception as e:
        panel_estado.error(f"⚠️ Error de conexión: {e}")
        time.sleep(5)