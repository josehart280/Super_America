'''En esta parte del proyecto se realizan las funciones necesarias para el analisis Basket Analitycs'''
import pandas as pd
import numpy as np
from itertools import combinations

def confianza(antecedente, consecuente, df_transacciones):
    #casos donde se compraron ambos productos
    conjuntos_ambos = df_transacciones[(df_transacciones[antecedente] == 1 ) & (df_transacciones[consecuente] == 1)]
    
    #Confianza  = compras conjuntas / compras del producto A
    if df_transacciones[antecedente].sum() > 0:
        return len(conjuntos_ambos) / df_transacciones[antecedente].sum()
    return 0


def lift(antecedente, consecuente, df_transacciones):
    #definimos los P(A) y P(B)
    soporte_a = df_transacciones[antecedente].mean()
    soporte_b = df_transacciones[consecuente].mean()
    
    #contamos cuantas veces se compraron ambos productos juntos
    conteo_ab = len(df_transacciones[(df_transacciones[antecedente]==1) &
                                     (df_transacciones[consecuente]==1)])
    
    #sacamos el soporte de ambos productos juntos
    soporte_ab = conteo_ab / len(df_transacciones)
    
    #calculo del lift
    if (soporte_a * soporte_b) > 0:
        return soporte_ab / (soporte_a * soporte_b)
    return 0


# FUNCIONES PARA APRIORI

def get_frequent_itemsets(df_transacciones, min_support):
    """
    Implementación del algoritmo Apriori para encontrar conjuntos de items frecuentes
    
    Args:
        df_transacciones: DataFrame binario de transacciones
        min_support: Soporte mínimo en DECIMAL (ej: 0.0005 = 0.05%)
    
    Returns:
        Diccionario con todos los itemsets frecuentes y sus soportes
    """
    n_transacciones = len(df_transacciones)
    items = df_transacciones.columns.tolist()

    
    # Diccionario para guardar todos los itemsets frecuentes
    frequent_itemsets = {}
    
    
    print(f"EJECUTANDO ALGORITMO APRIORI")
    print(f"Soporte mínimo: {min_support*100:.4f}% (decimal: {min_support:.6f})")
    print(f"Total transacciones: {n_transacciones}")
    print(f"Total productos a evaluar: {len(items)}")
    
    
    # OPTIMIZACIÓN: Calcular soportes de una sola vez
    print("\nCalculando soportes individuales...")
    soportes = df_transacciones.sum() / n_transacciones


    
    #Encontrar items individuales frecuentes (L1)
    L1 = {}
    items_procesados = 0


    for item in items:
        items_procesados += 1
        support = soportes[item]

        if support >= min_support:
            L1[frozenset([item])] = support
        
        # Mostrar progreso cada 1000 items
        if items_procesados % 1000 == 0:
            print(f"  Procesados {items_procesados}/{len(items)} items...")
    
    #importante para revisar si se encontraron items frecuentes con el soporte mínimo o no
    if not L1:
        print("No se encontraron items frecuentes con el soporte mínimo")
        return frequent_itemsets
    

    frequent_itemsets.update(L1)

    #validar que se encontraron items frecuentes con el soporte mínimo o no
    print(f"\nL1: {len(L1)} items frecuentes encontrados")
    print(f"Soporte más alto: {max(L1.values())*100:.2f}%")
    print(f"Soporte más bajo: {min(L1.values())*100:.4f}%")


    
    #Generar conjuntos de mayor tamaño
    k = 2
    current_L = L1
    
    while current_L:
        print(f"\nGenerando candidatos de tamaño {k}...")
        
        # Generar candidatos de tamaño k
        candidates = apriori_gen(list(current_L.keys()), k)


        
        if not candidates:
            print(f"No se pueden generar más candidatos")
            break
            
        print(f"{len(candidates)} candidatos generados")


        
        # Podar candidatos que no cumplan soporte mínimo
        Lk = {}
        candidatos_procesados = 0
        


        for candidate in candidates:
            candidatos_procesados += 1
            items_list = list(candidate)
            
            # Crear mascara para transacciones que contienen todos los items del candidato
            mask = pd.Series([True] * n_transacciones, index=df_transacciones.index)
            for item in items_list:
                mask = mask & (df_transacciones[item] == 1)
            
            support = mask.sum() / n_transacciones
            
            if support >= min_support:
                Lk[candidate] = support
            
            # Mostrar progreso cada 100 candidatos
            if candidatos_procesados % 100 == 0:
                print(f" Evaluados {candidatos_procesados}/{len(candidates)} candidatos...")


        
        if Lk:

            print(f"✅ L{k}: {len(Lk)} itemsets frecuentes encontrados")

            frequent_itemsets.update(Lk)
            current_L = Lk
            k += 1

        else:
            print(f"   No se encontraron itemsets frecuentes de tamaño {k}")
            break
    
    print(f"\n{'='*50}")
    print(f"RESUMEN FINAL APRIORI")
    print(f"{'='*50}")
    print(f"Total itemsets frecuentes encontrados: {len(frequent_itemsets)}")
    print(f"Tamaños encontrados: 1 a {k-1}")
    
    return frequent_itemsets


def apriori_gen(Lk_1, k):
    """
    Genera candidatos de tamaño k a partir de Lk-1
    Implementa la propiedad Apriori: todos los subconjuntos deben ser frecuentes
    """
    candidates = set()
    Lk_1_list = list(Lk_1)
    n = len(Lk_1_list)
    
    for i in range(n):
        for j in range(i+1, n):
            # Unir dos conjuntos si comparten los primeros k-2 items
            set1 = list(Lk_1_list[i])
            set2 = list(Lk_1_list[j])
            set1.sort()
            set2.sort()
            
            # Verificar si los primeros k-2 items son iguales
            if set1[:k-2] == set2[:k-2]:


                # Crear unión
                new_candidate = frozenset(Lk_1_list[i] | Lk_1_list[j])
                
                # Verificar si todos los subconjuntos de tamaño k-1 son frecuentes
                if has_frequent_subsets(new_candidate, Lk_1_list, k):
                    candidates.add(new_candidate)
    
    return list(candidates)


def has_frequent_subsets(candidate, Lk_1_list, k):
    """
    Verifica que todos los subconjuntos de tamaño k-1 del candidato sean frecuentes
    (Propiedad Apriori)

    """


    # Generar todos los subconjuntos de tamaño k-1
    candidate_list = list(candidate)
    subsets = combinations(candidate_list, k-1)
    
    for subset in subsets:

        if frozenset(subset) not in Lk_1_list:
            return False
    return True


def generate_rules_apriori(frequent_itemsets, df_transacciones, min_confidence=0.01, min_lift=1.0):
    """
    Genera reglas de asociación a partir de los itemsets frecuentes
    
    Args:
        frequent_itemsets: Diccionario con itemsets frecuentes y soportes
        df_transacciones: DataFrame binario de transacciones
        min_confidence: Confianza mínima en DECIMAL (ej: 0.01 = 1%)
        min_lift: Lift mínimo
    
    Returns:
        DataFrame con todas las reglas que cumplen los umbrales
    """
    rules = []
    n_transacciones = len(df_transacciones)
    
    
    print(f"GENERANDO REGLAS DE ASOCIACIÓN")
    print(f"Confianza mínima: {min_confidence*100:.2f}% (decimal: {min_confidence:.3f})")
    print(f"Lift mínimo: {min_lift}")
    

    
    total_itemsets = len([x for x in frequent_itemsets.keys() if len(x) >= 2])
    itemsets_procesados = 0


    
    # Para cada itemset de tamaño >= 2
    for itemset, support_ab in frequent_itemsets.items():

        if len(itemset) >= 2:
            itemsets_procesados += 1
            items_list = list(itemset)
            
            # Generar todas las posibles reglas (antecedente -> consecuente)
            for i in range(1, len(items_list)):

                for antecedente in combinations(items_list, i):
                    antecedente_set = frozenset(antecedente)
                    consecuente_set = itemset - antecedente_set

                    
                    if consecuente_set:  # Asegurar que el consecuente no esté vacío
                        # Calcular soporte del antecedente
                        mask_a = pd.Series([True] * n_transacciones)


                        for item in antecedente:
                            mask_a = mask_a & (df_transacciones[item] == 1)
                        support_a = mask_a.sum() / n_transacciones
                        
                        # Calcular confianza
                        confidence = support_ab / support_a if support_a > 0 else 0
                        
                        if confidence >= min_confidence:
                            # Calcular soporte del consecuente
                            mask_b = pd.Series([True] * n_transacciones)


                            for item in consecuente_set:
                                mask_b = mask_b & (df_transacciones[item] == 1)
                            support_b = mask_b.sum() / n_transacciones
                            
                            # Calcular lift
                            lift_value = support_ab / (support_a * support_b) if (support_a * support_b) > 0 else 0
                            
                            if lift_value >= min_lift:
                                rules.append({
                                    'antecedente': ','.join(list(antecedente)),
                                    'consecuente': ','.join(list(consecuente_set)),
                                    'soporte': round(support_ab * 100, 2),
                                    'soporte_a': round(support_a * 100, 2),
                                    'soporte_b': round(support_b * 100, 2),
                                    'confianza': round(confidence * 100, 2),
                                    'lift': round(lift_value, 2),
                                    'tamano_itemset': len(itemset)
                                })
            
            # Mostrar progreso cada 100 itemsets
            if itemsets_procesados % 100 == 0:
                print(f"   Procesados {itemsets_procesados}/{total_itemsets} itemsets... Reglas encontradas: {len(rules)}")
    
    print(f"\n✅ Total reglas generadas: {len(rules)}")
    return pd.DataFrame(rules)


# solo las las de mejor lift para mostrar despues en powerBI
def get_top_rules(df_rules, n=10, metric='lift'):
    """
    Obtiene las mejores n reglas según una métrica específica
    
    Args:
        df_rules: DataFrame con reglas generadas
        n: Número de reglas a retornar
        metric: Métrica para ordenar ('lift', 'confianza', 'soporte')
    
    Returns:
        DataFrame con las mejores reglas para una exportacion csv


    """
    if df_rules.empty:
        return df_rules
    
    valid_metrics = ['lift', 'confianza', 'soporte']
    if metric not in valid_metrics:
        metric = 'lift'
    
    return df_rules.nlargest(n, metric)


def analyze_product_associations(producto, df_rules, tipo='antecedente'):
    """
    Analiza las asociaciones de un producto específico
    
    Args:
        producto: Nombre del producto a analizar
        df_rules: DataFrame con reglas
        tipo: 'antecedente' (productos que llevan a este) o 'consecuente' (productos a los que lleva)
    
    Returns:
        DataFrame con las reglas filtradas
    """

    
    if tipo == 'antecedente':
        mask = df_rules['antecedente'].str.contains(producto, na=False)
    else:
        mask = df_rules['consecuente'].str.contains(producto, na=False)
    
    return df_rules[mask].sort_values('lift', ascending=False)