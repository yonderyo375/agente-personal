"""
Memoria del agente con Supabase
Guarda conversaciones y mensajes por usuario
"""

import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")


class MemoryManager:
    def __init__(self):
        if SUPABASE_URL and SUPABASE_KEY:
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.enabled = True
        else:
            # Fallback en memoria si no hay Supabase
            self._local: Dict = {}
            self.enabled = False

    async def get_conversations(self, user_id: str) -> List[Dict]:
        if not self.enabled:
            return []
        try:
            result = (
                self.client.table("conversations")
                .select("*")
                .eq("user_id", user_id)
                .order("updated_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception:
            return []

    async def get_messages(self, user_id: str, conversation_id: str) -> List[Dict]:
        if not self.enabled:
            key = f"{user_id}:{conversation_id}"
            return self._local.get(key, [])
        try:
            result = (
                self.client.table("messages")
                .select("*")
                .eq("conversation_id", conversation_id)
                .order("created_at")
                .execute()
            )
            return result.data or []
        except Exception:
            return []

    async def save_message(
        self, user_id: str, conversation_id: str, role: str, content: str
    ):
        now = datetime.utcnow().isoformat()

        if not self.enabled:
            key = f"{user_id}:{conversation_id}"
            if key not in self._local:
                self._local[key] = []
            self._local[key].append({"role": role, "content": content})
            return

        try:
            # Upsert conversation
            self.client.table("conversations").upsert({
                "id": conversation_id,
                "user_id": user_id,
                "updated_at": now,
                "title": content[:60] + "..." if len(content) > 60 else content
            }).execute()

            # Insert message
            self.client.table("messages").insert({
                "id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "created_at": now,
            }).execute()
        except Exception as e:
            print(f"Memory error: {e}")

    async def delete_conversation(self, user_id: str, conversation_id: str):
        if not self.enabled:
            key = f"{user_id}:{conversation_id}"
            self._local.pop(key, None)
            return
        try:
            self.client.table("messages").delete().eq("conversation_id", conversation_id).execute()
            self.client.table("conversations").delete().eq("id", conversation_id).execute()
        except Exception as e:
            print(f"Delete error: {e}")
