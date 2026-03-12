# -*- coding: utf-8 -*-

import pandas as pd
import os
import csv
import time

nombre_archivo = 'prueba.txt'
ruta_completa = os.path.join('..', 'data', 'raw', nombre_archivo)

def analizar():
    if not os.path.exists(ruta_completa):
        print(f"No encuentro el archivo en: {ruta_completa}")
        return None
    
    print("Iniciando la lectura de prueba (500 filas)...")
    tiempo_inicio = time.time()
    
    tamaño_bloque = 10
    filas_totales = 0
    lista_bloques = []
    
    try:
        #500 filas iniciales
        lector_datos = pd.read_csv(ruta_completa,
                         nrows=50,
                         chunksize=tamaño_bloque,
                         sep = ',', 
                         encoding = 'utf-8', 
                         skiprows=[1],
                         quoting=csv.QUOTE_NONE,
                         on_bad_lines='warn')
        
        for bloque in lector_datos:
            lista_bloques.append(bloque)
            filas_totales += len(bloque)
            print(f"Procesando....{filas_totales} filas leidas")
        
        print("Ensamblando los datos...")
        df_final = pd.concat(lista_bloques, ignore_index=True)
        
        tiempo_fin = time.time()
        segundos = round(tiempo_fin - tiempo_inicio, 2)
        
        print(f"¡Carga de prueba completada en {segundos} segundos!")
        print(f"Total de columnas: {len(df_final.columns)}")
        
        print("\n--- Tipos de datos detectados ---")
        print(df_final.dtypes.head(10))
        
        
        
        return df_final
    
    except Exception as e:
        print(f"Error al procesar el Archivo: {e}")
        return None
    
   
    

if __name__ == "__main__":
    datos = analizar()