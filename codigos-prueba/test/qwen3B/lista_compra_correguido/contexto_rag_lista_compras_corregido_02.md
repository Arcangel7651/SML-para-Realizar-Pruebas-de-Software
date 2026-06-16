# Contexto RAG — lista_compras_corregido

- Generado: 2026-06-16T06:56:11.670Z
- Total de fragmentos: 5

## Fragmento 1 — Advertencia del módulo

```text
ADVERTENCIA para el módulo 'lista_compras_corregido': en una generación previa, los tests generados tuvieron estos test smells: assertion_roulette. Al generar tests para este módulo, recuerda que no incluyas más de un assert por test sin un mensaje descriptivo en cada uno (segundo argumento de assert) — regla OR-6.
```

## Fragmento 2 — Advertencia del módulo

```text
ADVERTENCIA para el módulo 'lista_compras_corregido': en una generación previa, estos tests fallaron al ejecutarse porque su aserción no se cumplió:
  - test_agregar_item_con_nombre_existente: Failed: DID NOT RAISE <class 'ValueError'>
  - test_quitar_item_que_no_existe: Failed: DID NOT RAISE <class 'ValueError'>
  - test_total_carrito_con_items_diferentes: assert total == 6.5 → assert 3.5 == 6.5
  - test_total_carrito_con_item_negativo_precio: Failed: DID NOT RAISE <class 'ValueError'>
Revisa el comportamiento REAL de cada función (su código y su docstring) antes de fijar el valor esperado en el assert. No copies a ciegas el valor que la función devolvió solo para que el test pase: si ese valor no es el correcto según el contrato de la función, el test sería tautológico y ocultaría un bug.
```

## Fragmento 3 — Patrón recuperado por similitud

```text
[meta score=59.03 kept=3] Ejemplo verificado de tests pytest para el módulo 'lista_compras' (subconjunto de tests que pasaron) (funciones: agregar_item, quitar_item, total). 3 test(s) verificados que pasan, 59.0% de cobertura de línea. Código de prueba:
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
```

## Fragmento 4 — Ejemplo aprendido del módulo

```text
[meta score=76.05 kept=5] Ejemplo verificado de tests pytest para el módulo 'lista_compras_corregido' (subconjunto de tests que pasaron) (funciones: agregar_item, quitar_item, total). 5 test(s) verificados que pasan, 76.0% de cobertura de línea. Código de prueba:
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
```

## Fragmento 5 — Patrón recuperado por similitud

```text
Patron pytest: casos limite, valores de frontera y entradas invalidas. Probar sistematicamente: cero, uno, negativos, cadena vacia, None, lista vacia, valor maximo. Un test por caso limite para aislar fallos y mantener claridad en el nombre. Ejemplo completo: def test_promedio_lista_vacia_retorna_cero(self):     # Given     datos = []     # When     resultado = promedio(datos)     # Then     assert resultado == 0. def test_factorial_de_cero_retorna_uno(self):     assert factorial(0) == 1. def test_buscar_en_lista_vacia_retorna_None(self):     assert buscar([], 'x') is None. def test_potencia_con_exponente_negativo(self):     assert potencia(2, -1) == pytest.approx(0.5). def test_funcion_acepta_None_sin_lanzar_excepcion(self):     resultado = procesar(None)     assert resultado is not None. Cubrir la frontera inferior y superior del dominio de cada parametro.
```
