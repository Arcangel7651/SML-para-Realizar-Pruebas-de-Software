# Contexto RAG — conversor_temperatura

- Generado: 2026-06-16T07:38:32.400Z
- Total de fragmentos: 3

## Fragmento 1 — Patrón recuperado por similitud

```text
Patron pytest: prueba de excepciones con pytest.raises. Usar pytest.raises(TipoError) como context manager para capturar excepciones esperadas. Verificar el mensaje del error con el parametro match usando expresion regular. Capturar el ExceptionInfo para inspeccionar atributos adicionales de la excepcion. IMPORTANTE: este es un patron generico de ejemplo. Las funciones, metodos y mensajes de excepcion (dividir, obtener_elemento, parsear_fecha, 'division por cero', 'formato invalido', etc.) son ilustrativos: solo escribe un test de excepcion si el modulo bajo prueba tiene una funcion o metodo real que efectivamente lance esa excepcion (revisa el codigo fuente proporcionado). Nunca inventes metodos que no existen en el modulo. Ejemplo completo: def test_dividir_entre_cero_lanza_ValueError(self):     # Given     numerador = 10     # When / Then     with pytest.raises(ValueError, match='division por cero'):         dividir(numerador, 0). def test_acceder_indice_invalido_lanza_IndexError(self):     lista = [1, 2, 3]     with pytest.raises(IndexError):         obtener_elemento(lista, 99). def test_excinfo_contiene_mensaje_descriptivo(self):     with pytest.raises(ValueError) as excinfo:         parsear_fecha('no-es-fecha')     assert 'formato invalido' in str(excinfo.value). Nunca usar try/except dentro de un test: pytest.raises es la forma correcta.
```

## Fragmento 2 — Patrón recuperado por similitud

```text
Patron pytest: casos limite, valores de frontera y entradas invalidas. Probar sistematicamente: cero, uno, negativos, cadena vacia, None, lista vacia, valor maximo. Un test por caso limite para aislar fallos y mantener claridad en el nombre. Ejemplo completo: def test_promedio_lista_vacia_retorna_cero(self):     # Given     datos = []     # When     resultado = promedio(datos)     # Then     assert resultado == 0. def test_factorial_de_cero_retorna_uno(self):     assert factorial(0) == 1. def test_buscar_en_lista_vacia_retorna_None(self):     assert buscar([], 'x') is None. def test_potencia_con_exponente_negativo(self):     assert potencia(2, -1) == pytest.approx(0.5). def test_funcion_acepta_None_sin_lanzar_excepcion(self):     resultado = procesar(None)     assert resultado is not None. Cubrir la frontera inferior y superior del dominio de cada parametro.
```

## Fragmento 3 — Patrón recuperado por similitud

```text
Patron pytest: aserciones de valores concretos y resultados numericos. Comparar el valor de retorno exacto con el esperado usando assert resultado == esperado. Para flotantes usar pytest.approx: assert suma(0.1, 0.2) == pytest.approx(0.3). Verificar que la funcion retorna el valor correcto para entradas positivas, negativas y cero. IMPORTANTE: este es un patron generico de ejemplo. Los nombres de funcion (multiplicar, restar, dividir, etc.) son ilustrativos: nunca los copies literalmente, usa siempre las funciones y metodos reales del modulo bajo prueba. Ejemplo completo: def test_multiplicar_dos_positivos_retorna_producto_correcto(self):     # Given     a, b = 4, 5     # When     resultado = multiplicar(a, b)     # Then     assert resultado == 20. def test_restar_resultado_negativo(self):     assert restar(3, 10) == -7. def test_dividir_retorna_flotante_approx(self):     assert dividir(1, 3) == pytest.approx(0.3333, rel=1e-3). No mezclar verificacion de tipos en este patron: enfocarse solo en el valor de retorno.
```
