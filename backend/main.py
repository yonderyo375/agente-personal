"""
Agente IA - Backend Principal
FastAPI + Gemini + Supabase + MCP Tools
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import asyncio
from agent import AgentRunner
from memory import MemoryManager
from tools.file_handler import FileHandler

app = FastAPI(title="Agente IA", version="1.0.0")

# CORS - permite conexión desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: cambia a tu URL de frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = MemoryManager()
file_handler = FileHandler()


# ─── Modelos ────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    user_id: str
    conversation_id: Optional[str] = None
    stream: bool = True


class ConversationRequest(BaseModel):
    user_id: str


# ─── Endpoints ──────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "agent": "Agente IA", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/chat")
async def chat(req: ChatRequest):
    """Endpoint principal de chat con streaming."""
    try:
        agent = AgentRunner(user_id=req.user_id, conversation_id=req.conversation_id)

        if req.stream:
            async def generate():
                async for chunk in agent.run_stream(req.message):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            result = await agent.run(req.message)
            return {"response": result, "conversation_id": agent.conversation_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{user_id}")
async def get_conversations(user_id: str):
    """Lista todas las conversaciones del usuario."""
    convs = await memory.get_conversations(user_id)
    return {"conversations": convs}


@app.get("/conversations/{user_id}/{conversation_id}/messages")
async def get_messages(user_id: str, conversation_id: str):
    """Obtiene mensajes de una conversación."""
    messages = await memory.get_messages(user_id, conversation_id)
    return {"messages": messages}


@app.delete("/conversations/{user_id}/{conversation_id}")
async def delete_conversation(user_id: str, conversation_id: str):
    """Elimina una conversación."""
    await memory.delete_conversation(user_id, conversation_id)
    return {"status": "deleted"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), user_id: str = "default"):
    """Sube un archivo para que el agente lo analice."""
    content = await file.read()
    result = await file_handler.process(file.filename, content, user_id)
    return {"status": "ok", "file_id": result["file_id"], "summary": result["summary"]}


@app.get("/files/{user_id}")
async def list_files(user_id: str):
    """Lista archivos subidos por el usuario."""
    files = await file_handler.list_files(user_id)
    return {"files": files}


@app.get("/tools")
async def list_tools():
    """Lista todas las herramientas disponibles del agente."""
    from tools.registry import TOOLS_REGISTRY
    return {"tools": [{"name": t.name, "description": t.description} for t in TOOLS_REGISTRY]}
