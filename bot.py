import os
import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== НАСТРОЙКИ =====
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("Переменная TOKEN не установлена!")

# ВАШ TELEGRAM ID (только вы можете активировать подписку)
ADMIN_ID = 8493522297

# НОМЕР ТЕЛЕФОНА ДЛЯ ОПЛАТЫ (ЗАМЕНИТЕ НА СВОЙ)
PHONE_NUMBER = "+79276685512"  # 👈 ВСТАВЬТЕ СВОЙ НОМЕР

# ===== БАЗА ДАННЫХ =====
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        income INTEGER DEFAULT 0,
        subscription_until TEXT
    )
''')
conn.commit()

# ===== ЛОГИРОВАНИЕ =====
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ===== КОМАНДА /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "NoUsername"
    
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить доход", callback_data="add_income")],
        [InlineKeyboardButton("📊 Мой налог за месяц", callback_data="my_tax")],
        [InlineKeyboardButton("💎 Подписка 199 ₽/мес", callback_data="subscription")]
    ]
    await update.message.reply_text(
        "🤖 *Налоговый помощник для самозанятых*\n\n"
        "Я считаю налог 6% от вашего дохода.\n\n"
        "🔓 *Бесплатно:* ручной ввод суммы\n"
        "💎 *Подписка 199 ₽/мес:* авторасчёт + напоминалки\n\n"
        "Нажмите «Добавить доход» и введите сумму.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===== ДОБАВЛЕНИЕ ДОХОДА =====
async def add_income_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите сумму дохода цифрами (например: 15000):")
    context.user_data['waiting_for_income'] = True

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for_income'):
        try:
            amount = int(update.message.text.replace(' ', ''))
            user_id = update.effective_user.id
            cursor.execute('UPDATE users SET income = income + ? WHERE user_id = ?', (amount, user_id))
            conn.commit()
            await update.message.reply_text(f"✅ Добавлено {amount} ₽")
            context.user_data['waiting_for_income'] = False
        except:
            await update.message.reply_text("❌ Ошибка. Введите число без букв.")

# ===== МОЙ НАЛОГ =====
async def my_tax(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    cursor.execute('SELECT income FROM users WHERE user_id = ?', (user_id,))
    income = cursor.fetchone()[0] or 0
    tax = int(income * 0.06)
    await query.edit_message_text(
        f"📊 *Доход за месяц:* {income} ₽\n"
        f"💰 *Налог 6%:* {tax} ₽\n\n"
        f"🗓 Заплатить до 25 числа.",
        parse_mode="Markdown"
    )

# ===== ПОДПИСКА (ОПЛАТА ПО СБП) =====
async def subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    
    await query.edit_message_text(
        f"💎 *Подписка 199 ₽/мес*\n\n"
        f"Что даёт:\n"
        f"✅ Автоматический расчёт налога за месяц\n"
        f"✅ Напоминалки об оплате до 25 числа\n"
        f"✅ История всех доходов\n\n"
        f"🔐 *Как оплатить:*\n"
        f"1️⃣ Переведите 199 ₽ по номеру телефона:\n"
        f"`{PHONE_NUMBER}`\n\n"
        f"2️⃣ После оплаты пришлите скриншот чека сюда\n"
        f"3️⃣ Я активирую подписку вручную\n\n"
        f"✅ Подписка будет активна 30 дней\n\n"
        f"⏱ Обычно активирую в течение часа в рабочее время",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===== АКТИВАЦИЯ ПОДПИСКИ (ТОЛЬКО ДЛЯ АДМИНА) =====
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Проверка: только админ может активировать подписку
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для этой команды.\n\nЕсли вы оплатили подписку, отправьте чек сюда — я активирую вручную.")
        return
    
    # Получаем ID пользователя из команды /confirm 123456789
    args = context.args
    if not args:
        await update.message.reply_text(
            "ℹ️ *Как активировать подписку:*\n\n"
            "1. Узнайте ID пользователя (он виден в переписке или через @userinfobot)\n"
            "2. Напишите: `/confirm 123456789`\n\n"
            "Где 123456789 — ID пользователя",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_user_id = int(args[0])
        until = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute('UPDATE users SET subscription_until = ? WHERE user_id = ?', (until, target_user_id))
        conn.commit()
        await update.message.reply_text(f"✅ Подписка активирована для пользователя `{target_user_id}` на 30 дней!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}\nУбедитесь, что ID правильный.")

# ===== КНОПКА НАЗАД =====
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить доход", callback_data="add_income")],
        [InlineKeyboardButton("📊 Мой налог за месяц", callback_data="my_tax")],
        [InlineKeyboardButton("💎 Подписка 199 ₽/мес", callback_data="subscription")]
    ]
    
    await query.edit_message_text(
        "🤖 *Налоговый помощник для самозанятых*\n\n"
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===== ЗАПУСК БОТА =====
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CallbackQueryHandler(add_income_callback, pattern="add_income"))
    app.add_handler(CallbackQueryHandler(my_tax, pattern="my_tax"))
    app.add_handler(CallbackQueryHandler(subscription, pattern="subscription"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="back_to_menu"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ Бот запущен и работает...")
    app.run_polling()

if __name__ == "__main__":
    main()
