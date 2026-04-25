import time
import asyncio
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import socket
import struct

# ========== НАСТРОЙКИ ==========
TOKEN = "8590452175:AAGcmk1Gn-GnVZbUUAvLTRhd3QBslVE5bFk"
SERVER_IP = "hi3.qwertyx.host:27228"

# RCON настройки
RCON_HOST = "hi3.qwertyx.host"
RCON_PORT = 25575
RCON_PASS = "hazesmppassword"

# Твой Telegram ID (только ты можешь использовать админ-команды)
ADMIN_ID = 8493522297
# ===============================

cache = {"data": None, "time": 0}
chats = set()

# Простой RCON клиент
class SimpleRCON:
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.sock = None
        self.request_id = 0
    
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.host, self.port))
            self._send(3, self.password.encode('utf8'))
            response = self._receive()
            return response[0] == 2
        except:
            return False
    
    def _send(self, cmd_type, data):
        self.request_id += 1
        body = struct.pack('<ii', self.request_id, cmd_type) + data + b'\x00\x00'
        packet = struct.pack('<i', len(body)) + body
        self.sock.send(packet)
    
    def _receive(self):
        len_data = self.sock.recv(4)
        if len(len_data) < 4:
            return None
        packet_len = struct.unpack('<i', len_data)[0]
        packet = self.sock.recv(packet_len)
        request_id, cmd_type = struct.unpack('<ii', packet[:8])
        data = packet[8:-2].decode('utf8', errors='ignore')
        return (request_id, cmd_type, data)
    
    def command(self, cmd):
        if not self.connect():
            return "❌ Ошибка подключения к RCON"
        self._send(2, cmd.encode('utf8'))
        resp = self._receive()
        self.sock.close()
        return resp[2] if resp else "❌ Нет ответа от сервера"

rcon = SimpleRCON(RCON_HOST, RCON_PORT, RCON_PASS)

def run_rcon(command: str) -> str:
    try:
        return rcon.command(command)
    except Exception as e:
        return f"Ошибка Rcon: {e}"

def is_admin(update: Update) -> bool:
    """Проверяет, является ли отправитель админом"""
    return update.effective_user.id == ADMIN_ID

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

# ========== ОТЛАДОЧНАЯ КОМАНДА ==========
async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    is_admin = (user_id == ADMIN_ID)
    
    await update.message.reply_text(
        f"📌 **Отладка:**\n"
        f"Твой ID: `{user_id}`\n"
        f"ADMIN_ID в коде: `{ADMIN_ID}`\n"
        f"Совпадение: {'✅ ДА' if is_admin else '❌ НЕТ'}\n"
        f"Ты можешь использовать админ-команды: {'✅ ДА' if is_admin else '❌ НЕТ'}"
    )

# ========== АДМИН-КОМАНДЫ (только для ADMIN_ID, работают в любом чате) ==========
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У тебя нет доступа к этой команде.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("❌ Используй: /ban <ник> [причина]")
        return
    nick = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Нарушение правил"
    res = run_rcon(f"ban {nick} {reason}")
    await update.message.reply_text(f"✅ Игрок {nick} забанен.\nПричина: {reason}")

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
    res = run_rcon(f"mute {nick} {duration} {reason}")
    await update.message.reply_text(f"🔇 Игрок {nick} замучен на {duration}")

async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У тебя нет доступа к этой команде.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("❌ Используй: /unmute <ник>")
        return
    nick = context.args[0]
    res = run_rcon(f"unmute {nick}")
    await update.message.reply_text(f"✅ Игрок {nick} размучен.")

async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У тебя нет доступа к этой команде.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("❌ Используй: /kick <ник> [причина]")
        return
    nick = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Кик от администратора"
    res = run_rcon(f"kick {nick} {reason}")
    await update.message.reply_text(f"👢 Игрок {nick} кикнут.")

async def cmd_say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У тебя нет доступа к этой команде.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("❌ Используй: /say <сообщение>")
        return
    msg = " ".join(context.args)
    res = run_rcon(f"say {msg}")
    await update.message.reply_text(f"📢 Сообщение отправлено в чат сервера.")

async def cmd_list_rcon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ У тебя нет доступа к этой команде.")
        return
    res = run_rcon("list")
    await update.message.reply_text(f"📡 {res}")

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
/list — кто онлайн на сервере (через RCON)
/adminhelp — это меню

Обычные команды (доступны всем):
/status — статус сервера
/online — онлайн
/ip — IP сервера
/rules — правила
/myid — узнать свой ID
"""
    await update.message.reply_text(help_text)

# ===================================================

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
    print("🔐 Админ-команды работают в любом чате, но только для твоего ID")
    
    app.run_polling()

if __name__ == "__main__":
    main()
