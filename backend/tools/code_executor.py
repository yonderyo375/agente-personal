"""
Ejecutor de código Python seguro con sandbox
"""
import asyncio
import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr


async def execute_code(code: str, language: str = "python") -> str:
    """Ejecuta código Python en un sandbox y devuelve el output."""
    if language != "python":
        return f"Solo se soporta Python por ahora."

    # Capturar stdout y stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Namespace aislado con utilidades básicas
    safe_globals = {
        "__builtins__": {
            "print": print,
            "len": len, "range": range, "enumerate": enumerate,
            "zip": zip, "map": map, "filter": filter,
            "list": list, "dict": dict, "set": set, "tuple": tuple,
            "str": str, "int": int, "float": float, "bool": bool,
            "sum": sum, "max": max, "min": min, "abs": abs, "round": round,
            "sorted": sorted, "reversed": reversed,
            "isinstance": isinstance, "type": type,
            "True": True, "False": False, "None": None,
        }
    }

    # Intentar importar librerías útiles
    try:
        import math
        import json
        import re
        import datetime
        safe_globals["math"] = math
        safe_globals["json"] = json
        safe_globals["re"] = re
        safe_globals["datetime"] = datetime
    except Exception:
        pass

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(compile(code, "<agent_code>", "exec"), safe_globals)

        output = stdout_capture.getvalue()
        errors = stderr_capture.getvalue()

        if errors:
            return f"Output:\n{output}\n\nWarnings:\n{errors}" if output else f"Error:\n{errors}"
        return output if output else "✅ Código ejecutado sin output."

    except Exception:
        tb = traceback.format_exc()
        return f"❌ Error de ejecución:\n{tb}"
