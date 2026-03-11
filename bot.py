import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.error import TelegramError
from telegram.ext import (
    AIORateLimiter,
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
)
logger = logging.getLogger("clinicaordo_bot")

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "Você é um assistente útil, claro e objetivo. Responda em português do Brasil.",
)


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {name}")
    return value


def build_openai_client() -> tuple[AsyncOpenAI, str, str]:
    api_key = _required_env("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL")

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    client = AsyncOpenAI(**client_kwargs)
    return client, model, base_url or "https://api.openai.com/v1"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Olá! 👋\n"
        "Sou seu bot com IA.\n\n"
        "Envie qualquer mensagem e eu vou responder usando o modelo configurado.\n"
        "Comandos:\n"
        "/start - mensagem inicial\n"
        "/health - status da integração"
    )


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    app_data = context.application.bot_data
    await update.message.reply_text(
        "✅ Bot online\n"
        f"Modelo: {app_data['model']}\n"
        f"Base URL IA: {app_data['base_url']}"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text:
        return

    user_text = message.text.strip()
    if not user_text:
        return

    client: AsyncOpenAI = context.application.bot_data["openai_client"]
    model: str = context.application.bot_data["model"]

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        completion = await client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
        )

        response = completion.choices[0].message.content
        if not response:
            response = "Recebi sua mensagem, mas o modelo não retornou texto."

        await message.reply_text(response)

    except TelegramError as err:
        logger.exception("Erro ao responder no Telegram: %s", err)
    except Exception as err:  # noqa: BLE001
        logger.exception("Erro ao consultar modelo de IA: %s", err)
        await message.reply_text(
            "❌ Tive um erro ao consultar a IA. Verifique suas variáveis OPENAI_* e tente novamente."
        )


async def error_handler(update: Optional[object], context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error", exc_info=context.error)


async def post_init(application: Application) -> None:
    try:
        me = await application.bot.get_me()
        logger.info("Bot conectado como @%s (%s)", me.username, me.id)
    except Exception as err:  # noqa: BLE001
        logger.warning("Não foi possível validar getMe no startup: %s", err)


async def main() -> None:
    telegram_token = _required_env("TELEGRAM_BOT_TOKEN")
    openai_client, model, base_url = build_openai_client()

    application = (
        Application.builder()
        .token(telegram_token)
        .rate_limiter(AIORateLimiter())
        .post_init(post_init)
        .build()
    )

    application.bot_data["openai_client"] = openai_client
    application.bot_data["model"] = model
    application.bot_data["base_url"] = base_url

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("health", health_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    logger.info("Iniciando polling do Telegram...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    finally:
        logger.info("Encerrando bot...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot finalizado via KeyboardInterrupt")
