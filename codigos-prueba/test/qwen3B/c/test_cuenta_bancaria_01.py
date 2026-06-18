import pytest
from cuenta_bancaria import CuentaBancaria

class TestCuentaBancaria(object):

    def setup_method(self):
        self.cuenta = CuentaBancaria('John Doe', 100)

    def test_depositar_monto_positivo(self):
        # Given
        monto = 50
        # When
        nuevo_saldo = self.cuenta.depositar(monto)
        # Then
        assert nuevo_saldo == 150, "Depósito de monto positivo debería aumentar el saldo"

    def test_depositar_monto_cero(self):
        # Given
        monto = 0
        # When
        nuevo_saldo = self.cuenta.depositar(monto)
        # Then
        assert nuevo_saldo == 100, "Depósito de monto cero debería mantener el saldo"

    def test_depositar_monto_negativo(self):
        # Given
        monto = -50
        # When
        with pytest.raises(ValueError):
            self.cuenta.depositar(monto)

    def test_retirar_monto_suficiente(self):
        # Given
        monto = 50
        # When
        nuevo_saldo = self.cuenta.retirar(monto)
        # Then
        assert nuevo_saldo == 50, "Retiro de saldo suficiente debería reducir el saldo"

    def test_retirar_monto_inferior(self):
        # Given
        monto = 100
        # When
        nuevo_saldo = self.cuenta.retirar(monto)
        # Then
        assert nuevo_saldo == 0, "Retiro superior a saldo debería dejar el saldo en cero"

    def test_retirar_monto_superior(self):
        # Given
        monto = 150
        # When
        with pytest.raises(ValueError):
            self.cuenta.retirar(monto)

    def test_transferir_monto_valido(self):
        # Given
        otra_cuenta = CuentaBancaria('Jane Smith')
        monto = 50
        # When
        nuevo_saldo_origen = self.cuenta.transferir(otra_cuenta, monto)
        nuevo_saldo_destino = otra_cuenta.saldo
        # Then
        assert nuevo_saldo_origen == 50, "Transferencia de saldo válido debería reducir el saldo del origen"
        assert nuevo_saldo_destino == 150, "Transferencia de saldo válido debería aumentar el saldo del destino"

    def test_transferir_monto_insuficiente(self):
        # Given
        otra_cuenta = CuentaBancaria('Jane Smith')
        monto = 150
        # When
        with pytest.raises(ValueError):
            self.cuenta.transferir(otra_cuenta, monto)