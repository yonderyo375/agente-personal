"""Lector de archivos subidos."""
import os

FILE_STORE = {}  # En producción usar Supabase Storage

async def read_file_tool(file_id: str) -> str:
    content = FILE_STORE.get(file_id)
    if not content:
        return f"Archivo '{file_id}' no encontrado."
    return content[:5000]  # Limitar a 5000 chars
