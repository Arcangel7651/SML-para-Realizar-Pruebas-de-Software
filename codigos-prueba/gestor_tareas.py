"""
gestor_tareas.py — Gestión de una lista de tareas (To-Do).
CÓDIGO BUENO: validaciones de entrada y manejo de estados consistente.
"""


class GestorTareas:

    def __init__(self):
        self._tareas = []
        self._siguiente_id = 1

    def agregar_tarea(self, descripcion):
        if not isinstance(descripcion, str) or not descripcion.strip():
            raise ValueError("La descripción no puede estar vacía")
        tarea = {
            "id": self._siguiente_id,
            "descripcion": descripcion.strip(),
            "completada": False,
        }
        self._tareas.append(tarea)
        self._siguiente_id += 1
        return tarea["id"]

    def completar_tarea(self, tarea_id):
        for tarea in self._tareas:
            if tarea["id"] == tarea_id:
                tarea["completada"] = True
                return True
        raise KeyError(f"No existe una tarea con id {tarea_id}")

    def eliminar_tarea(self, tarea_id):
        for i, tarea in enumerate(self._tareas):
            if tarea["id"] == tarea_id:
                del self._tareas[i]
                return True
        raise KeyError(f"No existe una tarea con id {tarea_id}")

    def listar_pendientes(self):
        return [t for t in self._tareas if not t["completada"]]

    def total_tareas(self):
        return len(self._tareas)
