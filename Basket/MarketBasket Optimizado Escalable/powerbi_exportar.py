'''Este codigo fue la mayor creacion mia propia de momento, aplicando lo que se en python y lo que se de analisis de datos, es una version optimizada del codigo original que se encuentra en BasketMarket.py, esta version esta diseñada para ser mas eficiente y escalable, permitiendo analizar grandes volúmenes de datos con muchos productos sin saturar la memoria RAM, utilizando procesamiento por lotes y almacenamiento temporal en disco para manejar la matriz de co-ocurrencia y las reglas generadas. 
By Jose Porrras Ramirez'''

import pandas as pd

class PowerBIExporter:
    def __init__(self, archivo, hoja='VentasLimpias'):
        self.archivo = archivo
        self.hoja = hoja
    
    def exportar_para_powerbi(self, df_reglas, archivo_salida='market_basket_powerbi_completo.csv'):
        """
        Exporta resultados en formato listo para PowerBI y analisis segun el documento de requisitos 
        """
        if df_reglas is None or len(df_reglas) == 0:
            print(" No hay reglas para exportar")
            return
        
        print("\n" + "="*60)
        print("EXPORTANDO PARA POWERBI")
        print("="*60)
        
        #Pasamos los datos originales para códigos
        df_original = pd.read_excel(self.archivo, sheet_name=self.hoja, engine='openpyxl')
        productos_unicos = df_original[['Codigo_Producto', 'Descripcion']].drop_duplicates()
        
        # Hacer merge con reglas (puede haber múltiples códigos por producto)
        df_powerbi = df_reglas.copy()
        
        # Función para obtener código (tomar el primero si hay múltiples)
        def get_first_code(desc, df_codigos):
            codes = df_codigos[df_codigos['Descripcion'] == desc]['Codigo_Producto'].values
            return str(codes[0]) if len(codes) > 0 else 'N/A'     


        # Agregar códigos a antecedentes y consecuentes para enlazarlos en PowerBI
        df_powerbi['codigo_a'] = df_powerbi['antecedente'].apply(lambda x: get_first_code(x, productos_unicos))
        df_powerbi['codigo_c'] = df_powerbi['consecuente'].apply(lambda x: get_first_code(x, productos_unicos))
        
        # Seleccionar y renombrar columnas
        df_powerbi = df_powerbi[[
            'antecedente', 'codigo_a',
            'consecuente', 'codigo_c',
            'soporte_ab', 'confianza', 'lift',
            'soporte_a', 'soporte_c'
        ]]
        
        df_powerbi.columns = [
            'Producto_A', 'Codigo_A',
            'Producto_B', 'Codigo_B',
            'Soporte_Conjunto_%', 'Confianza_%', 'Lift',
            'Soporte_A_%', 'Soporte_B_%'
        ]
        
        #redondear valores
        for col in ['Soporte_Conjunto_%', 'Confianza_%', 'Soporte_A_%', 'Soporte_B_%']:
            df_powerbi[col] = df_powerbi[col].round(2)
        df_powerbi['Lift'] = df_powerbi['Lift'].round(3)
        
        #ordenar por lift para destacar las reglas más interesantes
        df_powerbi.sort_values(by='Lift', ascending=False, inplace=True)


        #Guardar como CSB
        df_powerbi.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
        
        print(f"\n Archivo guardado: {archivo_salida}")
        print(f" Reglas exportadas: {len(df_powerbi):,}")
        print(f" Productos A únicos: {df_powerbi['Producto_A'].nunique():,}")
        print(f" Productos B únicos: {df_powerbi['Producto_B'].nunique():,}")
        print(f" Total productos involucrados: {pd.unique(df_powerbi[['Producto_A', 'Producto_B']].values.ravel()).shape[0]:,}")
        
        return df_powerbi