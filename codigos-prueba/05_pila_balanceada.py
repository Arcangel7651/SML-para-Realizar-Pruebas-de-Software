"""
pila_balanceada.py — Verificación de paréntesis/llaves/corchetes balanceados.
CÓDIGO BUENO: implementación clásica con pila, maneja cadenas vacías y
caracteres no relacionados.
"""

PARES = {")": "(", "]": "[", "}": "{"}


def esta_balanceada(expresion):
    """
    Retorna True si todos los símbolos de apertura tienen su cierre
    correspondiente en el orden correcto.
    """
    pila = []
    for caracter in expresion:
        if caracter in "([{":
            pila.append(caracter)
        elif caracter in ")]}":
            if not pila or pila.pop() != PARES[caracter]:
                return False
    return len(pila) == 0
