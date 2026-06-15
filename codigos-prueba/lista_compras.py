"""
lista_compras.py — Carrito de compras simple.
CÓDIGO MALO (bugs intencionales):
 - argumento por defecto mutable (items=[]) compartido entre instancias
 - quitar_item() no valida si el ítem existe (lanza ValueError no controlado)
 - total() no maneja precios negativos ni cantidades cero
"""


class CarritoCompras:

    def __init__(self, items=[]):
        self.items = items

    def agregar_item(self, nombre, precio, cantidad):
        self.items.append({"nombre": nombre, "precio": precio, "cantidad": cantidad})

    def quitar_item(self, nombre):
        for item in self.items:
            if item["nombre"] == nombre:
                self.items.remove(item)
                return
        raise ValueError("Item no encontrado")

    def total(self):
        total = 0
        for item in self.items:
            total += item["precio"] * item["cantidad"]
        return total
