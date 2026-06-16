# Contexto RAG — lista_compras

- Generado: 2026-06-16T05:42:27.876Z
- Total de fragmentos: 5

## Fragmento 1 — Advertencia del módulo

```text
ADVERTENCIA para el módulo 'lista_compras': en una generación previa, los tests generados tuvieron estos test smells: assertion_roulette. Al generar tests para este módulo, recuerda que no incluyas más de un assert por test sin un mensaje descriptivo en cada uno (segundo argumento de assert) — regla OR-6.
```

## Fragmento 2 — Advertencia del módulo

```text
ADVERTENCIA para el módulo 'lista_compras': en una generación previa, estos tests fallaron al ejecutarse porque su aserción no se cumplió:
  - test_agregar_dos_items_diferentes_a_carrito_vacio: assert len(self.carrito.items) == 2 → AssertionError: assert 3 == 2 | +  where 3 = len([{'cantidad': 3, 'nombre': 'manzana', 'precio': 0.5}, {'cantidad': 3, 'nombre': 'manzana', 'precio': 0.5}, {'cantidad': 2, 'nombre': 'pera', 'precio': 0.
  - test_total_carrito_vacio: assert total == expected_total → assert 6.8 == 0
  - test_total_carrito_con_un_item: assert total == expected_total → assert 8.3 == 1.5
  - test_total_carrito_con_dos_items: assert total == expected_total → assert 10.600000000000001 == 2.3
Revisa el comportamiento REAL de cada función (su código y su docstring) antes de fijar el valor esperado en el assert. No copies a ciegas el valor que la función devolvió solo para que el test pase: si ese valor no es el correcto según el contrato de la función, el test sería tautológico y ocultaría un bug.
```

## Fragmento 3 — Ejemplo aprendido del módulo

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

## Fragmento 4 — Patrón recuperado por similitud

```text
Patron pytest: casos limite, valores de frontera y entradas invalidas. Probar sistematicamente: cero, uno, negativos, cadena vacia, None, lista vacia, valor maximo. Un test por caso limite para aislar fallos y mantener claridad en el nombre. Ejemplo completo: def test_promedio_lista_vacia_retorna_cero(self):     # Given     datos = []     # When     resultado = promedio(datos)     # Then     assert resultado == 0. def test_factorial_de_cero_retorna_uno(self):     assert factorial(0) == 1. def test_buscar_en_lista_vacia_retorna_None(self):     assert buscar([], 'x') is None. def test_potencia_con_exponente_negativo(self):     assert potencia(2, -1) == pytest.approx(0.5). def test_funcion_acepta_None_sin_lanzar_excepcion(self):     resultado = procesar(None)     assert resultado is not None. Cubrir la frontera inferior y superior del dominio de cada parametro.
```

## Fragmento 5 — Patrón recuperado por similitud

```text
Patron pytest: verificacion de estructura, tipo y contrato de retorno. Comprobar que la funcion retorna el tipo correcto antes de verificar el valor. Verificar longitud de colecciones con assert len(resultado) == n. Verificar presencia de claves en diccionarios con assert 'clave' in resultado. Verificar que todos los elementos de una lista cumplen un tipo con all() y isinstance(). Ejemplo completo: def test_obtener_usuarios_retorna_lista(self):     # Given / When     resultado = obtener_usuarios()     # Then     assert isinstance(resultado, list). def test_lista_usuarios_no_esta_vacia(self):     assert len(obtener_usuarios()) > 0. def test_cada_usuario_es_instancia_de_Usuario(self):     usuarios = obtener_usuarios()     assert all(isinstance(u, Usuario) for u in usuarios). def test_diccionario_retornado_tiene_claves_requeridas(self):     perfil = obtener_perfil(1)     assert isinstance(perfil, dict)     assert 'nombre' in perfil     assert 'email' in perfil     assert 'edad' in perfil. Separar la verificacion de tipo en un test propio de la verificacion de valor.
```
