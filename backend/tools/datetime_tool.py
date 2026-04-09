"""Herramienta de fecha y hora."""
from datetime import datetime
import pytz

def get_datetime(timezone: str = "America/Caracas") -> str:
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return now.strftime(f"📅 %A, %d de %B de %Y | ⏰ %H:%M:%S ({timezone})")
    except Exception:
        now = datetime.utcnow()
        return now.strftime("📅 %A, %d de %B de %Y | ⏰ %H:%M:%S (UTC)")
