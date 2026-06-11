import ast


def extract_classes(source_code: str) -> list[str]:
    """Nombres de las clases definidas a nivel de módulo (no anidadas)."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]


def extract_functions(source_code: str) -> list[dict]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    functions = []
    lines = source_code.splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("__") and node.name.endswith("__"):
            continue

        docstring = ast.get_docstring(node) or ""
        start = node.lineno - 1
        end = node.end_lineno
        body = "\n".join(lines[start:end])
        args = [arg.arg for arg in node.args.args]

        exceptions = []
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Raise) and subnode.exc is not None:
                exc = subnode.exc
                if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
                    exceptions.append(exc.func.id)
                elif isinstance(exc, ast.Name):
                    exceptions.append(exc.id)
        exceptions = list(dict.fromkeys(exceptions))

        functions.append({
            "nombre": node.name,
            "args": args,
            "docstring": docstring,
            "cuerpo": body,
            "excepciones": exceptions,
        })

    return functions
