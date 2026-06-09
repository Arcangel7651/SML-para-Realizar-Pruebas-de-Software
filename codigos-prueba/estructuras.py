"""
estructuras.py — Operaciones básicas con listas, pilas y colas.
"""


def invertir_lista(lista):
    """Retorna una nueva lista con los elementos en orden inverso."""
    return lista[::-1]


def eliminar_duplicados(lista):
    """Retorna una nueva lista sin elementos duplicados, preservando el orden."""
    vistos = []
    for elemento in lista:
        if elemento not in vistos:
            vistos.append(elemento)
    return vistos


def pila_push(pila, elemento):
    """Agrega un elemento al tope de la pila y la retorna."""
    pila.append(elemento)
    return pila


def pila_pop(pila):
    """
    Elimina y retorna el elemento del tope de la pila.
    Lanza IndexError si la pila está vacía.
    """
    if len(pila) == 0:
        raise IndexError("La pila está vacía.")
    return pila.pop()


def cola_enqueue(cola, elemento):
    """Agrega un elemento al final de la cola y la retorna."""
    cola.append(elemento)
    return cola


def cola_dequeue(cola):
    """
    Elimina y retorna el primer elemento de la cola.
    Lanza IndexError si la cola está vacía.
    """
    if len(cola) == 0:
        raise IndexError("La cola está vacía.")
    return cola.pop(0)