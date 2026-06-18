# Contexto RAG — procesador_descuentos_corregido

- Generado: 2026-06-16T21:06:27.108Z
- Total de fragmentos: 3

## Fragmento 1 — Patrón recuperado por similitud

```text
Patron pytest: casos limite, valores de frontera y entradas invalidas. Probar sistematicamente: cero, uno, negativos, cadena vacia, None, lista vacia, valor maximo. Un test por caso limite para aislar fallos y mantener claridad en el nombre. Ejemplo completo: def test_promedio_lista_vacia_retorna_cero(self):     # Given     datos = []     # When     resultado = promedio(datos)     # Then     assert resultado == 0. def test_factorial_de_cero_retorna_uno(self):     assert factorial(0) == 1. def test_buscar_en_lista_vacia_retorna_None(self):     assert buscar([], 'x') is None. def test_potencia_con_exponente_negativo(self):     assert potencia(2, -1) == pytest.approx(0.5). def test_funcion_acepta_None_sin_lanzar_excepcion(self):     resultado = procesar(None)     assert resultado is not None. Cubrir la frontera inferior y superior del dominio de cada parametro.
```

## Fragmento 2 — Patrón recuperado por similitud

```text
Patron pytest: aserciones de valores concretos y resultados numericos. Comparar el valor de retorno exacto con el esperado usando assert resultado == esperado. Para flotantes usar pytest.approx: assert suma(0.1, 0.2) == pytest.approx(0.3). Verificar que la funcion retorna el valor correcto para entradas positivas, negativas y cero. IMPORTANTE: este es un patron generico de ejemplo. Los nombres de funcion (multiplicar, restar, dividir, etc.) son ilustrativos: nunca los copies literalmente, usa siempre las funciones y metodos reales del modulo bajo prueba. Ejemplo completo: def test_multiplicar_dos_positivos_retorna_producto_correcto(self):     # Given     a, b = 4, 5     # When     resultado = multiplicar(a, b)     # Then     assert resultado == 20. def test_restar_resultado_negativo(self):     assert restar(3, 10) == -7. def test_dividir_retorna_flotante_approx(self):     assert dividir(1, 3) == pytest.approx(0.3333, rel=1e-3). No mezclar verificacion de tipos en este patron: enfocarse solo en el valor de retorno.
```

## Fragmento 3 — Patrón recuperado por similitud

```text
Patron pytest: verificacion de estructura, tipo y contrato de retorno. Comprobar que la funcion retorna el tipo correcto antes de verificar el valor. Verificar longitud de colecciones con assert len(resultado) == n. Verificar presencia de claves en diccionarios con assert 'clave' in resultado. Verificar que todos los elementos de una lista cumplen un tipo con all() y isinstance(). Ejemplo completo: def test_obtener_usuarios_retorna_lista(self):     # Given / When     resultado = obtener_usuarios()     # Then     assert isinstance(resultado, list). def test_lista_usuarios_no_esta_vacia(self):     assert len(obtener_usuarios()) > 0. def test_cada_usuario_es_instancia_de_Usuario(self):     usuarios = obtener_usuarios()     assert all(isinstance(u, Usuario) for u in usuarios). def test_diccionario_retornado_tiene_claves_requeridas(self):     perfil = obtener_perfil(1)     assert isinstance(perfil, dict)     assert 'nombre' in perfil     assert 'email' in perfil     assert 'edad' in perfil. Separar la verificacion de tipo en un test propio de la verificacion de valor.
```
