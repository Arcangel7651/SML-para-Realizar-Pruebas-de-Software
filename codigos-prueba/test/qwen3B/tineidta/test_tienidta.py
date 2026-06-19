import pytest
from tienidta import Tienda

class TestTienda(object):
    def setUp(self):
        self.tienda = Tienda()

    def test_aplicar_descuento_precio_negativo_lanza_error(self):
        with pytest.raises(ValueError):
            self.tienda.aplicar_descuento(-10, 20)

    def test_aplicar_descuento_porcentaje_negativo_lanza_error(self):
        with pytest.raises(ValueError):
            self.tienda.aplicar_descuento(100, -5)

    def test_aplicar_descuento_porcentaje_mayor_a_cien_lanza_error(self):
        with pytest.raises(ValueError):
            self.tienda.aplicar_descuento(100, 105)

    def test_aplicar_descuento_precio_positivo_y_porcentaje_correcto_calcula_correctamente(self):
        resultado = self.tienda.aplicar_descuento(100, 20)
        assert resultado == 80, "El descuento no se calcula correctamente"

    def test_aplicar_iva_sin_iva_dado_precio_positivo_calcula_correctamente(self):
        resultado = self.tienda.aplicar_iva(100)
        assert resultado == 116.0, "El IVA no se calcula correctamente"

    def test_aplicar_iva_con_iva_dado_precio_positivo_y_iva_correcto_calcula_correctamente(self):
        resultado = self.tienda.aplicar_iva(100, 20)
        assert resultado == 120.0, "El IVA no se calcula correctamente"

    def test_aplicar_descuento_con_precio_negativo_y_porcentaje_positivo_lanza_error(self):
        with pytest.raises(ValueError):
            self.tienda.aplicar_descuento(-10, 20)

    def test_aplicar_iva_con_precio_negativo_lanza_error(self):
        with pytest.raises(ValueError):
            self.tienda.aplicar_iva(-10)

    def test_calcula_total_sin_precios_en_lista_lanza_error(self):
        with pytest.raises(ValueError):
            self.tienda.calcular_total([])

    def test_calcula_total_con_precios_negativos_y_positivos_lanza_error(self):
        with pytest.raises(ValueError):
            self.tienda.calcular_total([10, -20, 30])

    def test_calcula_total_sin_precios_en_lista_devuelve_cero_correctamente(self):
        resultado = self.tienda.calcular_total([])
        assert resultado == 0, "El total no se calcula correctamente"

    def test_calcula_total_con_precios_positivos_y_negativos_calcule_correctamente(self):
        resultado = self.tienda.calcular_total([10, -20, 30])
        assert resultado == 20, "El total no se calcula correctamente"

    def test_es_envio_gratis_con_compra_menor_a_500_devuelve_falso_correctamente(self):
        assert not self.tienda.es_envio_gratis(499), "El envío no está gratuito"

    def test_es_envio_gratis_con_compra_mayor_o_igual_a_500_devuelve_verdadero_correctamente(self):
        assert self.tienda.es_envio_gratis(500), "El envío no está gratuito"

    def test_dividir_pago_con_personas_cero_lanza_error(self):
        with pytest.raises(ValueError):
            self.tienda.dividir_pago(100, 0)

    def test_dividir_pago_con_personas_negativo_lanza_error(self):
        with pytest.raises(ValueError):
            self.tienda.dividir_pago(100, -5)

    def test_dividir_pago_con_personas_positivo_y_total_positivo_devuelve_correctamente(self):
        resultado = self.tienda.dividir_pago(100, 2)
        assert resultado == 50, "La división del pago no se realiza correctamente"

    def test_clasificar_cliente_con_compras_negativas_lanza_error(self):
        with pytest.raises(ValueError):
            self.tienda.clasificar_cliente(-10)

    def test_clasificar_nuevo_cliente_con_compras_cero_devuelve_nuevo_correctamente(self):
        assert self.tienda.clasificar_cliente(0) == "nuevo", "El clasificado no es correcto"

    def test_clasificar_frecuente_cliente_con_compras_menores_a_10_devuelve_frecuente_correctamente(self):
        assert self.tienda.clasificar_cliente(5) == "frecuente", "El clasificado no es correcto"

    def test_clasificar_premium_cliente_con_compras_mayor_o_igual_a_10_devuelve_premium_correctamente(self):
        assert self.tienda.clasificar_cliente(20) == "premium", "El clasificado no es correcto"