# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 11:09:11 2026

@author: psistemaspl
"""

# -*- coding: utf-8 -*-

import pandas as pd
import os

# Tu archivo nuevo
nombre_archivo = 'mesa_cursores.txt'
ruta_completa = os.path.join('..', 'data', 'raw', nombre_archivo)

def procesar_cursores():
    if not os.path.exists(ruta_completa):
        print(f"No encuentro el archivo en: {ruta_completa}")
        return None
        
    print("Cargando y analizando mesa de cursores...")
    
    df = pd.read_csv(ruta_completa, sep=';', encoding='utf-8', on_bad_lines='skip')
    
    #Detectar Fechas vs Números
    for col in df.columns:
        muestra = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else ""
        
      
        if len(muestra) > 15 and muestra.count('.') >= 2 and ':' in muestra:
            # Lo convertimos a reloj de Python respetando el formato de ibaAnalyzer
            df[col] = pd.to_datetime(df[col], format='%d.%m.%Y %H:%M:%S.%f', errors='coerce')
        else:
            # Si no es fecha, lo forzamos a número decimal
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    print("¡Limpieza completada!")
    print("\n--- Tipos de datos detectados ---")
    print(df.dtypes.head(10))
    
    return df

if __name__ == "__main__":
    datos = procesar_cursores()