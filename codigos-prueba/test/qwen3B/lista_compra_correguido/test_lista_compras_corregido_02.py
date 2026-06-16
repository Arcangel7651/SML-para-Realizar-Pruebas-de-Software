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

    def test_total_carrito_vacio(self):
        # Given
        self.carrito.items = []

        # When
        total = self.carrito.total()

        # Then
        assert total == 0.0
        assert f"El total debería ser cero pero fue {total}"

    def test_quitar_item_que_no_existe(self):
        # Given
        nombre = "naranja"
        try:
            self.carrito.quitar_item(nombre)
        except ValueError as e:
            message = str(e)
            assert "Item no encontrado" in message

    def test_total_carrito_con_items_diferentes(self):
        # Given
        self.carrito.items.append({"nombre": "manzana", "precio": 0.5, "cantidad": 3})
        self.carrito.items.append({"nombre": "pera", "precio": 1.2, "cantidad": 2})

        # When
        total = self.carrito.total()

        # Then
        assert total == 4.7
        assert f"El total debería ser 4.7 pero fue {total}"

    def test_total_carrito_con_item_negativo_precio(self):
        # Given
        nombre = "manzana"
        precio = -1.5
        cantidad = 3

        # When
        with pytest.raises(ValueError) as e:
            self.carrito.agregar_item(nombre, precio, cantidad)
        assert "El precio no puede ser negativo" in str(e.value)

    def test_total_carrito_con_item_negativa_cantidad(self):
        # Given
        nombre = "manzana"
        precio = 0.5
        cantidad = -3

        # When
        with pytest.raises(ValueError) as e:
            self.carrito.agregar_item(nombre, precio, cantidad)
        assert "La cantidad debe ser mayor que cero" in str(e.value)

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

    def test_agregar_item_con_nombre_diferente(self):
        # Given
        nombre = "banana"
        precio = 0.3
        cantidad = 4

        # When
        self.carrito.agregar_item(nombre, precio, cantidad)

        # Then
        assert len(self.carrito.items) == 2
        assert self.carrito.items[1]["nombre"] == nombre
        assert self.carrito.items[1]["precio"] == precio
        assert self.carrito.items[1]["cantidad"] == cantidad

    def test_agregar_muchos_items_diferentes(self):
        # Given
        items = [
            {"nombre": "manzana", "precio": 0.5, "cantidad": 3},
            {"nombre": "pera", "precio": 1.2, "cantidad": 2},
            {"nombre": "uva", "precio": 0.8, "cantidad": 5}
        ]

        # When
        for item in items:
            self.carrito.agregar_item(item["nombre"], item["precio"], item["cantidad"])

        # Then
        assert len(self.carrito.items) == len(items)
        for i, item in enumerate(items):
            assert self.carrito.items[i]["nombre"] == item["nombre"]
            assert self.carrito.items[i]["precio"] == item["precio"]
            assert self.carrito.items[i]["cantidad"] == item["cantidad"]

    def test_agregar_item_con_muchas_cantidades(self):
        # Given
        nombre = "manzana"
        precio = 0.5
        cantidad = 10

        # When
        self.carrito.agregar_item(nombre, precio, cantidad)

        # Then
        assert len(self.carrito.items) == 1
        assert self.carrito.items[0]["nombre"] == nombre
        assert self.carrito.items[0]["precio"] == precio
        assert self.carrito.items[0]["cantidad"] == cantidad

    def test_quitar_item_que_existe_y_cantidad_una(self):
        # Given
        self.carrito.items.append({"nombre": "manzana", "precio": 0.5, "cantidad": 3})

        # When
        result = self.carrito.quitar_item("manzana")

        # Then
        assert result is True
        assert len(self.carrito.items) == 0

    def test_quitar_item_que_existe_y_cantidad_mayor(self):
        # Given
        self.carrito.items.append({"nombre": "manzana", "precio": 0.5, "cantidad": 3})

        # When
        result = self.carrito.quitar_item("manzana")

        # Then
        assert result is True
        assert len(self.carrito.items) == 1
        assert self.carrito.items[0]["cantidad"] == 2

    def test_quitar_item_que_existe_y_cantidad_minima(self):
        # Given
        self.carrito.items.append({"nombre": "manzana", "precio": 0.5, "cantidad": 1})

        # When
        result = self.carrito.quitar_item("manzana")

        # Then
        assert result is True
        assert len(self.carrito.items) == 0

    def test_quitar_item_que_no_existe_y_cantidad_una(self):
        # Given
        nombre = "naranja"
        cantidad = 1

        # When
        result = self.carrito.quitar_item(nombre)

        # Then
        assert result is False
        assert len(self.carrito.items) == 0

    def test_quitar_item_que_no_existe_y_cantidad_mayor(self):
        # Given
        nombre = "naranja"
        cantidad = 3

        # When
        result = self.carrito.quitar_item(nombre)

        # Then
        assert result is False
        assert len(self.carrito.items) == 0

    def test_quitar_item_que_no_existe_y_cantidad_minima(self):
        # Given
        nombre = "naranja"
        cantidad = 1

        # When
        result = self.carrito.quitar_item(nombre)

        # Then
        assert result is False
        assert len(self.carrito.items) == 0