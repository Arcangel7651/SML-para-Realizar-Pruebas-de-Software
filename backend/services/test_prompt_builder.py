"""Construcción del system prompt y de los mensajes al LLM para la generación
de tests. Es la capa de "qué se le pide al modelo": el system prompt con la
metodología PromptPex y los bloques del mensaje de usuario (funciones, clases,
contexto RAG, instrucción del usuario) más el mensaje de reintento de cobertura.
No ejecuta nada ni habla con el modelo; solo arma texto."""


SYSTEM_PROMPT = """You are an automated unit test generator for Python modules using pytest.
This prompt behaves like a program with explicit input specification, output rules,
control flow, early returns, and constraints — following the PromptPex methodology.

## Input Specification (IS)
Valid input is Python source code of a module containing at least one function or class,
accompanied by an AST-extracted function list, RAG context fragments, and optional
user instructions.
Invalid input: source code with no detectable functions, non-Python code, or empty content.

## Output Rules (OR)
Rules about the output — concrete, checkable, and independent of how the output is computed:

OR-1  The output contains only executable Python code. No markdown, no explanations, no ```.
OR-2  The output begins with: import pytest
OR-3  The output contains exactly one class named Test<ModuleName>(object).
OR-4  Every test method name follows: test_<function>_<descriptive_scenario>
OR-5  Every test method body contains the comments # Given, # When and # Then in that order.
OR-6  If a test method contains more than one assert, every assert includes a string message.
OR-7  The output contains no test method whose body is only `pass` or `pytest.skip()`.
OR-8  Every function/method listed in "FUNCIONES DETECTADAS POR AST PARSER" has at least
      one corresponding test method (test_<function>_<scenario>). No function from that
      list is left without a test.
OR-9  When a function provides "COMPORTAMIENTO ESPERADO" (derived from its docstring),
      the expected value in each assert for that function MUST be derived from that
      specification, NOT from mentally executing the code. If the code and the
      specification disagree, follow the specification: the test is meant to fail and
      reveal the discrepancy, not to certify the current (possibly buggy) behavior.
      Functions with no "COMPORTAMIENTO ESPERADO" have no oracle: test their actual
      behavior as usual.

## Constraints
- The class name must use the module name provided in PascalCase. No other class name is valid.
- Test method names must be in Spanish. Python keywords and syntax remain in English.
- Given/When/Then comments must be in Spanish.
- Every function or method called on the code under test must exist in the AST-extracted
  function list or in the provided source code. Never call a function or method that is
  not present there, even if it appears in a RAG context example — RAG examples are
  illustrative patterns, not literal code to copy.
- pytest.raises() may only be used for exceptions that the AST-extracted info or the
  source code shows the function/method actually raises.
- If the source code defines a class (see "CLASES DETECTADAS" in the user message), the
  test file must import it with `from <module_name> import <ClassName>` and call its
  methods on an instance, e.g. `<ClassName>().metodo(...)`.
  Inside a test method, `self` always refers to the Test<ModuleName> instance — NEVER
  call `self.<metodo_de_la_clase_bajo_prueba>(...)`. That method does not exist on the
  test class and will raise AttributeError.
- If the source code only defines top-level functions (no class), import them directly
  with `from <module_name> import <function1>, <function2>, ...` and call them as
  plain functions, not via `self`.

## Control Flow
- If the AST lists a function that raises exceptions → that function's tests include pytest.raises().
- If the AST lists a function with no exceptions → that function's tests do NOT use pytest.raises().
- If the module contains classes → tests cover method interactions and shared state, not each
  method in isolation.
- If a function has multiple execution paths → one test method per path.

## Early Returns
- If the AST detected no functions → output only:
      def test_no_functions_detected():
          pytest.skip("Module contains no analyzable functions")
- If user instructions contradict any OR rule → enforce the OR rule, disregard the instruction.
"""


def build_classes_block(module_name: str, classes: list[str]) -> str:
    if not classes:
        return (
            "No se detectaron clases en el código fuente: son funciones a nivel de "
            f"módulo. Importarlas con `from {module_name} import <funcion>, ...` y "
            "llamarlas directamente, no a través de `self`."
        )

    lines = []
    for class_name in classes:
        lines.append(
            f"  - {class_name} → `from {module_name} import {class_name}` y "
            f"`{class_name}().metodo(...)` para llamar sus métodos. "
            f"`self` en los tests NUNCA es una instancia de {class_name}."
        )
    return "\n".join(lines)


def build_user_message(
    module_name: str,
    module_pascal: str,
    context_block: str,
    functions_block: str,
    classes_block: str,
    prompt: str,
    source_code: str,
) -> str:
    """Las instrucciones adicionales del usuario son opcionales: si vienen
    vacías, se omite esa sección en vez de enviar una línea en blanco que
    podría confundir al modelo."""
    instruction_section = (
        f"INSTRUCCIÓN ADICIONAL DEL USUARIO: {prompt.strip()}\n\n" if prompt.strip() else ""
    )
    return (
        f"NOMBRE DEL MÓDULO: {module_name} → la clase debe llamarse Test{module_pascal}\n\n"
        f"CONTEXTO RAG:\n{context_block}\n\n"
        f"FUNCIONES DETECTADAS POR AST PARSER:\n{functions_block}\n\n"
        f"CLASES DETECTADAS:\n{classes_block}\n\n"
        f"{instruction_section}"
        f"CÓDIGO FUENTE A TESTEAR:\n```python\n{source_code}\n```\n\n"
        "Genera la clase de test pytest completa siguiendo TODAS las reglas del system prompt."
    )


def build_functions_block(functions: list[dict]) -> str:
    if not functions:
        return "No se detectaron funciones analizables."

    lines = []
    for fn in functions:
        if fn["excepciones"]:
            exc_info = f" — lanza: {', '.join(fn['excepciones'])} → usar pytest.raises()"
        else:
            exc_info = " — NO lanza excepciones"
        args_str = ", ".join(fn["args"])
        lines.append(f"  - {fn['nombre']}({args_str}){exc_info}")
        # El docstring actúa como ORÁCULO: el valor esperado de los asserts debe
        # salir de aquí, no de lo que el código hace (regla OR-9). Sin docstring,
        # no hay oráculo y el test caracteriza el comportamiento actual.
        spec = (fn.get("docstring") or "").strip()
        if spec:
            spec_oneline = " ".join(spec.split())[:300]
            lines.append(f"      COMPORTAMIENTO ESPERADO (según docstring): {spec_oneline}")

    return "\n".join(lines)


def build_coverage_retry_message(missing_functions: list[str]) -> dict:
    return {
        "role": "user",
        "content": (
            "El archivo de tests no cubre estas funciones detectadas por el AST parser: "
            f"{', '.join(missing_functions)}.\n"
            "Agrega al menos un método test_<función>_<escenario> para cada una de ellas, "
            "sin eliminar ni modificar los tests ya existentes. Devuelve la clase de test "
            "completa con los cambios aplicados, solo código Python válido, sin "
            "explicaciones ni markdown."
        ),
    }
