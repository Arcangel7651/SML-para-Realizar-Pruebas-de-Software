# Contexto RAG — estructuras

- Generado: 2026-06-16T04:31:45.282Z
- Total de fragmentos: 3

## Fragmento 1 — Patrón recuperado por similitud

```text
Patron pytest: verificacion de estructura, tipo y contrato de retorno. Comprobar que la funcion retorna el tipo correcto antes de verificar el valor. Verificar longitud de colecciones con assert len(resultado) == n. Verificar presencia de claves en diccionarios con assert 'clave' in resultado. Verificar que todos los elementos de una lista cumplen un tipo con all() y isinstance(). Ejemplo completo: def test_obtener_usuarios_retorna_lista(self):     # Given / When     resultado = obtener_usuarios()     # Then     assert isinstance(resultado, list). def test_lista_usuarios_no_esta_vacia(self):     assert len(obtener_usuarios()) > 0. def test_cada_usuario_es_instancia_de_Usuario(self):     usuarios = obtener_usuarios()     assert all(isinstance(u, Usuario) for u in usuarios). def test_diccionario_retornado_tiene_claves_requeridas(self):     perfil = obtener_perfil(1)     assert isinstance(perfil, dict)     assert 'nombre' in perfil     assert 'email' in perfil     assert 'edad' in perfil. Separar la verificacion de tipo en un test propio de la verificacion de valor.
```

## Fragmento 2 — Patrón recuperado por similitud

```text
[meta score=80.09 kept=9] Ejemplo verificado de tests pytest para el módulo 'algoritmos' (funciones: bubble_sort, binary_search, busqueda_lineal, encontrar_maximo, encontrar_minimo). 9 test(s) verificados que pasan, 80.0% de cobertura de línea. Código de prueba:
import pytest
from algoritmos import bubble_sort, binary_search, busqueda_lineal, encontrar_maximo, encontrar_minimo

class TestAlgoritmos(object):

    def test_bubble_sort_lista_vacia_retorna_lista_vacia(self):
        # Given
        lista = []
        
        # When
        resultado = bubble_sort(lista)
        
        # Then
        assert resultado == []

    def test_binary_search_encontrar_elemento_existente(self):
        # Given
        lista = [1, 2, 3, 4, 5]
        objetivo = 3
        
        # When
        indice = binary_search(lista, objetivo)
        
        # Then
        assert indice == 2

    def test_binary_search_encontrar_elemento_inexistente(self):
        # Given
        lista = [1, 2, 3, 4, 5]
        objetivo = 6
        
        # When
        indice = binary_search(lista, objetivo)
        
        # Then
        assert indice == -1

    def test_busqueda_lineal_encontrar_elemento_existente(self):
        # Given
        lista = [10, 20, 30, 40, 50]
        objetivo = 30
        
        # When
        indice = busqueda_lineal(lista, objetivo)
        
        # Then
        assert indice == 2

    def test_busqueda_lineal_encontrar_elemento_inexistente(self):
        # Given
        lista = [10, 20, 30, 40, 50]
        objetivo = 60
        
        # When
        indice = busqueda_lineal(lista, objetivo)
        
        # Then
        assert indice == -1

    def test_encontrar_maximo_lista_no_vacia(self):
        # Given
        lista = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
        
        # When
        maximo = encontrar_maximo(lista)
        
        # Then
        assert maximo == 9

    def test_encontrar_minimo_lista_no_vacia(self):
        # Given
        lista = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
        
        # When
        minimo = encontrar_minimo(lista)
        
        # Then
        assert minimo == 1

    def test_encontrar_maximo_lista_vacia_lanza_error(self):
        # Given
        lista = []
        
        # When / Then
        with pytest.raises(ValueError) as e:
            encontrar_maximo(lista)
        assert str(e.value) == "La lista está vacía."

    def test_encontrar_minimo_lista_vacia_lanza_error(self):
        # Given
        lista = []
        
        # When / Then
        with pytest.raises(ValueError) as e:
            encontrar_minimo(lista)
        assert str(e.value) == "La lista está vacía."
```

## Fragmento 3 — Patrón recuperado por similitud

```text
Patron pytest: casos limite, valores de frontera y entradas invalidas. Probar sistematicamente: cero, uno, negativos, cadena vacia, None, lista vacia, valor maximo. Un test por caso limite para aislar fallos y mantener claridad en el nombre. Ejemplo completo: def test_promedio_lista_vacia_retorna_cero(self):     # Given     datos = []     # When     resultado = promedio(datos)     # Then     assert resultado == 0. def test_factorial_de_cero_retorna_uno(self):     assert factorial(0) == 1. def test_buscar_en_lista_vacia_retorna_None(self):     assert buscar([], 'x') is None. def test_potencia_con_exponente_negativo(self):     assert potencia(2, -1) == pytest.approx(0.5). def test_funcion_acepta_None_sin_lanzar_excepcion(self):     resultado = procesar(None)     assert resultado is not None. Cubrir la frontera inferior y superior del dominio de cada parametro.
```
