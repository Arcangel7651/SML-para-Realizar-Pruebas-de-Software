"""
cuenta_bancaria.py — Cuenta bancaria simple.
"""


class CuentaBancaria:

    def __init__(self, titular, saldo_inicial=0):
        self.titular = titular
        self.saldo = saldo_inicial

    def depositar(self, monto):
        """Suma `monto` al saldo y devuelve el nuevo saldo. `monto` debe ser
        positivo; depositar 100 sobre un saldo de 0 deja el saldo en 100."""
        self.saldo = self.saldo + monto
        return self.saldo

    def retirar(self, monto):
        """Resta `monto` del saldo SOLO si hay fondos suficientes
        (monto <= saldo) y devuelve el nuevo saldo. Nunca deja el saldo
        negativo: retirar 50 de un saldo de 100 deja 50; retirar más que el
        saldo no modifica el saldo."""
        if monto > self.saldo:
            self.saldo -= monto
        return self.saldo

    def transferir(self, otra_cuenta, monto):
        """Mueve `monto` desde esta cuenta hacia `otra_cuenta`: retira de esta
        y deposita en la otra. La suma de ambos saldos se conserva."""
        self.retirar(monto)
        otra_cuenta.depositar(monto)
