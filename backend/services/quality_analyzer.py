import ast
import re


def has_given_when_then(code: str) -> bool:
    return bool(
        re.search(r"#\s*Given", code) and
        re.search(r"#\s*When", code) and
        re.search(r"#\s*Then", code)
    )


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


def _shares_stem(function_name: str, word: str) -> bool:
    """Heurística para tolerar variaciones verbo/sustantivo comunes en español
    entre el nombre de la función (infinitivo, p.ej. "dividir") y la palabra
    que el modelo usó para nombrar el test (p.ej. "division", "suma")."""
    a, b = function_name.lower(), word.lower()
    if a == b or a.startswith(b) or b.startswith(a):
        return True

    common = 0
    for ca, cb in zip(a, b):
        if ca != cb:
            break
        common += 1

    threshold = max(3, min(len(a), len(b)) // 2)
    return common > threshold


def count_tests_by_function(code: str, functions: list[str]) -> dict[str, int]:
    """Cuenta cuántos métodos test_* corresponden a cada función detectada por
    el AST parser. Primero intenta la convención de nombres exacta que pide el
    system prompt (test_<function>_<scenario>, regla OR-4); si el modelo usó
    una variante (p.ej. "test_division_entre_cero" para la función "dividir",
    o "test_suma" para "sumar"), recurre a una comparación de raíz tolerante
    a esas variaciones verbo/sustantivo."""
    counts = {fn: 0 for fn in functions}
    if not functions:
        return counts

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return counts

    # Probar primero los nombres más largos para que p.ej. "es_par" no quede
    # eclipsado por una coincidencia parcial de "es".
    candidates = sorted(functions, key=len, reverse=True)

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
            continue
        suffix = node.name[len("test_"):]
        first_word = suffix.split("_", 1)[0]

        match = next(
            (fn for fn in candidates if suffix == fn or suffix.startswith(fn + "_")),
            None,
        )
        if match is None:
            match = next((fn for fn in candidates if _shares_stem(fn, first_word)), None)

        if match is not None:
            counts[match] += 1

    return counts


def analyze(code: str, functions_found: list[str] | None = None) -> dict:
    return {
        "has_given_when_then": has_given_when_then(code),
        "smells_detected": detect_smells(code),
        "tests_per_function": count_tests_by_function(code, functions_found or []),
    }
