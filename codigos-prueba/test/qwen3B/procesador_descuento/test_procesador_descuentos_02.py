import pytest
from procesador_descuentos import aplicar_descuento, precio_unitario, aplicar_descuento_escalonado

class TestProcesadorDescuentos(object):

    def test_aplicar_descuento_cero_porcentaje(self):
        # Given
        precio = 100
        porcentaje = 0
        
        # When
        resultado = aplicar_descuento(precio, porcentaje)
        
        # Then
        assert resultado == precio

    def test_aplicar_descuento_uno_porcentaje(self):
        # Given
        precio = 100
        porcentaje = 1
        
        # When
        resultado = aplicar_descuento(precio, porcentaje)
        
        # Then
        assert resultado == precio - (precio * (porcentaje / 100))

    def test_aplicar_descuento_cien_porcentaje(self):
        # Given
        precio = 100
        porcentaje = 100
        
        # When
        resultado = aplicar_descuento(precio, porcentaje)
        
        # Then
        assert resultado == 0

    def test_precio_unitario_cero_cantidad(self):
        # Given
        precio_total = 0
        cantidad = 0
        
        # When
        with pytest.raises(ZeroDivisionError):
            precio_unitario(precio_total, cantidad)

    def test_precio_unitario_uno_cantidad(self):
        # Given
        precio_total = 1
        cantidad = 1
        
        # When
        resultado = precio_unitario(precio_total, cantidad)
        
        # Then
        assert resultado == 1

    def test_precio_unitario_muchos_articulos(self):
        # Given
        precio_total = 200
        cantidad = 10
        
        # When
        resultado = precio_unitario(precio_total, cantidad)
        
        # Then
        assert resultado == 20

    def test_aplicar_descuento_escalonado_uno_articulo(self):
        # Given
        precio = 100
        cantidad = 1
        
        # When
        resultado = aplicar_descuento_escalonado(precio, cantidad)
        
        # Then
        assert resultado == precio

    def test_aplicar_descuento_escalonado_cero_cantidad(self):
        # Given
        precio = 100
        cantidad = 0
        
        # When
        with pytest.raises(ZeroDivisionError):
            aplicar_descuento_escalonado(precio, cantidad)

    def test_aplicar_descuento_escalonado_quince_articulos(self):
        # Given
        precio = 100
        cantidad = 15
        
        # When
        resultado = aplicar_descuento_escalonado(precio, cantidad)
        
        # Then
        assert resultado == 95

    def test_aplicar_descuento_escalonado_cien_articulos(self):
        # Given
        precio = 100
        cantidad = 100
        
        # When
        resultado = aplicar_descuento_escalonado(precio, cantidad)
        
        # Then
        assert resultado == 80