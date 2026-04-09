"""
Agente Personal - Telegram Bot (modo Webhook para Render gratis)
"""

import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, constants
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from agent_core import AgentCore
import uvicorn

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")  # URL de Render

agent = AgentCore()
app_tg = Application.builder().token(TELEGRAM_TOKEN).build()
app = FastAPI()


# ─── Handlers de Telegram ───────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "usuario"
    await update.message.reply_text(
        f"👋 ¡Hola {name}! Soy tu agente personal.\n\n"
        "Puedo ayudarte con:\n"
        "🖥️ *Programación* — código en cualquier lenguaje\n"
        "⚙️ *Automatización* — scripts y flujos\n"
        "🎨 *Diseño* — arquitecturas y sistemas\n"
        "🔍 *Búsqueda* — información de la web\n"
        "🧮 *Cálculos* — matemáticas y lógica\n\n"
        "¡Escribime lo que necesitás!",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Comandos:*\n\n"
        "/start — Bienvenida\n"
        "/help — Esta ayuda\n"
        "/reset — Limpiar historial\n"
        "/tools — Ver herramientas\n\n"
        "También podés enviar archivos: `.py .txt .json .csv .pdf`",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    await agent.reset_history(user_id)
    await update.message.reply_text("🧹 Historial limpiado. Empezamos de cero.")

async def tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔧 *Herramientas activas:*\n\n"
        "🔍 Búsqueda web\n"
        "🖥️ Ejecutar código Python\n"
        "🧮 Calculadora\n"
        "📅 Fecha y hora\n"
        "📄 Leer archivos",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_text = update.message.text
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=constants.ChatAction.TYPING
    )
    try:
        response = await agent.run(user_id=user_id, message=user_text)
        for i in range(0, len(response), 4000):
            await update.message.reply_text(
                response[i:i+4000],
                parse_mode=constants.ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Error procesando tu mensaje. Intenta de nuevo.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    doc = update.message.document
    allowed = ['.py', '.txt', '.json', '.csv', '.md', '.html', '.js', '.pdf']
    file_name = doc.file_name or "archivo"
    ext = '.' + file_name.split('.')[-1].lower() if '.' in file_name else ''
    if ext not in allowed:
        await update.message.reply_text(f"⚠️ Solo acepto: {', '.join(allowed)}")
        return
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=constants.ChatAction.TYPING
    )
    try:
        file = await context.bot.get_file(doc.file_id)
        content_bytes = await file.download_as_bytearray()
        content_text = content_bytes.decode('utf-8', errors='ignore')
        caption = update.message.caption or f"Analiza este archivo: {file_name}"
        msg = f"{caption}\n\n```\n{content_text[:3000]}\n```"
        response = await agent.run(user_id=user_id, message=msg)
        for i in range(0, len(response), 4000):
            await update.message.reply_text(
                response[i:i+4000],
                parse_mode=constants.ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Error archivo: {e}")
        await update.message.reply_text("❌ No pude procesar el archivo.")


# ─── Registrar handlers ─────────────────────────────────────

app_tg.add_handler(CommandHandler("start", start))
app_tg.add_handler(CommandHandler("help", help_command))
app_tg.add_handler(CommandHandler("reset", reset))
app_tg.add_handler(CommandHandler("tools", tools))
app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app_tg.add_handler(MessageHandler(filters.Document.ALL, handle_document))


# ─── Endpoints FastAPI ──────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "agent": "Agente Personal", "version": "1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post(f"/webhook/{TELEGRAM_TOKEN}")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, app_tg.bot)
    await app_tg.initialize()
    await app_tg.process_update(update)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    """Al iniciar, registra el webhook en Telegram."""
    await app_tg.initialize()
    if WEBHOOK_URL and TELEGRAM_TOKEN:
        webhook_url = f"{WEBHOOK_URL}/webhook/{TELEGRAM_TOKEN}"
        await app_tg.bot.set_webhook(webhook_url)
        logger.info(f"Webhook registrado: {webhook_url}")
    else:
        logger.warning("WEBHOOK_URL no configurada — el bot no recibirá mensajes")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
