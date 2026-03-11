# ClinicaOrdo Bot (Telegram + IA)

O erro `404: NOT_FOUND` na Vercel aconteceu porque o projeto anterior só tinha um processo de polling (`python bot.py`), e na Vercel você precisa expor rotas HTTP (webhook).

## O que foi ajustado

- Mantive o `bot.py` para execução local (polling).
- Adicionei API HTTP para Vercel em `api/index.py`.
- Adicionei `vercel.json` para rotear `/` e `/api/*` para a função Python.
- Criei endpoint de webhook Telegram em `POST /api/telegram`.
- Adicionei endpoint de health em `GET /api/health`.
- Adicionei validação opcional com `TELEGRAM_WEBHOOK_SECRET`.

## Estrutura

- `bot.py` → modo local (polling)
- `api/index.py` → modo produção Vercel (webhook)
- `vercel.json` → roteamento da Vercel

## Variáveis de ambiente (Vercel)

Configure no painel da Vercel:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET` (recomendado)
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL` (opcional)
- `OPENAI_MODEL` (opcional, padrão `gpt-4o-mini`)
- `SYSTEM_PROMPT` (opcional)
- `LOG_LEVEL` (opcional)

## Deploy na Vercel

1. Suba este repositório para o GitHub.
2. Importe o projeto na Vercel.
3. Configure as variáveis de ambiente.
4. Faça deploy.

Após o deploy, teste:

- `https://SEU_DOMINIO/` deve responder JSON com `ok: true`
- `https://SEU_DOMINIO/api/health` deve responder health

## Registrar webhook no Telegram

Depois do deploy, registre o webhook apontando para `/api/telegram`:

```bash
curl -X POST "https://api.telegram.org/bot<SEU_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://SEU_DOMINIO/api/telegram",
    "secret_token": "SEU_TELEGRAM_WEBHOOK_SECRET"
  }'
```

Para validar:

```bash
curl "https://api.telegram.org/bot<SEU_TOKEN>/getWebhookInfo"
```

## Rodar localmente (opcional)

### Modo polling

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

## Segurança importante

⚠️ Como o token do Telegram foi exposto na conversa, **revogue esse token no BotFather e gere outro** antes de usar em produção.
