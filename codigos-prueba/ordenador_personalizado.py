"""
ordenador_personalizado.py — Ordenamiento por inserción y utilidades de listas.
"""


def insertion_sort(lista):
    """Devuelve una NUEVA lista con los elementos ordenados de menor a mayor,
    sin modificar la lista original. Por ejemplo, insertion_sort([3, 1, 2])
    devuelve [1, 2, 3]. Una lista vacía devuelve []."""
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
    """Devuelve el segundo valor más grande DISTINTO de la lista. Por ejemplo,
    encontrar_segundo_mayor([5, 1, 5, 3]) devuelve 3. Requiere al menos dos
    valores distintos; en caso contrario lanza una excepción."""
    ordenada = sorted(set(lista))
    return ordenada[-2]
