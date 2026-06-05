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


def analyze(code: str) -> dict:
    return {
        "has_given_when_then": has_given_when_then(code),
        "smells_detected": detect_smells(code),
    }
