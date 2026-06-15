"""
conversor_temperatura.py — Conversiones entre escalas de temperatura.
"""

CERO_ABSOLUTO_C = -273.15


def celsius_a_fahrenheit(celsius):
    """Convierte de Celsius a Fahrenheit."""
    if celsius < CERO_ABSOLUTO_C:
        raise ValueError("La temperatura no puede ser menor al cero absoluto")
    return celsius * 9 / 5 + 32


def fahrenheit_a_celsius(fahrenheit):
    """Convierte de Fahrenheit a Celsius."""
    celsius = (fahrenheit - 32) * 5 / 9
    if celsius < CERO_ABSOLUTO_C:
        raise ValueError("La temperatura no puede ser menor al cero absoluto")
    return celsius


def celsius_a_kelvin(celsius):
    """Convierte de Celsius a Kelvin."""
    if celsius < CERO_ABSOLUTO_C:
        raise ValueError("La temperatura no puede ser menor al cero absoluto")
    return celsius + 273.15


def kelvin_a_celsius(kelvin):
    """Convierte de Kelvin a Celsius."""
    if kelvin < 0:
        raise ValueError("La temperatura en Kelvin no puede ser negativa")
    return kelvin - 273.15
