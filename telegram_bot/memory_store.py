"""
Memoria del agente — Supabase + fallback en RAM
"""

import os
from typing import List, Dict
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Memoria en RAM como fallback si no hay Supabase
_ram_store: Dict[str, List] = {}


class MemoryStore:
    def __init__(self):
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                self.use_db = True
            except Exception:
                self.use_db = False
        else:
            self.use_db = False

    async def get_history(self, user_id: str) -> List[Dict]:
        """Obtiene historial formateado para Gemini (últimos 20 mensajes)."""
        if self.use_db:
            try:
                result = (
                    self.client.table("messages")
                    .select("role, content")
                    .eq("user_id", user_id)
                    .order("created_at")
                    .limit(20)
                    .execute()
                )
                msgs = result.data or []
                return [{"role": m["role"], "parts": [m["content"]]} for m in msgs]
            except Exception:
                pass

        # RAM fallback
        msgs = _ram_store.get(user_id, [])[-20:]
        return [{"role": m["role"], "parts": [m["content"]]} for m in msgs]

    async def save(self, user_id: str, role: str, content: str):
        """Guarda un mensaje en la memoria."""
        if self.use_db:
            try:
                import uuid
                from datetime import datetime
                self.client.table("messages").insert({
                    "id": str(uuid.uuid4()),
                    "conversation_id": user_id,
                    "user_id": user_id,
                    "role": role,
                    "content": content,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
                return
            except Exception:
                pass

        # RAM fallback
        if user_id not in _ram_store:
            _ram_store[user_id] = []
        _ram_store[user_id].append({"role": role, "content": content})
        # Limitar a 50 mensajes en RAM
        if len(_ram_store[user_id]) > 50:
            _ram_store[user_id] = _ram_store[user_id][-50:]

    async def clear(self, user_id: str):
        """Limpia el historial de un usuario."""
        if self.use_db:
            try:
                self.client.table("messages").delete().eq("user_id", user_id).execute()
                return
            except Exception:
                pass
        _ram_store.pop(user_id, None)
