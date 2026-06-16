"""
procesador_descuentos.py — Cálculo de precios con descuento.
"""


def aplicar_descuento(precio, porcentaje):
    """Devuelve el precio tras restarle `porcentaje`% de descuento.
    Por ejemplo, aplicar_descuento(100, 20) devuelve 80.0."""
    descuento = precio * (porcentaje / 100)
    return precio - descuento


def precio_unitario(precio_total, cantidad):
    """Devuelve el precio por unidad: precio_total dividido entre cantidad.
    `cantidad` debe ser mayor que 0; con cantidad 0 lanza una excepción."""
    return precio_total / cantidad


def aplicar_descuento_escalonado(precio, cantidad):
    """Aplica un descuento por volumen según la cantidad comprada:
    cantidad > 100 -> 20%; cantidad > 50 -> 10%; cantidad > 10 -> 5%;
    cantidad <= 10 -> 0%. Devuelve el precio ya con el descuento aplicado.
    Ejemplo: con cantidad 60 corresponde 10% de descuento."""
    if cantidad > 10:
        porcentaje = 5
    elif cantidad > 50:
        porcentaje = 10
    elif cantidad > 100:
        porcentaje = 20
    else:
        porcentaje = 0
    return aplicar_descuento(precio, porcentaje)
