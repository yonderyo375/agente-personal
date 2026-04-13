"""
Núcleo del Agente — GitHub Models (GPT-4o-mini) + Fallback Gemini
"""

import os
import asyncio
import logging
import pytz
from datetime import datetime
from typing import List, Dict, Any, Optional

# Clients
try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.core.credentials import AzureKeyCredential
except ImportError:
    # Si no están instalados, el bot usará Gemini
    ChatCompletionsClient = None

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
        
        # Tokens de GitHub
        self.github_tokens = [
            os.environ.get(f"GITHUB_TOKEN_{i}", "") for i in range(1, 6)
        ]
        self.github_tokens = [t for t in self.github_tokens if t]
        
        # Si no hay tokens específicos, intentar con GITHUB_TOKEN general
        if not self.github_tokens and os.environ.get("GITHUB_TOKEN"):
            self.github_tokens = [os.environ.get("GITHUB_TOKEN")]

        self.current_token_index = 0
        
        # Setup Gemini
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=SYSTEM_PROMPT
            )
        else:
            self.gemini_model = None

    def _get_github_client(self, token: str):
        if ChatCompletionsClient:
            return ChatCompletionsClient(
                endpoint="https://models.inference.ai.azure.com",
                credential=AzureKeyCredential(token),
            )
        return None

    async def run(self, user_id: str, message: str) -> str:
        """Método principal llamado por el bot."""
        # 1. Obtener historial (ya viene formateado con 'parts' para Gemini)
        history = await self.memory.get_history(user_id)
        
        # 2. Generar respuesta
        response_text = await self._generate_response(message, history)
        
        # 3. Guardar en memoria
        await self.memory.add_message(user_id, "user", message)
        await self.memory.add_message(user_id, "assistant", response_text)
        
        return response_text

    async def reset_history(self, user_id: str):
        """Limpia el historial."""
        await self.memory.clear_history(user_id)

    async def _generate_response(self, text: str, history: List[Dict] = None) -> str:
        """Lógica interna para elegir el modelo y generar la respuesta."""
        
        # Intentar con GitHub Tokens (GPT-4o-mini)
        if self.github_tokens and ChatCompletionsClient:
            # Convertir historial de 'parts' a 'content' para GitHub
            github_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if history:
                for msg in history:
                    role = "assistant" if msg["role"] == "model" else "user"
                    github_messages.append({"role": role, "content": msg["parts"][0]})
            github_messages.append({"role": "user", "content": text})

            for _ in range(len(self.github_tokens)):
                token = self.github_tokens[self.current_token_index]
                try:
                    client = self._get_github_client(token)
                    response = await asyncio.to_thread(
                        client.complete,
                        messages=github_messages,
                        model="gpt-4o-mini",
                        temperature=0.7
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"Error GitHub (Token {self.current_token_index}): {e}")
                    self.current_token_index = (self.current_token_index + 1) % len(self.github_tokens)
                    continue

        # Fallback a Gemini
        if self.gemini_model:
            try:
                # Gemini ya acepta el formato del historial que viene de memory_store
                chat = self.gemini_model.start_chat(history=history or [])
                response = await asyncio.to_thread(chat.send_message, text)
                return response.text
            except Exception as e:
                logger.error(f"Error Gemini: {e}")
                return f"❌ Error: Modelos agotados. Detalle: {str(e)}"
        
        return "❌ Error: No hay modelos configurados (faltan tokens)."

    def _get_datetime(self) -> str:
        try:
            tz = pytz.timezone("America/Caracas")
            now = datetime.now(tz)
            return now.strftime("Hoy es %A %d de %B de %Y, son las %H:%M (Venezuela)")
        except Exception:
            return datetime.utcnow().strftime("Fecha: %Y-%m-%d %H:%M UTC")
