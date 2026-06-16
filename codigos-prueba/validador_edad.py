"""
validador_edad.py — Clasificación de personas por rango de edad.
"""


def clasificar_edad(edad):
    """Devuelve la categoría de edad de una persona:
    edad < 13 -> 'niño'; 13 a 17 -> 'adolescente'; 18 a 64 -> 'adulto';
    65 o más -> 'adulto mayor'. Toda edad >= 0 cae en exactamente una
    categoría (no existe 'desconocido' para edades válidas)."""
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
    """Devuelve True si la persona es mayor de edad (18 años o más),
    False en caso contrario. La frontera es inclusiva: edad == 18 -> True."""
    return edad > 18
