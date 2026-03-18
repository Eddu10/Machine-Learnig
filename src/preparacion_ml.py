# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 11:49:16 2026

@author: psistemaspl
"""

import pandas as pd
import os
import csv

nombre_archivo = 'test_2.txt'
ruta_completa = os.path.join('..', 'data', 'raw', nombre_archivo)

def cargar_datos_limpios():
    print(f"Cargando datos continuos de {nombre_archivo}...")
    
    df = pd.read_csv(ruta_completa,
                     sep=',',
                     encoding='utf-8',
                     skiprows=[1],
                     quoting=csv.QUOTE_NONE,
                     on_bad_lines='skip')
    
    df.columns = df.columns.str.strip()
    
    col_tiempo  = None
    for col in df.columns:
        if 'time' in col.lower() or 'date' in col.lower():
            col_tiempo = col
            break
    
    if col_tiempo:
        df[col_tiempo] = pd.to_datetime(df[col_tiempo], errorrs='coerce')
        df = df.dropna(subset=[col_tiempo])
        columnas_sensores = df.columns.drop(col_tiempo)
    else:
        columnas_sensores = df.columns
        
    #todo a numeros
    print("Limpiando señales")
    for col in columnas_sensores:
        df[col] = df.to_numeric(df[col], errors='coerce')
    
    print(f"Datos listos, {len(df)} filas cargadas correctamente")
    return df, col_tiempo


if __name__ == '__mai__':
    datos_historicos, columna_tiempo = cargar_datos_limpios()