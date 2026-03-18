# -*- coding: utf-8 -*-

import pandas as pd
import os
import matplotlib.pyplot as plt

nombre_archivo = 'mesa_cursores.txt'
ruta_completa = os.path.join('..', 'data', 'raw', nombre_archivo)

def graficar_seguro():
    print("⏳ Cargando datos de la mesa de cursores...")
    df = pd.read_csv(ruta_completa, sep=';', encoding='utf-8', on_bad_lines='skip')
    
    # 1. Limpiamos espacios invisibles en los nombres de las columnas
    df.columns = df.columns.str.strip()
    
    # Usaremos las columnas que vi en tus fotos
    col_tiempo = 'Unnamed: 1'
    col_valor = '[4:25.max]'
    
    if col_tiempo in df.columns and col_valor in df.columns:
        print(f"✅ Columnas encontradas: {col_tiempo} y {col_valor}")
        
        # 2. EL TRUCO: Le decimos el formato EXACTO de la fecha de ibaAnalyzer
        # %d (día) . %m (mes) . %Y (año) %H:%M:%S (hora) . %f (milisegundos)
        df[col_tiempo] = pd.to_datetime(df[col_tiempo], format='%d.%m.%Y %H:%M:%S.%f', errors='coerce')
        
        # 3. Forzamos el valor a número
        df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce')
        
        # Limpiamos las filas que hayan quedado vacías
        df_limpio = df.dropna(subset=[col_tiempo, col_valor])
        print(f"📊 Filas listas para graficar: {len(df_limpio)}")
        
        if len(df_limpio) > 0:
            print("📈 Dibujando gráfica...")
            plt.figure(figsize=(12, 5))
            
            plt.plot(df_limpio[col_tiempo], df_limpio[col_valor], marker='o', 
                     color='blue', linewidth=1.5, label='Valor Máximo [4:25]')
            
            plt.title('Tendencia de la Señal [4:25] (Mesa de Cursores)')
            plt.xlabel('Fecha y Hora')
            plt.ylabel('Valor del Sensor')
            plt.grid(True)
            plt.xticks(rotation=45) 
            plt.legend()
            plt.tight_layout()
            
            # --- NUEVAS LÍNEAS: GUARDAR COMO FOTO ---
            ruta_foto = os.path.abspath('mi_primera_grafica.png')
            plt.savefig(ruta_foto, dpi=300) # dpi=300 es para alta calidad HD
            print(f"📸 ¡FOTO GUARDADA! Búscala en esta ruta: {ruta_foto}")
            # ----------------------------------------
            
            plt.show()
            print("✅ ¡Proceso completado!")
        else:
            print("⚠️ Sigue sin haber filas válidas.")
            
    else:
        print("❌ No se encontraron las columnas. Estos son los nombres reales en tu archivo:")
        print(df.columns.tolist())

if __name__ == "__main__":
    graficar_seguro()