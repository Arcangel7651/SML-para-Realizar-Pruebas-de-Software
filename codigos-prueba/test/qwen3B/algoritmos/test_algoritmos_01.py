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