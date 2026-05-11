import time
import asyncio
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
TOKEN = "8658864645:AAEevMxzgbB31nSXXP_xB-yEJAU7q714SS5w"
JAVA_IP = "hi3.qwertyx.host:27228"
BEDROCK_IP = "hi3.qwertyx.host:29098"
MAP_URL = "http://hi3.qwertyx.host:27100"
ADMIN_ID = 8493522297
# ===============================

cache = {"data": None, "time": 0, "uptime_start": None}
chats = set()

def format_uptime(seconds):
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
    if cache["data"] and now - cache["time"] < 15:
        return cache["data"]
    try:
        server = JavaServer.lookup(JAVA_IP)
        status = await server.async_status()
        players = [p.name for p in status.players.sample] if status.players.sample else []
        
        java_players = [p for p in players if not p.startswith(".")]
        bedrock_players = [p for p in players if p.startswith(".")]
        
        data = {
            "online": True,
            "players": status.players.online,
            "max": status.players.max,
            "motd": str(status.description),
            "version": status.version.name,
            "list": players,
            "java_list": java_players,
            "bedrock_list": bedrock_players,
        }
        cache["data"] = data
        cache["time"] = now
        if cache["uptime_start"] is None:
            cache["uptime_start"] = now
        return data
    except:
        return {"online": False, "list": [], "java_list": [], "bedrock_list": [], "players": 0, "max": 0}

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Статус", callback_data="status"),
         InlineKeyboardButton("📊 Онлайн", callback_data="online")],
        [InlineKeyboardButton("👥 Список", callback_data="list"),
         InlineKeyboardButton("💻 Java IP", callback_data="java_ip"),
         InlineKeyboardButton("📱 Bedrock IP", callback_data="bedrock_ip")],
        [InlineKeyboardButton("🗺️ Карта", callback_data="map"),
         InlineKeyboardButton("📜 Правила", callback_data="rules"),
         InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]
    ])

async def start(update, context):
    chats.add(update.effective_chat.id)
    await update.message.reply_text(
        "🎮 HazeRage\n"
        "👇 Выбери действие:",
        reply_markup=get_keyboard()
    )

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    
    data = await get_status()
    
    if query.data == "status":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        else:
            text = f"🟢 HazeRage\n👥 {data['players']}/{data['max']}\n🎮 {data['version']}"
        await query.edit_message_text(text, reply_markup=get_keyboard())
    
    elif query.data == "online":
        text = f"👥 {data['players']}/{data['max']}" if data["online"] else "🔴 Сервер выключен"
        await query.edit_message_text(text, reply_markup=get_keyboard())
    
    elif query.data == "list":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        elif data["players"] == 0:
            text = "🌙 Никого нет"
        else:
            java = ', '.join(data["java_list"]) if data["java_list"] else "нет"
            bedrock = ', '.join(data["bedrock_list"]) if data["bedrock_list"] else "нет"
            text = f"👥 {data['players']}/{data['max']}\n💻 Java: {java}\n📱 Bedrock: {bedrock}"
        await query.edit_message_text(text, reply_markup=get_keyboard())
    
    elif query.data == "java_ip":
        text = f"💻 Java\n{JAVA_IP}\n✅ 1.21.11+"
        await query.edit_message_text(text, reply_markup=get_keyboard())
    
    elif query.data == "bedrock_ip":
        text = f"📱 Bedrock\n{BEDROCK_IP}\n✅ 1.21.130+"
        await query.edit_message_text(text, reply_markup=get_keyboard())
    
    elif query.data == "map":
        text = f"🗺️ Карта\n{MAP_URL}"
        await query.edit_message_text(text, reply_markup=get_keyboard())
    
    elif query.data == "rules":
        text = "📜 ПРАВИЛА\n🚫 Неприличные постройки\n🚫 Оскорбления\n⚔️ ПВП, грифинг, воровство"
        await query.edit_message_text(text, reply_markup=get_keyboard())
    
    elif query.data == "refresh":
        await query.edit_message_text("🔄...", reply_markup=get_keyboard())
        cache["data"] = None
        cache["time"] = 0
        data = await get_status()
        text = f"🟢 {data['players']}/{data['max']}" if data["online"] else "🔴 Сервер выключен"
        await query.edit_message_text(text, reply_markup=get_keyboard())

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ip", lambda u,c: u.message.reply_text(f"💻 Java: {JAVA_IP}\n📱 Bedrock: {BEDROCK_IP}")))
    app.add_handler(CommandHandler("list", lambda u,c: None))  # кнопка обрабатывает
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Бот HazeRage запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
