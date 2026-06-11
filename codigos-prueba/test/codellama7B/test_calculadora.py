import pytest
from calculadora import Calculadora

class TestCalculadora(object):
    def test_sumar_dos_numeros(self):
        # Given
        a, b = 4, 5
        # When
        resultado = Calculadora().sumar(a, b)
        # Then
        assert resultado == 9

    def test_restar_resultado_negativo(self):
        # Given
        numerador, denominador = 3, 10
        # When / Then
        with pytest.raises(ValueError, match="No se puede dividir entre cero"):
            Calculadora().dividir(numerador, denominador)

    def test_multiplicar_dos_positivos_retorna_producto_correcto(self):
        # Given
        a, b = 4, 5
        # When
        resultado = Calculadora().multiplicar(a, b)
        # Then
        assert resultado == 20

    def test_dividir_retorna_flotante_approx(self):
        # Given
        numerador, denominador = 1, 3
        # When
        resultado = Calculadora().dividir(numerador, denominador)
        # Then
        assert resultado == pytest.approx(0.333, rel=1e-3)

    def test_acceder_indice_invalido_lanza_IndexError(self):
        lista = [1, 2, 3]
        with pytest.raises(IndexError):
            Calculadora().obtener_elemento(lista, 99)

    def test_excinfo_contiene_mensaje_descriptivo(self):
        with pytest.raises(ValueError) as excinfo:
            Calculadora().parsear_fecha('no-es-fecha')
        assert 'formato invalido' in str(excinfo.value)

    def test_dividir_entre_cero_lanza_ValueError(self):
        numerador, denominador = 10, 0
        with pytest.raises(ValueError):
            Calculadora().dividir(numerador, denominador)