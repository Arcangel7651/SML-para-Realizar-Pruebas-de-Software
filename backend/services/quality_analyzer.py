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


def detect_smells(code: str, functions: list[str] | None = None) -> list[str]:
    smells = []
    func_set = set(functions or [])

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

        # ── empty_raises ────────────────────────────────────────
        # `with pytest.raises(...)` cuyo cuerpo no invoca ninguna función bajo
        # prueba: nada lanza, el test falla sin probar el código.
        if _has_empty_raises(node, func_set):
            if "empty_raises" not in smells:
                smells.append("empty_raises")

        # ── assert_in_except ────────────────────────────────────
        # try/except con el assert dentro del except: si la excepción no se
        # lanza, el assert nunca corre y el test pasa de forma vacua.
        if _has_assert_in_except(node):
            if "assert_in_except" not in smells:
                smells.append("assert_in_except")

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


def _is_pytest_raises_item(item: ast.withitem) -> bool:
    """True si el item de un `with` es una llamada a pytest.raises(...) (o
    raises(...) importado suelto)."""
    call = item.context_expr
    if not isinstance(call, ast.Call):
        return False
    func = call.func
    return (
        (isinstance(func, ast.Attribute) and func.attr == "raises")
        or (isinstance(func, ast.Name) and func.id == "raises")
    )


def _has_empty_raises(test_node: ast.FunctionDef, func_set: set[str]) -> bool:
    """True si el test tiene un `with pytest.raises(...)` cuyo cuerpo NO invoca
    ninguna función bajo prueba. Patrón típico del modelo: asigna las variables
    dentro del bloque pero olvida la llamada, así que nada lanza y el test falla
    con 'DID NOT RAISE' sin que el código tenga un bug."""
    if not func_set:
        return False
    for sub in ast.walk(test_node):
        if not isinstance(sub, ast.With):
            continue
        if not any(_is_pytest_raises_item(it) for it in sub.items):
            continue
        called = set()
        for stmt in sub.body:
            called |= _functions_called_in(stmt)
        if not (called & func_set):
            return True
    return False


def _has_assert_in_except(test_node: ast.FunctionDef) -> bool:
    """True si el test verifica una excepción con try/except y la(s) aserción(es)
    viven DENTRO del except: si la excepción no se lanza, el except no entra y el
    assert nunca corre → el test 'pasa' de forma vacua sin probar nada. La forma
    correcta es `with pytest.raises(TipoError): funcion(...)`."""
    for sub in ast.walk(test_node):
        if isinstance(sub, ast.Try):
            for handler in sub.handlers:
                if any(isinstance(n, ast.Assert) for n in ast.walk(handler)):
                    return True
    return False


def find_vacuous_except_tests(code: str) -> set[str]:
    """Nombres de los tests con el patrón assert-dentro-de-except (pasan de
    forma vacua si la excepción no se lanza). Se usa para no aprenderlos como
    ejemplos verificados (romper la auto-perpetuación del smell)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("test_")
        and _has_assert_in_except(node)
    }


def find_empty_raises_tests(code: str, functions: list[str] | None) -> set[str]:
    """Nombres de los tests con un bloque `pytest.raises` 'vacío' (sin invocar
    ninguna función bajo prueba). Se usa para NO flagear sus fallos 'DID NOT
    RAISE' como posibles bugs: el roto es el test, no el código."""
    func_set = set(functions or [])
    if not func_set:
        return set()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    bad = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name.startswith("test_")
            and _has_empty_raises(node, func_set)
        ):
            bad.add(node.name)
    return bad


def analyze(
    code: str,
    functions_found: list[str] | None = None,
    expected_class_name: str | None = None,
) -> dict:
    return {
        "has_given_when_then": has_given_when_then(code),
        "smells_detected": detect_smells(code, functions_found),
        "tests_per_function": count_tests_by_function(code, functions_found or []),
        "is_clean_output": is_clean_code_output(code),
        "starts_with_import_pytest": starts_with_import_pytest(code),
        "has_expected_test_class": has_expected_test_class(code, expected_class_name),
        "expected_class_name": expected_class_name,
    }
