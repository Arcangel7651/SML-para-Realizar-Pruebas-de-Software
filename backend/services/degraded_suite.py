"""Redes de seguridad cuando la salida del modelo no compila o no pasa entera.
Reúne la extracción de métodos test_* por bloques de texto (preservando los
comentarios Given/When/Then) y, sobre ella: el filtrado al subconjunto que pasó
(para aprender solo de lo verificado) y la suite degradada de respaldo (rescata
lo que compila y cubre el resto con pytest.skip()) para que la corrida siempre
produzca métricas reales en vez de quedar vacía."""

import ast
import re
import textwrap

from services.quality_analyzer import count_tests_by_function


_TEST_METHOD_RE = re.compile(r"^([ \t]*)def (test_\w+)\s*\(", re.MULTILINE)


def _salvage_test_methods(code: str) -> list[str]:
    """Cuando el archivo completo no compila (ni tras el reintento), rescata
    los métodos test_* que sí son sintácticamente válidos por sí solos,
    descartando el resto. Permite conservar parte del trabajo del LLM en
    vez de tirar todo el archivo a la basura."""
    lines = code.splitlines()
    matches = list(_TEST_METHOD_RE.finditer(code))

    salvaged = []
    for m in matches:
        indent = len(m.group(1))
        start_line = code[:m.start()].count("\n")
        end_line = len(lines)
        for j in range(start_line + 1, len(lines)):
            stripped = lines[j].strip()
            if not stripped:
                continue
            cur_indent = len(lines[j]) - len(lines[j].lstrip())
            if cur_indent <= indent:
                end_line = j
                break

        block = lines[start_line:end_line]
        dedented = "\n".join(
            l[indent:] if len(l) >= indent else l.lstrip() for l in block
        )
        try:
            ast.parse(dedented)
        except SyntaxError:
            continue
        salvaged.append(dedented.rstrip())

    return salvaged


def filter_to_passing_tests(code: str, passing: set[str]) -> str:
    """Devuelve el código conservando el encabezado (imports, clase, fixtures
    al inicio) y SOLO los métodos test_* cuyo nombre está en `passing`.
    Se basa en líneas (no en ast.unparse) para preservar los comentarios
    Given/When/Then. Usado para aprender únicamente del subconjunto de tests
    verificados que pasaron, sin arrastrar los que fallaron."""
    lines = code.splitlines()
    matches = list(_TEST_METHOD_RE.finditer(code))
    if not matches:
        return code

    first_start = code[: matches[0].start()].count("\n")
    header = lines[:first_start]

    kept_blocks = []
    for m in matches:
        name = m.group(2)
        indent = len(m.group(1))
        start_line = code[: m.start()].count("\n")
        end_line = len(lines)
        for j in range(start_line + 1, len(lines)):
            stripped = lines[j].strip()
            if not stripped:
                continue
            cur_indent = len(lines[j]) - len(lines[j].lstrip())
            if cur_indent <= indent:
                end_line = j
                break
        if name not in passing:
            continue
        block = lines[start_line:end_line]
        while block and not block[-1].strip():
            block.pop()
        kept_blocks.append("\n".join(block))

    if not kept_blocks:
        return code

    return "\n".join(header).rstrip() + "\n\n" + "\n\n".join(kept_blocks) + "\n"


def _build_skip_stub(name: str, reason: str) -> str:
    safe_reason = reason.replace('"', "'")
    return (
        f"    def test_{name}_no_generado(self):\n"
        f"        # Given: el modelo no generó un test válido para '{name}'\n"
        f"        # When: se ejecuta la suite generada\n"
        f"        # Then: se omite hasta regenerar manualmente\n"
        f'        pytest.skip("Generación de SLM falló: {safe_reason}")'
    )


def _build_degraded_imports(module_name: str, functions_found: list[str], classes: list[str]) -> str:
    names = classes or functions_found
    if not names:
        return f"# {module_name}: no se detectaron símbolos importables"
    return f"from {module_name} import {', '.join(dict.fromkeys(names))}"


def build_degraded_tests(
    raw_code: str,
    module_name: str,
    module_pascal: str,
    functions_found: list[str],
    classes: list[str],
    compile_error: str | None,
) -> str:
    """Última red de seguridad cuando ni la generación inicial ni el
    reintento compilan. Rescata los métodos test_* que sí compilan de
    forma aislada y cubre con pytest.skip() cualquier función sin un test
    sobreviviente, para que la suite siempre se pueda ejecutar y produzca
    métricas reales (en vez de terminar vacía)."""
    salvaged = _salvage_test_methods(raw_code)
    salvaged_code = "\n\n".join(salvaged)
    covered = count_tests_by_function(salvaged_code, functions_found)

    reason = (compile_error or "error de compilación desconocido").splitlines()[0][:200]
    stubs = [
        _build_skip_stub(fn, reason)
        for fn, count in covered.items()
        if count == 0
    ]
    if not functions_found and not salvaged:
        stubs = [_build_skip_stub("modulo", reason)]

    salvaged_methods = [textwrap.indent(s, "    ") for s in salvaged]
    body = "\n\n".join(salvaged_methods + stubs)

    return (
        "import pytest\n"
        f"{_build_degraded_imports(module_name, functions_found, classes)}\n\n\n"
        f"class Test{module_pascal}(object):\n"
        f"{body}\n"
    )


def missing_function_coverage(tests_code: str, functions_found: list[str]) -> list[str]:
    """Funciones detectadas por el AST parser que no tienen ningún
    test_<funcion>_<escenario> asociado (OR-8). Se usa para decidir si vale
    la pena un retry pidiéndole al modelo que complete la cobertura."""
    counts = count_tests_by_function(tests_code, functions_found)
    return [fn for fn, count in counts.items() if count == 0]
