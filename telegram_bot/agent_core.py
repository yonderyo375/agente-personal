"""
Núcleo del Agente — Gemini + Herramientas + Memoria Supabase
"""

import os
import asyncio
import json
import httpx
import ast
import math
import operator
from datetime import datetime
import pytz
import google.generativeai as genai
from memory_store import MemoryStore

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

SYSTEM_PROMPT = """Eres un agente de IA autónomo y altamente capaz. Tu nombre es **Nexus**.

Eres experto en:
- 🖥️ Programación (Python, JavaScript, Bash, SQL, y más)
- ⚙️ Automatización (scripts, cron jobs, APIs, bots)
- 🎨 Diseño de sistemas y arquitecturas
- 🔍 Búsqueda e investigación de información
- 🧮 Cálculos matemáticos complejos
- 📋 Análisis de código y archivos

Tu comportamiento:
- Siempre das código funcional y bien comentado
- Explicas paso a paso cuando se necesita
- Eres directo, conciso y muy capaz
- Usas emojis con moderación para mejor lectura
- Formateas el código usando bloques de código
- Respondes en el mismo idioma que el usuario

Cuando el usuario pide código, lo generas completo y listo para usar.
Cuando detectas un error, lo corriges directamente sin excusas."""


class AgentCore:
    def __init__(self):
        self.memory = MemoryStore()
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT,
        )

    async def run(self, user_id: str, message: str) -> str:
        """Procesa un mensaje y devuelve la respuesta del agente."""
        # Obtener historial
        history = await self.memory.get_history(user_id)

        # Detectar si necesita herramientas
        tool_result = await self._try_tool(message)
        if tool_result:
            message = f"{message}\n\n[Resultado de herramienta]: {tool_result}"

        # Construir chat con historial
        chat = self.model.start_chat(history=history)

        try:
            response = await asyncio.to_thread(chat.send_message, message)
            reply = response.text or "No pude generar una respuesta."
        except Exception as e:
            reply = f"❌ Error del modelo: {str(e)}"

        # Guardar en memoria
        await self.memory.save(user_id, "user", message)
        await self.memory.save(user_id, "model", reply)

        return reply

    async def reset_history(self, user_id: str):
        """Limpia el historial de un usuario."""
        await self.memory.clear(user_id)

    async def _try_tool(self, message: str) -> str:
        """Detecta si el mensaje necesita una herramienta y la ejecuta."""
        msg_lower = message.lower()

        # Búsqueda web
        if any(w in msg_lower for w in ["busca", "buscar", "search", "qué es", "quién es", "cuál es", "noticias", "precio de", "cotización"]):
            keywords = message[:100]
            return await self._web_search(keywords)

        # Fecha/hora
        if any(w in msg_lower for w in ["qué hora", "que hora", "fecha", "hoy es", "día de hoy"]):
            return self._get_datetime()

        # Cálculo
        if any(w in msg_lower for w in ["calcula", "calculate", "cuánto es", "cuanto es", "resultado de"]):
            return ""  # Gemini lo maneja solo

        return ""

    async def _web_search(self, query: str) -> str:
        """Búsqueda web con DuckDuckGo."""
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": "1", "no_redirect": "1"}
                )
                data = resp.json()

            results = []
            if data.get("AbstractText"):
                results.append(data["AbstractText"])
            for topic in data.get("RelatedTopics", [])[:3]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(topic["Text"][:200])

            return "\n".join(results) if results else ""
        except Exception:
            return ""

    def _get_datetime(self) -> str:
        """Retorna fecha y hora actual."""
        try:
            tz = pytz.timezone("America/Caracas")
            now = datetime.now(tz)
            return now.strftime("Hoy es %A %d de %B de %Y, son las %H:%M (Venezuela)")
        except Exception:
            return datetime.utcnow().strftime("Fecha: %Y-%m-%d %H:%M UTC")
