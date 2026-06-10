import pytest
from algoritmos import bubble_sort, binary_search, busqueda_lineal, encontrar_maximo, encontrar_minimo

class TestAlgoritmos:
    def test_bubble_sort(self):
        lista = [4, 2, 7, 1, 3]
        resultado = bubble_sort(lista)
        assert resultado == [1, 2, 3, 4, 7]

    def test_binary_search(self):
        lista = [1, 2, 3, 4, 5, 6, 7]
        assert binary_search(lista, 1) == 0
        assert binary_search(lista, 2) == 1
        assert binary_search(lista, 3) == 2
        assert binary_search(lista, 4) == 3
        assert binary_search(lista, 5) == 4
        assert binary_search(lista, 6) == 5
        assert binary_search(lista, 7) == 6
        assert binary_search(lista, 8) == -1

    def test_busqueda_lineal(self):
        lista = [1, 2, 3, 4, 5, 6, 7]
        assert busqueda_lineal(lista, 1) == 0
        assert busqueda_lineal(lista, 2) == 1
        assert busqueda_lineal(lista, 3) == 2
        assert busqueda_lineal(lista, 4) == 3
        assert busqueda_lineal(lista, 5) == 4
        assert busqueda_lineal(lista, 6) == 5
        assert busqueda_lineal(lista, 7) == 6
        assert busqueda_lineal(lista, 8) == -1

    def test_encontrar_maximo(self):
        lista = [1, 2, 3, 4, 5]
        assert encontrar_maximo(lista) == 5
        lista = [-1, 0, 2, 3, -4]
        assert encontrar_maximo(lista) == 2

    def test_encontrar_minimo(self):
        lista = [1, 2, 3, 4, 5]
        assert encontrar_minimo(lista) == 1
        lista = [-1, 0, 2, 3, -4]
        assert encontrar_minimo(lista) == -4