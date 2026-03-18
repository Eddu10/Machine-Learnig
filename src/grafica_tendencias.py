# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 14:49:58 2026

@author: psistemaspl
"""

import pandas as pd
import os
import csv
import matplotlib.pyplot as plt

nombre_archivo = 'test_2.txt'
ruta_completa = os.path.join('..', 'data', 'raw', nombre_archivo)

def visualizar_datos():
    print("Cargando  datos para la grafica...")
    
    df = pd.read_csv(ruta_completa, nrows=1000, sep=',', encoding='utf-8',
                     skiprows=[1], quoting=csv.QUOTE_NONE, on_bad_lines='skip')
    
    
    #time a un reloj de python
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
    
    df=df.dropna(subset=['Time'])
    
    #forzar que todas las columnas sean numeros
    columnas_sensores = df.columns.drop('Time')
    for col in columnas_sensores:
        df[col]=pd.to_numeric(df[col], errors='coerce')
    
    #grafica
    print("Generado Grafica....")
    plt.figure(figsize=(12, 5))
    
    plt.plot(df['Time'], df['[2:55]'], label='Señal [2:55]', color='blue', linewidth=1.5)
    plt.plot(df['Time'], df['[2:68]'], label='Señal [2:68]', color='red', linewidth=1.5)
    
    
    plt.title('Tendencia de Sensores del PLC')
    plt.xlabel('Hora')
    plt.ylabel('Valor del sensor')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    plt.show()
    print("Grafica completada")
    

if __name__ == "__main__":
    visualizar_datos()