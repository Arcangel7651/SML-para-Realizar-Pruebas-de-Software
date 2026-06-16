"""
lista_compras_corregido.py — Carrito de compras simple.
"""


class CarritoCompras:

    def __init__(self, items=None):
        # Cada instancia tiene su propia lista (sin argumento por defecto mutable).
        self.items = list(items) if items is not None else []

    def agregar_item(self, nombre, precio, cantidad):
        # Valida las entradas para no acumular datos inválidos.
        if precio < 0:
            raise ValueError("El precio no puede ser negativo")
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        self.items.append({"nombre": nombre, "precio": precio, "cantidad": cantidad})

    def quitar_item(self, nombre):
        # Quita el ítem si existe. Retorna True si lo quitó, False si no estaba
        # (no lanza una excepción no controlada).
        for item in self.items:
            if item["nombre"] == nombre:
                self.items.remove(item)
                return True
        return False

    def total(self):
        return sum(item["precio"] * item["cantidad"] for item in self.items)
