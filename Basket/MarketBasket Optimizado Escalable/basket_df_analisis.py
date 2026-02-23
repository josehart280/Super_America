'''Este codigo fue la mayor creacion mia propia de momento, aplicando lo que se en python y lo que se de analisis de datos, es una version optimizada del codigo original que se encuentra en BasketMarket.py, esta version esta diseñada para ser mas eficiente y escalable, permitiendo analizar grandes volúmenes de datos con muchos productos sin saturar la memoria RAM, utilizando procesamiento por lotes y almacenamiento temporal en disco para manejar la matriz de co-ocurrencia y las reglas generadas. 
By Jose Porrras Ramirez'''

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import time
import gc
import os
from scipy.sparse import csr_matrix, lil_matrix, save_npz, load_npz

import warnings
warnings.filterwarnings('ignore')

from cargar_datos import DataLoader
from crear_matriz import MatrixBuilder
from generar_reglas import RuleGenerator
from powerbi_exportar import PowerBIExporter

class MarketBasketAnalyzerUltra:
    """
    Versión ultra-escalable que procesa por lotes y usa disco para grandes volúmenes basado para poca RAM (16GB o menos) y datasets com muchos productos como supermercados
    """
    
    def __init__(self, archivo, hoja='VentasLimpias', temp_dir='temp_basket'):
        self.archivo = archivo
        self.hoja = hoja
        self.temp_dir = temp_dir
        self.df = None
        self.productos_dict = {}
        self.productos_inv_dict = {}
        self.soportes = None
        self.n_transacciones = 0
        
        #Crear directorio temporal ya que la ram no es suficiente para manejar todo en memoria almenos no en mi computadora
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        self.data_loader = DataLoader(archivo, hoja, temp_dir)
        self.matrix_builder = MatrixBuilder(temp_dir)
        self.rule_generator = RuleGenerator(temp_dir)
        self.powerbi_exporter = PowerBIExporter(archivo, hoja)
    
    def cargar_datos_completos(self, min_ocurrencias=5):
        """
        Carga TODOS los productos que aparecen al menos min_ocurrencias veces
        """
        self.df, self.productos_dict, self.productos_inv_dict, self.n_transacciones = self.data_loader.cargar_datos_completos(min_ocurrencias)
        return self
    
    def crear_matriz_co_ocurrencia_por_lotes(self, lote_size=500):
        """
        Crea matriz de co-ocurrencia procesando por lotes y guardando en disco para mejorar eficiencia y evitar problemas de memoria, permitiendo analizar datasets de supermercados con miles de productos y millones de transacciones
        """
        self.soportes = self.matrix_builder.crear_matriz_co_ocurrencia_por_lotes(
            self.df, self.productos_dict, self.n_transacciones, lote_size
        )
        return self
    
    def calcular_reglas_por_lotes(self, min_soporte_pct, min_confianza_pct, 
                              min_lift=1.0, max_reglas=50000, generar_inversas=True):
        """
        Calcula reglas procesando por lotes y limitando resultados
        """
        return self.rule_generator.calcular_reglas_por_lotes(
        self.productos_dict, 
        self.productos_inv_dict, 
        self.n_transacciones,
        min_soporte_pct, 
        min_confianza_pct, 
        min_lift, 
        max_reglas, 
        generar_inversas
    )
    
    def exportar_para_powerbi(self, df_reglas, archivo_salida='market_basket_powerbi_completo.csv'):
        """
        Exporta resultados en formato listo para PowerBI y analisis segun el documento de requisitos 
        """
        return self.powerbi_exporter.exportar_para_powerbi(df_reglas, archivo_salida)
    
    def limpiar_temp(self):
        """Limpia archivos temporales"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        print(f" Archivos temporales eliminados")