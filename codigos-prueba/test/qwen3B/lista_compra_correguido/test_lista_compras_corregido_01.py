import pytest
from lista_compras_corregido import CarritoCompras


class TestListaComprasCorregido(object):

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
        with pytest.raises(ValueError) as e:
            self.carrito.agregar_item(nombre, precio, cantidad)
        assert "Item no encontrado" in str(e.value)

    def test_quitar_item_que_no_existe(self):
        # Given
        nombre = "naranja"

        # When
        with pytest.raises(ValueError) as e:
            self.carrito.quitar_item(nombre)
        assert "Item no encontrado" in str(e.value)

    def test_total_carrito_vacio(self):
        # Given
        self.carrito.items = []

        # When
        total = self.carrito.total()

        # Then
        assert total == 0.0
        assert f"El total debería ser cero pero fue {total}"

    def test_agregar_item_con_negativo_precio(self):
        # Given
        nombre = "manzana"
        precio = -1.5
        cantidad = 3

        # When
        with pytest.raises(ValueError) as e:
            self.carrito.agregar_item(nombre, precio, cantidad)
        assert "El precio no puede ser negativo" in str(e.value)

    def test_agregar_item_con_negativa_cantidad(self):
        # Given
        nombre = "manzana"
        precio = 0.5
        cantidad = -3

        # When
        with pytest.raises(ValueError) as e:
            self.carrito.agregar_item(nombre, precio, cantidad)
        assert "La cantidad debe ser mayor que cero" in str(e.value)

    def test_quitar_item_no_existente(self):
        # Given
        nombre = "naranja"
        try:
            self.carrito.quitar_item(nombre)
        except ValueError as e:
            message = str(e)
            assert "Item no encontrado" in message

    def test_total_carrito_con_items_diferentes(self):
        # Given
        self.carrito.items = [
            {"nombre": "manzana", "precio": 0.5, "cantidad": 3},
            {"nombre": "pera", "precio": 1.0, "cantidad": 2}
        ]

        # When
        total = self.carrito.total()

        # Then
        assert total == 6.5

    def test_total_carrito_con_item_negativo_precio(self):
        # Given
        self.carrito.items = [
            {"nombre": "manzana", "precio": -1.5, "cantidad": 3}
        ]

        # When
        with pytest.raises(ValueError) as e:
            self.carrito.total()
        assert "El precio no puede ser negativo" in str(e.value)

    def test_total_carrito_con_item_negativa_cantidad(self):
        # Given
        self.carrito.items = [
            {"nombre": "manzana", "precio": 0.5, "cantidad": -3}
        ]

        # When
        with pytest.raises(ValueError) as e:
            self.carrito.total()
        assert "La cantidad debe ser mayor que cero" in str(e.value)