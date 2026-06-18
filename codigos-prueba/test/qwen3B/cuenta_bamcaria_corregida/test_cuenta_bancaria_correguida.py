import pytest
from cuenta_bancaria_correguida import CuentaBancaria

class TestCuentaBancariaCorreguida(object):

    def test_depositar_cero_retorna_saldo_inicial(self, CuentaBancaria):
        # Given
        cuenta = CuentaBancaria(titular='Ana')
        
        # When
        saldo_previo = cuenta.saldo
        resultado = cuenta.depositar(0)
        
        # Then
        assert resultado == saldo_previo

    def test_depositar_uno_retorna_saldo_incrementado(self, CuentaBancaria):
        # Given
        cuenta = CuentaBancaria(titular='Ana')
        
        # When
        saldo_previo = cuenta.saldo
        resultado = cuenta.depositar(1)
        
        # Then
        assert resultado == saldo_previo + 1

    def test_depositar_negativo_no_aumenta_saldo(self, CuentaBancaria):
        # Given
        cuenta = CuentaBancaria(titular='Ana')
        
        # When
        saldo_previo = cuenta.saldo
        resultado = cuenta.depositar(-5)
        
        # Then
        assert resultado == saldo_previo

    def test_depositar_monto_maximo_retorna_saldo_incrementado(self, CuentaBancaria):
        # Given
        cuenta = CuentaBancaria(titular='Ana')
        max_saldo = 1000.0
        
        # When
        saldo_previo = cuenta.saldo
        resultado = cuenta.depositar(max_saldo)
        
        # Then
        assert resultado == max_saldo

    def test_retirar_cero_no_modifica_saldo(self, CuentaBancaria):
        # Given
        cuenta = CuentaBancaria(titular='Ana')
        
        # When
        saldo_previo = cuenta.saldo
        resultado = cuenta.retirar(0)
        
        # Then
        assert resultado == saldo_previo

    def test_retirar_uno_reduccion_saldo(self, CuentaBancaria):
        # Given
        cuenta = CuentaBancaria(titular='Ana', saldo_inicial=10)
        
        # When
        saldo_previo = cuenta.saldo
        resultado = cuenta.retirar(1)
        
        # Then
        assert resultado == saldo_previo - 1

    def test_retirar_negativo_no_modifica_saldo(self, CuentaBancaria):
        # Given
        cuenta = CuentaBancaria(titular='Ana')
        
        # When
        saldo_previo = cuenta.saldo
        resultado = cuenta.retirar(-5)
        
        # Then
        assert resultado == saldo_previo

    def test_retirar_monto_superior_a_saldo_no_modifica_saldo(self, CuentaBancaria):
        # Given
        cuenta = CuentaBancaria(titular='Ana', saldo_inicial=10)
        
        # When
        saldo_previo = cuenta.saldo
        resultado = cuenta.retirar(20)
        
        # Then
        assert resultado == saldo_previo

    def test_transferir_cero_no_modifica_saldos(self, CuentaBancaria):
        # Given
        cuenta_origen = CuentaBancaria(titular='Ana')
        cuenta_destino = CuentaBancaria(titular='Juan')
        
        # When
        resultado = cuenta_origen.transferir(cuenta_destino, 0)
        
        # Then
        assert resultado is False
        assert cuenta_origen.saldo == 0
        assert cuenta_destino.saldo == 0

    def test_transferir_uno_aumenta_saldos(self, CuentaBancaria):
        # Given
        cuenta_origen = CuentaBancaria(titular='Ana', saldo_inicial=10)
        cuenta_destino = CuentaBancaria(titular='Juan')
        
        # When
        resultado = cuenta_origen.transferir(cuenta_destino, 1)
        
        # Then
        assert resultado is True
        assert cuenta_origen.saldo == 9
        assert cuenta_destino.saldo == 1

    def test_transferir_negativo_no_modifica_saldos(self, CuentaBancaria):
        # Given
        cuenta_origen = CuentaBancaria(titular='Ana')
        cuenta_destino = CuentaBancaria(titular='Juan')
        
        # When
        resultado = cuenta_origen.transferir(cuenta_destino, -5)
        
        # Then
        assert resultado is False
        assert cuenta_origen.saldo == 0
        assert cuenta_destino.saldo == 0

    def test_transferir_monto_superior_a_saldo_no_modifica_saldos(self, CuentaBancaria):
        # Given
        cuenta_origen = CuentaBancaria(titular='Ana', saldo_inicial=10)
        cuenta_destino = CuentaBancaria(titular='Juan')
        
        # When
        resultado = cuenta_origen.transferir(cuenta_destino, 20)
        
        # Then
        assert resultado is False
        assert cuenta_origen.saldo == 10
        assert cuenta_destino.saldo == 0

    def test_transferir_monto_superior_a_saldo_de_la_cuenta_origen_no_modifica_saldos(self, CuentaBancaria):
        # Given
        cuenta_origen = CuentaBancaria(titular='Ana', saldo_inicial=10)
        cuenta_destino = CuentaBancaria(titular='Juan')
        
        # When
        resultado = cuenta_origen.transferir(cuenta_destino, 25)
        
        # Then
        assert resultado is False
        assert cuenta_origen.saldo == 10
        assert cuenta_destino.saldo == 0

    def test_transferir_monto_mayor_que_saldo_de_cuentas_no_modifica_saldos(self, CuentaBancaria):
        # Given
        cuenta_origen = CuentaBancaria(titular='Ana', saldo_inicial=5)
        cuenta_destino = CuentaBancaria(titular='Juan', saldo_inicial=3)
        
        # When
        resultado = cuenta_origen.transferir(cuenta_destino, 10)
        
        # Then
        assert resultado is False
        assert cuenta_origen.saldo == 5
        assert cuenta_destino.saldo == 3

    def test_transferir_monto_no_negativo_de_cuentas_no_modifica_saldos(self, CuentaBancaria):
        # Given
        cuenta_origen = CuentaBancaria(titular='Ana', saldo_inicial=5)
        cuenta_destino = CuentaBancaria(titular='Juan', saldo_inicial=3)
        
        # When
        resultado = cuenta_origen.transferir(cuenta_destino, -10)
        
        # Then
        assert resultado is False
        assert cuenta_origen.saldo == 5
        assert cuenta_destino.saldo == 3