import time
import asyncio
import urllib.request
import json
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
TOKEN = "8590452175:AAGcmk1Gn-GnVZbUUAvLTRhd3QBslVE5bFk"
SERVER_IP = "hi3.qwertyx.host:27228"

PTERO_API_KEY = "ptlc_j9A9o5AyW4N6MRkF4rs88WMY5DSKFFmAnaC5dxQ0lZF"
PTERO_SERVER_ID = "c3e8da46"
PTERO_PANEL_URL = "https://control.qwertyx.host"

ADMIN_ID = 8493522297
# ===============================

cache = {"data": None, "time": 0}
chats = set()

def send_command(command: str) -> str:
    url = f"{PTERO_PANEL_URL}/api/client/servers/{PTERO_SERVER_ID}/command"
    headers = {
        "Authorization": f"Bearer {PTERO_API_KEY}",
        "Content-Type": "application/json"
    }
    data = json.dumps({"command": command}).encode()
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=10) as resp:
            return "✅ Команда отправлена" if resp.status == 204 else f"❌ Ошибка {resp.status}"
    except Exception as e:
        return f"❌ Ошибка: {e}"

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
        }
        cache["data"] = data
        cache["time"] = now
        return data
    except:
        return {"online": False, "list": []}

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Статус", callback_data="status"),
         InlineKeyboardButton("📊 Онлайн", callback_data="online")],
        [InlineKeyboardButton("👥 Список", callback_data="list"),
         InlineKeyboardButton("🖥️ IP", callback_data="ip")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules"),
         InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chats.add(update.effective_chat.id)
    await update.message.reply_text("🎮 HazeSMP\n👇 Кнопки:", reply_markup=get_main_keyboard())

async def cmd_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🖥️ {SERVER_IP}")

async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📜 Правила:\n🚫 Не строй неприличные постройки\n🚫 Не задевай родню\n✅ Бан за нарушения")

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_status()
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
    elif data["players"] == 0:
        await update.message.reply_text("🌙 Никого нет")
    else:
        await update.message.reply_text(f"👥 {', '.join(data['list'])}")

async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Твой ID: {update.effective_user.id}")

async def cmd_say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    if not context.args:
        await update.message.reply_text("❌ /say текст")
        return
    result = send_command("say " + " ".join(context.args))
    await update.message.reply_text(f"📢 {result}")

async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    if len(context.args) < 1:
        await update.message.reply_text("❌ /ban ник")
        return
    result = send_command("ban " + " ".join(context.args))
    await update.message.reply_text(f"✅ {result}")

async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ /mute ник время")
        return
    result = send_command("mute " + " ".join(context.args))
    await update.message.reply_text(f"🔇 {result}")

async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    if len(context.args) < 1:
        await update.message.reply_text("❌ /unmute ник")
        return
    result = send_command("unmute " + " ".join(context.args))
    await update.message.reply_text(f"✅ {result}")

async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    if len(context.args) < 1:
        await update.message.reply_text("❌ /kick ник")
        return
    result = send_command("kick " + " ".join(context.args))
    await update.message.reply_text(f"👢 {result}")

async def cmd_list_rcon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    result = send_command("list")
    await update.message.reply_text(f"📡 {result}")

async def cmd_admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    await update.message.reply_text(
        "/ban ник - бан\n/mute ник время - мут\n/unmute ник - снять мут\n/kick ник - кик\n/say текст - написать в чат\n/list - список игроков"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = await get_status()
    action = query.data

    if action == "status":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        else:
            text = f"🟢 Работает\n📊 {data['players']}/{data['max']}\n🎮 {data['version']}\n📝 {data['motd']}"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())
    elif action == "online":
        text = f"📊 {data['players']}/{data['max']}" if data["online"] else "🔴 Выключен"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())
    elif action == "list":
        if not data["online"]:
            text = "🔴 Выключен"
        elif data["players"] == 0:
            text = "🌙 Никого нет"
        else:
            text = f"👥 {', '.join(data['list'])}"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())
    elif action == "ip":
        await query.edit_message_text(f"🖥️ {SERVER_IP}", reply_markup=get_main_keyboard())
    elif action == "rules":
        await query.edit_message_text("📜 Правила:\n🚫 Не строй неприличные постройки\n🚫 Не задевай родню", reply_markup=get_main_keyboard())
    elif action == "refresh":
        cache["data"] = None
        await query.edit_message_text("🔄...", reply_markup=get_main_keyboard())
        new_data = await get_status()
        if new_data["online"]:
            text = f"🟢 Работает\n📊 {new_data['players']}/{new_data['max']}"
        else:
            text = "🔴 Выключен"
        await query.edit_message_text(text, reply_markup=get_main_keyboard())

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_status()
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
    else:
        await update.message.reply_text(f"🟢 Работает\n📊 {data['players']}/{data['max']}\n🎮 {data['version']}\n📝 {data['motd']}")

async def cmd_online(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("say", cmd_say))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("mute", cmd_mute))
    app.add_handler(CommandHandler("unmute", cmd_unmute))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("list", cmd_list_rcon))
    app.add_handler(CommandHandler("adminhelp", cmd_admin_help))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("✅ Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
