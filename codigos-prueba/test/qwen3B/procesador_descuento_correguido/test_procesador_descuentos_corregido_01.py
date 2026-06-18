import pytest
from procesador_descuentos_corregido import aplicar_descuento, precio_unitario, aplicar_descuento_escalonado


class TestProcesadorDescuentosCorregido(object):
    def test_aplicar_descuento_cero(self):
        # Given
        precio = 100
        porcentaje = 0
        # When
        resultado = aplicar_descuento(precio, porcentaje)
        # Then
        assert resultado == 100

    def test_aplicar_descuento_uno_porciento(self):
        # Given
        precio = 100
        porcentaje = 1
        # When
        resultado = aplicar_descuento(precio, porcentaje)
        # Then
        assert resultado == 99.0

    def test_aplicar_descuento_cincuenta_porciento(self):
        # Given
        precio = 100
        porcentaje = 50
        # When
        resultado = aplicar_descuento(precio, porcentaje)
        # Then
        assert resultado == 50.0

    def test_aplicar_descuento_negativo_porciento(self):
        # Given
        precio = 100
        porcentaje = -5
        # When
        resultado = aplicar_descuento(precio, porcentaje)
        # Then
        assert resultado == 105.0

    def test_aplicar_descuento_negativo_cien_porciento(self):
        # Given
        precio = 100
        porcentaje = -100
        # When
        resultado = aplicar_descuento(precio, porcentaje)
        # Then
        assert resultado == 0.0

    def test_aplicar_descuento_negativo_ventaja(self):
        # Given
        precio = 100
        porcentaje = -25
        # When
        resultado = aplicar_descuento(precio, porcentaje)
        # Then
        assert resultado == 75.0

    def test_precio_unitario_cero_total(self):
        # Given
        precio_total = 0
        cantidad = 10
        # When
        resultado = precio_unitario(precio_total, cantidad)
        # Then
        assert resultado == 0.0

    def test_precio_unitario_uno_total(self):
        # Given
        precio_total = 1
        cantidad = 10
        # When
        resultado = precio_unitario(precio_total, cantidad)
        # Then
        assert resultado == 0.1

    def test_precio_unitario_muchos_total(self):
        # Given
        precio_total = 200
        cantidad = 10
        # When
        resultado = precio_unitario(precio_total, cantidad)
        # Then
        assert resultado == 20.0

    def test_precio_unitario_cero_cantidad(self):
        # Given
        precio_total = 200
        cantidad = 0
        # When
        with pytest.raises(ZeroDivisionError):
            precio_unitario(precio_total, cantidad)

    def test_precio_unitario_negativo_cantidad(self):
        # Given
        precio_total = 200
        cantidad = -1
        # When
        resultado = precio_unitario(precio_total, cantidad)
        # Then
        assert resultado == -200.0

    def test_aplicar_descuento_escalonado_menos_de_10(self):
        # Given
        precio = 100
        cantidad = 9
        # When
        resultado = aplicar_descuento_escalonado(precio, cantidad)
        # Then
        assert resultado == 100.0

    def test_aplicar_descuento_escalonado_10_a_49(self):
        # Given
        precio = 100
        cantidad = 50
        # When
        resultado = aplicar_descuento_escalonado(precio, cantidad)
        # Then
        assert resultado == 95.0

    def test_aplicar_descuento_escalonado_50_a_99(self):
        # Given
        precio = 100
        cantidad = 60
        # When
        resultado = aplicar_descuento_escalonado(precio, cantidad)
        # Then
        assert resultado == 90.0

    def test_aplicar_descuento_escalonado_mas_de_100(self):
        # Given
        precio = 100
        cantidad = 150
        # When
        resultado = aplicar_descuento_escalonado(precio, cantidad)
        # Then
        assert resultado == 80.0

    def test_aplicar_descuento_escalonado_negativo_cantidad(self):
        # Given
        precio = 100
        cantidad = -1
        # When
        with pytest.raises(ZeroDivisionError):
            aplicar_descuento_escalonado(precio, cantidad)