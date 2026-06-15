"""
lista_compras.py — Carrito de compras simple.
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
