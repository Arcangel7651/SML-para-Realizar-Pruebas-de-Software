"""
procesador_descuentos.py — Cálculo de precios con descuento.
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
