# Contexto RAG — validador_edad

- Generado: 2026-06-15T02:00:49.600Z
- Total de fragmentos: 4

## Fragmento 1 — Advertencia del módulo

```text
ADVERTENCIA para el módulo 'validador_edad': en una generación previa, estos tests fallaron al ejecutarse porque su aserción no se cumplió:
  - test_clasificar_20_es_adulto: assert resultado == "adulto", "Clasificación de 20 años debe ser 'adulto'" → AssertionError: Clasificación de 20 años debe ser 'adulto' | assert 'adulto mayor' == 'adulto'
  - test_es_mayor_de_edad_65_no_es: assert not resultado, "Edad 65 no debería ser mayor de edad" → AssertionError: Edad 65 no debería ser mayor de edad | assert not True
Revisa el comportamiento REAL de cada función (su código y su docstring) antes de fijar el valor esperado en el assert. No copies a ciegas el valor que la función devolvió solo para que el test pase: si ese valor no es el correcto según el contrato de la función, el test sería tautológico y ocultaría un bug.
```

## Fragmento 2 — Ejemplo aprendido del módulo

```text
[meta score=90.08 kept=8] Ejemplo verificado de tests pytest para el módulo 'validador_edad' (subconjunto de tests que pasaron) (funciones: clasificar_edad, es_mayor_de_edad). 8 test(s) verificados que pasan, 90.0% de cobertura de línea. Código de prueba:
import pytest
from validador_edad import clasificar_edad, es_mayor_de_edad


class TestValidadorEdad(object):
    def setup_method(self):
        self.clasificar_edad = clasificar_edad
        self.es_mayor_de_edad = es_mayor_de_edad

    # Given: edad 12, expect 'niño'

    def test_clasificar_12_es_nino(self):
        # When
        resultado = self.clasificar_edad(12)
        # Then
        assert resultado == "niño", "Clasificación de 12 años debe ser 'niño'"

    def test_clasificar_14_es_adolescente(self):
        # When
        resultado = self.clasificar_edad(14)
        # Then
        assert resultado == "adolescente", "Clasificación de 14 años debe ser 'adolescente'"

    def test_clasificar_64_es_adulto_mayor(self):
        # When
        resultado = self.clasificar_edad(64)
        # Then
        assert resultado == "adulto mayor", "Clasificación de 64 años debe ser 'adulto mayor'"

    def test_clasificar_65_es_desconocido(self):
        # When
        resultado = self.clasificar_edad(65)
        # Then
        assert resultado == "desconocido", "Clasificación de 65 años debe ser 'desconocido'"

    def test_es_mayor_de_edad_13_no_es(self):
        # When
        resultado = self.es_mayor_de_edad(13)
        # Then
        assert not resultado, "Edad 13 no debería ser mayor de edad"

    def test_es_mayor_de_edad_18_no_es(self):
        # When
        resultado = self.es_mayor_de_edad(18)
        # Then
        assert not resultado, "Edad 18 no debería ser mayor de edad"

    def test_es_mayor_de_edad_20_si_es(self):
        # When
        resultado = self.es_mayor_de_edad(20)
        # Then
        assert resultado, "Edad 20 debería ser mayor de edad"

    def test_es_mayor_de_edad_64_si_es(self):
        # When
        resultado = self.es_mayor_de_edad(64)
        # Then
        assert resultado, "Edad 64 debería ser mayor de edad"
```

## Fragmento 3 — Patrón recuperado por similitud

```text
Patron pytest: casos limite, valores de frontera y entradas invalidas. Probar sistematicamente: cero, uno, negativos, cadena vacia, None, lista vacia, valor maximo. Un test por caso limite para aislar fallos y mantener claridad en el nombre. Ejemplo completo: def test_promedio_lista_vacia_retorna_cero(self):     # Given     datos = []     # When     resultado = promedio(datos)     # Then     assert resultado == 0. def test_factorial_de_cero_retorna_uno(self):     assert factorial(0) == 1. def test_buscar_en_lista_vacia_retorna_None(self):     assert buscar([], 'x') is None. def test_potencia_con_exponente_negativo(self):     assert potencia(2, -1) == pytest.approx(0.5). def test_funcion_acepta_None_sin_lanzar_excepcion(self):     resultado = procesar(None)     assert resultado is not None. Cubrir la frontera inferior y superior del dominio de cada parametro.
```

## Fragmento 4 — Patrón recuperado por similitud

```text
Patron SMS-UTGen: estructura Given-When-Then obligatoria en cada metodo de test. Cada test contiene exactamente tres secciones: # Given (precondiciones), # When (accion bajo prueba), # Then (verificacion del resultado). El nombre del metodo describe el escenario completo en espanol: test_cuando_<condicion>_entonces_<resultado_esperado>. Ejemplo con excepcion: def test_cuando_saldo_insuficiente_entonces_lanza_error(self):     # Given     cuenta = Cuenta(titular='Luis', saldo=0.0)     monto = 100.0     # When / Then     with pytest.raises(SaldoInsuficienteError, match='fondos insuficientes'):         cuenta.retirar(monto). Ejemplo sin excepcion: def test_cuando_deposito_valido_entonces_saldo_aumenta(self):     # Given     cuenta = Cuenta(titular='Maria', saldo=200.0)     # When     cuenta.depositar(50.0)     # Then     assert cuenta.saldo == 250.0. UTGen demostro reduccion del 20 porciento en tiempo de correccion de bugs gracias a nombres descriptivos que identifican el fallo sin leer el cuerpo.
```
