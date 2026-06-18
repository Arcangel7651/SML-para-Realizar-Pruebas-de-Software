"""
cuenta_bancaria.py — Cuenta bancaria simple.
"""


class CuentaBancaria:

    def __init__(self, titular, saldo_inicial=0):
        """Crea una cuenta bancaria con un titular y un saldo inicial.
        Si no se especifica un saldo inicial, este comienza en 0."""
        self.titular = titular
        self.saldo = saldo_inicial

    def depositar(self, monto):
        """Suma `monto` al saldo y devuelve el nuevo saldo. `monto` debe ser
        positivo; depositar 100 sobre un saldo de 0 deja el saldo en 100.
        Si `monto` no es positivo, el saldo no se modifica."""
        if monto <= 0:
            return self.saldo

        self.saldo += monto
        return self.saldo

    def retirar(self, monto):
        """Resta `monto` del saldo SOLO si hay fondos suficientes
        (monto <= saldo) y devuelve el nuevo saldo. Nunca deja el saldo
        negativo: retirar 50 de un saldo de 100 deja 50; retirar más que el
        saldo no modifica el saldo.

        Si `monto` no es positivo, el saldo permanece sin cambios."""
        if monto <= 0:
            return self.saldo

        if monto <= self.saldo:
            self.saldo -= monto

        return self.saldo

    def transferir(self, otra_cuenta, monto):
        """Mueve `monto` desde esta cuenta hacia `otra_cuenta`: retira de esta
        y deposita en la otra. La suma de ambos saldos se conserva cuando la
        transferencia se realiza correctamente.

        Si el retiro no puede realizarse, ninguna de las cuentas se modifica.
        Devuelve `True` si la transferencia fue exitosa y `False` en caso
        contrario."""
        if monto <= 0:
            return False

        if monto <= self.saldo:
            self.retirar(monto)
            otra_cuenta.depositar(monto)
            return True

        return False