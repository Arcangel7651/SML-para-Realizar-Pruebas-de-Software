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

    # Given: edad 13, expect False
    def test_es_mayor_de_edad_13_no_es(self):
        # When
        resultado = self.es_mayor_de_edad(13)
        # Then
        assert not resultado, "Edad 13 no debería ser mayor de edad"

    # Given: edad 18, expect False
    def test_es_mayor_de_edad_18_no_es(self):
        # When
        resultado = self.es_mayor_de_edad(18)
        # Then
        assert not resultado, "Edad 18 no debería ser mayor de edad"

    # Given: edad 20, expect True
    def test_es_mayor_de_edad_20_si_es(self):
        # When
        resultado = self.es_mayor_de_edad(20)
        # Then
        assert resultado, "Edad 20 debería ser mayor de edad"

    # Given: edad 64, expect True
    def test_es_mayor_de_edad_64_si_es(self):
        # When
        resultado = self.es_mayor_de_edad(64)
        # Then
        assert resultado, "Edad 64 debería ser mayor de edad"