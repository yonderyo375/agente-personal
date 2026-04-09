"""
Agente autónomo con Gemini + herramientas MCP
"""

import os
import uuid
import json
import asyncio
from typing import AsyncGenerator, Optional
import google.generativeai as genai
from memory import MemoryManager
from tools.registry import TOOLS_REGISTRY, execute_tool

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

SYSTEM_PROMPT = """Eres un agente de IA autónomo y altamente capaz. Tu nombre es **Nexus**.

Puedes:
- Responder preguntas complejas con razonamiento profundo
- Escribir, revisar y ejecutar código en múltiples lenguajes
- Buscar información actualizada en la web
- Analizar archivos (PDFs, imágenes, documentos)
- Realizar tareas autónomamente paso a paso
- Usar herramientas externas para completar tareas

Cuando recibas una tarea:
1. Analiza qué se necesita
2. Usa las herramientas disponibles si es necesario
3. Razona paso a paso
4. Da una respuesta completa y útil

Siempre responde en el mismo idioma que el usuario.
Eres directo, conciso y muy capaz. No finjas limitaciones que no tienes."""


class AgentRunner:
    def __init__(self, user_id: str, conversation_id: Optional[str] = None):
        self.user_id = user_id
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.memory = MemoryManager()
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT,
            tools=self._build_gemini_tools(),
        )

    def _build_gemini_tools(self):
        """Convierte las herramientas al formato de Gemini function calling."""
        declarations = []
        for tool in TOOLS_REGISTRY:
            declarations.append(
                genai.protos.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.schema,
                )
            )
        return [genai.protos.Tool(function_declarations=declarations)] if declarations else None

    async def _get_history(self):
        """Obtiene historial formateado para Gemini."""
        messages = await self.memory.get_messages(self.user_id, self.conversation_id)
        history = []
        for msg in messages[-20:]:  # últimos 20 mensajes
            history.append({
                "role": msg["role"],
                "parts": [msg["content"]]
            })
        return history

    async def run(self, user_message: str) -> str:
        """Ejecuta el agente y devuelve la respuesta completa."""
        history = await self._get_history()
        chat = self.model.start_chat(history=history)

        # Guardar mensaje del usuario
        await self.memory.save_message(
            self.user_id, self.conversation_id, "user", user_message
        )

        response = await asyncio.to_thread(chat.send_message, user_message)

        # Manejar tool calls
        final_response = await self._handle_tool_calls(chat, response)

        # Guardar respuesta
        await self.memory.save_message(
            self.user_id, self.conversation_id, "model", final_response
        )

        return final_response

    async def run_stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """Ejecuta el agente con streaming de respuesta."""
        history = await self._get_history()
        chat = self.model.start_chat(history=history)

        await self.memory.save_message(
            self.user_id, self.conversation_id, "user", user_message
        )

        full_response = ""

        response = await asyncio.to_thread(
            chat.send_message, user_message, stream=True
        )

        for chunk in response:
            try:
                text = chunk.text
                if text:
                    full_response += text
                    yield text
            except Exception:
                # Puede ser un tool call
                pass

        # Si hay tool calls, procesarlos
        try:
            resolved = response.resolve()
            for part in resolved.candidates[0].content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    tool_name = part.function_call.name
                    tool_args = dict(part.function_call.args)

                    yield f"\n\n🔧 *Usando herramienta: {tool_name}...*\n\n"

                    tool_result = await execute_tool(tool_name, tool_args)
                    tool_response = chat.send_message(
                        genai.protos.Content(
                            parts=[genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=tool_name,
                                    response={"result": tool_result}
                                )
                            )]
                        )
                    )

                    final_text = tool_response.text or ""
                    full_response += final_text
                    yield final_text
        except Exception:
            pass

        if full_response:
            await self.memory.save_message(
                self.user_id, self.conversation_id, "model", full_response
            )

    async def _handle_tool_calls(self, chat, response) -> str:
        """Maneja las llamadas a herramientas y devuelve la respuesta final."""
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            parts = response.candidates[0].content.parts

            has_tool_call = any(
                hasattr(p, "function_call") and p.function_call for p in parts
            )

            if not has_tool_call:
                return response.text or ""

            # Ejecutar cada herramienta
            tool_responses = []
            for part in parts:
                if hasattr(part, "function_call") and part.function_call:
                    tool_name = part.function_call.name
                    tool_args = dict(part.function_call.args)
                    result = await execute_tool(tool_name, tool_args)

                    tool_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response={"result": str(result)}
                            )
                        )
                    )

            response = await asyncio.to_thread(
                chat.send_message,
                genai.protos.Content(parts=tool_responses)
            )

        return response.text or "No pude completar la tarea."
