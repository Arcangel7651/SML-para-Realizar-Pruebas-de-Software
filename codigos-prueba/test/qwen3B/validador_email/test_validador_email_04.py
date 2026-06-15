import pytest
from validador_email import es_email_valido, extraer_dominio

class TestValidadorEmail(object):

    def test_es_email_valido_sin_dom(self):
        # Given
        correo = "usuario@"

        # When / Then
        with pytest.raises(ValueError, match='Correo electrónico inválido'):
            extraer_dominio(correo)

    def test_extraer_dominio_correo_no_valido(self):
        # Given
        correo = "usuario@dominio_comun"

        # When / Then
        with pytest.raises(ValueError, match='Correo electrónico inválido'):
            extraer_dominio(correo)

    def test_extraer_dominio_con_correo_vacio(self):
        # Given
        correo = ""

        # When / Then
        with pytest.raises(ValueError, match='Correo electrónico inválido'):
            extraer_dominio(correo)

    def test_es_email_valido_cadena_correcta(self):
        # Given
        correo = "usuario@dominio.com"

        # When / Then
        assert es_email_valido(correo) == True

    def test_es_email_valido_sin_punto_arroba(self):
        # Given
        correo = "usuariodominio.com"

        # When / Then
        assert es_email_valido(correo) == False

    def test_es_email_valido_con_dominio_numerico(self):
        # Given
        correo = "usuario@123.com"

        # When / Then
        assert es_email_valido(correo) == True