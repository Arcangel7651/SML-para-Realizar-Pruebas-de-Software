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

    @pytest.mark.parametrize("fahrenheit, celsius", [
        (32, 0),
        (-40, -40),
        (212, 100)
    ])
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

    @pytest.mark.parametrize("celsius, kelvin", [
        (0, 273.15),
        (-40, -40 + 273.15),
        (100, 100 + 273.15)
    ])
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

    @pytest.mark.parametrize("kelvin, celsius", [
        (0, -273.15),
        (-40 + 273.15, -40),
        (100 + 273.15, 100)
    ])
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

    def test_fahrenheit_a_celsius_raises_value_error_below_zero(self):
        """GIVEN una temperatura en Fahrenheit que no puede convertirse a Celsius,
           WHEN se intenta convertir a Celsius,
           THEN se lanza un ValueError con el mensaje 'La temperatura no puede ser menor al cero absoluto'."""
        # Given
        fahrenheit = -41
        
        # When / Then
        with pytest.raises(ValueError, match=r"La temperatura no puede ser menor al cero absoluto"):
            fahrenheit_a_celsius(fahrenheit)

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