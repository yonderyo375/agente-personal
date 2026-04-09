"""
Registro central de herramientas del agente (MCP-style)
Agrega tus propias herramientas aquí
"""

from dataclasses import dataclass
from typing import Callable, Dict, Any
from tools.web_search import web_search
from tools.code_executor import execute_code
from tools.calculator import calculate
from tools.datetime_tool import get_datetime
from tools.file_reader import read_file_tool


@dataclass
class Tool:
    name: str
    description: str
    schema: dict
    handler: Callable


# ─── Definición de herramientas ─────────────────────────────

TOOLS_REGISTRY: list[Tool] = [

    Tool(
        name="web_search",
        description="Busca información actualizada en internet. Úsala cuando necesites datos recientes, noticias, precios, o cualquier información que pueda haber cambiado.",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "La búsqueda a realizar"}
            },
            "required": ["query"]
        },
        handler=web_search
    ),

    Tool(
        name="execute_code",
        description="Ejecuta código Python y devuelve el resultado. Útil para cálculos complejos, procesamiento de datos, y automatizaciones.",
        schema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Código Python a ejecutar"},
                "language": {"type": "string", "description": "Lenguaje (default: python)", "enum": ["python"]}
            },
            "required": ["code"]
        },
        handler=execute_code
    ),

    Tool(
        name="calculate",
        description="Realiza cálculos matemáticos precisos.",
        schema={
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Expresión matemática a calcular, ej: '(2+3)*4'"}
            },
            "required": ["expression"]
        },
        handler=calculate
    ),

    Tool(
        name="get_datetime",
        description="Obtiene la fecha y hora actual.",
        schema={
            "type": "object",
            "properties": {
                "timezone": {"type": "string", "description": "Zona horaria, ej: 'America/Caracas'"}
            },
            "required": []
        },
        handler=get_datetime
    ),

    Tool(
        name="read_file",
        description="Lee el contenido de un archivo subido por el usuario.",
        schema={
            "type": "object",
            "properties": {
                "file_id": {"type": "string", "description": "ID del archivo a leer"}
            },
            "required": ["file_id"]
        },
        handler=read_file_tool
    ),
]


# ─── Ejecutor de herramientas ────────────────────────────────

async def execute_tool(name: str, args: Dict[str, Any]) -> str:
    """Ejecuta una herramienta por nombre y devuelve el resultado como string."""
    tool = next((t for t in TOOLS_REGISTRY if t.name == name), None)
    if not tool:
        return f"Herramienta '{name}' no encontrada."
    try:
        import asyncio
        import inspect
        if inspect.iscoroutinefunction(tool.handler):
            result = await tool.handler(**args)
        else:
            result = await asyncio.to_thread(tool.handler, **args)
        return str(result)
    except Exception as e:
        return f"Error ejecutando {name}: {str(e)}"
