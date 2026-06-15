# Contexto RAG — matriz

- Generado: 2026-06-15T05:47:34.184Z
- Total de fragmentos: 4

## Fragmento 1 — Advertencia del módulo

```text
ADVERTENCIA para el módulo 'matriz': en una generación previa, estos tests fallaron al ejecutarse porque su aserción no se cumplió:
  - test_sumar_matrices_nula_y_no_vacia_lanza_error: Failed: DID NOT RAISE <class 'ValueError'>
Revisa el comportamiento REAL de cada función (su código y su docstring) antes de fijar el valor esperado en el assert. No copies a ciegas el valor que la función devolvió solo para que el test pase: si ese valor no es el correcto según el contrato de la función, el test sería tautológico y ocultaría un bug.
```

## Fragmento 2 — Ejemplo aprendido del módulo

```text
[meta score=89.06 kept=6] Ejemplo verificado de tests pytest para el módulo 'matriz' (subconjunto de tests que pasaron) (funciones: transponer, sumar_matrices, multiplicar_matrices). 6 test(s) verificados que pasan, 89.0% de cobertura de línea. Código de prueba:
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
```

## Fragmento 3 — Ejemplo aprendido del módulo

```text
[meta score=84.05 kept=5] Ejemplo verificado de tests pytest para el módulo 'matriz' (subconjunto de tests que pasaron) (funciones: transponer, sumar_matrices, multiplicar_matrices). 5 test(s) verificados que pasan, 84.0% de cobertura de línea. Código de prueba:
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
```

## Fragmento 4 — Ejemplo aprendido del módulo

```text
[meta score=78.04 kept=4] Ejemplo verificado de tests pytest para el módulo 'matriz' (subconjunto de tests que pasaron) (funciones: transponer, sumar_matrices, multiplicar_matrices). 4 test(s) verificados que pasan, 78.0% de cobertura de línea. Código de prueba:
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
```
