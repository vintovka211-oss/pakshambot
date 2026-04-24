import os
import time
import asyncio
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== ВСТАВЬТЕ СВОЙ ТОКЕН СЮДА ==========
TELEGRAM_TOKEN = "8590452175:AAEkNVYCmmsPLD6JUjyFte1vtXMgHZG4veI"
# ==============================================

SERVER_IP = "hi3.qwertyx.host:27228"

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
        "/status — статус сервера\n"
        "/online — онлайн\n"
        "/ping — пинг\n"
        "/ip — IP сервера\n\n"
        "📢 Бот присылает уведомления о входе/выходе",
        parse_mode="Markdown"
    )

async def ip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Копировать (приложение)", copy_text=SERVER_IP)],
        [InlineKeyboardButton("📄 Показать IP текстом", callback_data="show_ip")]
    ]
    await update.message.reply_text(
        "🖥️ **IP сервера:**\n\n👇 Выберите способ:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_ip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"🖥️ **IP сервера:**\n\n`{SERVER_IP}`\n\n*(Нажмите на IP, чтобы выделить и скопировать)*",
        parse_mode="Markdown"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    data = await get_server_status()
    
    if data['online']:
        ping = data['ping']
        if ping < 50: ping_emoji = "🟢"
        elif ping < 100: ping_emoji = "🟡"
        elif ping < 150: ping_emoji = "🟠"
        else: ping_emoji = "🔴"
        
        msg = (
            f"🟢 **Сервер работает**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Онлайн: {data['players_online']}/{data['players_max']}\n"
            f"📡 Пинг: {data['ping']} мс {ping_emoji}\n"
            f"🎮 Версия: {data['version']}\n"
            f"📝 {data['motd']}"
        )
    else:
        msg = "🔴 **Сервер выключен**"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def online_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_server_status()
    if data['online']:
        await update.message.reply_text(f"📊 Онлайн: {data['players_online']}/{data['players_max']}")
    else:
        await update.message.reply_text("🔴 Сервер выключен")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_server_status()
    if data['online']:
        await update.message.reply_text(f"📡 Пинг: {data['ping']} мс")
    else:
        await update.message.reply_text("🔴 Сервер выключен")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ip", ip_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("online", online_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CallbackQueryHandler(show_ip_callback, pattern="show_ip"))
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(check_players(app))
    
    print("✅ Бот запущен")
    print(f"📡 Сервер: {SERVER_IP}")
    
    app.run_polling()

if __name__ == "__main__":
    main()
