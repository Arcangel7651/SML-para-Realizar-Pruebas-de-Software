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
        assert resultado == 9, "El resultado de la suma no es el esperado"

    def test_restar_resultado_negativo(self):
        # Given
        a, b = 3, 10
        # When
        resultado = self.calc.restar(a, b)
        # Then
        assert resultado == -7, "El resultado de la resta no es el esperado"

    def test_multiplicar_dos_positivos_retorna_producto_correcto(self):
        # Given
        a, b = 4, 5
        # When
        resultado = self.calc.multiplicar(a, b)
        # Then
        assert resultado == 20, "El resultado de la multiplicación no es el esperado"

    def test_dividir_resultado_flotante_approx(self):
        # Given
        a, b = 1, 3
        # When
        resultado = self.calc.dividir(a, b)
        # Then
        assert resultado == pytest.approx(0.3333, rel=1e-3), "El resultado de la división no es el esperado"

    def test_potencia_con_exponente_negativo(self):
        # Given
        base, exponente = 2, -1
        # When
        resultado = self.calc.potencia(base, exponente)
        # Then
        assert resultado == pytest.approx(0.5), "El resultado de la potenciación no es el esperado"

    def test_es_par_numero_paro_retorna_true(self):
        # Given
        numero = 4
        # When
        es_par = self.calc.es_par(numero)
        # Then
        assert es_par is True, "La función 'es_par' no devuelve el resultado esperado para un número par"

    def test_es_par_numero_impar_retorna_false(self):
        # Given
        numero = 5
        # When
        es_par = self.calc.es_par(numero)
        # Then
        assert es_par is False, "La función 'es_par' no devuelve el resultado esperado para un número impar"

    def test_sumar_cero_con_positivo(self):
        # Given
        a, b = 0, 5
        # When
        resultado = self.calc.sumar(a, b)
        # Then
        assert resultado == 5, "El resultado de la suma con cero y un número positivo no es el esperado"

    def test_restar_menos_cero_de_negativo(self):
        # Given
        a, b = -3, 0
        # When
        resultado = self.calc.restar(a, b)
        # Then
        assert resultado == -3, "El resultado de la resta con cero y un número negativo no es el esperado"

    def test_multiplicar_con_cero(self):
        # Given
        a, b = 0, 5
        # When
        resultado = self.calc.multiplicar(a, b)
        # Then
        assert resultado == 0, "El resultado de la multiplicación con cero y un número no es el esperado"

    def test_es_par_numero_menor_que_cero(self):
        # Given
        numero = -5
        # When
        es_par = self.calc.es_par(numero)
        # Then
        assert es_par is False, "La función 'es_par' no devuelve el resultado esperado para un número menor que cero"

    def test_dividir_retiro_de_zero_raises_exception(self):
        with pytest.raises(ValueError) as excinfo:
            self.calc.dividir(1, 0)
        assert str(excinfo.value) == "No se puede dividir entre cero", "La función 'dividir' no lanza la excepción esperada cuando se divide por cero"

    def test_sumar_negativos_retorna_negativo_correcto(self):
        # Given
        a, b = -4, -5
        # When
        resultado = self.calc.sumar(a, b)
        # Then
        assert resultado == -9, "El resultado de la suma de dos números negativos no es el esperado"

    def test_restar_positivo_de_negativo_retorna_negativo_correcto(self):
        # Given
        a, b = 3, -10
        # When
        resultado = self.calc.restar(a, b)
        # Then
        assert resultado == -7, "El resultado de la resta de un número positivo y otro negativo no es el esperado"

    def test_multiplicar_negativos_retorna_positivo_correcto(self):
        # Given
        a, b = -4, 5
        # When
        resultado = self.calc.multiplicar(a, b)
        # Then
        assert resultado == -20, "El resultado de la multiplicación de dos números negativos no es el esperado"

    def test_dividir_negativo_por_positivo_retorna_flotante_approx(self):
        # Given
        a, b = -1, 3
        # When
        resultado = self.calc.dividir(a, b)
        # Then
        assert resultado == pytest.approx(-0.3333, rel=1e-3), "El resultado de la división negativa por positivo no es el esperado"

    def test_potencia_de_negativo_con_exponente_par_retorna_positivo(self):
        # Given
        base, exponente = -2, 2
        # When
        resultado = self.calc.potencia(base, exponente)
        # Then
        assert resultado == 4, "El resultado de la potenciación negativa con exponente par no es el esperado"

    def test_potencia_de_negativo_con_exponente_impar_retorna_negativo(self):
        # Given
        base, exponente = -2, -1
        # When
        resultado = self.calc.potencia(base, exponente)
        # Then
        assert resultado == -0.5, "El resultado de la potenciación negativa con exponente impar no es el esperado"