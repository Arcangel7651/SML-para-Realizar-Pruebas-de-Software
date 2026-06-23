# Contexto RAG — calculadora

- Generado: 2026-06-19T16:00:09.875Z
- Total de fragmentos: 5

## Fragmento 1 — Advertencia del módulo

```text
ADVERTENCIA para el módulo 'calculadora': en una generación previa, los tests generados tuvieron estos test smells: generic_name. Al generar tests para este módulo, recuerda que los nombres de test deben seguir test_<función>_<escenario_descriptivo>, nunca test_<función> a secas sin describir el escenario (OR-4).
```

## Fragmento 2 — Advertencia del módulo

```text
ADVERTENCIA para el módulo 'calculadora': en una generación previa, estos tests fallaron al ejecutarse porque su aserción no se cumplió:
  - test_factorial_de_cero_retorna_uno: assert factorial(0) == 1 → NameError: name 'factorial' is not defined
  - test_buscar_en_lista_vacia_retorna_None: assert buscar([], 'x') is None → NameError: name 'buscar' is not defined
Revisa el comportamiento REAL de cada función (su código y su docstring) antes de fijar el valor esperado en el assert. No copies a ciegas el valor que la función devolvió solo para que el test pase: si ese valor no es el correcto según el contrato de la función, el test sería tautológico y ocultaría un bug.
```

## Fragmento 3 — Ejemplo aprendido del módulo

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

## Fragmento 4 — Patrón recuperado por similitud

```text
Patron pytest: aserciones de valores concretos y resultados numericos. Comparar el valor de retorno exacto con el esperado usando assert resultado == esperado. Para flotantes usar pytest.approx: assert suma(0.1, 0.2) == pytest.approx(0.3). Verificar que la funcion retorna el valor correcto para entradas positivas, negativas y cero. IMPORTANTE: este es un patron generico de ejemplo. Los nombres de funcion (multiplicar, restar, dividir, etc.) son ilustrativos: nunca los copies literalmente, usa siempre las funciones y metodos reales del modulo bajo prueba. Ejemplo completo: def test_multiplicar_dos_positivos_retorna_producto_correcto(self):     # Given     a, b = 4, 5     # When     resultado = multiplicar(a, b)     # Then     assert resultado == 20. def test_restar_resultado_negativo(self):     assert restar(3, 10) == -7. def test_dividir_retorna_flotante_approx(self):     assert dividir(1, 3) == pytest.approx(0.3333, rel=1e-3). No mezclar verificacion de tipos en este patron: enfocarse solo en el valor de retorno.
```

## Fragmento 5 — Patrón recuperado por similitud

```text
Patron pytest: fixtures para datos de prueba reutilizables entre multiples tests. Definir con @pytest.fixture fuera de la clase e inyectar como parametro en el metodo. Scope function recrea la fixture en cada test; module y session la comparten. Usar yield en lugar de return para fixtures que necesitan limpieza posterior. Ejemplo completo: @pytest.fixture def usuario_con_saldo():     u = Usuario(nombre='Ana', saldo=500.0)     yield u     u.saldo = 0  # limpieza. @pytest.fixture(scope='module') def conexion_bd():     conn = BaseDatos(':memory:')     conn.inicializar_esquema()     yield conn     conn.cerrar(). class TestCartera:     def test_depositar_aumenta_saldo(self, usuario_con_saldo):         # Given         saldo_previo = usuario_con_saldo.saldo         # When         usuario_con_saldo.depositar(100)         # Then         assert usuario_con_saldo.saldo == saldo_previo + 100. Preferir fixtures sobre setup_method cuando el dato se reutiliza en varias clases.
```
