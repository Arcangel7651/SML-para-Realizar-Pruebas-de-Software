import pytest
from calculadora import Calculadora

class TestCalculadora(object):

    def setup_method(self):
        self.calc = Calculadora()

    def teardown_method(self):
        # No es necesario hacer nada para esta prueba simple, pero se puede incluir si se requiere limpiar algún estado o realizar otras operaciones
        pass

    # Patron RAG: aserciones de valores concretos y resultados numericos

    @pytest.mark.parametrize("a, b, expected", [
        (4, 5, 9),
        (3, 10, -7),
        (2, 5, 20),
        pytest.param(1, 3, 0.3333, marks=pytest.mark.xfail(reason="flotante no exato")),
        pytest.param(4, -1, 0.5, marks=pytest.mark.xfail(reason="flotante no exato")),
    ])
    def test_sumar(self, a, b, expected):
        # Given
        # When
        resultado = self.calc.sumar(a, b)
        # Then
        assert resultado == expected

    @pytest.mark.parametrize("a, b", [
        (3, 10),
        (-3, 0),
    ])
    def test_restar(self, a, b):
        # Given
        # When
        resultado = self.calc.restar(a, b)
        # Then
        assert resultado == -7

    @pytest.mark.parametrize("a, b", [
        (4, 5),
        pytest.param(2, 5, marks=pytest.mark.xfail(reason="flotante no exato")),
    ])
    def test_multiplicar(self, a, b):
        # Given
        # When
        resultado = self.calc.multiplicar(a, b)
        # Then
        assert resultado == 20

    @pytest.mark.parametrize("a, b", [
        pytest.param(1, 3, 0.3333, marks=pytest.mark.xfail(reason="flotante no exato")),
        pytest.param(4, -1, 0.5, marks=pytest.mark.xfail(reason="flotante no exato")),
    ])
    def test_dividir(self, a, b):
        # Given
        # When
        with pytest.raises(ValueError, match="No se puede dividir entre cero"):
            self.calc.dividir(a, b)

    @pytest.mark.parametrize("base, exponente", [
        (2, 5),
        pytest.param(4, -1, marks=pytest.mark.xfail(reason="flotante no exato")),
    ])
    def test_potencia(self, base, exponente):
        # Given
        # When
        resultado = self.calc.potencia(base, exponente)
        # Then
        assert resultado == base ** exponente

    @pytest.mark.parametrize("numero", [
        4,
        -5,
    ])
    def test_es_par(self, numero):
        # Given
        # When
        es_par = self.calc.es_par(numero)
        # Then
        assert es_par is True