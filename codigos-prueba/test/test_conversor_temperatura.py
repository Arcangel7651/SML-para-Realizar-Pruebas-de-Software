import pytest
from conversor_temperatura import celsius_a_fahrenheit, fahrenheit_a_celsius, celsius_a_kelvin, kelvin_a_celsius

class TestConversorTemperatura:
    def test_celsius_a_fahrenheit(self):
        # Given
        celsius = 0
        fahrenheit_esperado = 32
        
        # When
        fahrenheit_obtenido = celsius_a_fahrenheit(celsius)
        
        # Then
        assert fahrenheit_obtenido == fahrenheit_esperado
    
    def test_fahrenheit_a_celsius(self):
        # Given
        fahrenheit = 32
        celsius_esperado = 0
        
        # When
        celsius_obtenido = fahrenheit_a_celsius(fahrenheit)
        
        # Then
        assert celsius_obtenido == celsius_esperado
    
    def test_celsius_a_kelvin(self):
        # Given
        celsius = 0
        kelvin_esperado = 273.15
        
        # When
        kelvin_obtenido = celsius_a_kelvin(celsius)
        
        # Then
        assert kelvin_obtenido == kelvin_esperado
    
    def test_kelvin_a_celsius(self):
        # Given
        kelvin = 273.15
        celsius_esperado = 0
        
        # When
        celsius_obtenido = kelvin_a_celsius(kelvin)
        
        # Then
        assert celsius_obtenido == celsius_esperado
    
    def test_conversiones_fahrenheit(self):
        # Given
        fahrenheit_orig = 50
        
        # When
        fahrenheit_convertido = celsius_a_fahrenheit(fahrenheit_orig)
        
        # Then
        assert fahrenheit_convertido == fahrenheit_orig
    
    def test_conversiones_celsius(self):
        # Given
        celsius_orig = 50
        
        # When
        celsius_convertido = fahrenheit_a_celsius(celsius_orig)
        
        # Then
        assert celsius_convertido == celsius_orig
    
    def test_conversiones_kelvin(self):
        # Given
        kelvin_orig = 50
        
        # When
        kelvin_convertido = celsius_a_kelvin(kelvin_orig)
        
        # Then
        assert kelvin_convertido == kelvin_orig
    
    def test_conversiones_celsius_raises(self):
        # Given
        celsius = -100
        
        # When/Then
        with pytest.raises(ValueError, match='La temperatura no puede ser menor al cero absoluto'):
            celsius_a_kelvin(celsius)