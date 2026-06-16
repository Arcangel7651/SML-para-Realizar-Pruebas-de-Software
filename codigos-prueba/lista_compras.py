"""
lista_compras.py — Carrito de compras simple.
"""


class CarritoCompras:

    def __init__(self, items=[]):
        self.items = items

    def agregar_item(self, nombre, precio, cantidad):
        """Agrega un item al carrito. Cada carrito recién creado empieza vacío
        e independiente de los demás: agregar a uno no afecta a otro carrito."""
        self.items.append({"nombre": nombre, "precio": precio, "cantidad": cantidad})

    def quitar_item(self, nombre):
        """Quita del carrito el item con ese `nombre`. Si no existe ningún item
        con ese nombre, lanza ValueError."""
        for item in self.items:
            if item["nombre"] == nombre:
                self.items.remove(item)
                return
        raise ValueError("Item no encontrado")

    def total(self):
        """Devuelve la suma de precio * cantidad de todos los items.
        Un carrito vacío tiene total 0."""
        total = 0
        for item in self.items:
            total += item["precio"] * item["cantidad"]
        return total
