"""
ordenador_personalizado.py — Ordenamiento por inserción y utilidades de listas.
CÓDIGO MALO (bugs intencionales):
 - insertion_sort no controla j == -1, por lo que `resultado[j]` se evalúa
   como `resultado[-1]` (indexación negativa de Python), produciendo
   comparaciones incorrectas en ciertos casos
 - encontrar_segundo_mayor lanza IndexError con listas vacías, de un solo
   elemento, o con todos los elementos repetidos (set queda con 1 elemento)
"""


def insertion_sort(lista):
    resultado = lista[:]
    for i in range(1, len(resultado)):
        actual = resultado[i]
        j = i - 1
        while resultado[j] > actual:
            resultado[j + 1] = resultado[j]
            j = j - 1
        resultado[j + 1] = actual
    return resultado


def encontrar_segundo_mayor(lista):
    ordenada = sorted(set(lista))
    return ordenada[-2]
