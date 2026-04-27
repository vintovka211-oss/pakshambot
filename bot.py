import time
import asyncio
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
TOKEN = "8590452175:AAHXgI4NGGfBAxzvnnjW0ZM4_MixECdB8FQ"
SERVER_IP = "hi3.qwertyx.host:27228"
ADMIN_ID = 8493522297  # Твой Telegram ID
# ===============================

cache = {"data": None, "time": 0}
chats = set()

def format_uptime(seconds):
    """Форматирует время в дни/часы/минуты"""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    if days > 0:
        return f"{days}д {hours}ч {minutes}м"
    elif hours > 0:
        return f"{hours}ч {minutes}м"
    else:
        return f"{minutes}м"

async def get_status():
    now = time.time()
    if cache["data"] and now - cache["time"] < 10:
        return cache["data"]
    try:
        server = JavaServer.lookup(SERVER_IP)
        status = await server.async_status()
        players = [p.name for p in status.players.sample] if status.players.sample else []
        data = {
            "online": True,
            "players": status.players.online,
            "max": status.players.max,
            "motd": str(status.description),
            "version": status.version.name,
            "list": players,
        }
        cache["data"] = data
        cache["time"] = now
        return data
    except:
        return {"online": False, "list": []}

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Статус", callback_data="status"),
         InlineKeyboardButton("📊 Онлайн", callback_data="online")],
        [InlineKeyboardButton("👥 Список", callback_data="list"),
         InlineKeyboardButton("🖥️ IP", callback_data="ip")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules"),
         InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]
    ])

async def start(update, context):
    chats.add(update.effective_chat.id)
    await update.message.reply_text("🎮 HazeSMP\n👇 Нажми на кнопку:", reply_markup=get_keyboard())

async def cmd_ip(update, context):
    await update.message.reply_text(f"🖥️ IP: {SERVER_IP}")

async def cmd_list(update, context):
    data = await get_status()
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
    elif data["players"] == 0:
        await update.message.reply_text("🌙 Никого нет")
    else:
        await update.message.reply_text(f"👥 Онлайн: {', '.join(data['list'])}")

async def cmd_rules(update, context):
    await update.message.reply_text(
        "📜 ПРАВИЛА HazeSMP\n\n"
        "🚫 Не строить неприличные постройки\n"
        "🚫 Не оскорблять и не задевать родню игроков\n"
        "✅ Нарушители получают бан!"
    )

async def cmd_uptime(update, context):
    if cache["uptime_start"]:
        uptime = time.time() - cache["uptime_start"]
        await update.message.reply_text(f"⏱ Сервер работает: {format_uptime(uptime)}")
    else:
        await update.message.reply_text("🔴 Сервер выключен")

async def cmd_myid(update, context):
    await update.message.reply_text(f"🆔 Твой ID: {update.effective_user.id}")

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = await get_status()

    if query.data == "status":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        else:
            text = f"🟢 Сервер работает\n📊 Онлайн: {data['players']}/{data['max']}\n🎮 Версия: {data['version']}\n📝 {data['motd']}"
        await query.edit_message_text(text, reply_markup=get_keyboard())
    elif query.data == "online":
        text = f"📊 Онлайн: {data['players']}/{data['max']}" if data["online"] else "🔴 Сервер выключен"
        await query.edit_message_text(text, reply_markup=get_keyboard())
    elif query.data == "list":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        elif data["players"] == 0:
            text = "🌙 Никого нет"
        else:
            text = f"👥 {', '.join(data['list'])}"
        await query.edit_message_text(text, reply_markup=get_keyboard())
    elif query.data == "ip":
        await query.edit_message_text(f"🖥️ {SERVER_IP}", reply_markup=get_keyboard())
    elif query.data == "rules":
        await query.edit_message_text("📜 ПРАВИЛА\n🚫 Не строй неприличные постройки\n🚫 Не задевай родню", reply_markup=get_keyboard())
    elif query.data == "refresh":
        cache["data"] = None
        await query.edit_message_text("🔄 Обновление...", reply_markup=get_keyboard())
        new_data = await get_status()
        if new_data["online"]:
            text = f"🟢 Сервер работает\n📊 Онлайн: {new_data['players']}/{new_data['max']}"
        else:
            text = "🔴 Сервер выключен"
        await query.edit_message_text(text, reply_markup=get_keyboard())

async def cmd_status(update, context):
    data = await get_status()
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
    else:
        await update.message.reply_text(f"🟢 Сервер работает\n📊 Онлайн: {data['players']}/{data['max']}\n🎮 Версия: {data['version']}\n📝 {data['motd']}")

async def cmd_online(update, context):
    data = await get_status()
    if data["online"]:
        await update.message.reply_text(f"📊 Онлайн: {data['players']}/{data['max']}")
    else:
        await update.message.reply_text("🔴 Сервер выключен")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ip", cmd_ip))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("rules", cmd_rules))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("online", cmd_online))
    app.add_handler(CommandHandler("uptime", cmd_uptime))
    app.add_handler(CommandHandler("myid", cmd_myid))

    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Бот запущен!")
    print(f"📡 Сервер: {SERVER_IP}")
    app.run_polling()

if __name__ == "__main__":
    main()
