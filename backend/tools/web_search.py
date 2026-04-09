"""
Herramienta de búsqueda web usando DuckDuckGo (gratis, sin API key)
"""
import httpx
import json


async def web_search(query: str) -> str:
    """Busca en la web y devuelve resultados resumidos."""
    try:
        # DuckDuckGo Instant Answer API (gratis)
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_redirect": "1",
            "no_html": "1",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        results = []

        # Respuesta directa
        if data.get("AbstractText"):
            results.append(f"📋 {data['AbstractText']}")
            if data.get("AbstractURL"):
                results.append(f"🔗 Fuente: {data['AbstractURL']}")

        # Tópicos relacionados
        for topic in data.get("RelatedTopics", [])[:5]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(f"• {topic['Text'][:200]}")

        if results:
            return "\n".join(results)
        else:
            return f"No encontré resultados directos para '{query}'. Intenta reformular la búsqueda."

    except Exception as e:
        return f"Error en búsqueda: {str(e)}"
