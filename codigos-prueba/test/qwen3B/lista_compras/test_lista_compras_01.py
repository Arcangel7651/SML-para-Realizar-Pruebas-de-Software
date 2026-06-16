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

    def test_agregar_dos_items_diferentes_a_carrito_vacio(self):
        # Given
        manzana = {"nombre": "manzana", "precio": 0.5, "cantidad": 3}
        pera = {"nombre": "pera", "precio": 0.4, "cantidad": 2}

        # When
        self.carrito.agregar_item(*list(manzana.values()))
        self.carrito.agregar_item(*list(pera.values()))

        # Then
        assert len(self.carrito.items) == 2
        assert self.carrito.items[0]["nombre"] == "manzana"
        assert self.carrito.items[0]["precio"] == 0.5
        assert self.carrito.items[0]["cantidad"] == 3
        assert self.carrito.items[1]["nombre"] == "pera"
        assert self.carrito.items[1]["precio"] == 0.4
        assert self.carrito.items[1]["cantidad"] == 2

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

    def test_total_carrito_vacio(self):
        # Given
        expected_total = 0

        # When
        total = self.carrito.total()

        # Then
        assert total == expected_total

    def test_total_carrito_con_un_item(self):
        # Given
        manzana = {"nombre": "manzana", "precio": 0.5, "cantidad": 3}
        expected_total = manzana["precio"] * manzana["cantidad"]

        # When
        self.carrito.agregar_item(*list(manzana.values()))
        total = self.carrito.total()

        # Then
        assert total == expected_total

    def test_total_carrito_con_dos_items(self):
        # Given
        manzana = {"nombre": "manzana", "precio": 0.5, "cantidad": 3}
        pera = {"nombre": "pera", "precio": 0.4, "cantidad": 2}
        expected_total = (manzana["precio"] * manzana["cantidad"]) + (pera["precio"] * pera["cantidad"])

        # When
        self.carrito.agregar_item(*list(manzana.values()))
        self.carrito.agregar_item(*list(pera.values()))
        total = self.carrito.total()

        # Then
        assert total == expected_total

    def test_quitar_item_que_no_existe(self):
        # Given
        nombre = "naranja"
        try:
            self.carrito.quitar_item(nombre)
        except ValueError as e:
            message = str(e)
            assert "Item no encontrado" in message

    def teardown_method(self):
        self.carrito = None