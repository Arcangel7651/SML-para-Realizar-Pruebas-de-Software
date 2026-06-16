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

    def test_total_carrito_vacio(self):
        # When
        total = self.carrito.total()

        # Then
        assert total == 0.0, f"El total debería ser cero pero fue {total}"

    def test_total_carrito_con_un_item(self):
        # Given
        nombre = "manzana"
        precio = 0.5
        cantidad = 3
        self.carrito.agregar_item(nombre, precio, cantidad)

        # When
        total = self.carrito.total()

        # Then
        assert total == 1.5, f"El total debería ser 1.5 pero fue {total}"

    def test_total_carrito_con_dos_items(self):
        # Given
        nombre1 = "manzana"
        precio1 = 0.5
        cantidad1 = 3
        self.carrito.agregar_item(nombre1, precio1, cantidad1)

        nombre2 = "pera"
        precio2 = 0.7
        cantidad2 = 2
        self.carrito.agregar_item(nombre2, precio2, cantidad2)

        # When
        total = self.carrito.total()

        # Then
        assert total == 3.6, f"El total debería ser 3.6 pero fue {total}"

    def test_agregar_dos_items_diferentes_a_carrito_vacio(self):
        # Given
        nombre1 = "manzana"
        precio1 = 0.5
        cantidad1 = 3

        nombre2 = "pera"
        precio2 = 0.7
        cantidad2 = 2

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
        cantidad = 3
        self.carrito.agregar_item(nombre, 0.5, cantidad)
        self.carrito.agregar_item(nombre, 0.6, cantidad)

        # When
        self.carrito.quitar_item(nombre)

        # Then
        assert len(self.carrito.items) == 1
        assert self.carrito.items[0]["nombre"] == nombre
        assert self.carrito.items[0]["precio"] == 0.5
        assert self.carrito.items[0]["cantidad"] == cantidad

    def test_agregar_y_quitar_item(self):
        # Given
        nombre = "manzana"
        precio = 0.5
        cantidad = 3

        # When
        self.carrito.agregar_item(nombre, precio, cantidad)
        self.carrito.quitar_item(nombre)

        # Then
        assert len(self.carrito.items) == 1
        assert self.carrito.items[0]["nombre"] == nombre
        assert self.carrito.items[0]["precio"] == precio
        assert self.carrito.items[0]["cantidad"] == cantidad

    def test_agregar_muchos_items_y_quitar_uno(self):
        # Given
        nombres = ["manzana", "pera"]
        precios = [0.5, 0.7]
        cantidades = [3, 2]

        for nombre, precio, cantidad in zip(nombres, precios, cantidades):
            self.carrito.agregar_item(nombre, precio, cantidad)

        # When
        self.carrito.quitar_item("manzana")

        # Then
        assert len(self.carrito.items) == 1
        assert self.carrito.items[0]["nombre"] == "pera"
        assert self.carrito.items[0]["precio"] == 0.7
        assert self.carrito.items[0]["cantidad"] == 2

    def test_agregar_item_y_quitar_muchos(self):
        # Given
        nombre = "manzana"
        precio = 0.5
        cantidad = 3

        self.carrito.agregar_item(nombre, precio, cantidad)

        # When
        self.carrito.quitar_item("manzana")
        self.carrito.quitar_item("pera")

        # Then
        assert len(self.carrito.items) == 0

    def test_total_carrito_con_muchos_items(self):
        # Given
        nombres = ["manzana", "pera"]
        precios = [0.5, 0.7]
        cantidades = [3, 2]

        for nombre, precio, cantidad in zip(nombres, precios, cantidades):
            self.carrito.agregar_item(nombre, precio, cantidad)

        # When
        total = self.carrito.total()

        # Then
        assert total == 3.6, f"El total debería ser 3.6 pero fue {total}"

    def test_total_carrito_con_muchos_items_diferentes(self):
        # Given
        nombres = ["manzana", "pera", "uva"]
        precios = [0.5, 0.7, 1.2]
        cantidades = [3, 2, 4]

        for nombre, precio, cantidad in zip(nombres, precios, cantidades):
            self.carrito.agregar_item(nombre, precio, cantidad)

        # When
        total = self.carrito.total()

        # Then
        assert total == 7.0, f"El total debería ser 7.0 pero fue {total}"