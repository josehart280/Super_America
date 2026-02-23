'''Este codigo fue la mayor creacion mia propia de momento, aplicando lo que se en python y lo que se de analisis de datos, es una version optimizada del codigo original que se encuentra en BasketMarket.py, esta version esta diseñada para ser mas eficiente y escalable, permitiendo analizar grandes volúmenes de datos con muchos productos sin saturar la memoria RAM, utilizando procesamiento por lotes y almacenamiento temporal en disco para manejar la matriz de co-ocurrencia y las reglas generadas. 
By Jose Porrras Ramirez'''

import numpy as np
import time
import gc
import os
from scipy.sparse import lil_matrix, save_npz

class MatrixBuilder:
    def __init__(self, temp_dir='temp_basket'):
        self.temp_dir = temp_dir
    
    def crear_matriz_co_ocurrencia_por_lotes(self, df, productos_dict, n_transacciones, lote_size=500):
        """
        Crea matriz de co-ocurrencia procesando por lotes y guardando en disco para mejorar eficiencia y evitar problemas de memoria, permitiendo analizar datasets de supermercados con miles de productos y millones de transacciones
        """
        print("\n" + "="*60)
        print("CREANDO MATRIZ DE CO-OCURRENCIA (PROCESAMIENTO POR LOTES)")
        print("="*60)
        
        start = time.time()
        
        #Agrupar por factura
        facturas = df.groupby('ID_Compra')['Descripcion'].agg(list)
        n_productos = len(productos_dict)
        
        #Inicializar soportes
        soportes = np.zeros(n_productos, dtype=np.int32)
        
        #Procesar facturas para calcular soportes primero en vez de hacerlo masivamente como en el anterior codigo
        print("\nCalculando soportes individuales...")
        facturas_procesadas = 0
        total_facturas = len(facturas)
        
        #reducimos el numero de co-ocurrencias a calcular
        for items in facturas:
            items_unicos = set(items)

            for item in items_unicos:
                if item in productos_dict:

                    soportes[productos_dict[item]] += 1
            facturas_procesadas += 1
            #Mostrar progreso cada 10,000 facturas procesadas
            if facturas_procesadas % 10000 == 0:
                print(f"  Procesadas {facturas_procesadas:,}/{total_facturas:,} facturas...")
        
        #Guardar soportes en disco temporales para analisis posterior
        np.save(f'{self.temp_dir}/soportes.npy', soportes)
        
        # Identificar productos frecuentes  asi filtramos y vemos que tan alto es el sopoerte promedio, esto es importante para entender la distribución de los productos y ajustar umbrales de soporte en el analisis de reglas
        soporte_medio = np.mean(soportes)
        print(f"\nEstadisticas de soporte:")
        print(f" Soporte promedio: {soporte_medio:.2f} facturas")
        print(f" Productos con soporte > 0: {(soportes > 0).sum():,}")
        print(f" Productos con soporte > 10: {(soportes > 10).sum():,}")
        print(f" Productos con soporte > 50: {(soportes > 50).sum():,}")
        
        #Calcular co-ocurrencias por lotes
        #despues de calcular soportes individuales, ahora si calculamos co-ocurrencias pero por lotes para evitar saturar la memoria
        print("\n Calculando co-ocurrencias por lotes...")
        
        #divido productos en lotes
        todos_productos = np.arange(n_productos)

        #procesamos por partes para no saturar la memoria
        lotes_productos = [todos_productos[i:i+lote_size] for i in range(0, n_productos, lote_size)]
        


        print(f"Total de lotes a procesar: {len(lotes_productos)}")




        #Procesar cada lote
        for lote_idx, lote_productos in enumerate(lotes_productos):
            start_lote = time.time()
            
            #Crear matriz para este lote
            matriz_lote = lil_matrix((len(lote_productos),  n_productos),  dtype=np.int32)
            
            #Mapeo de indices globales a locales para este lote, esto es importante para reducir el tamaño de la matriz y mejorar eficiencia al trabajar con índices numéricos en lugar de strings
            idx_global_a_local = {global_idx: local_idx for local_idx, global_idx in enumerate(lote_productos)}
            
            #Procesar cada factura y actualizar co-ocurrencias solo para productos en este lote
            for items in facturas:

                items_unicos = set(items)

                indices = [productos_dict[item] for item in items_unicos if item in productos_dict]
                
                #Solo nos interesan las co-ocurrencias con productos de este lote, esto es clave para reducir el número de co-ocurrencias a calcular y mejorar eficiencia
                for i, idx_a in enumerate(indices):
                    if idx_a in idx_global_a_local:
                        local_a = idx_global_a_local[idx_a]
                        for j, idx_c in enumerate(indices):
                            if i != j:  #No contar consigo mismo y evitar duplicados
                                matriz_lote[local_a, idx_c] += 1
            
            #Guardar 
            save_npz(f'{self.temp_dir}/lote_{lote_idx}.npz', matriz_lote.tocsr())
            
            #Mostrar progreso por depuracion nada mas
            tiempo_lote = time.time() - start_lote
            print(f"Lote {lote_idx + 1}/{len(lotes_productos)} completado en {tiempo_lote:.2f} seg")
            
            #Liberar memoria IMPORTANTE para no saturar RAM, ya me paso que se saturaba la memoria al procesar el siguiente lote porque no se liberaba la matriz del lote anterior
            del matriz_lote
            gc.collect()
        
        print(f"\n Matriz creada por lotes en {time.time() - start:.2f} seg")
        print(f" Archivos guardados en: {self.temp_dir}")
        
        return soportes