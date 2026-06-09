"""
algoritmos.py — Algoritmos básicos de búsqueda y ordenamiento.
"""


def bubble_sort(lista):
    """Ordena una lista de números de menor a mayor usando bubble sort."""
    resultado = lista[:]
    n = len(resultado)
    for i in range(n):
        for j in range(0, n - i - 1):
            if resultado[j] > resultado[j + 1]:
                resultado[j], resultado[j + 1] = resultado[j + 1], resultado[j]
    return resultado


def binary_search(lista, objetivo):
    """
    Busca un elemento en una lista ordenada.
    Retorna el índice si lo encuentra, -1 si no existe.
    """
    izquierda, derecha = 0, len(lista) - 1
    while izquierda <= derecha:
        medio = (izquierda + derecha) // 2
        if lista[medio] == objetivo:
            return medio
        elif lista[medio] < objetivo:
            izquierda = medio + 1
        else:
            derecha = medio - 1
    return -1


def busqueda_lineal(lista, objetivo):
    """
    Busca un elemento en una lista de forma secuencial.
    Retorna el índice del primer elemento encontrado, -1 si no existe.
    """
    for i, elemento in enumerate(lista):
        if elemento == objetivo:
            return i
    return -1


def encontrar_maximo(lista):
    """
    Retorna el valor máximo de una lista.
    Lanza ValueError si la lista está vacía.
    """
    if len(lista) == 0:
        raise ValueError("La lista está vacía.")
    return max(lista)


def encontrar_minimo(lista):
    """
    Retorna el valor mínimo de una lista.
    Lanza ValueError si la lista está vacía.
    """
    if len(lista) == 0:
        raise ValueError("La lista está vacía.")
    return min(lista)
