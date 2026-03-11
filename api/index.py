import logging
import os
from typing import Any

import httpx
from flask import Flask, jsonify, request
from openai import OpenAI

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
)
logger = logging.getLogger("clinicaordo_bot.vercel")

app = Flask(__name__)

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "Você é um assistente útil, claro e objetivo. Responda em português do Brasil.",
)


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {name}")
    return value


def _openai_client() -> tuple[OpenAI, str]:
    client_kwargs: dict[str, Any] = {"api_key": _required_env("OPENAI_API_KEY")}
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        client_kwargs["base_url"] = base_url
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return OpenAI(**client_kwargs), model


def _send_telegram_message(chat_id: int, text: str) -> None:
    token = _required_env("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    with httpx.Client(timeout=20.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()


def _is_webhook_authorized() -> bool:
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if not secret:
        return True
    return request.headers.get("X-Telegram-Bot-Api-Secret-Token") == secret


@app.get("/")
def home() -> tuple[Any, int]:
    return jsonify({"ok": True, "service": "clinicaordo-bot", "mode": "vercel-webhook"}), 200


@app.get("/api/health")
def health() -> tuple[Any, int]:
    return jsonify(
        {
            "ok": True,
            "has_telegram_token": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        }
    ), 200


@app.post("/api/telegram")
def telegram_webhook() -> tuple[Any, int]:
    if not _is_webhook_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    update = request.get_json(silent=True) or {}
    message = update.get("message") or update.get("edited_message") or {}
    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    chat_id = chat.get("id")

    if not chat_id:
        return jsonify({"ok": True, "ignored": "no_chat"}), 200

    if not text:
        _send_telegram_message(chat_id, "Envie uma mensagem de texto para eu responder 😊")
        return jsonify({"ok": True, "ignored": "no_text"}), 200

    if text == "/start":
        _send_telegram_message(
            chat_id,
            "Olá! 👋\nSou seu bot com IA via webhook na Vercel.\nEnvie qualquer mensagem para começar.",
        )
        return jsonify({"ok": True}), 200

    if text == "/health":
        _send_telegram_message(
            chat_id,
            f"✅ Bot online\nModelo: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}\nModo: webhook (Vercel)",
        )
        return jsonify({"ok": True}), 200

    try:
        client, model = _openai_client()
        completion = client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )
        answer = completion.choices[0].message.content or "Recebi sua mensagem, mas o modelo não retornou texto."
        _send_telegram_message(chat_id, answer)
        return jsonify({"ok": True}), 200
    except Exception as err:  # noqa: BLE001
        logger.exception("Erro no webhook do Telegram: %s", err)
        _send_telegram_message(
            chat_id,
            "❌ Tive um erro ao consultar a IA. Verifique as variáveis OPENAI_* e tente novamente.",
        )
        return jsonify({"ok": False, "error": "internal_error"}), 200
