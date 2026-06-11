import pytest
from estructuras import invertir_lista, eliminar_duplicados, pila_push, pila_pop, cola_enqueue, cola_dequeue

class TestEstructuras:
    def test_invertir_lista(self):
        # Given
        lista = [1, 2, 3, 4, 5]

        # When
        resultado = invertir_lista(lista)

        # Then
        assert resultado == [5, 4, 3, 2, 1]

    def test_eliminar_duplicados(self):
        # Given
        lista = [1, 1, 2, 2, 3, 3, 4, 4]

        # When
        resultado = eliminar_duplicados(lista)

        # Then
        assert resultado == [1, 2, 3, 4]

    def test_pila_push(self):
        # Given
        pila = []
        elemento = "elem"

        # When
        resultado = pila_push(pila, elemento)

        # Then
        assert resultado == ["elem"]

    def test_pila_pop(self):
        # Given
        pila = ["elem"]

        # When
        resultado = pila_pop(pila)

        # Then
        assert resultado == "elem"

    def test_cola_enqueue(self):
        # Given
        cola = []
        elemento = "elem"

        # When
        resultado = cola_enqueue(cola, elemento)

        # Then
        assert resultado == ["elem"]

    def test_cola_dequeue(self):
        # Given
        cola = ["elem"]

        # When
        resultado = cola_dequeue(cola)

        # Then
        assert resultado == "elem"

def test_no_functions_detected():
    pytest.skip("Module contains no analyzable functions")