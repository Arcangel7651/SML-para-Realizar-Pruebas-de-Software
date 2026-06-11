"""
procesador_descuentos.py — Cálculo de precios con descuento.
CÓDIGO MALO (bugs intencionales):
 - no valida porcentajes fuera de rango (negativos o mayores a 100)
 - división entre cero al calcular precio_unitario si cantidad es 0
 - aplicar_descuento_escalonado tiene lógica de comparación invertida
"""


def aplicar_descuento(precio, porcentaje):
    descuento = precio * (porcentaje / 100)
    return precio - descuento


def precio_unitario(precio_total, cantidad):
    return precio_total / cantidad


def aplicar_descuento_escalonado(precio, cantidad):
    if cantidad > 10:
        porcentaje = 5
    elif cantidad > 50:
        porcentaje = 10
    elif cantidad > 100:
        porcentaje = 20
    else:
        porcentaje = 0
    return aplicar_descuento(precio, porcentaje)
