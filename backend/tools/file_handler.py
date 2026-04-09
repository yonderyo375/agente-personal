"""
Handler para archivos subidos por usuarios.
Soporta: .txt, .pdf, .py, .json, .csv, .md
"""
import uuid
import os
from tools.file_reader import FILE_STORE

class FileHandler:
    async def process(self, filename: str, content: bytes, user_id: str) -> dict:
        file_id = str(uuid.uuid4())[:8]
        ext = os.path.splitext(filename)[1].lower()

        if ext in [".txt", ".md", ".py", ".js", ".json", ".csv", ".html", ".css"]:
            text = content.decode("utf-8", errors="ignore")
        elif ext == ".pdf":
            try:
                import PyPDF2
                import io
                reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = "\n".join(p.extract_text() for p in reader.pages if p.extract_text())
            except Exception:
                text = content.decode("utf-8", errors="ignore")
        else:
            text = f"[Archivo binario: {filename}, {len(content)} bytes]"

        FILE_STORE[file_id] = text
        summary = f"Archivo '{filename}' procesado. {len(text)} caracteres. ID: {file_id}"
        return {"file_id": file_id, "summary": summary}

    async def list_files(self, user_id: str) -> list:
        return [{"file_id": k, "preview": v[:100]} for k, v in FILE_STORE.items()]
