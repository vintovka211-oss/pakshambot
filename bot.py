import time
import asyncio
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== ВСТАВЬТЕ НОВЫЙ ТОКЕН ==========
TOKEN = "8590452175:AAGcmk1Gn-GnVZbUUAvLTRhd3QBslVE5bFk"
# ==========================================

SERVER_IP = "hi3.qwertyx.host:27228"

cache = {"data": None, "time": 0}
chats = set()

async def get_status():
    now = time.time()
    if cache["data"] and now - cache["time"] < 10:
        return cache["data"]
    try:
        server = JavaServer.lookup(SERVER_IP)
        status = await server.async_status()
        
        players_list = []
        if status.players.sample:
            for p in status.players.sample:
                players_list.append(p.name)
        
        data = {
            "online": True,
            "players": status.players.online,
            "max": status.players.max,
            "motd": str(status.description),
            "version": status.version.name,
            "list": players_list,
            "names_hidden": status.players.online > 0 and len(players_list) == 0
        }
        cache["data"] = data
        cache["time"] = now
        return data
    except:
        return {"online": False, "list": [], "names_hidden": False}

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Статус", callback_data="status"),
         InlineKeyboardButton("📊 Онлайн", callback_data="online")],
        [InlineKeyboardButton("👥 Список игроков", callback_data="list"),
         InlineKeyboardButton("🖥️ IP", callback_data="ip")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules"),
         InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]
    ])
    return keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chats.add(chat_id)
    await update.message.reply_text(
        "🎮 **HazeSMP**\n\n👇 Нажми на кнопку:",
        reply_markup=get_main_keyboard()
    )

async def cmd_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🖥️ `{SERVER_IP}`")

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_status()
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
        return
    if data["names_hidden"]:
        await update.message.reply_text(f"⚠️ Имена скрыты хостингом\n📊 Онлайн: {data['players']}/{data['max']}")
        return
    if data["players"] == 0:
        await update.message.reply_text("🌙 На сервере никого нет")
        return
    players_list = "\n".join([f"👤 {p}" for p in data["list"]])
    await update.message.reply_text(f"👥 Игроки ({data['players']}/{data['max']}):\n\n{players_list}")

async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules_text = """📜 **Правила сервера HazeSMP**

🚫 **Запрещено:**
• Строить неприличные постройки (писюны, свастики и т.д.)
• Оскорблять и задевать родню игроков

✅ **Нарушители получают бан!**

💬 Уважайте других игроков и играйте честно!"""
    
    await update.message.reply_text(rules_text, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = await get_status()
    action = query.data
    
    if action == "status":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        else:
            hidden_note = "\n⚠️ Имена скрыты" if data.get("names_hidden", False) else ""
            text = (f"🟢 Сервер работает\n"
                   f"━━━━━━━━━━━━━━━━━━━\n"
                   f"📊 Онлайн: {data['players']}/{data['max']}\n"
                   f"🎮 Версия: {data['version']}\n"
                   f"📝 {data['motd']}{hidden_note}")
        await query.edit_message_text(text, reply_markup=get_main_keyboard())
    
    elif action == "online":
        if data["online"]:
            text = f"📊 Сейчас на сервере: {data['players']} / {data['max']} игроков"
        else:
            text = "🔴 Сервер выключен"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())
    
    elif action == "list":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        elif data["names_hidden"]:
            text = f"⚠️ Имена скрыты\n📊 Онлайн: {data['players']}/{data['max']}"
        elif data["players"] == 0:
            text = "🌙 На сервере никого нет"
        else:
            players_list = "\n".join([f"👤 {p}" for p in data["list"]])
            text = f"👥 Игроки ({data['players']}/{data['max']}):\n\n{players_list}"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())
    
    elif action == "ip":
        await query.edit_message_text(f"🖥️ {SERVER_IP}", reply_markup=get_main_keyboard())
    
    elif action == "rules":
        rules_text = """📜 **Правила сервера HazeSMP**

🚫 **Запрещено:**
• Строить неприличные постройки (писюны, свастики и т.д.)
• Оскорблять и задевать родню игроков

✅ **Нарушители получают бан!**

💬 Уважайте других игроков и играйте честно!"""
        await query.edit_message_text(rules_text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    
    elif action == "refresh":
        cache["data"] = None
        await query.edit_message_text("🔄 Обновление...", reply_markup=get_main_keyboard())
        new_data = await get_status()
        if new_data["online"]:
            hidden_note = "\n⚠️ Имена скрыты" if new_data.get("names_hidden", False) else ""
            text = (f"🟢 Сервер работает\n"
                   f"━━━━━━━━━━━━━━━━━━━\n"
                   f"📊 Онлайн: {new_data['players']}/{new_data['max']}\n"
                   f"🎮 Версия: {new_data['version']}\n"
                   f"📝 {new_data['motd']}{hidden_note}")
        else:
            text = "🔴 Сервер выключен"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_status()
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
    else:
        hidden_note = "\n⚠️ Имена скрыты" if data.get("names_hidden", False) else ""
        text = (f"🟢 Сервер работает\n"
               f"━━━━━━━━━━━━━━━━━━━\n"
               f"📊 Онлайн: {data['players']}/{data['max']}\n"
               f"🎮 Версия: {data['version']}\n"
               f"📝 {data['motd']}{hidden_note}")
        await update.message.reply_text(text)

async def cmd_online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_status()
    if data["online"]:
        await update.message.reply_text(f"📊 Сейчас на сервере: {data['players']} / {data['max']} игроков")
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
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Бот запущен!")
    print(f"📡 Сервер: {SERVER_IP}")
    
    app.run_polling()

if __name__ == "__main__":
    main()
