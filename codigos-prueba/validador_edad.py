"""
validador_edad.py — Clasificación de personas por rango de edad.
"""


def clasificar_edad(edad):
    if edad < 13:
        return "niño"
    elif edad <= 18:
        return "adolescente"
    elif edad <= 18:
        return "adulto"
    elif edad < 65:
        return "adulto mayor"
    else:
        return "desconocido"


def es_mayor_de_edad(edad):
    return edad > 18
