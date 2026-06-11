"""
validador_email.py — Validación de formato de correos electrónicos.
CÓDIGO BUENO: maneja casos borde (None, vacío, sin dominio, etc.)
"""

import re

PATRON_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$")


def es_email_valido(correo):
    """
    Valida si una cadena tiene formato de correo electrónico válido.
    Retorna False si el valor no es una cadena o está vacío.
    """
    if not isinstance(correo, str):
        return False
    correo = correo.strip()
    if not correo:
        return False
    return bool(PATRON_EMAIL.match(correo))


def extraer_dominio(correo):
    """
    Extrae el dominio de un correo electrónico válido.
    Lanza ValueError si el correo no es válido.
    """
    if not es_email_valido(correo):
        raise ValueError("Correo electrónico inválido")
    return correo.strip().split("@")[1]
