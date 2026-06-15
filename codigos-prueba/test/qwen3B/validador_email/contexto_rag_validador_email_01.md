# Contexto RAG — validador_email

- Generado: 2026-06-15T04:31:27.097Z
- Total de fragmentos: 3

## Fragmento 1 — Patrón recuperado por similitud

```text
Patron pytest: prueba de excepciones con pytest.raises. Usar pytest.raises(TipoError) como context manager para capturar excepciones esperadas. Verificar el mensaje del error con el parametro match usando expresion regular. Capturar el ExceptionInfo para inspeccionar atributos adicionales de la excepcion. IMPORTANTE: este es un patron generico de ejemplo. Las funciones, metodos y mensajes de excepcion (dividir, obtener_elemento, parsear_fecha, 'division por cero', 'formato invalido', etc.) son ilustrativos: solo escribe un test de excepcion si el modulo bajo prueba tiene una funcion o metodo real que efectivamente lance esa excepcion (revisa el codigo fuente proporcionado). Nunca inventes metodos que no existen en el modulo. Ejemplo completo: def test_dividir_entre_cero_lanza_ValueError(self):     # Given     numerador = 10     # When / Then     with pytest.raises(ValueError, match='division por cero'):         dividir(numerador, 0). def test_acceder_indice_invalido_lanza_IndexError(self):     lista = [1, 2, 3]     with pytest.raises(IndexError):         obtener_elemento(lista, 99). def test_excinfo_contiene_mensaje_descriptivo(self):     with pytest.raises(ValueError) as excinfo:         parsear_fecha('no-es-fecha')     assert 'formato invalido' in str(excinfo.value). Nunca usar try/except dentro de un test: pytest.raises es la forma correcta.
```

## Fragmento 2 — Patrón recuperado por similitud

```text
Patron pytest: verificacion de estructura, tipo y contrato de retorno. Comprobar que la funcion retorna el tipo correcto antes de verificar el valor. Verificar longitud de colecciones con assert len(resultado) == n. Verificar presencia de claves en diccionarios con assert 'clave' in resultado. Verificar que todos los elementos de una lista cumplen un tipo con all() y isinstance(). Ejemplo completo: def test_obtener_usuarios_retorna_lista(self):     # Given / When     resultado = obtener_usuarios()     # Then     assert isinstance(resultado, list). def test_lista_usuarios_no_esta_vacia(self):     assert len(obtener_usuarios()) > 0. def test_cada_usuario_es_instancia_de_Usuario(self):     usuarios = obtener_usuarios()     assert all(isinstance(u, Usuario) for u in usuarios). def test_diccionario_retornado_tiene_claves_requeridas(self):     perfil = obtener_perfil(1)     assert isinstance(perfil, dict)     assert 'nombre' in perfil     assert 'email' in perfil     assert 'edad' in perfil. Separar la verificacion de tipo en un test propio de la verificacion de valor.
```

## Fragmento 3 — Patrón recuperado por similitud

```text
Patron pytest: casos limite, valores de frontera y entradas invalidas. Probar sistematicamente: cero, uno, negativos, cadena vacia, None, lista vacia, valor maximo. Un test por caso limite para aislar fallos y mantener claridad en el nombre. Ejemplo completo: def test_promedio_lista_vacia_retorna_cero(self):     # Given     datos = []     # When     resultado = promedio(datos)     # Then     assert resultado == 0. def test_factorial_de_cero_retorna_uno(self):     assert factorial(0) == 1. def test_buscar_en_lista_vacia_retorna_None(self):     assert buscar([], 'x') is None. def test_potencia_con_exponente_negativo(self):     assert potencia(2, -1) == pytest.approx(0.5). def test_funcion_acepta_None_sin_lanzar_excepcion(self):     resultado = procesar(None)     assert resultado is not None. Cubrir la frontera inferior y superior del dominio de cada parametro.
```
