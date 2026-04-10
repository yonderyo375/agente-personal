"""
Núcleo del Agente — GitHub Models (GPT-4o-mini) + Fallback Gemini
"""

import os
import asyncio
import json
import httpx
import pytz
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Clients
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential
import google.generativeai as genai

from memory_store import MemoryStore

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres un agente de IA autónomo y altamente capaz. Tu nombre es **Nexus**.

Eres experto en:
- 🖥️ Programación (Python, JavaScript, Bash, SQL, y más)
- ⚙️ Automatización (scripts, cron jobs, APIs, bots)
- 🎨 Diseño de sistemas y arquitecturas (especialmente producción de anime)
- 🔍 Búsqueda e investigación de información
- 📋 Análisis de código y archivos

Tu comportamiento:
- Siempre das código funcional y bien comentado
- Explicas paso a paso cuando se necesita
- Eres directo, conciso y muy capaz
- Usas emojis con moderación para mejor lectura
- Respondes en el mismo idioma que el usuario

Contexto actual: Estás ayudando a Gael Fuentes con su proyecto de anime "Sombra de Pacto".
"""

class AgentCore:
    def __init__(self):
        self.memory = MemoryStore()
        
        # Lista de tokens de GitHub para rotación manual o fallback
        self.github_tokens = [
            os.environ.get("GITHUB_TOKEN_1", ""),
            os.environ.get("GITHUB_TOKEN_2", ""),
            os.environ.get("GITHUB_TOKEN_3", ""),
            os.environ.get("GITHUB_TOKEN_4", ""),
            os.environ.get("GITHUB_TOKEN_5", "")
        ]
        # Filtrar tokens vacíos
        self.github_tokens = [t for t in self.github_tokens if t]
        
        self.current_token_index = 0
        
        # Setup Gemini as second fallback
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
        self.gemini_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT
        )

    def _get_github_client(self, token: str):
        return ChatCompletionsClient(
            endpoint="https://models.inference.ai.azure.com",
            credential=AzureKeyCredential(token),
        )

    async def get_response(self, user_id: str, text: str, history: List[Dict] = None) -> str:
        """Obtiene respuesta priorizando GitHub Models (GPT-4o-mini)."""
        
        # 1. Preparar mensajes para el formato OpenAI/Azure
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            for msg in history[-10:]: # Últimos 10 mensajes para contexto
                role = "assistant" if msg["role"] == "model" else "user"
                messages.append({"role": role, "content": msg["content"]})
        
        messages.append({"role": "user", "content": text})

        # 2. Intentar con GitHub Tokens
        for i in range(len(self.github_tokens)):
            token = self.github_tokens[self.current_token_index]
            try:
                client = self._get_github_client(token)
                # Ejecución en thread para no bloquear el loop asíncrono si la librería es síncrona
                response = await asyncio.to_thread(
                    client.complete,
                    messages=messages,
                    model="gpt-4o-mini",
                    temperature=0.7,
                    max_tokens=4096
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error con GitHub Token {self.current_token_index}: {e}")
                # Rotar al siguiente token para la próxima vez
                self.current_token_index = (self.current_token_index + 1) % len(self.github_tokens)
                continue

        # 3. Fallback a Gemini si GitHub falla
        try:
            chat = self.gemini_model.start_chat(history=history)
            response = await asyncio.to_thread(chat.send_message, text)
            return response.text
        except Exception as e:
            return f"❌ Error: Todos los modelos (GitHub y Gemini) están saturados o con error de cuota.\nDetalle: {str(e)}"

    def _get_datetime(self) -> str:
        try:
            tz = pytz.timezone("America/Caracas")
            now = datetime.now(tz)
            return now.strftime("Hoy es %A %d de %B de %Y, son las %H:%M (Venezuela)")
        except Exception:
            return datetime.utcnow().strftime("Fecha: %Y-%m-%d %H:%M UTC")
