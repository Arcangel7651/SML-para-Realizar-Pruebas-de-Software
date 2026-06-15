import pytest
from matriz import transponer, sumar_matrices, multiplicar_matrices


class TestMatriz(object):

    def setup_method(self):
        pass

    def teardown_method(self):
        # No es necesario hacer nada para esta prueba simple, pero se puede incluir si se requiere limpiar algún estado o realizar otras operaciones
        pass

    def test_transponer_matriz_no_vacia_retorna_matriz_transpuesta_correcta(self):
        # Given
        matriz = [[1, 2], [3, 4]]
        # When
        resultado = transponer(matriz)
        # Then
        assert resultado == [[1, 3], [2, 4]]

    def test_transponer_matriz_lado_unico_retorna_matriz_identidad(self):
        # Given
        matriz = [[1]]
        # When
        resultado = transponer(matriz)
        # Then
        assert resultado == [[1]]

    def test_sumar_matrices_mismas_dimensiones_elementos(self):
        # Given
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        # When
        resultado = sumar_matrices(a, b)
        # Then
        assert resultado == [[6, 8], [10, 12]]

    def test_multiplicar_matrices_compatibles_filas_columnas(self):
        # Given
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        # When
        resultado = multiplicar_matrices(a, b)
        # Then
        assert resultado == [[19, 22], [43, 50]]

    def test_transponer_matriz_vacia_retorna_matriz_vacia(self):
        # Given
        matriz = []
        # When
        resultado = transponer(matriz)
        # Then
        assert resultado == []

    def test_sumar_matrices_diferentes_dimensiones_lanza_error(self):
        # Given
        a = [[1, 2], [3, 4]]
        b = [[5, 6]]
        # When
        with pytest.raises(ValueError) as excinfo:
            sumar_matrices(a, b)
        # Then
        assert str(excinfo.value) == "Las matrices deben tener las mismas dimensiones"

    def test_multiplicar_matrices_incompatibles_dimensiones_lanza_error(self):
        # Given
        a = [[1, 2]]
        b = [[5, 6], [7, 8]]
        # When
        with pytest.raises(ValueError) as excinfo:
            multiplicar_matrices(a, b)
        # Then
        assert str(excinfo.value) == "Dimensiones incompatibles para la multiplicación"

    def test_sumar_matrices_lado_unico_retorna_matriz_identidad(self):
        # Given
        matriz = [[1]]
        # When
        resultado = sumar_matrices(matriz, matriz)
        # Then
        assert resultado == [[2]]

    def test_multiplicar_matrices_una_fila_y_una_columna_lanza_error(self):
        # Given
        a = [[1]]
        b = [[5]]
        # When
        with pytest.raises(ValueError) as excinfo:
            multiplicar_matrices(a, b)
        # Then
        assert str(excinfo.value) == "Dimensiones incompatibles para la multiplicación"