# Contexto RAG — validador_edad

- Generado: 2026-06-19T01:25:01.561Z
- Total de fragmentos: 3

## Fragmento 1 — Ejemplo aprendido del módulo

```text
[meta score=90.08 kept=8] Ejemplo verificado de tests pytest para el módulo 'validador_edad' (subconjunto de tests que pasaron) (funciones: clasificar_edad, es_mayor_de_edad). 8 test(s) verificados que pasan, 90.0% de cobertura de línea. Código de prueba:
import pytest
from validador_edad import clasificar_edad, es_mayor_de_edad


class TestValidadorEdad(object):
    def setup_method(self):
        self.clasificar_edad = clasificar_edad
        self.es_mayor_de_edad = es_mayor_de_edad

    # Given: edad 12, expect 'niño'

    def test_clasificar_12_es_nino(self):
        # When
        resultado = self.clasificar_edad(12)
        # Then
        assert resultado == "niño", "Clasificación de 12 años debe ser 'niño'"

    def test_clasificar_14_es_adolescente(self):
        # When
        resultado = self.clasificar_edad(14)
        # Then
        assert resultado == "adolescente", "Clasificación de 14 años debe ser 'adolescente'"

    def test_clasificar_64_es_adulto_mayor(self):
        # When
        resultado = self.clasificar_edad(64)
        # Then
        assert resultado == "adulto mayor", "Clasificación de 64 años debe ser 'adulto mayor'"

    def test_clasificar_65_es_desconocido(self):
        # When
        resultado = self.clasificar_edad(65)
        # Then
        assert resultado == "desconocido", "Clasificación de 65 años debe ser 'desconocido'"

    def test_es_mayor_de_edad_13_no_es(self):
        # When
        resultado = self.es_mayor_de_edad(13)
        # Then
        assert not resultado, "Edad 13 no debería ser mayor de edad"

    def test_es_mayor_de_edad_18_no_es(self):
        # When
        resultado = self.es_mayor_de_edad(18)
        # Then
        assert not resultado, "Edad 18 no debería ser mayor de edad"

    def test_es_mayor_de_edad_20_si_es(self):
        # When
        resultado = self.es_mayor_de_edad(20)
        # Then
        assert resultado, "Edad 20 debería ser mayor de edad"

    def test_es_mayor_de_edad_64_si_es(self):
        # When
        resultado = self.es_mayor_de_edad(64)
        # Then
        assert resultado, "Edad 64 debería ser mayor de edad"
```

## Fragmento 2 — Patrón recuperado por similitud

```text
Patron pytest: casos limite, valores de frontera y entradas invalidas. Probar sistematicamente: cero, uno, negativos, cadena vacia, None, lista vacia, valor maximo. Un test por caso limite para aislar fallos y mantener claridad en el nombre. Ejemplo completo: def test_promedio_lista_vacia_retorna_cero(self):     # Given     datos = []     # When     resultado = promedio(datos)     # Then     assert resultado == 0. def test_factorial_de_cero_retorna_uno(self):     assert factorial(0) == 1. def test_buscar_en_lista_vacia_retorna_None(self):     assert buscar([], 'x') is None. def test_potencia_con_exponente_negativo(self):     assert potencia(2, -1) == pytest.approx(0.5). def test_funcion_acepta_None_sin_lanzar_excepcion(self):     resultado = procesar(None)     assert resultado is not None. Cubrir la frontera inferior y superior del dominio de cada parametro.
```

## Fragmento 3 — Patrón recuperado por similitud

```text
Patron pytest: verificacion de estructura, tipo y contrato de retorno. Comprobar que la funcion retorna el tipo correcto antes de verificar el valor. Verificar longitud de colecciones con assert len(resultado) == n. Verificar presencia de claves en diccionarios con assert 'clave' in resultado. Verificar que todos los elementos de una lista cumplen un tipo con all() y isinstance(). Ejemplo completo: def test_obtener_usuarios_retorna_lista(self):     # Given / When     resultado = obtener_usuarios()     # Then     assert isinstance(resultado, list). def test_lista_usuarios_no_esta_vacia(self):     assert len(obtener_usuarios()) > 0. def test_cada_usuario_es_instancia_de_Usuario(self):     usuarios = obtener_usuarios()     assert all(isinstance(u, Usuario) for u in usuarios). def test_diccionario_retornado_tiene_claves_requeridas(self):     perfil = obtener_perfil(1)     assert isinstance(perfil, dict)     assert 'nombre' in perfil     assert 'email' in perfil     assert 'edad' in perfil. Separar la verificacion de tipo en un test propio de la verificacion de valor.
```
