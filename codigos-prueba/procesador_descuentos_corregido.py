"""
procesador_descuentos_corregido.py — Cálculo de precios con descuento.

Versión CORRECTA (control) del módulo buggy `procesador_descuentos.py`.
Las funciones llevan docstring de comportamiento esperado para que el
oráculo (LLM-as-judge) tenga una especificación independiente del código.
"""


def aplicar_descuento(precio, porcentaje):
    """Devuelve el precio tras aplicarle un descuento del `porcentaje` indicado.

    El descuento es precio * (porcentaje / 100) y se resta del precio.
    No se hace clamping: un porcentaje de 0 deja el precio igual, 100 lo deja
    en 0, y un porcentaje negativo AUMENTA el precio (descuento negativo).
    Ejemplos: aplicar_descuento(100, 0) == 100; aplicar_descuento(100, 50) == 50;
    aplicar_descuento(100, -5) == 105.
    """
    descuento = precio * (porcentaje / 100)
    return precio - descuento


def precio_unitario(precio_total, cantidad):
    """Devuelve el precio por unidad: precio_total / cantidad.

    No valida la cantidad: si `cantidad` es 0 se propaga ZeroDivisionError;
    si `cantidad` es negativa el resultado es negativo (no lanza excepción).
    Ejemplos: precio_unitario(200, 10) == 20; precio_unitario(100, -1) == -100.
    """
    return precio_total / cantidad


def aplicar_descuento_escalonado(precio, cantidad):
    """Aplica un descuento por volumen según la cantidad comprada.

    Escala (umbrales estrictos, se evalúa de mayor a menor):
      - cantidad > 100  -> 20 %
      - cantidad > 50   -> 10 %
      - cantidad > 10   ->  5 %
      - en otro caso    ->  0 % (sin descuento)
    El porcentaje resultante se aplica con `aplicar_descuento`.
    Ejemplos (precio=100): cantidad 5 -> 100; cantidad 20 -> 95;
    cantidad 60 -> 90; cantidad 150 -> 80.
    """
    if cantidad > 100:
        porcentaje = 20
    elif cantidad > 50:
        porcentaje = 10
    elif cantidad > 10:
        porcentaje = 5
    else:
        porcentaje = 0
    return aplicar_descuento(precio, porcentaje)
