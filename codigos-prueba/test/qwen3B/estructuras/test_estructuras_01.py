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