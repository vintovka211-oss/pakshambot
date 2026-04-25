import time
import asyncio
import socket
import struct
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==================================================
# 1. НАСТРОЙКИ (ЗАМЕНИ НА СВОИ)
# ==================================================
TOKEN = "8590452175:AAGcmk1Gn-GnVZbUUAvLTRhd3QBslVE5bFk"   # Токен бота (получи у @BotFather)
SERVER_IP = "hi3.qwertyx.host:27228"              # IP твоего сервера

# RCON настройки (уже должны быть в server.properties на сервере)
RCON_HOST = "hi3.qwertyx.host"     # IP сервера
RCON_PORT = 27562                   # Порт RCON (как в server.properties)
RCON_PASS = "hazesmppassword"       # Пароль RCON (как в server.properties)

# Твой Telegram ID (команды бана/мута будут доступны только тебе)
ADMIN_ID = 8493522297
# ==================================================

# Кэш для статуса сервера (чтобы не дёргать постоянно)
cache = {"data": None, "time": 0}
chats = set()  # Список чатов, где запущен бот

# ==================================================
# 2. КЛАСС ДЛЯ RCON (подключение к серверу Minecraft)
# ==================================================
class Rcon:
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
            self._send(3, self.password.encode('utf-8'))
            response = self._receive()
            return response and response[0] == 2
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
        data = packet[8:-2].decode('utf-8', errors='ignore')
        return (request_id, cmd_type, data)

    def command(self, cmd):
        if not self.connect():
            return "❌ RCON не подключён. Проверь файл server.properties и перезапусти сервер."
        self._send(2, cmd.encode('utf-8'))
        resp = self._receive()
        self.sock.close()
        return resp[2] if resp else "❌ Нет ответа от сервера"

# Создаём объект RCON
rcon = Rcon(RCON_HOST, RCON_PORT, RCON_PASS)

def send_command(cmd):
    """Отправляет команду на сервер через RCON"""
    return rcon.command(cmd)

def is_admin(update):
    """Проверяет, является ли отправитель админом"""
    return update.effective_user.id == ADMIN_ID

# ==================================================
# 3. СТАТУС СЕРВЕРА (пинг, онлайн, motd)
# ==================================================
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

# ==================================================
# 4. КНОПКИ ДЛЯ ТЕЛЕГРАМ
# ==================================================
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Статус", callback_data="status"),
         InlineKeyboardButton("📊 Онлайн", callback_data="online")],
        [InlineKeyboardButton("👥 Список", callback_data="list"),
         InlineKeyboardButton("🖥️ IP", callback_data="ip")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules"),
         InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]
    ])

# ==================================================
# 5. ОБЫЧНЫЕ КОМАНДЫ (доступны всем)
# ==================================================
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
        "🚫 Не строить неприличные постройки (писюны, свастики)\n"
        "🚫 Не оскорблять и не задевать родню игроков\n"
        "✅ Нарушители получают бан навсегда!"
    )

async def cmd_myid(update, context):
    await update.message.reply_text(f"🆔 Твой Telegram ID: {update.effective_user.id}")

# ==================================================
# 6. АДМИН-КОМАНДЫ (только для ADMIN_ID, через RCON)
# ==================================================
async def cmd_say(update, context):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    if not context.args:
        await update.message.reply_text("❌ /say текст")
        return
    msg = " ".join(context.args)
    result = send_command(f"say {msg}")
    await update.message.reply_text(f"📢 {result}")

async def cmd_ban(update, context):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    if not context.args:
        await update.message.reply_text("❌ /ban ник [причина]")
        return
    result = send_command("ban " + " ".join(context.args))
    await update.message.reply_text(f"✅ {result}")

async def cmd_mute(update, context):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ /mute ник время (1h, 30m, 1d)")
        return
    result = send_command("mute " + " ".join(context.args))
    await update.message.reply_text(f"🔇 {result}")

async def cmd_unmute(update, context):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    if not context.args:
        await update.message.reply_text("❌ /unmute ник")
        return
    result = send_command("unmute " + " ".join(context.args))
    await update.message.reply_text(f"✅ {result}")

async def cmd_kick(update, context):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    if not context.args:
        await update.message.reply_text("❌ /kick ник [причина]")
        return
    result = send_command("kick " + " ".join(context.args))
    await update.message.reply_text(f"👢 {result}")

async def cmd_list_rcon(update, context):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    result = send_command("list")
    await update.message.reply_text(f"📡 {result}")

async def cmd_admin_help(update, context):
    if not is_admin(update):
        await update.message.reply_text("⛔ Нет доступа")
        return
    await update.message.reply_text(
        "⚙️ АДМИН-КОМАНДЫ (только для тебя):\n"
        "/ban ник — бан игрока\n"
        "/mute ник время — мут (1h, 30m, 1d)\n"
        "/unmute ник — снять мут\n"
        "/kick ник — кикнуть\n"
        "/say текст — написать в чат сервера\n"
        "/list — список игроков в консоль\n"
        "/adminhelp — это меню"
    )

# ==================================================
# 7. КНОПКИ МЕНЮ (обработчик)
# ==================================================
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
        await query.edit_message_text(
            "📜 ПРАВИЛА HazeSMP\n\n🚫 Не строй неприличные постройки\n🚫 Не задевай родню\n✅ Бан за нарушения",
            reply_markup=get_keyboard()
        )
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

# ==================================================
# 8. ЗАПУСК БОТА
# ==================================================
def main():
    app = Application.builder().token(TOKEN).build()

    # Команды для всех
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ip", cmd_ip))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("rules", cmd_rules))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("online", cmd_online))
    app.add_handler(CommandHandler("myid", cmd_myid))

    # Админ-команды
    app.add_handler(CommandHandler("say", cmd_say))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("mute", cmd_mute))
    app.add_handler(CommandHandler("unmute", cmd_unmute))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("list", cmd_list_rcon))
    app.add_handler(CommandHandler("adminhelp", cmd_admin_help))

    # Кнопки
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Бот запущен!")
    print(f"📡 Сервер: {SERVER_IP}")
    print(f"👑 Твой ID: {ADMIN_ID}")
    app.run_polling()

if __name__ == "__main__":
    main()
