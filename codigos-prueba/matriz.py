"""
matriz.py — Operaciones básicas con matrices representadas como listas de listas.
CÓDIGO BUENO: valida dimensiones antes de operar.
"""


def transponer(matriz):
    """Retorna la transpuesta de una matriz (lista de listas)."""
    if not matriz:
        return []
    filas = len(matriz)
    columnas = len(matriz[0])
    for fila in matriz:
        if len(fila) != columnas:
            raise ValueError("La matriz no tiene filas de igual longitud")
    return [[matriz[i][j] for i in range(filas)] for j in range(columnas)]


def sumar_matrices(a, b):
    """Suma dos matrices del mismo tamaño elemento por elemento."""
    if len(a) != len(b) or any(len(fa) != len(fb) for fa, fb in zip(a, b)):
        raise ValueError("Las matrices deben tener las mismas dimensiones")
    return [[a[i][j] + b[i][j] for j in range(len(a[i]))] for i in range(len(a))]


def multiplicar_matrices(a, b):
    """Multiplica dos matrices compatibles (columnas de a == filas de b)."""
    if not a or not b or len(a[0]) != len(b):
        raise ValueError("Dimensiones incompatibles para la multiplicación")
    filas_a, columnas_a = len(a), len(a[0])
    columnas_b = len(b[0])
    resultado = [[0] * columnas_b for _ in range(filas_a)]
    for i in range(filas_a):
        for j in range(columnas_b):
            resultado[i][j] = sum(a[i][k] * b[k][j] for k in range(columnas_a))
    return resultado
