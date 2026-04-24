import time
import asyncio
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =============================================
# 👇 ВСТАВЬТЕ СВОЙ ТОКЕН СЮДА (в кавычки)
TOKEN = "8590452175:AAEkNVYCmmsPLD6JUjyFte1vtXMgHZG4veI"
# =============================================

SERVER_IP = "hi3.qwertyx.host:27228"

# Переменные для кэша
last_status_time = 0
cached_status = None

# Список чатов, где активен бот
active_chats = set()

# Последний список игроков для отслеживания входов/выходов
last_players = set()


async def get_server_status():
    """Получает статус сервера (с кэшем 10 секунд)"""
    global last_status_time, cached_status
    now = time.time()
    
    if cached_status and (now - last_status_time) < 10:
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
            'motd': str(status.description),
            'version': status.version.name,
            'players_list': []
        }
        
        # Получаем список имён игроков (если есть)
        if status.players.sample:
            result['players_list'] = [p.name for p in status.players.sample]
        
        cached_status = result
        last_status_time = now
        return result
        
    except Exception:
        return {'online': False, 'players_list': []}


async def send_to_all_chats(app, message):
    """Отправляет сообщение во все чаты, где есть бот"""
    for chat_id in active_chats.copy():
        try:
            await app.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception:
            active_chats.discard(chat_id)


async def player_tracker(app):
    """Фоновая задача — отслеживает вход и выход игроков"""
    global last_players
    
    while True:
        try:
            status = await get_server_status()
            
            if status['online']:
                current_players = set(status['players_list'])
                
                # Новые игроки
                for player in current_players - last_players:
                    await send_to_all_chats(app, f"🟢 **{player}** зашёл на сервер")
                
                # Игроки, которые вышли
                for player in last_players - current_players:
                    await send_to_all_chats(app, f"🔴 **{player}** вышел с сервера")
                
                last_players = current_players
            
            await asyncio.sleep(5)
            
        except Exception:
            await asyncio.sleep(5)


# ============ КОМАНДЫ БОТА ============

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start — запуск бота в чате"""
    chat_id = update.effective_chat.id
    active_chats.add(chat_id)
    
    await update.message.reply_text(
        "🎮 **Бот сервера Minecraft запущен!**\n\n"
        "📋 **Доступные команды:**\n"
        "/status — полный статус сервера\n"
        "/online — сколько игроков онлайн\n"
        "/ping — пинг до сервера\n"
        "/ip — IP адрес сервера\n\n"
        "✅ Бот будет уведомлять о входе и выходе игроков",
        parse_mode="Markdown"
    )


async def cmd_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ip — показать IP сервера с возможностью копирования"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Скопировать IP", copy_text=SERVER_IP)],
        [InlineKeyboardButton("📄 Показать текстом", callback_data="show_ip_text")]
    ])
    
    await update.message.reply_text(
        "🖥️ **IP адрес сервера:**\n\nВыберите способ:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def callback_show_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки — показать IP текстом"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"🖥️ **IP адрес сервера:**\n\n`{SERVER_IP}`\n\n"
        f"👉 Нажмите на IP, чтобы выделить и скопировать",
        parse_mode="Markdown"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status — полная информация о сервере"""
    await update.message.chat.send_action("typing")
    data = await get_server_status()
    
    if not data['online']:
        await update.message.reply_text("🔴 **Сервер выключен**", parse_mode="Markdown")
        return
    
    # Оценка пинга
    ping = data['ping']
    if ping < 50:
        ping_status = "🟢 Отлично"
    elif ping < 100:
        ping_status = "🟡 Хорошо"
    elif ping < 150:
        ping_status = "🟠 Средне"
    else:
        ping_status = "🔴 Высокий"
    
    message = (
        f"🟢 **Сервер работает**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Онлайн:** {data['players_online']} / {data['players_max']}\n"
        f"📡 **Пинг:** {data['ping']} мс ({ping_status})\n"
        f"🎮 **Версия:** {data['version']}\n"
        f"📝 **MOTD:** {data['motd']}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    
    await update.message.reply_text(message, parse_mode="Markdown")


async def cmd_online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/online — только количество игроков"""
    data = await get_server_status()
    
    if not data['online']:
        await update.message.reply_text("🔴 Сервер выключен")
        return
    
    online = data['players_online']
    max_players = data['players_max']
    
    if online == 0:
        emoji = "🌙"
        text = "Никого нет"
    elif online < 5:
        emoji = "🌱"
        text = "Немного"
    elif online < 15:
        emoji = "📈"
        text = "Оживлённо"
    else:
        emoji = "🔥"
        text = "Многолюдно"
    
    await update.message.reply_text(
        f"{emoji} **Сейчас на сервере:** {online} / {max_players} игроков\n_{text}_",
        parse_mode="Markdown"
    )


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ping — только пинг"""
    data = await get_server_status()
    
    if not data['online']:
        await update.message.reply_text("🔴 Сервер выключен, пинг не определить")
        return
    
    ping = data['ping']
    
    if ping < 50:
        emoji = "🟢"
        text = "отличный"
    elif ping < 100:
        emoji = "🟡"
        text = "хороший"
    elif ping < 150:
        emoji = "🟠"
        text = "средний"
    else:
        emoji = "🔴"
        text = "высокий"
    
    await update.message.reply_text(
        f"{emoji} **Пинг до сервера:** {ping} мс — {text}",
        parse_mode="Markdown"
    )


# ============ ЗАПУСК ============

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Регистрируем команды
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("online", cmd_online))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("ip", cmd_ip))
    
    # Регистрируем обработчик кнопок
    app.add_handler(CallbackQueryHandler(callback_show_ip, pattern="show_ip_text"))
    
    # Запускаем фоновую задачу отслеживания игроков
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(player_tracker(app))
    
    print("✅ Бот запущен!")
    print(f"📡 Отслеживает сервер: {SERVER_IP}")
    print("🤖 При добавлении в группу напишите /start")
    
    app.run_polling()


if __name__ == "__main__":
    main()
