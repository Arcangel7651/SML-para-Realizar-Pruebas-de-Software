# Contexto RAG — estructuras

- Generado: 2026-06-16T04:57:07.300Z
- Total de fragmentos: 3

## Fragmento 1 — Ejemplo aprendido del módulo

```text
[meta score=100.09 kept=9] Ejemplo verificado de tests pytest para el módulo 'estructuras' (funciones: invertir_lista, eliminar_duplicados, pila_push, pila_pop, cola_enqueue, cola_dequeue). 9 test(s) verificados que pasan, 100.0% de cobertura de línea. Código de prueba:
import pytest

from estructuras import invertir_lista, eliminar_duplicados, pila_push, pila_pop, cola_enqueue, cola_dequeue

class TestEstructuras(object):

    def test_invertir_lista_vacia_retorna_lista_vacia(self):
        # Given / When
        lista = []
        
        # Then
        assert invertir_lista(lista) == []

    def test_eliminar_duplicados_sin_duplicados(self):
        # Given
        lista = [1, 2, 3, 4, 5]
        
        # Then
        assert eliminar_duplicados(lista) == [1, 2, 3, 4, 5]

    def test_eliminar_duplicados_con_duplicados(self):
        # Given
        lista = [1, 2, 2, 3, 4, 4, 5]
        
        # Then
        assert eliminar_duplicados(lista) == [1, 2, 3, 4, 5]

    def test_pila_push_agrega_elemento_al_topo(self):
        # Given
        pila = []
        
        # When
        pila = pila_push(pila, 'elemento')
        
        # Then
        assert pila == ['elemento']

    def test_pila_pop_elimina_y_retorna_elemento_del_topo(self):
        # Given
        pila = ['elemento']
        
        # When
        resultado = pila_pop(pila)
        
        # Then
        assert resultado == 'elemento'
        assert pila == []

    def test_cola_enqueue_agrega_elemento_al_final(self):
        # Given
        cola = []
        
        # When
        cola = cola_enqueue(cola, 'elemento')
        
        # Then
        assert cola == ['elemento']

    def test_cola_dequeue_elimina_y_retorna_primer_elemento_de_la_cola(self):
        # Given
        cola = ['elemento']
        
        # When
        resultado = cola_dequeue(cola)
        
        # Then
        assert resultado == 'elemento'
        assert cola == []

    def test_pila_pop_lanza_IndexError_si_pila_esta_vacia(self):
        with pytest.raises(IndexError) as excinfo:
            pila_pop([])
        assert "La pila está vacía." in str(excinfo.value)

    def test_cola_dequeue_lanza_IndexError_si_cola_esta_vacia(self):
        with pytest.raises(IndexError) as excinfo:
            cola_dequeue([])
        assert "La cola está vacía." in str(excinfo.value)
```

## Fragmento 2 — Ejemplo aprendido del módulo

```text
[meta score=87.07 kept=7] Ejemplo verificado de tests pytest para el módulo 'estructuras' (funciones: invertir_lista, eliminar_duplicados, pila_push, pila_pop, cola_enqueue, cola_dequeue). 7 test(s) verificados que pasan, 87.0% de cobertura de línea. Código de prueba:
import pytest

from estructuras import invertir_lista, eliminar_duplicados, pila_push, pila_pop, cola_enqueue, cola_dequeue

class TestEstructuras(object):

    def test_invertir_lista_vacia_retorna_lista_vacia(self):
        # Given / When
        lista = []
        
        # Then
        assert invertir_lista(lista) == []

    def test_eliminar_duplicados_sin_duplicados(self):
        # Given
        lista = [1, 2, 3, 4, 5]
        
        # When
        resultado = eliminar_duplicados(lista)
        
        # Then
        assert resultado == [1, 2, 3, 4, 5]

    def test_eliminar_duplicados_con_duplicados(self):
        # Given
        lista = [1, 2, 2, 3, 4, 4, 5]
        
        # Then
        assert eliminar_duplicados(lista) == [1, 2, 3, 4, 5]

    def test_pila_push_agrega_elemento_al_topo(self):
        # Given
        pila = []
        
        # When
        pila = pila_push(pila, 'elemento')
        
        # Then
        assert pila == ['elemento']

    def test_pila_pop_elimina_y_retorna_elemento_del_topo(self):
        # Given
        pila = ['elemento']
        
        # When
        resultado = pila_pop(pila)
        
        # Then
        assert resultado == 'elemento'
        assert pila == []

    def test_cola_enqueue_agrega_elemento_al_final(self):
        # Given
        cola = []
        
        # When
        cola = cola_enqueue(cola, 'elemento')
        
        # Then
        assert cola == ['elemento']

    def test_cola_dequeue_elimina_y_retorna_primer_elemento_de_la_cola(self):
        # Given
        cola = ['elemento']
        
        # When
        resultado = cola_dequeue(cola)
        
        # Then
        assert resultado == 'elemento'
        assert cola == []
```

## Fragmento 3 — Patrón recuperado por similitud

```text
Patron pytest: verificacion de estructura, tipo y contrato de retorno. Comprobar que la funcion retorna el tipo correcto antes de verificar el valor. Verificar longitud de colecciones con assert len(resultado) == n. Verificar presencia de claves en diccionarios con assert 'clave' in resultado. Verificar que todos los elementos de una lista cumplen un tipo con all() y isinstance(). Ejemplo completo: def test_obtener_usuarios_retorna_lista(self):     # Given / When     resultado = obtener_usuarios()     # Then     assert isinstance(resultado, list). def test_lista_usuarios_no_esta_vacia(self):     assert len(obtener_usuarios()) > 0. def test_cada_usuario_es_instancia_de_Usuario(self):     usuarios = obtener_usuarios()     assert all(isinstance(u, Usuario) for u in usuarios). def test_diccionario_retornado_tiene_claves_requeridas(self):     perfil = obtener_perfil(1)     assert isinstance(perfil, dict)     assert 'nombre' in perfil     assert 'email' in perfil     assert 'edad' in perfil. Separar la verificacion de tipo en un test propio de la verificacion de valor.
```
