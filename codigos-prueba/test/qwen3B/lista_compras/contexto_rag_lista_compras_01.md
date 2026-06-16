# Contexto RAG — lista_compras

- Generado: 2026-06-16T05:25:21.971Z
- Total de fragmentos: 3

## Fragmento 1 — Patrón recuperado por similitud

```text
Patron pytest: casos limite, valores de frontera y entradas invalidas. Probar sistematicamente: cero, uno, negativos, cadena vacia, None, lista vacia, valor maximo. Un test por caso limite para aislar fallos y mantener claridad en el nombre. Ejemplo completo: def test_promedio_lista_vacia_retorna_cero(self):     # Given     datos = []     # When     resultado = promedio(datos)     # Then     assert resultado == 0. def test_factorial_de_cero_retorna_uno(self):     assert factorial(0) == 1. def test_buscar_en_lista_vacia_retorna_None(self):     assert buscar([], 'x') is None. def test_potencia_con_exponente_negativo(self):     assert potencia(2, -1) == pytest.approx(0.5). def test_funcion_acepta_None_sin_lanzar_excepcion(self):     resultado = procesar(None)     assert resultado is not None. Cubrir la frontera inferior y superior del dominio de cada parametro.
```

## Fragmento 2 — Patrón recuperado por similitud

```text
Patron pytest: verificacion de estructura, tipo y contrato de retorno. Comprobar que la funcion retorna el tipo correcto antes de verificar el valor. Verificar longitud de colecciones con assert len(resultado) == n. Verificar presencia de claves en diccionarios con assert 'clave' in resultado. Verificar que todos los elementos de una lista cumplen un tipo con all() y isinstance(). Ejemplo completo: def test_obtener_usuarios_retorna_lista(self):     # Given / When     resultado = obtener_usuarios()     # Then     assert isinstance(resultado, list). def test_lista_usuarios_no_esta_vacia(self):     assert len(obtener_usuarios()) > 0. def test_cada_usuario_es_instancia_de_Usuario(self):     usuarios = obtener_usuarios()     assert all(isinstance(u, Usuario) for u in usuarios). def test_diccionario_retornado_tiene_claves_requeridas(self):     perfil = obtener_perfil(1)     assert isinstance(perfil, dict)     assert 'nombre' in perfil     assert 'email' in perfil     assert 'edad' in perfil. Separar la verificacion de tipo en un test propio de la verificacion de valor.
```

## Fragmento 3 — Patrón recuperado por similitud

```text
Patron pytest: clase de test con setup_method y teardown_method. setup_method(self) se ejecuta antes de cada metodo de test para crear estado limpio. teardown_method(self) se ejecuta despues de cada test para liberar recursos. Usar self.instancia para compartir el objeto bajo prueba entre metodos sin acoplamiento. Ejemplo completo: class TestPila:     def setup_method(self):         self.pila = Pila()     def test_apilar_elemento_incrementa_tamano(self):         # Given         tamano_inicial = self.pila.tamano()         # When         self.pila.apilar(42)         # Then         assert self.pila.tamano() == tamano_inicial + 1.     def test_desapilar_pila_vacia_lanza_IndexError(self):         with pytest.raises(IndexError):             self.pila.desapilar().     def teardown_method(self):         self.pila = None. No agregar __init__ a la clase de test: pytest no la instancia con argumentos.
```
