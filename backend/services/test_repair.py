"""Fixes determinísticos sobre el código de prueba generado por el modelo.
Corrigen los dos fallos más comunes que dejan la suite con 0% de cobertura sin
que el archivo deje de compilar: olvidar el import del módulo bajo prueba e
invocar los métodos de la clase sobre `self` (estilo unittest). Son
transformaciones de texto/AST, sin llamadas al modelo."""

import ast
import re


def _referenced_names(code: str) -> set[str]:
    """Nombres (ast.Name) usados en el código de prueba."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}


def _already_imports_module(code: str, module_name: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module_name:
            return True
        if isinstance(node, ast.Import) and any(a.name == module_name for a in node.names):
            return True
    return False


def _ensure_module_import(
    code: str, module_name: str, classes: list[str], functions_found: list[str]
) -> str:
    """Fix determinístico del fallo más común: el modelo genera tests que usan
    `Calculadora()` o `funcion()` del módulo bajo prueba pero olvida importarlos.
    Eso compila (NameError es error de ejecución), pero hace fallar TODOS los
    tests con 0% de cobertura. Si detecta símbolos del módulo usados sin
    importar, inyecta `from <module> import <símbolos>` tras `import pytest`.

    Si el módulo define clases, los símbolos importables son las clases (sus
    métodos no se importan); si solo hay funciones a nivel de módulo, esas."""
    if _already_imports_module(code, module_name):
        return code

    symbols = classes if classes else functions_found
    used = _referenced_names(code)
    needed = [s for s in dict.fromkeys(symbols) if s in used]
    if not needed:
        return code

    import_line = f"from {module_name} import {', '.join(needed)}"
    lines = code.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("import pytest"):
            insert_at = i + 1
            break
    lines.insert(insert_at, import_line)
    return "\n".join(lines)


def _fix_self_method_calls(code: str, classes: list[str], functions_found: list[str]) -> str:
    """Reescribe `self.<metodo>(...)` por `<Clase>().<metodo>(...)` para los
    métodos de la clase bajo prueba. El modelo a veces invoca los métodos sobre
    `self` (estilo unittest), pero en pytest `self` es la instancia de
    Test<Modulo>, no de la clase bajo prueba, así que `self.sumar(...)` lanza
    AttributeError y ningún test toca el código real (0% de cobertura). Solo se
    reescriben nombres que son métodos reales de la clase (lista del AST), para
    no tocar helpers legítimos del test."""
    if not classes or not functions_found:
        return code
    class_name = classes[0]
    # nombres más largos primero para que p.ej. "es_par" no quede eclipsado
    methods = sorted(dict.fromkeys(functions_found), key=len, reverse=True)
    pattern = re.compile(r"\bself\.(" + "|".join(re.escape(m) for m in methods) + r")\b")
    return pattern.sub(rf"{class_name}().\1", code)


def repair_generated_tests(
    code: str, module_name: str, classes: list[str], functions_found: list[str]
) -> str:
    """Aplica los fixes determinísticos a la salida del modelo, en orden:
    1) corrige `self.<metodo>()` -> `<Clase>().<metodo>()` (así el código pasa
       a referenciar la clase), y luego
    2) inyecta el import de la clase/funciones si falta.
    El orden importa: el paso 2 detecta que la clase se usa gracias al paso 1."""
    code = _fix_self_method_calls(code, classes, functions_found)
    code = _ensure_module_import(code, module_name, classes, functions_found)
    return code
