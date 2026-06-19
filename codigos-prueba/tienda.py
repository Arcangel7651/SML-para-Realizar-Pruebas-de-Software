class Tienda:
    """
    Clase simple para simular operaciones básicas de una tienda.

    Este código está pensado para practicar pruebas unitarias.
    Incluye operaciones normales, validaciones y excepciones.
    """

    def aplicar_descuento(self, precio, porcentaje):
        """
        Aplica un descuento a un precio.

        Args:
            precio: precio original del producto.
            porcentaje: porcentaje de descuento entre 0 y 100.

        Returns:
            Precio después de aplicar el descuento.

        Raises:
            ValueError: si el precio es negativo o el porcentaje no es válido.
        """
        if precio < 0:
            raise ValueError("El precio no puede ser negativo")

        if porcentaje < 0 or porcentaje > 100:
            raise ValueError("El porcentaje debe estar entre 0 y 100")

        descuento = precio * (porcentaje / 100)
        return precio - descuento

    def aplicar_iva(self, precio, iva=16):
        """
        Aplica IVA a un precio.

        Args:
            precio: precio base.
            iva: porcentaje de IVA. Por defecto es 16.

        Returns:
            Precio con IVA incluido.

        Raises:
            ValueError: si el precio es negativo.
        """
        if precio < 0:
            raise ValueError("El precio no puede ser negativo")

        return precio + (precio * iva / 100)

    def calcular_total(self, precios):
        """
        Calcula el total de una lista de precios.

        Args:
            precios: lista de precios.

        Returns:
            Suma total de los precios.

        Raises:
            ValueError: si la lista está vacía o contiene precios negativos.
        """
        if len(precios) == 0:
            raise ValueError("La lista de precios no puede estar vacía")

        total = 0

        for precio in precios:
            if precio < 0:
                raise ValueError("La lista no puede contener precios negativos")
            total += precio

        return total

    def es_envio_gratis(self, total):
        """
        Verifica si una compra tiene envío gratis.

        Args:
            total: total de la compra.

        Returns:
            True si el total es mayor o igual a 500, False en caso contrario.
        """
        return total >= 500

    def dividir_pago(self, total, personas):
        """
        Divide el total de una compra entre varias personas.

        Args:
            total: cantidad total a pagar.
            personas: número de personas.

        Returns:
            Cantidad que debe pagar cada persona.

        Raises:
            ValueError: si el número de personas es cero o negativo.
        """
        if personas <= 0:
            raise ValueError("El número de personas debe ser mayor que cero")

        return total / personas

    def clasificar_cliente(self, compras):
        """
        Clasifica a un cliente según el número de compras realizadas.

        Args:
            compras: número de compras del cliente.

        Returns:
            'nuevo', 'frecuente' o 'premium'.

        Raises:
            ValueError: si el número de compras es negativo.
        """
        if compras < 0:
            raise ValueError("El número de compras no puede ser negativo")

        if compras == 0:
            return "nuevo"

        if compras < 10:
            return "frecuente"

        return "premium"