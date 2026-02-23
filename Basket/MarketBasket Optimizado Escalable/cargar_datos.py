'''Este codigo fue la mayor creacion mia propia de momento, aplicando lo que se en python y lo que se de analisis de datos, es una version optimizada del codigo original que se encuentra en BasketMarket.py, esta version esta diseñada para ser mas eficiente y escalable, permitiendo analizar grandes volúmenes de datos con muchos productos sin saturar la memoria RAM, utilizando procesamiento por lotes y almacenamiento temporal en disco para manejar la matriz de co-ocurrencia y las reglas generadas. 
By Jose Porrras Ramirez'''

import pandas as pd
import numpy as np
import os

class DataLoader:
    def __init__(self, archivo, hoja='VentasLimpias', temp_dir='temp_basket'):
        self.archivo = archivo
        self.hoja = hoja
        self.temp_dir = temp_dir
    
    def cargar_datos_completos(self, min_ocurrencias=5):
        """
        Carga TODOS los productos que aparecen al menos min_ocurrencias veces
        """
        print("="*60)
        print("CARGANDO DATOS COMPLETOS")
        print("="*60)
        
        #Cargar datos
        df = pd.read_excel(self.archivo, sheet_name='VentasLimpias', engine='openpyxl')
        

        #Estadisticas iniciales para posterior comparación y limpieza 
        print(f"Facturas unicas: {df['ID_Compra'].nunique():,}")
        print(f"Productos únicos iniciales: {df['Descripcion'].nunique():,}")
        


        #Filtrar productos con muy pocas ocurrencias (ruido) segun analisis previo, esto es importante para reducir el tamaño de la matriz de co-ocurrencia y evitar productos que no aportan valor 
        freq_productos = df.groupby('Descripcion')['ID_Compra'].nunique()

        productos_validos = freq_productos[freq_productos >= min_ocurrencias].index
        df = df[df['Descripcion'].isin(productos_validos)]
        


        #comprobar que se ha cargado correctamente
        print(f"\nFiltrando productos con ≥ {min_ocurrencias} facturas...")

        print(f"Productos después de filtro: {df['Descripcion'].nunique():,}")
        


        # Crear diccionarios de productos porque son la ultima parte que se carga en memoria y es necesario para mapear a índices en la matriz de co-ocurrencia, esto es importante para reducir el tamaño de la matriz y mejorar eficiencia al trabajar con índices numéricos en lugar de strings
        productos_unicos = df['Descripcion'].unique()
        productos_dict = {prod: idx for idx, prod in enumerate(productos_unicos)}
        # de paso nos libramos de los productos con muy pocas ocurrencias que no aportan valor y solo generan ruido en el análisis, esto es importante para mejorar la calidad de las reglas generadas y reducir el tiempo de procesamiento al enfocarnos en productos más relevantes para los clientes y el negocio
        productos_inv_dict = {idx: prod for prod, idx in productos_dict.items()}


        #grupar por factura para tener una lista unica
        n_transacciones = df['ID_Compra'].nunique()
        
        print(f"\nResumen final:")
        print(f" Facturas: {n_transacciones:,}")
        print(f" Productos: {len(productos_dict):,}")
        print(f" Líneas: {len(df):,}")
        
        return df, productos_dict, productos_inv_dict, n_transacciones