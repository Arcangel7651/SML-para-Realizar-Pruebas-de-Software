# Contexto RAG — conversor_temperatura

- Generado: 2026-06-16T07:54:40.811Z
- Total de fragmentos: 3

## Fragmento 1 — Ejemplo aprendido del módulo

```text
[meta score=62.07 kept=7] Ejemplo verificado de tests pytest para el módulo 'conversor_temperatura' (subconjunto de tests que pasaron) (funciones: celsius_a_fahrenheit, fahrenheit_a_celsius, celsius_a_kelvin, kelvin_a_celsius). 7 test(s) verificados que pasan, 62.0% de cobertura de línea. Código de prueba:
import pytest
from conversor_temperatura import celsius_a_fahrenheit, fahrenheit_a_celsius, celsius_a_kelvin, kelvin_a_celsius


class TestConversorTemperatura(object):

    @pytest.mark.parametrize("celsius, fahrenheit", [
        (0, 32),
        (-40, -40),
        (100, 212)
    ])

    def test_celsius_a_fahrenheit(self, celsius, fahrenheit):
        """GIVEN una temperatura en Celsius,
           WHEN se convierte a Fahrenheit,
           THEN el resultado es el esperado."""
        # Given
        expected_result = fahrenheit
        
        # When
        result = celsius_a_fahrenheit(celsius)
        
        # Then
        assert result == expected_result, f"El conversion de {celsius} °C a Fahrenheit debe ser {expected_result} °F"

    def test_fahrenheit_a_celsius(self, fahrenheit, celsius):
        """GIVEN una temperatura en Fahrenheit,
           WHEN se convierte a Celsius,
           THEN el resultado es el esperado."""
        # Given
        expected_result = celsius
        
        # When
        result = fahrenheit_a_celsius(fahrenheit)
        
        # Then
        assert result == expected_result, f"El conversion de {fahrenheit} °F a Celsius debe ser {expected_result} °C"

    def test_celsius_a_kelvin(self, celsius, kelvin):
        """GIVEN una temperatura en Celsius,
           WHEN se convierte a Kelvin,
           THEN el resultado es el esperado."""
        # Given
        expected_result = kelvin
        
        # When
        result = celsius_a_kelvin(celsius)
        
        # Then
        assert result == expected_result, f"El conversion de {celsius} °C a Kelvin debe ser {expected_result} K"

    def test_kelvin_a_celsius(self, kelvin, celsius):
        """GIVEN una temperatura en Kelvin,
           WHEN se convierte a Celsius,
           THEN el resultado es el esperado."""
        # Given
        expected_result = celsius
        
        # When
        result = kelvin_a_celsius(kelvin)
        
        # Then
        assert result == expected_result, f"El conversion de {kelvin} K a Celsius debe ser {expected_result} °C"

    def test_celsius_a_fahrenheit_raises_value_error_below_zero(self):
        """GIVEN una temperatura en Celsius que no puede convertirse a Fahrenheit,
           WHEN se intenta convertir a Fahrenheit,
           THEN se lanza un ValueError con el mensaje 'La temperatura no puede ser menor al cero absoluto'."""
        # Given
        celsius = -274
        
        # When / Then
        with pytest.raises(ValueError, match=r"La temperatura no puede ser menor al cero absoluto"):
            celsius_a_fahrenheit(celsius)

    def test_celsius_a_kelvin_raises_value_error_below_zero(self):
        """GIVEN una temperatura en Celsius que no puede convertirse a Kelvin,
           WHEN se intenta convertir a Kelvin,
           THEN se lanza un ValueError con el mensaje 'La temperatura no puede ser menor al cero absoluto'."""
        # Given
        celsius = -274
        
        # When / Then
        with pytest.raises(ValueError, match=r"La temperatura no puede ser menor al cero absoluto"):
            celsius_a_kelvin(celsius)

    def test_kelvin_a_celsius_raises_value_error_below_zero(self):
        """GIVEN una temperatura en Kelvin que no puede convertirse a Celsius,
           WHEN se intenta convertir a Celsius,
           THEN se lanza un ValueError con el mensaje 'La temperatura en Kelvin no puede ser negativa'."""
        # Given
        kelvin = -1
        
        # When / Then
        with pytest.raises(ValueError, match=r"La temperatura en Kelvin no puede ser negativa"):
            kelvin_a_celsius(kelvin)
```

## Fragmento 2 — Patrón recuperado por similitud

```text
Patron pytest: prueba de excepciones con pytest.raises. Usar pytest.raises(TipoError) como context manager para capturar excepciones esperadas. Verificar el mensaje del error con el parametro match usando expresion regular. Capturar el ExceptionInfo para inspeccionar atributos adicionales de la excepcion. IMPORTANTE: este es un patron generico de ejemplo. Las funciones, metodos y mensajes de excepcion (dividir, obtener_elemento, parsear_fecha, 'division por cero', 'formato invalido', etc.) son ilustrativos: solo escribe un test de excepcion si el modulo bajo prueba tiene una funcion o metodo real que efectivamente lance esa excepcion (revisa el codigo fuente proporcionado). Nunca inventes metodos que no existen en el modulo. Ejemplo completo: def test_dividir_entre_cero_lanza_ValueError(self):     # Given     numerador = 10     # When / Then     with pytest.raises(ValueError, match='division por cero'):         dividir(numerador, 0). def test_acceder_indice_invalido_lanza_IndexError(self):     lista = [1, 2, 3]     with pytest.raises(IndexError):         obtener_elemento(lista, 99). def test_excinfo_contiene_mensaje_descriptivo(self):     with pytest.raises(ValueError) as excinfo:         parsear_fecha('no-es-fecha')     assert 'formato invalido' in str(excinfo.value). Nunca usar try/except dentro de un test: pytest.raises es la forma correcta.
```

## Fragmento 3 — Patrón recuperado por similitud

```text
Patron pytest: casos limite, valores de frontera y entradas invalidas. Probar sistematicamente: cero, uno, negativos, cadena vacia, None, lista vacia, valor maximo. Un test por caso limite para aislar fallos y mantener claridad en el nombre. Ejemplo completo: def test_promedio_lista_vacia_retorna_cero(self):     # Given     datos = []     # When     resultado = promedio(datos)     # Then     assert resultado == 0. def test_factorial_de_cero_retorna_uno(self):     assert factorial(0) == 1. def test_buscar_en_lista_vacia_retorna_None(self):     assert buscar([], 'x') is None. def test_potencia_con_exponente_negativo(self):     assert potencia(2, -1) == pytest.approx(0.5). def test_funcion_acepta_None_sin_lanzar_excepcion(self):     resultado = procesar(None)     assert resultado is not None. Cubrir la frontera inferior y superior del dominio de cada parametro.
```
