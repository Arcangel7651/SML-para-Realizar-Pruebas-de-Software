import pytest
from validador_edad import clasificar_edad, es_mayor_de_edad

class TestValidadorEdad(object):

    def test_clasificar_edad_edad_menor_que_13(self):
        # Given
        edad = 5
        
        # When
        resultado = clasificar_edad(edad)
        
        # Then
        assert resultado == "niño"

    def test_clasificar_edad_edad_entre_13_y_18_incluyendo_13(self):
        # Given
        edad = 13
        
        # When
        resultado = clasificar_edad(edad)
        
        # Then
        assert resultado == "niño"

    def test_clasificar_edad_edad_entre_13_y_18_incluyendo_18(self):
        # Given
        edad = 18
        
        # When
        resultado = clasificar_edad(edad)
        
        # Then
        assert resultado == "adolescente"

    def test_clasificar_edad_edad_entre_19_y_65_incluyendo_19(self):
        # Given
        edad = 19
        
        # When
        resultado = clasificar_edad(edad)
        
        # Then
        assert resultado == "adolescente"

    def test_clasificar_edad_edad_entre_19_y_65_incluyendo_65(self):
        # Given
        edad = 65
        
        # When
        resultado = clasificar_edad(edad)
        
        # Then
        assert resultado == "adulto mayor"

    def test_clasificar_edad_edad_mayor_que_65(self):
        # Given
        edad = 70
        
        # When
        resultado = clasificar_edad(edad)
        
        # Then
        assert resultado == "desconocido"

    def test_es_mayor_de_edad_edad_menor_que_19(self):
        # Given
        edad = 18
        
        # When
        resultado = es_mayor_de_edad(edad)
        
        # Then
        assert resultado is False

    def test_es_mayor_de_edad_edad_entre_19_y_65_incluyendo_19(self):
        # Given
        edad = 20
        
        # When
        resultado = es_mayor_de_edad(edad)
        
        # Then
        assert resultado is True

    def test_es_mayor_de_edad_edad_entre_65_y_100_incluyendo_65(self):
        # Given
        edad = 65
        
        # When
        resultado = es_mayor_de_edad(edad)
        
        # Then
        assert resultado is True

    def test_es_mayor_de_edad_edad_mayor_que_100(self):
        # Given
        edad = 101
        
        # When
        resultado = es_mayor_de_edad(edad)
        
        # Then
        assert resultado is False