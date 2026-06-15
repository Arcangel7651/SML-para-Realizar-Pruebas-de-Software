class Calculadora:

    def sumar(self, a, b):
        return a + b

    def restar(self, a, b):
        return a - b

    def multiplicar(self, a, b):
        return a * b

    def dividir(self, a, b):
        if b == 0:
            raise ValueError("No se puede dividir entre cero")
        return a / b

    def potencia(self, base, exponente):
        return base ** exponente

    def es_par(self, numero):
        return numero % 2 == 0
