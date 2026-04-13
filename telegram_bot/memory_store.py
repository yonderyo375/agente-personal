"""
Memoria del agente — Supabase + fallback en RAM
"""

import os
import logging
from typing import List, Dict
from supabase import create_client, Client

logger = logging.getLogger(__name__)

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
                logger.info("Conectado a Supabase")
            except Exception as e:
                logger.error(f"Error conectando a Supabase: {e}")
                self.use_db = False
        else:
            logger.warning("Faltan credenciales de Supabase, usando memoria en RAM")
            self.use_db = False

    async def get_history(self, user_id: str) -> List[Dict]:
        """Obtiene historial formateado para los modelos (últimos 20 mensajes)."""
        if self.use_db:
            try:
                # Nota: El user_id de Telegram es un string numérico. 
                # La columna en Supabase debe ser TEXT o BIGINT, no UUID.
                result = (
                    self.client.table("messages")
                    .select("role, content")
                    .eq("user_id", str(user_id))
                    .order("created_at", desc=False)
                    .limit(20)
                    .execute()
                )
                msgs = result.data or []
                # Formato para Gemini
                return [{"role": m["role"], "parts": [m["content"]]} for m in msgs]
            except Exception as e:
                logger.error(f"Error al obtener historial de DB: {e}")
                pass

        # RAM fallback
        msgs = _ram_store.get(str(user_id), [])[-20:]
        return [{"role": "model" if m["role"] == "assistant" else m["role"], "parts": [m["content"]]} for m in msgs]

    async def add_message(self, user_id: str, role: str, content: str):
        """Guarda un mensaje en la memoria."""
        user_id_str = str(user_id)
        if self.use_db:
            try:
                from datetime import datetime
                # Intentamos insertar sin ID para que Supabase use su default (si es UUID) 
                # o generamos uno si es necesario.
                data = {
                    "user_id": user_id_str,
                    "role": role,
                    "content": content,
                    "created_at": datetime.utcnow().isoformat()
                }
                self.client.table("messages").insert(data).execute()
                logger.info(f"Mensaje guardado en DB para {user_id_str}")
                return
            except Exception as e:
                logger.error(f"Error al guardar en DB: {e}")
                pass

        # RAM fallback
        if user_id_str not in _ram_store:
            _ram_store[user_id_str] = []
        _ram_store[user_id_str].append({"role": role, "content": content})
        
        # Limitar a 50 mensajes en RAM
        if len(_ram_store[user_id_str]) > 50:
            _ram_store[user_id_str] = _ram_store[user_id_str][-50:]
        logger.info(f"Mensaje guardado en RAM para {user_id_str}")

    async def clear_history(self, user_id: str):
        """Limpia el historial de un usuario."""
        user_id_str = str(user_id)
        if self.use_db:
            try:
                self.client.table("messages").delete().eq("user_id", user_id_str).execute()
                logger.info(f"Historial borrado en DB para {user_id_str}")
                return
            except Exception as e:
                logger.error(f"Error al borrar en DB: {e}")
                pass
        _ram_store.pop(user_id_str, None)
        logger.info(f"Historial borrado en RAM para {user_id_str}")
