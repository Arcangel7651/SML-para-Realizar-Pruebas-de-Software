import ast
import re


def has_given_when_then(code: str) -> bool:
    return bool(
        re.search(r"#\s*Given", code) and
        re.search(r"#\s*When", code) and
        re.search(r"#\s*Then", code)
    )


def is_clean_code_output(code: str) -> bool:
    """OR-1: la salida debe ser solo código ejecutable, sin cercas de
    markdown ni texto conversacional mezclado. Si _extract_code dejó algún
    ``` dentro del bloque de código, la regla no se cumplió."""
    return bool(code.strip()) and "```" not in code


def starts_with_import_pytest(code: str) -> bool:
    """OR-2: la salida debe comenzar con `import pytest`."""
    return code.lstrip().startswith("import pytest")


def find_test_classes(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test")
    ]


def has_expected_test_class(code: str, expected_class_name: str | None) -> bool:
    """OR-3: la salida debe contener exactamente una clase Test<Módulo>(object)."""
    classes = find_test_classes(code)
    if len(classes) != 1:
        return False
    return expected_class_name is None or classes[0] == expected_class_name


def _is_pytest_skip_call(node: ast.stmt) -> bool:
    if not isinstance(node, ast.Expr):
        return False
    call = node.value
    if not isinstance(call, ast.Call):
        return False
    func = call.func
    return (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id == "pytest"
        and func.attr == "skip"
    )


def detect_smells(code: str) -> list[str]:
    smells = []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return smells

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not node.name.startswith("test_"):
            continue

        # ── assertion_roulette ──────────────────────────────────
        asserts = [n for n in ast.walk(node) if isinstance(n, ast.Assert)]
        if len(asserts) > 3 and not any(a.msg is not None for a in asserts):
            if "assertion_roulette" not in smells:
                smells.append("assertion_roulette")

        # ── empty_test ──────────────────────────────────────────
        body = node.body
        # saltar docstring si existe
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            body = body[1:]
        if body and all(
            isinstance(s, ast.Pass) or _is_pytest_skip_call(s)
            for s in body
        ):
            if "empty_test" not in smells:
                smells.append("empty_test")

        # ── generic_name ────────────────────────────────────────
        # Genérico si el nombre es test_X sin más palabras (sin segundo _)
        suffix = node.name[len("test_"):]
        if suffix and "_" not in suffix:
            if "generic_name" not in smells:
                smells.append("generic_name")

    return smells


def _functions_called_in(node: ast.FunctionDef) -> set[str]:
    """Nombres de funciones/métodos que el cuerpo del test realmente INVOCA:
    `funcion(...)` (ast.Call con func ast.Name) o `instancia.metodo(...)`
    (ast.Call con func ast.Attribute). Solo cuentan llamadas reales, no meras
    menciones, para no confundir una variable llamada como un método (p.ej.
    `total`) con una invocación de ese método."""
    called = set()
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        func = sub.func
        if isinstance(func, ast.Name):
            called.add(func.id)
        elif isinstance(func, ast.Attribute):
            called.add(func.attr)
    return called


def count_tests_by_function(code: str, functions: list[str]) -> dict[str, int]:
    """Cuenta cuántos métodos test_* EJERCEN cada función detectada por el AST,
    según lo que el cuerpo del test realmente invoca (no según el NOMBRE del
    test). Un test que solo se *llama* `test_<funcion>_...` pero no invoca a la
    función no cuenta para ella: así un test bien nombrado pero mal implementado
    no simula cobertura (regla OR-8). Un test que invoca varias funciones cuenta
    para todas (útil en tests de interacción estilo AGONETEST)."""
    counts = {fn: 0 for fn in functions}
    if not functions:
        return counts

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return counts

    func_set = set(functions)
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
            continue
        for fn in func_set & _functions_called_in(node):
            counts[fn] += 1

    return counts


def analyze(
    code: str,
    functions_found: list[str] | None = None,
    expected_class_name: str | None = None,
) -> dict:
    return {
        "has_given_when_then": has_given_when_then(code),
        "smells_detected": detect_smells(code),
        "tests_per_function": count_tests_by_function(code, functions_found or []),
        "is_clean_output": is_clean_code_output(code),
        "starts_with_import_pytest": starts_with_import_pytest(code),
        "has_expected_test_class": has_expected_test_class(code, expected_class_name),
        "expected_class_name": expected_class_name,
    }
