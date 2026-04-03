import os
import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Токен из переменной окружения (безопасно)
TOKEN = os.environ.get("TOKEN")

if not TOKEN:
    raise ValueError("Переменная TOKEN не установлена!")

# База данных
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

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Команда /start
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

# Добавление дохода
async def add_income_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите сумму дохода цифрами (например: 15000):")
    context.user_data['waiting_for_income'] = True

# Обработка введённой суммы
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

# Показать налог
async def my_tax(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    cursor.execute('SELECT income FROM users WHERE user_id = ?', (user_id,))
    income = cursor.fetchone()[0] or 0
    tax = int(income * 0.06)
    await query.edit_message_text(f"📊 Доход за месяц: {income} ₽\n💰 Налог 6%: {tax} ₽\n\n🗓 Заплатить до 25 числа.")

# Подписка
async def subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💎 *Подписка 199 ₽/мес*\n\n"
        "Что даёт:\n"
        "✅ Автоматический расчёт налога\n"
        "✅ Напоминалки об оплате\n"
        "✅ История доходов\n\n"
        "🔗 *Как оплатить:*\n"
        "Переведите 199 ₽ на карту *1234 5678 9012 3456* и напишите /confirm\n\n"
        "После подтверждения подписка активируется на 30 дней.",
        parse_mode="Markdown"
    )

# Подтверждение оплаты
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    until = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    cursor.execute('UPDATE users SET subscription_until = ? WHERE user_id = ?', (until, user_id))
    conn.commit()
    await update.message.reply_text("✅ Подписка активирована на 30 дней!")

# Запуск
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CallbackQueryHandler(add_income_callback, pattern="add_income"))
    app.add_handler(CallbackQueryHandler(my_tax, pattern="my_tax"))
    app.add_handler(CallbackQueryHandler(subscription, pattern="subscription"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
