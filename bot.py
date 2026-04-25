import time
import asyncio
import aiohttp
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
TOKEN = "8590452175:AAGcmk1Gn-GnVZbUUAvLTRhd3QBslVE5bFk"           # Токен от BotFather
SERVER_IP = "hi3.qwertyx.host:27228"         # IP сервера

# Pterodactyl API настройки
PTERO_API_KEY = "ptlc_j9A9o5AyW4N6MRkF4rs88WMY5DSKFFmAnaC5dxQ0lZF"
PTERO_SERVER_ID = "c3e8da46"
PTERO_PANEL_URL = "https://control.qwertyx.host"

ADMIN_ID = 8493522297                         # Твой Telegram ID
# ===============================

cache = {"data": None, "time": 0}
chats = set()

async def send_command(command: str) -> str:
    """Отправляет команду на сервер через Pterodactyl API"""
    url = f"{PTERO_PANEL_URL}/api/client/servers/{PTERO_SERVER_ID}/command"
    headers = {
        "Authorization": f"Bearer {PTERO_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {"command": command}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 204:
                    return "✅ Команда отправлена"
                else:
                    text = await resp.text()
                    return f"❌ Ошибка {resp.status}: {text}"
        except Exception as e:
            return f"❌ Ошибка подключения: {e}"

def is_admin(update: Update) -> bool:
    return update.effective_user.id == ADMIN_ID

async def get_status():
    now = time.time()
    if cache["data"] and now - cache["time"] < 10:
        return cache["data"]
    try:
        server = JavaServer.lookup(SERVER_IP)
        status = await server.async_status()
        players_list = [p.name for p in status.players.sample] if status.players.sample else []
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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Статус", callback_data="status"),
         InlineKeyboardButton("📊 Онлайн", callback_data="online")],
        [InlineKeyboardButton("👥 Список игроков", callback_data="list"),
         InlineKeyboardButton("🖥️ IP", callback_data="ip")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules"),
         InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chats.add(update.effective_chat.id)
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
        await update.message.reply_text(f"⚠️ Имена скрыты\n📊 Онлайн: {data['players']}/{data['max']}")
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

async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📌 Твой ID: `{update.effective_user.id}`\n"
        f"ADMIN_ID в коде: `{ADMIN_ID}`\n"
        f"Совпадение: {'✅ ДА' if update.effective_user.id == ADMIN_ID else '❌ НЕТ'}"
    )

# ========== АДМИН-КОМАНДЫ (через API) ==========
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У тебя нет доступа к этой команде.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("❌ Используй: /ban <ник> [причина]")
        return
    nick = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Нарушение правил"
    result = await send_command(f"ban {nick} {reason}")
    await update.message.reply_text(f"✅ {result}\nИгрок {nick} забанен.\nПричина: {reason}")

async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У тебя нет доступа к этой команде.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Используй: /mute <ник> <время> [причина]\nПример: /mute Nikita 1h спам")
        return
    nick = context.args[0]
    duration = context.args[1]
    reason = " ".join(context.args[2:]) if len(context.args) > 2 else "Нарушение"
    result = await send_command(f"mute {nick} {duration} {reason}")
    await update.message.reply_text(f"🔇 {result}\nИгрок {nick} замучен на {duration}")

async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У тебя нет доступа к этой команде.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("❌ Используй: /unmute <ник>")
        return
    nick = context.args[0]
    result = await send_command(f"unmute {nick}")
    await update.message.reply_text(f"✅ {result}\nИгрок {nick} размучен.")

async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У тебя нет доступа к этой команде.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("❌ Используй: /kick <ник> [причина]")
        return
    nick = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Кик от администратора"
    result = await send_command(f"kick {nick} {reason}")
    await update.message.reply_text(f"👢 {result}\nИгрок {nick} кикнут.")

async def cmd_say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У тебя нет доступа к этой команде.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("❌ Используй: /say <сообщение>")
        return
    msg = " ".join(context.args)
    result = await send_command(f"say {msg}")
    await update.message.reply_text(f"📢 {result}")

async def cmd_list_rcon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У тебя нет доступа к этой команде.")
        return
    result = await send_command("list")
    await update.message.reply_text(f"📡 {result}\nСписок игроков появится в консоли сервера.")

async def cmd_admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У тебя нет доступа.")
        return
    help_text = """
⚙️ **Админ-команды через Telegram:**

/ban <ник> [причина] — забанить игрока
/mute <ник> <время> [причина] — замутить (1h, 30m, 1d)
/unmute <ник> — снять мут
/kick <ник> [причина] — кикнуть
/say <текст> — отправить сообщение в чат сервера
/list — кто онлайн на сервере (в консоль)
/adminhelp — это меню

Обычные команды (доступны всем):
/status — статус сервера
/online — онлайн
/ip — IP сервера
/rules — правила
/myid — узнать свой ID
"""
    await update.message.reply_text(help_text)

# ========== ОБРАБОТЧИК КНОПОК ==========
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
    
    # Обычные команды (доступны всем)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ip", cmd_ip))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("rules", cmd_rules))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("online", cmd_online))
    app.add_handler(CommandHandler("myid", cmd_myid))
    
    # Админ-команды (только для ADMIN_ID)
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("mute", cmd_mute))
    app.add_handler(CommandHandler("unmute", cmd_unmute))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("say", cmd_say))
    app.add_handler(CommandHandler("list", cmd_list_rcon))
    app.add_handler(CommandHandler("adminhelp", cmd_admin_help))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Бот запущен!")
    print(f"📡 Сервер: {SERVER_IP}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print(f"🔗 API панель: {PTERO_PANEL_URL}")
    print("🔐 Админ-команды работают через Pterodactyl API")
    
    app.run_polling()

if __name__ == "__main__":
    main()
