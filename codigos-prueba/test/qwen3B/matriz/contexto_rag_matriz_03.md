# Contexto RAG — matriz

- Generado: 2026-06-15T05:33:56.861Z
- Total de fragmentos: 4

## Fragmento 1 — Advertencia del módulo

```text
ADVERTENCIA para el módulo 'matriz': en una generación previa, estos tests fallaron al ejecutarse porque su aserción no se cumplió:
  - test_sumar_matrices_diferentes_dimensiones_lanza_error: Failed: DID NOT RAISE <class 'ValueError'>
  - test_sumar_matrices_nula_y_no_vacia_lanza_error: Failed: DID NOT RAISE <class 'ValueError'>
Revisa el comportamiento REAL de cada función (su código y su docstring) antes de fijar el valor esperado en el assert. No copies a ciegas el valor que la función devolvió solo para que el test pase: si ese valor no es el correcto según el contrato de la función, el test sería tautológico y ocultaría un bug.
```

## Fragmento 2 — Ejemplo aprendido del módulo

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

## Fragmento 3 — Ejemplo aprendido del módulo

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

## Fragmento 4 — Patrón recuperado por similitud

```text
[meta score=100.12 kept=12] Ejemplo verificado de tests pytest para el módulo 'calculadora' (funciones: sumar, restar, multiplicar, dividir, potencia, es_par). 12 test(s) verificados que pasan, 100.0% de cobertura de línea. Código de prueba:
import pytest
from calculadora import Calculadora


class TestCalculadora(object):

    def setup_method(self):
        self.calc = Calculadora()

    def teardown_method(self):
        # No es necesario hacer nada para esta prueba simple, pero se puede incluir si se requiere limpiar algún estado o realizar otras operaciones
        pass

    # Patron RAG: aserciones de valores concretos y resultados numericos

    def test_sumar_dos_positivos_retorna_producto_correcto(self):
        # Given
        a, b = 4, 5
        # When
        resultado = self.calc.sumar(a, b)
        # Then
        assert resultado == 9

    def test_restar_resultado_negativo(self):
        # Given
        a, b = 3, 10
        # When
        resultado = self.calc.restar(a, b)
        # Then
        assert resultado == -7

    def test_multiplicar_dos_positivos_retorna_producto_correcto(self):
        # Given
        a, b = 4, 5
        # When
        resultado = self.calc.multiplicar(a, b)
        # Then
        assert resultado == 20

    def test_dividir_resultado_flotante_approx(self):
        # Given
        a, b = 1, 3
        # When
        resultado = self.calc.dividir(a, b)
        # Then
        assert resultado == pytest.approx(0.3333, rel=1e-3)

    def test_potencia_con_exponente_negativo(self):
        # Given
        base, exponente = 2, -1
        # When
        resultado = self.calc.potencia(base, exponente)
        # Then
        assert resultado == pytest.approx(0.5)

    def test_es_par_numero_paro_retorna_true(self):
        # Given
        numero = 4
        # When
        es_par = self.calc.es_par(numero)
        # Then
        assert es_par is True

    def test_es_par_numero_impar_retorna_false(self):
        # Given
        numero = 5
        # When
        es_par = self.calc.es_par(numero)
        # Then
        assert es_par is False

    def test_sumar_cero_con_positivo(self):
        # Given
        a, b = 0, 5
        # When
        resultado = self.calc.sumar(a, b)
        # Then
        assert resultado == 5

    def test_restar_menos_cero_de_negativo(self):
        # Given
        a, b = -3, 0
        # When
        resultado = self.calc.restar(a, b)
        # Then
        assert resultado == -3

    def test_multiplicar_con_cero(self):
        # Given
        a, b = 0, 5
        # When
        resultado = self.calc.multiplicar(a, b)
        # Then
        assert resultado == 0

    def test_es_par_numero_menor_que_cero(self):
        # Given
        numero = -5
        # When
        es_par = self.calc.es_par(numero)
        # Then
        assert es_par is False

    def test_dividir_retiro_de_zero_raises_exception(self):
        with pytest.raises(ValueError, match="No se puede dividir entre cero"):
            self.calc.dividir(1, 0)
```
