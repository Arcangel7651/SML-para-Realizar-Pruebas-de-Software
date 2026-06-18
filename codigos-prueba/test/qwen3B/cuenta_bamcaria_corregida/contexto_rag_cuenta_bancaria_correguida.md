# Contexto RAG — cuenta_bancaria_correguida

- Generado: 2026-06-18T19:13:03.478Z
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
Patron pytest: fixtures para datos de prueba reutilizables entre multiples tests. Definir con @pytest.fixture fuera de la clase e inyectar como parametro en el metodo. Scope function recrea la fixture en cada test; module y session la comparten. Usar yield en lugar de return para fixtures que necesitan limpieza posterior. Ejemplo completo: @pytest.fixture def usuario_con_saldo():     u = Usuario(nombre='Ana', saldo=500.0)     yield u     u.saldo = 0  # limpieza. @pytest.fixture(scope='module') def conexion_bd():     conn = BaseDatos(':memory:')     conn.inicializar_esquema()     yield conn     conn.cerrar(). class TestCartera:     def test_depositar_aumenta_saldo(self, usuario_con_saldo):         # Given         saldo_previo = usuario_con_saldo.saldo         # When         usuario_con_saldo.depositar(100)         # Then         assert usuario_con_saldo.saldo == saldo_previo + 100. Preferir fixtures sobre setup_method cuando el dato se reutiliza en varias clases.
```
