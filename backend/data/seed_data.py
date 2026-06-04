SEED_DOCUMENTS = [
    {
        "id": "basic_assertions",
        "text": (
            "Patron pytest: aserciones basicas. "
            "Usar assert valor == esperado para comparar valores simples. "
            "assert resultado is not None para verificar existencia. "
            "assert isinstance(obj, MiClase) para verificar tipos. "
            "Ejemplo: def test_suma_retorna_entero(): assert suma(2, 3) == 5"
        ),
    },
    {
        "id": "exception_testing",
        "text": (
            "Patron pytest: prueba de excepciones. "
            "Usar pytest.raises(TipoError) como contexto para capturar excepciones esperadas. "
            "Ejemplo: with pytest.raises(ValueError): dividir(10, 0). "
            "Verificar el mensaje: with pytest.raises(ValueError, match='division por cero'). "
            "Siempre importar pytest al inicio del archivo de tests."
        ),
    },
    {
        "id": "edge_cases",
        "text": (
            "Patron pytest: casos limite y valores de frontera. "
            "Probar con cero, negativos, cadena vacia, None y listas vacias. "
            "Incluir el caso limite mas pequeno y el mas grande del dominio. "
            "Un test por caso limite para mantener claridad. "
            "Ejemplo: def test_lista_vacia_retorna_cero(): assert promedio([]) == 0"
        ),
    },
    {
        "id": "parametrize",
        "text": (
            "Patron pytest: parametrize para multiples entradas. "
            "@pytest.mark.parametrize('entrada,esperado', [(2,4),(3,9),(-1,1)]) "
            "def test_cuadrado(entrada, esperado): assert cuadrado(entrada) == esperado. "
            "Permite reutilizar la misma logica de test con distintos datos. "
            "Usar nombres de parametros descriptivos para identificar fallos rapidamente."
        ),
    },
    {
        "id": "class_with_setup",
        "text": (
            "Patron pytest: clases de test con setup_method. "
            "class TestCalculadora: def setup_method(self): self.calc = Calculadora(). "
            "setup_method se ejecuta antes de cada metodo de test. "
            "Permite compartir estado inicial sin acoplamiento entre tests. "
            "Usar teardown_method para limpiar recursos si es necesario."
        ),
    },
    {
        "id": "fixtures",
        "text": (
            "Patron pytest: fixtures para datos de prueba reutilizables. "
            "@pytest.fixture def usuario_valido(): return Usuario(nombre='Ana', edad=30). "
            "Las fixtures se inyectan como parametros en los tests. "
            "Scope: function (default), class, module, session. "
            "Preferir fixtures sobre setup/teardown para mayor legibilidad."
        ),
    },
    {
        "id": "mocking",
        "text": (
            "Patron pytest: mocking con unittest.mock. "
            "from unittest.mock import MagicMock, patch. "
            "@patch('modulo.ClaseExterna') def test_servicio(mock_clase): mock_clase.return_value.metodo.return_value = 42. "
            "Usar mock.assert_called_once_with(arg) para verificar llamadas. "
            "Aislar la unidad bajo prueba de sus dependencias externas."
        ),
    },
    {
        "id": "type_verification",
        "text": (
            "Patron pytest: verificacion de tipos y contratos. "
            "assert isinstance(resultado, list) para colecciones. "
            "assert all(isinstance(x, int) for x in lista) para elementos. "
            "Verificar longitudes: assert len(resultado) == 3. "
            "Verificar claves en diccionarios: assert 'nombre' in resultado. "
            "Combinar verificacion de tipo con verificacion de valor cuando sea relevante."
        ),
    },
    {
        "id": "given_when_then_pattern",
        "text": (
            "Patron SMS-UTGen: estructura Given-When-Then en tests unitarios. "
            "Cada test debe contener comentarios internos # Given, # When, # Then. "
            "El nombre del metodo debe describir el escenario completo en español. "
            "Ejemplo: "
            "def test_cuando_usuario_sin_saldo_entonces_lanza_excepcion(): "
            "    # Given "
            "    cuenta = Cuenta(saldo=0) "
            "    # When / Then "
            "    with pytest.raises(SaldoInsuficienteError): "
            "        cuenta.retirar(100). "
            "UTGen demostro que esta estructura reduce el tiempo de correccion de bugs en 20%. "
            "Los nombres descriptivos permiten identificar el fallo sin leer el cuerpo del test."
        ),
    },
    {
        "id": "class_level_testing",
        "text": (
            "Patron SMS-AGONETEST: testing a nivel de clase, no de metodo. "
            "Generar una sola clase de test que cubra la clase bajo prueba completa. "
            "Incluir tests que ejerciten la interaccion entre metodos de la misma clase. "
            "Verificar el estado compartido: un metodo modifica, otro metodo lee. "
            "Ejemplo: class TestCarrito: "
            "    def test_agregar_y_luego_calcular_total_refleja_cambio(self): "
            "        # Given "
            "        carrito = Carrito() "
            "        # When "
            "        carrito.agregar(Producto('lapiz', 5.0)) "
            "        carrito.agregar(Producto('cuaderno', 15.0)) "
            "        # Then "
            "        assert carrito.total() == 20.0. "
            "AGONETEST mostro que este enfoque detecta mas regresiones de integracion interna."
        ),
    },
]
