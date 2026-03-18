# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 14:47:56 2026

@author: psistemaspl
"""

import pandas as pd
import os
import csv
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest


nombre_archivo = 'test_2.txt'
ruta_completa =os.path.join('..', 'data', 'raw', nombre_archivo)

def detector_anomalias():
    print("Cargando datos historicos....")
    
    #carga y limpieza
    df = pd.read_csv(ruta_completa,
                     sep=',', 
                     encoding='utf-8',
                     skiprows=[1],
                     quoting=csv.QUOTE_NONE,
                     on_bad_lines='skip')
    
    df.columns = df.columns.str.strip()
    
    #buscamos la columna de tiempo
    col_tiempo = None
    for col in df.columns:
        if 'time' in col.lower() or 'date' in col.lower():
            col_tiempo = col
            break
        
    if col_tiempo:
        df[col_tiempo] = pd.to_datetime(df[col_tiempo], errors='coerce')
        df = df.dropna(subset=[col_tiempo])
      
        print(f"Filas con tiempo válido: {len(df)}")
        
        if len(df) == 0:
            print("ERROR CRÍTICO: La tabla quedó vacía tras limpiar el tiempo.")
            return None # Abortar misión para no saturar a la IA
    else:
        print("No se detecto columna de tiempo")
        return None
    
    
        
    #preparacion ia
    print("Preparando datos para ia")
    
    #columnas_sensores = df.select_dtypes(include=['float64', 'int64']).columns
    #df_sensores = df[columnas_sensores].dropna()
    columnas_sensores = df.columns.drop(col_tiempo)
    for col in columnas_sensores:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna()
    
    #preparacion ia
    print("Preparando datos para ia")
    df_sensores = df[columnas_sensores]
    
    #entrenamiento modelo isolation forest
    print("Entrenando el algoritmo IF")
    
    modelo=IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
    
    #analiza los datos
    df_sensores['Anomalia'] = modelo.fit_predict(df_sensores)
    
    #union en la tabla
    df_final = df.loc[df_sensores.index].copy()
    df_final['Anomalia'] = df_sensores['Anomalia']
    
    #resultados 1-normal, -1-anomalia
    normales = len(df_final[df_final['Anomalia'] == 1])
    anomalos = len(df_final[df_final['Anomalia'] == -1])
    print(f"¡Análisis completado! Datos normales: {normales} | Anomalías detectadas: {anomalos}")
    
   
    #grafica de resusltados
   
    print("Generando gráfica con detecciones en todas las señales")
    
    #filtro para graficar
    df_normal = df_final[df_final['Anomalia'] == 1]
    df_peligro = df_final[df_final['Anomalia'] == -1]
    
    plt.figure(figsize=(25, 10))
    
    eje_x_normal = df_normal[col_tiempo] if col_tiempo else df_normal.index
    eje_x_peligro = df_peligro[col_tiempo] if col_tiempo else df_peligro.index
    
    for sensor in columnas_sensores:
        plt.plot(eje_x_normal, df_normal[sensor], linestyle='-', marker='', alpha=0.5, label=f'Normal {sensor}')
        plt.plot(eje_x_peligro, df_peligro[sensor], linestyle='none', marker='o', color='red', markersize=6)
    

    plt.title('Detector de IA: Anomalias en todos los sensores', fontsize=18)
    plt.xlabel('Tiempo', fontsize=14)
    plt.ylabel('Valor del sensor', fontsize=14)
    
    plt.xticks(rotation=60, ha='right')
    
    plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    
    """ruta_foto = os.path.abspath('anomalias_detectadas.png')
    plt.savefig(ruta_foto, dpi=300, bbox_inches='tight')
    print(f"¡FOTO DE ANOMALÍAS GUARDADA EN: {ruta_foto}")"""
    
    plt.show()
    
    return df_final
    
if __name__ == "__main__":
    datos_analizados = detector_anomalias()