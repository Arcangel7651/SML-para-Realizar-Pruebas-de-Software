"""
pila_balanceada.py — Verificación de paréntesis/llaves/corchetes balanceados.
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
