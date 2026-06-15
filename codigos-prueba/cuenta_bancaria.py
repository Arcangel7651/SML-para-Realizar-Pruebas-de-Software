"""
cuenta_bancaria.py — Cuenta bancaria simple.
"""


class CuentaBancaria:

    def __init__(self, titular, saldo_inicial=0):
        self.titular = titular
        self.saldo = saldo_inicial

    def depositar(self, monto):
        self.saldo = self.saldo + monto
        return self.saldo

    def retirar(self, monto):
        if monto > self.saldo:
            self.saldo -= monto
        return self.saldo

    def transferir(self, otra_cuenta, monto):
        self.retirar(monto)
        otra_cuenta.depositar(monto)
