import os
import time
import asyncio
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# === НАСТРОЙКИ (токен и IP возьмите из переменных окружения Railway) ===
TOKEN = os.getenv("8590452175:AAEkNVYCmmsPLD6JUjyFte1vtXMgHZG4veI")
SERVER_IP = os.getenv("SERVER_IP", "hi3.qwertyx.host:27228")
# ===

last_check = 0
cached_status = None
last_players = set()
active_chats = set()

async def get_server_status():
    global last_check, cached_status
    now = time.time()
    if cached_status and (now - last_check) < 10:
        return cached_status
    try:
        server = JavaServer.lookup(SERVER_IP)
        status = server.status()
        ping = server.ping()
        result = {
            'online': True,
            'players_online': status.players.online,
            'players_max': status.players.max,
            'ping': int(ping),
            'motd': status.description,
            'version': status.version.name,
            'players_list': [p.name for p in status.players.sample] if status.players.sample else []
        }
        cached_status = result
        last_check = now
        return result
    except:
        return {'online': False, 'players_list': []}

async def notify_all_chats(app: Application, message: str):
    for chat_id in active_chats:
        try:
            await app.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except:
            pass

async def check_players(app: Application):
    global last_players
    while True:
        try:
            status = await get_server_status()
            if status['online']:
                current_players = set(status['players_list'])
                joined = current_players - last_players
                for player in joined:
                    await notify_all_chats(app, f"🟢 **{player}** зашёл на сервер")
                left = last_players - current_players
                for player in left:
                    await notify_all_chats(app, f"🔴 **{player}** вышел с сервера")
                last_players = current_players
            await asyncio.sleep(5)
        except:
            await asyncio.sleep(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    active_chats.add(chat_id)
    await update.message.reply_text(
        "🎮 **Бот сервера Minecraft запущен!**\n\n"
        "/status — статус сервера\n/online — онлайн\n/ping — пинг\n/ip — IP с кнопкой",
        parse_mode="Markdown"
    )

async def ip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📋 Скопировать IP", copy_text=SERVER_IP)]]
    await update.message.reply_text(
        f"🖥️ **IP:** `{SERVER_IP}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_server_status()
    if data['online']:
        msg = f"🟢 **Сервер работает**\n📊 {data['players_online']}/{data['players_max']}\n📡 {data['ping']} мс\n🎮 {data['version']}\n📝 {data['motd']}"
    else:
        msg = "🔴 Сервер выключен"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def online_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_server_status()
    await update.message.reply_text(f"📊 Онлайн: {data['players_online']}/{data['players_max']}" if data['online'] else "🔴 Сервер выключен")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_server_status()
    await update.message.reply_text(f"📡 Пинг: {data['ping']} мс" if data['online'] else "🔴 Сервер выключен")

def main():
    if not TOKEN:
        print("❌ Ошибка: переменная TELEGRAM_TOKEN не установлена")
        return
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ip", ip_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("online", online_command))
    app.add_handler(CommandHandler("ping", ping_command))
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(check_players(app))
    
    print("✅ Бот запущен на Railway")
    app.run_polling()

if __name__ == "__main__":
    main()
