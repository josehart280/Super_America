'''Este codigo fue la mayor creacion mia propia de momento, aplicando lo que se en python y lo que se de analisis de datos, es una version optimizada del codigo original que se encuentra en BasketMarket.py, esta version esta diseñada para ser mas eficiente y escalable, permitiendo analizar grandes volúmenes de datos con muchos productos sin saturar la memoria RAM, utilizando procesamiento por lotes y almacenamiento temporal en disco para manejar la matriz de co-ocurrencia y las reglas generadas. 
By Jose Porrras Ramirez'''

from basket_df_analisis import MarketBasketAnalyzerUltra
import pandas as pd
import time



def busqueda_adaptativa_umbrales(analyzer, umbrales_iniciales, top_n=100):
    """
    Imita la búsqueda de umbrales del código original
    """

    #configuraciones de umbrales  probar
    configuraciones = [
        {"soporte": umbrales_iniciales["soporte"], "confianza": umbrales_iniciales["confianza"], "lift": 1.0},
        {"soporte": umbrales_iniciales["soporte"]/2, "confianza": umbrales_iniciales["confianza"], "lift": 1.0},
        {"soporte": umbrales_iniciales["soporte"], "confianza": umbrales_iniciales["confianza"]/2, "lift": 1.0},
        {"soporte": umbrales_iniciales["soporte"]/2, "confianza": umbrales_iniciales["confianza"]/2, "lift": 1.0},
        {"soporte": 0.05, "confianza": 0.15, "lift": 1.0},  #0.1% soporte, 1% confianza
    ]
    
    todas_reglas = []
    
    for i, config in enumerate(configuraciones):


        print(f"\n{'='*60}")
        print(f"CONFIGURACIÓN {i+1}: Soporte={config['soporte']}%, Confianza={config['confianza']}%")
        print(f"{'='*60}")

        
        reglas = analyzer.calcular_reglas_por_lotes(
            min_soporte_pct=config['soporte'],
            min_confianza_pct=config['confianza'],
            min_lift=config['lift'],
            max_reglas=50000,
            generar_inversas=(i == len(configuraciones)-1)  # Generar inversas solo en la última
        )


        
        if reglas is not None and len(reglas) > 0:

            print(f"\n Reglas encontradas: {len(reglas):,}")
            todas_reglas.append(reglas)
            


            # Si ya tenemos suficientes reglas, paramos (como en el original)
            if len(reglas) >= top_n:
                print(f"\n🎯 Alcanzadas {len(reglas)} reglas, suficiente para top_n={top_n}")
                return pd.concat(todas_reglas, ignore_index=True) if len(todas_reglas) > 1 else reglas
    


    # Combinar todas las reglas encontradas
    if todas_reglas:
        df_combinado = pd.concat(todas_reglas, ignore_index=True)
        df_combinado.drop_duplicates(subset=['antecedente', 'consecuente'], inplace=True)
        return df_combinado
    
    return None















# Ejecución principal
if __name__ == "__main__":
    #ruta
    archivo = 'C:\\Users\\joans\\Documents\\data\\Super America\\Datos\\Ventas Limpias.xlsx'
    
    print("="*60)
    print(" MARKET BASKET ANALYSIS ESCALABLE")
    print("="*60)
    
    
    #Crear analizador con directorio temporal
    analyzer = MarketBasketAnalyzerUltra(archivo, temp_dir='basket_temp')
    start_total = time.time()


    try:


        #Cargamos TODOS los productos (solo filtrar los muy raros)
        analyzer.cargar_datos_completos(min_ocurrencias=5)  # Productos en al menos 5 facturas  que seria 0.5% aproximadamente
        
        #Crear dataframe por lotes
        analyzer.crear_matriz_co_ocurrencia_por_lotes(lote_size=300)
        
        #Calcular reglas con umbrales bajos
        print("\n" + "_"*60)
        print("CALCULANDO REGLAS CON DIFERENTES CONFIGURACIONES")
        print("_"*60)
        
        umbrales_iniciales = {
            "soporte": 0.005,    # 0.5% 
            "confianza": 0.015    # 3% 
        }

        df_reglas = busqueda_adaptativa_umbrales(analyzer, umbrales_iniciales, top_n=100)

        
        #Combinar resultados
        if df_reglas is not None and len(df_reglas) > 0:
            #ver reglas
            print(f"\n REGLAS ENCONTRADAS: {len(df_reglas):,}")


        #Estadísticas generales si algo no esta bien aqui nos damos cuenta en las estadisticas
            print(f"\nESTADÍSTICAS GENERALES:")
            print(f" Total reglas: {len(df_reglas):,}")
            print(f" Confianza promedio: {df_reglas['confianza'].mean():.2f}%")
            print(f" Lift promedio: {df_reglas['lift'].mean():.2f}")
            print(f" Reglas con lift > 2: {(df_reglas['lift'] > 2).sum():,}")
            print(f" Reglas con lift > 5: {(df_reglas['lift'] > 5).sum():,}")




            #para asegurarnos imprimamos las primeras reglas para ver que tan interesantes son
            print(f"\n TOP REGLAS (por lift):")
            print("-" * 80)
            for i, row in df_reglas.head(10).iterrows():
                print(f"{i+1:2d}. {row['antecedente'][:35]:35} → {row['consecuente'][:35]:35} "
                      f"(lift: {row['lift']:.2f}, conf: {row['confianza']:.1f}%, sop: {row['soporte_ab']:.2f}%)")

            # Guardar resultados completos
            analyzer.exportar_para_powerbi(df_reglas, 'market_basket_completo_ultra.csv')


            top_100 = df_reglas.head(100).copy()
            top_100.to_csv('Top_100_Reglas_Ultra.csv', index=False, encoding='utf-8-sig')

            df_reglas.to_csv('Reglas_Asociacion_Completas_Ultra.csv', index=False, encoding='utf-8-sig')

            
            print(f" market_basket_completo_ultra.csv ({len(df_reglas):,} reglas)")
            print(f" Top_100_Reglas_Ultra.csv (100 mejores reglas)")



            #Como programador voy a verificar consistencia de la confianza por consola solo por si acaso 

            confianzas_mayor_100 = (df_reglas['confianza'] > 100).sum()
            if confianzas_mayor_100 > 0:
                print(f"\nADVERTENCIA: {confianzas_mayor_100} reglas tienen confianza > 100%")
            else:
                print(f"\nVERIFICACION: Todas las confianzas son ≤ 100%")


        else:
            print("\n No se encontraron reglas con estos umbrales.")
            print("   Probando con umbrales más bajos...")      

            #si las ventas son muy dispersas y aleatorias podemos probar con umbrales más bajos para ver si encontramos algo interesante, esto es importante para entender la naturaleza de los datos y ajustar el análisis según sea necesario


            reglas_backup = analyzer.calcular_reglas_por_lotes(
                min_soporte_pct=0.0002,    # 0.3%
                min_confianza_pct=0.60,   # 60% de confianza
                min_lift=1.1,
                max_reglas=50000
            ) 


            if reglas_backup is not None and len(reglas_backup) > 0:
                print(f"\nReglas encontradas con umbrales reducidos: {len(reglas_backup):,}")
                analyzer.exportar_para_powerbi(reglas_backup, 'market_basket_completo_ultra_backup.csv')


        # Tiempo total
        tiempo_total = time.time() - start_total
        print(f"\nTiempo total de analisis: {tiempo_total:.2f} segundos")
              
    except Exception as e:
        print(f"\n ERROR DURANTE LA EJECUCIÓN: {e}")
        import traceback
        traceback.print_exc()
    finally:
        #Preguntar si limpiar archivos temporales para liberar el espacio que ocupamos hce rato
        respuesta = input("\nDesea limpiar los archivos temporales? (s/n): ")
        if respuesta.lower() == 's':
            analyzer.limpiar_temp()
    
    print("\n" + "#"*60)
    print("ANÁLISIS  COMPLETADO")
    print("#"*60)




