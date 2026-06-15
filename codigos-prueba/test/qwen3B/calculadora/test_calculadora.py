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

    # Patron RAG: casos limite, valores de frontera y entradas invalidas
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

    def test_dividir_cero_por_uno_lanza_excepcion(self):
        with pytest.raises(ValueError) as excinfo:
            self.calc.dividir(0, 1)

    def test_potencia_de_cero_con_negativo(self):
        # Given
        base = 0
        exponente = -1
        # When
        resultado = self.calc.potencia(base, exponente)
        # Then
        assert resultado == pytest.approx(float('inf'), rel=1e-3)

    def test_es_par_numero_menor_que_cero(self):
        # Given
        numero = -5
        # When
        es_par = self.calc.es_par(numero)
        # Then
        assert es_par is False

    def test_es_par_numero_mayor_que_cero(self):
        # Given
        numero = 5
        # When
        es_par = self.calc.es_par(numero)
        # Then
        assert es_par is True

    # Agonetest: una sola clase de test cubre la clase bajo prueba completa
    def test_agregar_producto_y_verificar_total_refleja_precio(self):
        # Given
        producto = Producto(nombre='lapiz', precio=5.0)
        # When
        self.calc.agregar(producto)
        # Then
        assert self.calc.total() == 5.0

    def test_agregar_varios_productos_acumula_total_correctamente(self):
        # Given
        self.calc.agregar(Producto('lapiz', 5.0))
        self.calc.agregar(Producto('cuaderno', 15.0))
        # When
        total = self.calc.total()
        # Then
        assert total == 20.0

    def test_vaciar_carrito_despues_de_agregar_deja_total_en_cero(self):
        self.calc.agregar(Producto('x', 10.0))
        self.calc.vaciar()
        assert self.calc.total() == 0.0