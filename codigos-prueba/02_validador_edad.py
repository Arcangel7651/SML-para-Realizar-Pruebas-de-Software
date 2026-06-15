"""
validador_edad.py — Clasificación de personas por rango de edad.
CÓDIGO MALO (bugs intencionales):
 - error de "off-by-one" en los límites de los rangos (18 cae en dos categorías
   y 65 queda sin categoría)
 - permite edades negativas sin validación
 - es_mayor_de_edad usa '>' en vez de '>='
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
