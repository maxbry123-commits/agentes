 cat /opt/nct/telegram-bot/bot.py 2>/dev/null | head -200
#!/usr/bin/env python3
"""Telegram bot NCT - whitelist 1232223511 (Max)"""
import os
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
if not TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN no configurado")
    exit(1)
if not ALLOWED_CHAT or ALLOWED_CHAT.startswith("PENDING"):
    print("ERROR: TELEGRAM_CHAT_ID es PENDING")
    exit(1)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import subprocess, json, urllib.request

def is_auth(update):
    return str(update.effective_chat.id) == ALLOWED_CHAT

async def deny(update, context):
    await update.message.reply_text("Acceso denegado.")

async def start(update, context):
    if not is_auth(update): return await deny(update, context)
    await update.message.reply_text(
        f"Hola Max (chat_id={update.effective_chat.id}).\n\n"
        "Comandos:\n"
        "/status - health check\n"
        "/claude <prompt> - claude-code-vps-A\n"
        "/mimo <prompt> - mimo-code-vps-A\n"
        "/openclaw <prompt> - openclaw\n"
        "/api <modelo> - test modelo via LiteLLM\n"
        "/restart <svc> - reinicia servicio\n"
        "/help - esta ayuda"
    )

async def status(update, context):
    if not is_auth(update): return await deny(update, context)
    try:
        r = subprocess.run(['bash', '/opt/nct/scripts/health/nct_health_v2.sh'],
                          capture_output=True, text=True, timeout=10)
        out = r.stdout[:3500]
    except Exception as e:
        out = f"ERROR: {e}"
    await update.message.reply_text(f"```\n{out}\n```", parse_mode='Markdown')

async def call_agent(agent, prompt, model="cerebras-coder"):
    """Llama al wrapper HTTP del agente"""
    port = 8081 if agent == "claude" else 8082
    body = json.dumps({"prompt": prompt, "model": model}).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=body,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data.get("response", data.get("error", "no response"))
    except Exception as e:
        return f"ERROR wrapper: {e}"

async def claude_cmd(update, context):
    if not is_auth(update): return await deny(update, context)
    prompt = ' '.join(context.args) or 'di HOLA'
    await update.message.reply_text("claude-code pensando...")
    out = await call_agent("claude", prompt)
    await update.message.reply_text(f"claude-code-vps-A:\n\n{out[:3500]}")

async def mimo_cmd(update, context):
    if not is_auth(update): return await deny(update, context)
    prompt = ' '.join(context.args) or 'di HOLA'
    await update.message.reply_text("mimo-code pensando...")
    out = await call_agent("mimo", prompt)
    await update.message.reply_text(f"mimo-code-vps-A:\n\n{out[:3500]}")

async def openclaw_cmd(update, context):
    if not is_auth(update): return await deny(update, context)
    prompt = ' '.join(context.args) or 'di HOLA'
    await update.message.reply_text("openclaw pensando...")
    # OpenClaw CLI
    try:
        r = subprocess.run(['openclaw', 'agent', '--prompt', prompt],
                          capture_output=True, text=True, timeout=60)
        out = (r.stdout or r.stderr)[:3500]
    except FileNotFoundError:
        out = "openclaw CLI no encontrado, uso wrapper 18789"
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:18789/agent",
                data=json.dumps({"prompt": prompt}).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                out = resp.read().decode()[:3500]
        except Exception as e:
            out = f"ERROR openclaw: {e}"
    except Exception as e:
        out = f"ERROR: {e}"
    await update.message.reply_text(f"openclaw:\n\n{out}")

async def api_cmd(update, context):
    if not is_auth(update): return await deny(update, context)
    target = context.args[0] if context.args else 'cerebras-coder'
    try:
        body = json.dumps({
            "model": target,
            "messages": [{"role": "user", "content": "di HOLA en 5 palabras"}],
            "max_tokens": 30
        }).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:4000/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            out = resp.read().decode()[:3500]
    except Exception as e:
        out = f"ERROR: {e}"
    await update.message.reply_text(f"```\n{out}\n```", parse_mode='Markdown')

async def restart_cmd(update, context):
    if not is_auth(update): return await deny(update, context)
    if not context.args:
        return await update.message.reply_text("uso: /restart <servicio>")
    svc = context.args[0]
    r = subprocess.run(['systemctl', 'restart', svc], capture_output=True, text=True)
    await update.message.reply_text(f"restart {svc}: rc={r.returncode}\n{r.stderr[:500]}")

async def help_cmd(update, context):
    if not is_auth(update): return await deny(update, context)
    await update.message.reply_text(
        "/status - health check VPS\n"
        "/claude <prompt> - claude-code-vps-A\n"
        "/mimo <prompt> - mimo-code-vps-A\n"
        "/openclaw <prompt> - openclaw\n"
        "/api <modelo> - test modelo via LiteLLM\n"
        "/restart <svc> - reinicia servicio"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("claude", claude_cmd))
    app.add_handler(CommandHandler("mimo", mimo_cmd))
    app.add_handler(CommandHandler("openclaw", openclaw_cmd))
    app.add_handler(CommandHandler("api", api_cmd))
    app.add_handler(CommandHandler("restart", restart_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    print(f"Bot whitelist activo: {ALLOWED_CHAT}")
    app.run_polling()

if __name__ == "__main__":
    main()
root@vmi3428294:~# echo 