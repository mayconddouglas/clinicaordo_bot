# ClinicaOrdo Bot (Telegram + IA)

Este repositório agora contém uma implementação funcional para conectar seu bot do Telegram a um agente de IA.

## O que foi corrigido

- Estrutura mínima de execução do bot criada.
- Integração com Telegram via `python-telegram-bot` com polling.
- Integração com IA via API compatível com OpenAI (`openai` SDK).
- Tratamento de erros para evitar falhas silenciosas no chat.
- Comandos `/start` e `/health` para diagnóstico rápido.
- Suporte a `.env` para configuração segura de tokens/chaves.

## Pré-requisitos

- Python 3.10+
- Token do bot Telegram (via BotFather)
- API key do provedor de IA (OpenAI ou compatível)

## Configuração

1. Crie e ative um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instale dependências:

```bash
pip install -r requirements.txt
```

3. Configure variáveis de ambiente:

```bash
cp .env.example .env
```

Depois edite `.env` e preencha:

- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- (Opcional) `OPENAI_BASE_URL`
- (Opcional) `OPENAI_MODEL`

## Executar

```bash
python bot.py
```

Se estiver tudo certo, o log mostrará o username do bot conectado.

## Diagnóstico de erro no Telegram

Se no Telegram aparecer erro ao responder:

1. Verifique se `TELEGRAM_BOT_TOKEN` está correto.
2. Verifique se `OPENAI_API_KEY` está válida.
3. Se usar outro provedor, defina `OPENAI_BASE_URL` corretamente.
4. Use `/health` no chat para confirmar modelo e endpoint configurados.
5. Veja o stack trace no terminal para identificar detalhes.

## Segurança importante

⚠️ Seu token do Telegram foi compartilhado em texto aberto. O ideal é **revogar e gerar um novo token no BotFather** antes de usar em produção.

Nunca comite `.env` no Git.
