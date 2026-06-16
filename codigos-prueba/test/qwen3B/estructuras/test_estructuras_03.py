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

    def test_pila_push_agrega_numeros_al_topo(self):
        # Given
        pila = []
        
        # When
        for i in range(5, 0, -1):
            pila = pila_push(pila, i)
        
        # Then
        assert pila == list(range(5))

    def test_pila_pop_elimina_numeros_del_topo(self):
        # Given
        pila = list(range(5))
        
        # When
        for i in range(4, -1, -1):
            resultado = pila_pop(pila)
            
            # Then
            assert resultado == i
            assert len(pila) == 4 if i != 0 else 0

    def test_cola_enqueue_agrega_numeros_al_final(self):
        # Given
        cola = []
        
        # When
        for i in range(5, 0, -1):
            cola = cola_enqueue(cola, i)
        
        # Then
        assert cola == list(range(1, 6))

    def test_cola_dequeue_elimina_numeros_del_principio(self):
        # Given
        cola = list(range(1, 6))
        
        # When
        for i in range(5, 0, -1):
            resultado = cola_dequeue(cola)
            
            # Then
            assert resultado == i
            assert len(cola) == 4 if i != 1 else 0

    def test_pila_pop_lanza_IndexError_si_pila_esta_vacia(self):
        with pytest.raises(IndexError) as excinfo:
            pila_pop([])
        assert "La pila está vacía." in str(excinfo.value)

    def test_cola_dequeue_lanza_IndexError_si_cola_esta_vacia(self):
        with pytest.raises(IndexError) as excinfo:
            cola_dequeue([])
        assert "La cola está vacía." in str(excinfo.value)