# Contexto RAG — procesador_descuentos

- Generado: 2026-06-16T19:25:36.417Z
- Total de fragmentos: 4

## Fragmento 1 — Advertencia del módulo

```text
ADVERTENCIA para el módulo 'procesador_descuentos': en una generación previa, estos tests fallaron al ejecutarse porque su aserción no se cumplió:
  - test_aplicar_descuento_escalonado_cero_cantidad: assert resultado == 80 → Failed: DID NOT RAISE <class 'ZeroDivisionError'> | assert 95.0 == 80
Revisa el comportamiento REAL de cada función (su código y su docstring) antes de fijar el valor esperado en el assert. No copies a ciegas el valor que la función devolvió solo para que el test pase: si ese valor no es el correcto según el contrato de la función, el test sería tautológico y ocultaría un bug.
```

## Fragmento 2 — Ejemplo aprendido del módulo

```text
[meta score=70.07 kept=7] Ejemplo verificado de tests pytest para el módulo 'procesador_descuentos' (subconjunto de tests que pasaron) (funciones: aplicar_descuento, precio_unitario, aplicar_descuento_escalonado). 7 test(s) verificados que pasan, 70.0% de cobertura de línea. Código de prueba:
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
```

## Fragmento 3 — Patrón recuperado por similitud

```text
Patron pytest: casos limite, valores de frontera y entradas invalidas. Probar sistematicamente: cero, uno, negativos, cadena vacia, None, lista vacia, valor maximo. Un test por caso limite para aislar fallos y mantener claridad en el nombre. Ejemplo completo: def test_promedio_lista_vacia_retorna_cero(self):     # Given     datos = []     # When     resultado = promedio(datos)     # Then     assert resultado == 0. def test_factorial_de_cero_retorna_uno(self):     assert factorial(0) == 1. def test_buscar_en_lista_vacia_retorna_None(self):     assert buscar([], 'x') is None. def test_potencia_con_exponente_negativo(self):     assert potencia(2, -1) == pytest.approx(0.5). def test_funcion_acepta_None_sin_lanzar_excepcion(self):     resultado = procesar(None)     assert resultado is not None. Cubrir la frontera inferior y superior del dominio de cada parametro.
```

## Fragmento 4 — Patrón recuperado por similitud

```text
Patron pytest: aserciones de valores concretos y resultados numericos. Comparar el valor de retorno exacto con el esperado usando assert resultado == esperado. Para flotantes usar pytest.approx: assert suma(0.1, 0.2) == pytest.approx(0.3). Verificar que la funcion retorna el valor correcto para entradas positivas, negativas y cero. IMPORTANTE: este es un patron generico de ejemplo. Los nombres de funcion (multiplicar, restar, dividir, etc.) son ilustrativos: nunca los copies literalmente, usa siempre las funciones y metodos reales del modulo bajo prueba. Ejemplo completo: def test_multiplicar_dos_positivos_retorna_producto_correcto(self):     # Given     a, b = 4, 5     # When     resultado = multiplicar(a, b)     # Then     assert resultado == 20. def test_restar_resultado_negativo(self):     assert restar(3, 10) == -7. def test_dividir_retorna_flotante_approx(self):     assert dividir(1, 3) == pytest.approx(0.3333, rel=1e-3). No mezclar verificacion de tipos en este patron: enfocarse solo en el valor de retorno.
```
