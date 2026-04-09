"""
Agente Personal - Telegram Bot
Funciones: programación, automatización, diseño, memoria con Supabase
"""

import os
import logging
import asyncio
from telegram import Update, constants
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from agent_core import AgentCore

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
agent = AgentCore()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    name = update.effective_user.first_name or "usuario"
    await update.message.reply_text(
        f"👋 ¡Hola {name}! Soy tu agente personal.\n\n"
        "Puedo ayudarte con:\n"
        "🖥️ *Programación* — escribir, revisar y explicar código\n"
        "⚙️ *Automatización* — crear scripts y flujos\n"
        "🎨 *Diseño* — ideas, estructuras, wireframes en texto\n"
        "🔍 *Búsqueda* — información actualizada de la web\n"
        "🧮 *Cálculos* — matemáticas y lógica\n\n"
        "Simplemente escribime lo que necesitás. ¿Empezamos?",
        parse_mode=constants.ParseMode.MARKDOWN
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    await update.message.reply_text(
        "🤖 *Comandos disponibles:*\n\n"
        "/start — Mensaje de bienvenida\n"
        "/help — Ver esta ayuda\n"
        "/reset — Limpiar historial de conversación\n"
        "/tools — Ver herramientas disponibles\n\n"
        "También podés enviarme:\n"
        "📎 Archivos (.py, .txt, .json, .csv, .pdf)\n"
        "💬 Preguntas en lenguaje natural\n"
        "📋 Código para revisar o depurar",
        parse_mode=constants.ParseMode.MARKDOWN
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /reset — limpia el historial"""
    user_id = str(update.effective_user.id)
    await agent.reset_history(user_id)
    await update.message.reply_text("🧹 Historial limpiado. Empezamos de cero.")


async def tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /tools — lista herramientas"""
    await update.message.reply_text(
        "🔧 *Herramientas activas:*\n\n"
        "🔍 `web_search` — Buscar en internet\n"
        "🖥️ `execute_code` — Ejecutar código Python\n"
        "🧮 `calculate` — Calcular expresiones matemáticas\n"
        "📅 `get_datetime` — Fecha y hora actual\n"
        "📄 `read_file` — Leer archivos subidos\n\n"
        "_Más herramientas próximamente..._",
        parse_mode=constants.ParseMode.MARKDOWN
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto del usuario."""
    user_id = str(update.effective_user.id)
    user_text = update.message.text

    # Mostrar "escribiendo..."
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=constants.ChatAction.TYPING
    )

    try:
        response = await agent.run(user_id=user_id, message=user_text)
        # Telegram tiene límite de 4096 chars por mensaje
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode=constants.ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(response, parse_mode=constants.ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        await update.message.reply_text(
            "❌ Hubo un error procesando tu solicitud. Intenta de nuevo."
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja archivos enviados por el usuario."""
    user_id = str(update.effective_user.id)
    doc = update.message.document

    allowed_ext = ['.py', '.txt', '.json', '.csv', '.md', '.html', '.js', '.pdf']
    file_name = doc.file_name or "archivo"
    ext = '.' + file_name.split('.')[-1].lower() if '.' in file_name else ''

    if ext not in allowed_ext:
        await update.message.reply_text(
            f"⚠️ Formato no soportado. Acepto: {', '.join(allowed_ext)}"
        )
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=constants.ChatAction.TYPING
    )

    try:
        file = await context.bot.get_file(doc.file_id)
        content_bytes = await file.download_as_bytearray()
        content_text = content_bytes.decode('utf-8', errors='ignore')

        # Procesar archivo con el agente
        caption = update.message.caption or f"Analiza este archivo: {file_name}"
        message_with_file = f"{caption}\n\n```\n{content_text[:3000]}\n```"

        response = await agent.run(user_id=user_id, message=message_with_file)

        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode=constants.ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(response, parse_mode=constants.ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Error con archivo: {e}")
        await update.message.reply_text("❌ No pude procesar el archivo. Intenta de nuevo.")


def main():
    """Punto de entrada principal."""
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN no configurado")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("tools", tools))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("🤖 Agente Personal iniciado en Telegram...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
