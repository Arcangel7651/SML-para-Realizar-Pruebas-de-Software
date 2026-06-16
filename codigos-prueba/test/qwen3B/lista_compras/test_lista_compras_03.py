import pytest
from lista_compras import CarritoCompras


class TestListaCompras(object):

    def setup_method(self):
        self.carrito = CarritoCompras()

    def test_agregar_item_a_carrito_vacio(self):
        # Given
        nombre = "manzana"
        precio = 0.5
        cantidad = 3

        # When
        self.carrito.agregar_item(nombre, precio, cantidad)

        # Then
        assert len(self.carrito.items) == 1
        assert self.carrito.items[0]["nombre"] == nombre
        assert self.carrito.items[0]["precio"] == precio
        assert self.carrito.items[0]["cantidad"] == cantidad

    def test_agregar_item_con_nombre_existente(self):
        # Given
        nombre = "manzana"
        precio = 0.5
        cantidad = 3
        self.carrito.agregar_item(nombre, precio, cantidad)

        # When
        try:
            self.carrito.agregar_item(nombre, precio, cantidad)
        except ValueError as e:
            message = str(e)
            assert "Item no encontrado" in message

    def test_quitar_item_que_no_existe(self):
        # Given
        nombre = "naranja"
        try:
            self.carrito.quitar_item(nombre)
        except ValueError as e:
            message = str(e)
            assert "Item no encontrado" in message

    def test_agregar_dos_items_diferentes_a_carrito_vacio(self):
        # Given
        nombre1 = "manzana"
        precio1 = 0.5
        cantidad1 = 3
        nombre2 = "naranja"
        precio2 = 0.8
        cantidad2 = 4

        # When
        self.carrito.agregar_item(nombre1, precio1, cantidad1)
        self.carrito.agregar_item(nombre2, precio2, cantidad2)

        # Then
        assert len(self.carrito.items) == 2
        assert self.carrito.items[0]["nombre"] == nombre1
        assert self.carrito.items[0]["precio"] == precio1
        assert self.carrito.items[0]["cantidad"] == cantidad1
        assert self.carrito.items[1]["nombre"] == nombre2
        assert self.carrito.items[1]["precio"] == precio2
        assert self.carrito.items[1]["cantidad"] == cantidad2

    def test_quitar_item_de_carrito_con_muchos_items(self):
        # Given
        nombre = "manzana"
        cantidad1 = 3
        cantidad2 = 4

        for _ in range(cantidad1 + cantidad2):
            self.carrito.agregar_item(nombre, 0.5, 1)

        # When
        self.carrito.quitar_item(nombre)

        # Then
        assert len(self.carrito.items) == cantidad1 + cantidad2 - 1

    def test_total_carrito_con_un_item(self):
        # Given
        nombre = "manzana"
        precio = 0.5
        cantidad = 3

        self.carrito.agregar_item(nombre, precio, cantidad)

        # When
        total = self.carrito.total()

        # Then
        assert total == precio * cantidad
        assert f"El total debería ser {precio * cantidad} pero fue {total}"

    def test_total_carrito_con_dos_items(self):
        # Given
        nombre1 = "manzana"
        precio1 = 0.5
        cantidad1 = 3
        nombre2 = "naranja"
        precio2 = 0.8
        cantidad2 = 4

        self.carrito.agregar_item(nombre1, precio1, cantidad1)
        self.carrito.agregar_item(nombre2, precio2, cantidad2)

        # When
        total = self.carrito.total()

        # Then
        assert total == (precio1 * cantidad1) + (precio2 * cantidad2)
        assert f"El total debería ser {(precio1 * cantidad1) + (precio2 * cantidad2)} pero fue {total}"

    def test_total_carrito_vacio(self):
        # Given
        self.carrito.items = []

        # When
        total = self.carrito.total()

        # Then
        assert total == 0.0
        assert f"El total debería ser cero pero fue {total}"

    def test_quitar_todo_el_carrito(self):
        # Given
        nombre1 = "manzana"
        precio1 = 0.5
        cantidad1 = 3
        nombre2 = "naranja"
        precio2 = 0.8
        cantidad2 = 4

        self.carrito.agregar_item(nombre1, precio1, cantidad1)
        self.carrito.agregar_item(nombre2, precio2, cantidad2)

        # When
        self.carrito.quitar_todo()

        # Then
        assert len(self.carrito.items) == 0