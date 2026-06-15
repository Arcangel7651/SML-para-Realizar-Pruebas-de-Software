# Contexto RAG — validador_edad

- Generado: 2026-06-15T01:49:11.393Z
- Total de fragmentos: 3

## Fragmento 1 — Patrón recuperado por similitud

```text
Patron pytest: casos limite, valores de frontera y entradas invalidas. Probar sistematicamente: cero, uno, negativos, cadena vacia, None, lista vacia, valor maximo. Un test por caso limite para aislar fallos y mantener claridad en el nombre. Ejemplo completo: def test_promedio_lista_vacia_retorna_cero(self):     # Given     datos = []     # When     resultado = promedio(datos)     # Then     assert resultado == 0. def test_factorial_de_cero_retorna_uno(self):     assert factorial(0) == 1. def test_buscar_en_lista_vacia_retorna_None(self):     assert buscar([], 'x') is None. def test_potencia_con_exponente_negativo(self):     assert potencia(2, -1) == pytest.approx(0.5). def test_funcion_acepta_None_sin_lanzar_excepcion(self):     resultado = procesar(None)     assert resultado is not None. Cubrir la frontera inferior y superior del dominio de cada parametro.
```

## Fragmento 2 — Patrón recuperado por similitud

```text
Patron SMS-UTGen: estructura Given-When-Then obligatoria en cada metodo de test. Cada test contiene exactamente tres secciones: # Given (precondiciones), # When (accion bajo prueba), # Then (verificacion del resultado). El nombre del metodo describe el escenario completo en espanol: test_cuando_<condicion>_entonces_<resultado_esperado>. Ejemplo con excepcion: def test_cuando_saldo_insuficiente_entonces_lanza_error(self):     # Given     cuenta = Cuenta(titular='Luis', saldo=0.0)     monto = 100.0     # When / Then     with pytest.raises(SaldoInsuficienteError, match='fondos insuficientes'):         cuenta.retirar(monto). Ejemplo sin excepcion: def test_cuando_deposito_valido_entonces_saldo_aumenta(self):     # Given     cuenta = Cuenta(titular='Maria', saldo=200.0)     # When     cuenta.depositar(50.0)     # Then     assert cuenta.saldo == 250.0. UTGen demostro reduccion del 20 porciento en tiempo de correccion de bugs gracias a nombres descriptivos que identifican el fallo sin leer el cuerpo.
```

## Fragmento 3 — Patrón recuperado por similitud

```text
Patron SMS-AGONETEST: una sola clase de test cubre la clase bajo prueba completa. Incluir tests que ejerciten la interaccion entre metodos: uno modifica estado, otro lo lee. Verificar invariantes de la clase: propiedades que deben mantenerse tras cualquier operacion. Cubrir el ciclo de vida del objeto: construccion, uso, estado limite, destruccion. Ejemplo completo de interaccion entre metodos: class TestCarrito:     def setup_method(self):         self.carrito = Carrito()     def test_agregar_producto_y_verificar_total_refleja_precio(self):         # Given         producto = Producto(nombre='lapiz', precio=5.0)         # When         self.carrito.agregar(producto)         # Then         assert self.carrito.total() == 5.0.     def test_agregar_varios_productos_acumula_total_correctamente(self):         # Given         self.carrito.agregar(Producto('lapiz', 5.0))         self.carrito.agregar(Producto('cuaderno', 15.0))         # When         total = self.carrito.total()         # Then         assert total == 20.0.     def test_vaciar_carrito_despues_de_agregar_deja_total_en_cero(self):         self.carrito.agregar(Producto('x', 10.0))         self.carrito.vaciar()         assert self.carrito.total() == 0.0. AGONETEST demostro mayor deteccion de regresiones de integracion interna frente al enfoque de testear cada metodo de forma completamente aislada.
```
