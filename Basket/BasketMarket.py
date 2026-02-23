'''Este codigo es el codigo Basket Analytics, poniendo en practica lo que he aprendido durante mi carrera,
aqui he utilizado un excel donde despues se crea un dataframe con los datos de los tickets para analizarlos y usar el algoritmo Apriori
Trate de poner comentarios en cada parte del codigo para que se entienda lo que hace cada parte, ademas de imprimir por consola las configuraciones y los resultados para que sea mas facil de interpretar, tambien exporto los resultados a un csv para poder analizarlos mejor despues Se pueden eliminar todos las impresiones de la consola y aun asi funciona el codigo por si se desea usarlo sin tanta informacion en la consola, puedes cambiar parametros segun necesites de la configurcion inicial prara obtener resultados esperados'''

import pandas as pd
import Funciones as fn
from itertools import combinations
import time

# 
# CONFIGURACIÓN DE PARÁMETROS 
# 

# --- SOPORTE MÍNIMO 
# Define el % mínimo de transacciones que debe aparecer un producto
# EJEMPLO: 0.05 = 0.05% de 31,640 transacciones = 15-16 transacciones
SOPORTE_MINIMO = 0.00005  # Rango típico: 0.03 a 1.0 (más bajo = más reglas)

# --- CONFIANZA MÍNIMA
# Probabilidad mínima de que se compre B dado que se compró A
CONFIANZA_MINIMA = 10 # Rango típico: 5 a 30 (más bajo = más reglas)

# --- LIFT MÍNIMO
# Mide significancia estadística (1 = independiente, >1 = relación positiva)
LIFT_MINIMO = 1.1  # Rango típico: 1.1 a 2.0

# --- OTRAS CONFIGURACIONES
TOP_REGLAS_A_MOSTRAR = 50  # Cuántas reglas mostrar en consola
EXPORTAR_RESULTADOS = True  

# Fin de lsa configuraciones






MIN_CONFIDENCE_DECIMAL = CONFIANZA_MINIMA / 100


# Validamos por consola las cofiguraciones antes de ejecutar
print("="*60)
print("CONFIGURACIÓN ACTUAL DEL ANÁLISIS")
print("="*60)
print(f"SOPORTE MÍNIMO: {SOPORTE_MINIMO}% de transacciones")
print(f"   (equivale a {SOPORTE_MINIMO:.4f} en decimal)")
print(f"CONFIANZA MÍNIMA: {CONFIANZA_MINIMA}% de probabilidad")
print(f"   (equivale a {MIN_CONFIDENCE_DECIMAL:.3f} en decimal)")
print(f"LIFT MÍNIMO: {LIFT_MINIMO}")
print(f"Mostrar top {TOP_REGLAS_A_MOSTRAR} reglas")
print("="*60)
print()

try:
    archivo = 'C:\\Users\\joans\\Documents\\data\\Super America\\Datos\\Ventas Limpias.xlsx'
    
    print("Cargando archivo de ventas...")
    inicio_carga = time.time()

    df = pd.read_excel(archivo)
    print(f"Archivo cargado en {time.time() - inicio_carga:.2f} segundos")

    print(f"Registros totales: {len(df)}")

    #imprimo la informacion del dataframe para verificar los tipos de datos
    print("\nInfo del dataframe:")
    df.info()

    # Convertir la columna 'fecha' a formato datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'])


    #dataframe con solo las columnas necesarias
    print("\nDataframe con solo las columnas necesarias para el analisis:")
    df_cesta = df[['ID_Compra', 'Descripcion']]


    print(f"Total transacciones únicas: {df_cesta['ID_Compra'].nunique()}")
    print(f"Total productos únicos: {df_cesta['Descripcion'].nunique()}")

    #Agrupar productos por pedido
    print("\nAgrupando productos por pedido...")
    df_agrupado = df_cesta.groupby('ID_Compra')['Descripcion'].apply(lambda x: ','.join(x))
    
    #Eliminar duplicados dentro del mismo pedido (por si acaso)
    df_agrupado = df_agrupado.apply(lambda x: ','.join(sorted(set(x.split(',')))))
    
    print(f"Pedidos procesados: {len(df_agrupado)}")

    #Crear matriz binaria (one-hot encoding)
    print("\nCreando matriz de transacciones...")
    df_transacciones = df_agrupado.str.get_dummies(sep=',')

    print(f"Dimensiones matriz: {df_transacciones.shape}")
    print(f"Filas (transacciones): {df_transacciones.shape[0]}")
    print(f" Columnas (productos): {df_transacciones.shape[1]}")

    # Calcular estadísticas básicas
    
    print("ESTADÍSTICAS BÁSICAS")
    print("")
    
    # Productos más frecuentes
    print("\nTop 10 productos más frecuentes (% de pedidos):")
    soporte = df_transacciones.mean() * 100
    top_productos = soporte.nlargest(10)
    for producto, sop in top_productos.items():
        # Calcular número aproximado de transacciones
        num_trans = int(sop / 100 * len(df_transacciones))
        print(f"  {producto}: {sop:.2f}% (≈{num_trans} transacciones)")
    
    # Distribución de tamaño de pedidos
    tamanos_pedidos = df_transacciones.sum(axis=1)
    print(f"\nEstadísticas de tamaño de pedido:")
    print(f" Mínimo: {tamanos_pedidos.min()} producto(s)")
    print(f" Máximo: {tamanos_pedidos.max()} producto(s)")
    print(f" Promedio: {tamanos_pedidos.mean():.2f} productos")
    print(f" Mediana: {tamanos_pedidos.median():.0f} productos")
    
    

    # APLICAR ALGORITMO APRIORI
    print("\n" + "="*50)
    print("ALGORITMO APRIORI")
    print("="*50)
    
    # Calcular número de transacciones para el soporte
    num_transacciones_soporte = int(SOPORTE_MINIMO * len(df_transacciones))
    
    print(f"\nConfiguración:")
    print(f" Soporte mínimo: {SOPORTE_MINIMO}% ({num_transacciones_soporte} transacciones)")
    print(f" (valor decimal usado: {SOPORTE_MINIMO:.6f})")
    print(f" Confianza mínima: {CONFIANZA_MINIMA}%")
    print(f" (valor decimal usado: {MIN_CONFIDENCE_DECIMAL:.3f})")
    print(f" Lift mínimo: {LIFT_MINIMO}")
    

    # MEdimos el tiempo para saber si ocupamos optimizar mas el algoritmo (Esto depende de las configuraciones iniciales y los productos que tengamos, si tenemos muchos productos y un soporte muy bajo, el algoritmo puede tardar mucho a mi me tardo casi 20 min)
    inicio_apriori = time.time()
    
    # Encontrar itemsets frecuentes
    #EL SOPORTE EN DECIMAL (MIN_SUPPORT_DECIMAL)
    frequent_itemsets = fn.get_frequent_itemsets(df_transacciones, SOPORTE_MINIMO)
    
    if frequent_itemsets:
        print(f"\nTiempo de ejecución Apriori: {time.time() - inicio_apriori:.2f} segundos")
        
        # Generar reglas de asociación
        inicio_reglas = time.time()
        df_asociaciones = fn.generate_rules_apriori(
            frequent_itemsets, 
            df_transacciones, 
            min_confidence=MIN_CONFIDENCE_DECIMAL,  # Pasamos confianza en decimal no ocupa calculo despues
            min_lift=LIFT_MINIMO
        )
        print(f"⏱️ Tiempo generación reglas: {time.time() - inicio_reglas:.2f} segundos")
        


        if not df_asociaciones.empty:
            
            
            print("RESULTADOS DEL ANÁLISIS")
            print(f"Total reglas encontradas: {len(df_asociaciones)}")
            print("="*50)



            
            # Mostrar top reglas por lift
            print(f"\n🔝 Top {TOP_REGLAS_A_MOSTRAR} reglas por LIFT (mayor significancia estadística):")
            top_lift = df_asociaciones.nlargest(TOP_REGLAS_A_MOSTRAR, 'lift')


            for idx, row in top_lift.iterrows():
                print(f"\n  {row['antecedente']} → {row['consecuente']}")
                print(f"    Soporte: {row['soporte']}% | Confianza: {row['confianza']}% | Lift: {row['lift']}")



            
            print("\n" + "="*50)
            print("RESUMEN DE MÉTRICAS")
            print("="*50)

            print(f"  Lift promedio: {df_asociaciones['lift'].mean():.2f}")
            print(f"  Lift máximo: {df_asociaciones['lift'].max():.2f}")
            print(f"  Confianza promedio: {df_asociaciones['confianza'].mean():.2f}%")
            print(f"  Soporte promedio: {df_asociaciones['soporte'].mean():.2f}%")
            
            
            # Exportar resultados
            if EXPORTAR_RESULTADOS:
                print("\nExportando resultados...")
                
                # Exportar reglas completas
                df_asociaciones.to_csv('reglasBasket_apriori.csv', index=False, sep=';', decimal=',', encoding='utf-8-sig')

                
                # Exportar top reglas
                top_lift.to_csv('top_reglas_lift.csv', index=False, sep=';', decimal=',', encoding='utf-8-sig')

                
                print("Archivos exportados exitosamente:")
                print("reglasBasket_apriori.csv (todas las reglas)")
                print("top_reglas_lift.csv (top reglas)")

            else:

                print("Exportación desactivada en configuración.")
            
        else:


            print("\nNo se generaron reglas con los umbrales especificados.")
            print(" Posibles soluciones:")
            print(" Reducir CONFIANZA_MINIMA (ej: 0.5% o 0.3%)")
            print(" Reducir LIFT_MINIMO (ej: 1.1)")
            print(" Aumentar SOPORTE_MINIMO para tener más itemsets frecuentes")
    else:
        print("\nNo se encontraron itemsets frecuentes con el soporte mínimo especificado.")
        print(" Posibles soluciones:")
        print(f"  Reducir SOPORTE_MINIMO (actual: {SOPORTE_MINIMO}%)")
        print("  Verificar que los datos tengan productos que se repiten")



except KeyError as e:
    print(f"Error procesando datos: {e}")
    print("Verifica que las columnas en el archivo Excel tengan los nombres esperados")

    
except FileNotFoundError:
    print(f"Error: No se encontró el archivo en la ruta especificada")
    
except Exception as e:
    print(f"Error inesperado: {e}")