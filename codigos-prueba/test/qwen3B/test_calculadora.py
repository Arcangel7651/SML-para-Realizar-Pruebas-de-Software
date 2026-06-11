import pytest
from calculadora import Calculadora

class TestCalculadora(object):

    def test_sumar_dos_positivos_retorna_producto_correcto(self):
        # Given
        a, b = 4, 5
        # When
        resultado = Calculadora().sumar(a, b)
        # Then
        assert resultado == 9

    def test_restar_resultado_negativo(self):
        # Given
        a, b = 10, 3
        # When
        resultado = Calculadora().restar(a, b)
        # Then
        assert resultado == -7

    def test_multiplicar_dos_positivos_retorna_producto_correcto(self):
        # Given
        a, b = 4, 5
        # When
        resultado = Calculadora().multiplicar(a, b)
        # Then
        assert resultado == 20

    def test_dividir_resultado_correcto_en_flotantes(self):
        # Given
        a, b = 1.5, 0.5
        # When
        resultado = Calculadora().dividir(a, b)
        # Then
        assert pytest.approx(resultado, rel=1e-3) == 3.0

    def test_potencia_base_2_exponente_3_retorna_8(self):
        # Given
        base, exponente = 2, 3
        # When
        resultado = Calculadora().potencia(base, exponente)
        # Then
        assert resultado == 8

    def test_es_par_numero_impar_retorna_false(self):
        # Given
        numero = 7
        # When
        es_par = Calculadora().es_par(numero)
        # Then
        assert not es_par

    def test_dividir_entre_cero_lanza_ValueError(self):
        with pytest.raises(ValueError, match='No se puede dividir entre cero'):
            Calculadora().dividir(10, 0)