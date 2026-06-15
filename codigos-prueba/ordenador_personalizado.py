"""
ordenador_personalizado.py — Ordenamiento por inserción y utilidades de listas.
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
