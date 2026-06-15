import pytest
from validador_edad import clasificar_edad, es_mayor_de_edad


class TestValidadorEdad(object):

    def test_clasificar_edad_niño(self):
        # Given
        edad = 12

        # When
        categoria = clasificar_edad(edad)

        # Then
        assert categoria == "niño"

    def test_clasificar_edad_adolescente(self):
        # Given
        edad = 15

        # When
        categoria = clasificar_edad(edad)

        # Then
        assert categoria == "adolescente"

    def test_clasificar_edad_adulto_mayor(self):
        # Given
        edad = 64

        # When
        categoria = clasificar_edad(edad)

        # Then
        assert categoria == "adulto mayor"

    def test_clasificar_edad_desconocido(self):
        # Given
        edad = 70

        # When
        categoria = clasificar_edad(edad)

        # Then
        assert categoria == "desconocido"

    def test_es_mayor_de_edad_adulto(self):
        # Given
        edad = 20

        # When
        resultado = es_mayor_de_edad(edad)

        # Then
        assert resultado is True

    def test_es_mayor_de_edad_infantil(self):
        # Given
        edad = 5

        # When
        resultado = es_mayor_de_edad(edad)

        # Then
        assert resultado is False

    def test_es_mayor_de_edad_adulto_mayor(self):
        # Given
        edad = 65

        # When
        resultado = es_mayor_de_edad(edad)

        # Then
        assert resultado is True