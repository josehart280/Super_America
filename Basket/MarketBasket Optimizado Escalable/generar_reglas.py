'''Este codigo fue la mayor creacion mia propia de momento, aplicando lo que se en python y lo que se de analisis de datos, es una version optimizada del codigo original que se encuentra en BasketMarket.py, esta version esta diseñada para ser mas eficiente y escalable, permitiendo analizar grandes volúmenes de datos con muchos productos sin saturar la memoria RAM, utilizando procesamiento por lotes y almacenamiento temporal en disco para manejar la matriz de co-ocurrencia y las reglas generadas. 
By Jose Porrras Ramirez'''

import numpy as np
import pandas as pd
import time
import gc
import os
from scipy.sparse import load_npz

class RuleGenerator:
    def __init__(self, temp_dir='temp_basket'):
        self.temp_dir = temp_dir
    
    def calcular_reglas_por_lotes(self, productos_dict, productos_inv_dict, n_transacciones,
                                  min_soporte_pct, min_confianza_pct, 
                                  min_lift=1.0, max_reglas=50000, generar_inversas=True):
        """
        Calcula reglas procesando por lotes y limitando resultados
        """

        #Depuracion para ver el impacto de los umbrales en el numero de reglas generadas, esto es importante para ajustar los umbrales y entender el trade-off entre cantidad y calidad de las reglas generadas
        print("\n" + "="*60)
        
        print(f"CALCULANDO REGLAS POR LOTES")
        print(f"Soporte mnimo : {min_soporte_pct}% | Confianza: {min_confianza_pct}% | Lift: {min_lift}")
        print("="*60)
        start = time.time()
        

        #porcentajes a absolutos
        min_soporte = min_soporte_pct /100
        min_confianza = min_confianza_pct 
        n_trans = n_transacciones
        umbral_soporte_abs = int(min_soporte * n_trans)
        
        print(f"\n Umbral soporte: {umbral_soporte_abs} facturas")
        
        # Cargar soportes
        soportes = np.load(f'{self.temp_dir}/soportes.npy')
        


        #Identificar productos frecuentes para reducir el numeor de reglas  a calcular
        productos_frecuentes = np.where(soportes >= umbral_soporte_abs)[0]
        print(f"   Productos frecuentes: {len(productos_frecuentes):,}")
        


        #Si hay demasiados productos frecuentes, limitarlos
        if len(productos_frecuentes) > 5000:
            print(f" Demasiados productos frecuentes, limitando a top 5000...")
            # Ordenar por soporte y tomar top
            top_indices = np.argsort(soportes[productos_frecuentes])[-5000:]
            productos_frecuentes = productos_frecuentes[top_indices]
            print(f"  Productos después de limitar: {len(productos_frecuentes):,}")
        
        #Procesar lotes de la matriz uno por uno
        archivos_lote = sorted([f for f in os.listdir(self.temp_dir) if f.startswith('lote_') and f.endswith('.npz')])
        


        todas_reglas = []
        reglas_por_lote = []
        inicio_global = 0 

        #Procesar cada lote de reglas
        for lote_idx, archivo_lote in enumerate(archivos_lote):
            print(f"\nProcesando lote {lote_idx + 1}/{len(archivos_lote)}...")
            
            
            matriz_lote = load_npz(f'{self.temp_dir}/{archivo_lote}').tocsr()

            n_filas = matriz_lote.shape[0]            #cantidad de productos en este lote
            
            indices_lote = np.arange(inicio_global, inicio_global + n_filas)  

            productos_en_lote = 0
            
            #Filtrar solo productos frecuentes en este lote
            for local_a in range(n_filas):
                idx_a = indices_lote[local_a]
                if idx_a not in productos_frecuentes:
                    continue

                productos_en_lote += 1


                fila = matriz_lote[local_a].toarray().flatten()


                #encontrar co-ocurrencias significativas para este producto antecedente

                co_ocurrencias = np.where(fila >= umbral_soporte_abs)[0]






                #Filtrar solo productos frecuentes para el consecuente en el CSV
                for idx_c in co_ocurrencias:
                    if idx_c <= idx_a:  # Evitar duplicados
                        continue
                    
                    if idx_c not in productos_frecuentes:
                        continue
                    
                    #calculamos métricas
                    soporte_a = soportes[idx_a]
                    soporte_c = soportes[idx_c]
                    soporte_ab = fila[idx_c]

                    #calculo basico de basket market 
                    confianza = soporte_ab / soporte_a
                    lift = (soporte_ab * n_trans) / (soporte_a * soporte_c)

                    if confianza >= min_confianza and lift >= min_lift:
                        reglas_por_lote.append({
                            'antecedente': productos_inv_dict[idx_a],
                            'consecuente': productos_inv_dict[idx_c],
                            'soporte_a': soporte_a / n_trans * 100,
                            'soporte_c': soporte_c / n_trans * 100,
                            'soporte_ab': soporte_ab / n_trans * 100,
                            'confianza': confianza * 100,
                            'lift': round(lift/125, 2), #el lift no se toca ni se divide en este caso solo lo hice porque los soportes son tan     minimos que unicamente se pueden intepretar en esta escala comparando productos x ventas en estos 3MESES
                            'conteo': int(soporte_ab)
                        })


            print(f"   Productos procesados en este lote: {productos_en_lote}")


            inicio_global += n_filas

            #Si acumulamos muchas reglas, guardar lote de resultados si hay muchos
            if len(reglas_por_lote) > 10000:

                df_lote = pd.DataFrame(reglas_por_lote)
                df_lote.to_csv(f'{self.temp_dir}/reglas_lote_{lote_idx}.csv', index=False)
                todas_reglas.extend(reglas_por_lote)

                reglas_por_lote = []


                print(f"\n Guardadas {len(df_lote):,} reglas intermedias")
            
            #Liberar memoria
            
            del matriz_lote
            
            gc.collect()
        
        #Agregar últimas reglas
        if reglas_por_lote:
            
            todas_reglas.extend(reglas_por_lote)
        

        #Crear DataFrame final para el CSV
        df_reglas = pd.DataFrame(todas_reglas)


        if generar_inversas and len(df_reglas) > 0 and len(df_reglas) < max_reglas:
            print(f"\nGenerando reglas inversas...")
            reglas_inversas = []
            
            for _, row in df_reglas.iterrows():
                # Calcular confianza inversa
                confianza_inv = row['soporte_ab'] / row['soporte_c']
                
                # Usar umbral mínimo similar al original (1%)
                if confianza_inv >= 1.0:  # 1% como en el original
                    reglas_inversas.append({
                        'antecedente': row['consecuente'],
                        'consecuente': row['antecedente'],
                        'soporte_a': row['soporte_c'],
                        'soporte_c': row['soporte_a'],
                        'soporte_ab': row['soporte_ab'],
                        'confianza': confianza_inv,
                        'lift': row['lift'],  # El lift es simétrico
                        'conteo': row['conteo']
                    })
            
            if reglas_inversas:
                df_inversas = pd.DataFrame(reglas_inversas)
                df_reglas = pd.concat([df_reglas, df_inversas], ignore_index=True)
                df_reglas.drop_duplicates(subset=['antecedente', 'consecuente'], inplace=True)

                print(f"  Anadidas {len(df_inversas)} reglas inversas")


        
        #Filtrar por umbral de confianza y lift para asegurar calidad de reglas
        if len(df_reglas) > 0:
            df_reglas.sort_values(by='lift', ascending=False, inplace=True)
            
            #Limitar número de reglas si es necesario en este caso las quiero todas pero si se quisiera limitar a las mejores se podria hacer aqui, esto es importante para evitar saturar la memoria y enfocarse en las reglas más relevantes para el negocio
            if max_reglas and len(df_reglas) > max_reglas:
                print(f"\nLimitando a top {max_reglas} reglas...")
                df_reglas = df_reglas.head(max_reglas)
        
        #comprobacion
        print(f"\nReglas calculadas en {time.time() - start:.2f} seg")
        print(f" Reglas encontradas: {len(df_reglas):,}")
        
        return df_reglas