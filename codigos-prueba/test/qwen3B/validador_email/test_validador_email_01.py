import pytest
from validador_email import extraer_dominio

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