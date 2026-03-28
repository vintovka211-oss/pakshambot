from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import *
from database import *
from keyboards import *
from games import play_slots, play_dice

class GameStates(StatesGroup):
    waiting_bet = State()

class DonateStates(StatesGroup):
    waiting_amount = State()
    waiting_method = State()

class WithdrawStates(StatesGroup):
    waiting_amount = State()

async def start_command(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    await update_user(user_id, username=message.from_user.username or str(user_id))
    
    await message.answer(
        f"🎮 **Добро пожаловать!**\n\n"
        f"👤 ID: {user_id}\n"
        f"💰 Баланс: {user['balance']}{CURRENCY}\n"
        f"💎 {COIN_NAME}: {user['pac_balance']}\n\n"
        f"Используйте кнопки ниже!",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = callback.data
    
    if data == "main_menu":
        user = await get_user(user_id)
        await callback.message.edit_text(
            f"👤 ID: {user_id}\n💰 Баланс: {user['balance']}{CURRENCY}\n💎 {COIN_NAME}: {user['pac_balance']}",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "games":
        await callback.message.edit_text("🎮 Выберите игру:", reply_markup=get_games_keyboard())
    
    elif data == "game_slots":
        await callback.message.answer("🎰 Введите сумму ставки:")
        await state.update_data(game="slots")
        await state.set_state(GameStates.waiting_bet)
    
    elif data == "game_dice":
        await callback.message.answer("🎲 Введите сумму ставки и число (1-6):")
        await state.update_data(game="dice")
        await state.set_state(GameStates.waiting_bet)
    
    elif data == "deposit":
        await callback.message.edit_text(
            f"💎 Введите сумму в {CURRENCY}:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(DonateStates.waiting_amount)
    
    elif data == "withdraw":
        user = await get_user(user_id)
        await callback.message.edit_text(
            f"💸 Баланс: {user['pac_balance']} {COIN_NAME}\nМин. вывод: {MIN_WITHDRAW_PAC} {COIN_NAME}\n\nВведите сумму:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(WithdrawStates.waiting_amount)
    
    elif data == "top":
        top = await get_top_users(10)
        text = "🏆 **ТОП-10:**\n"
        for i, (uid, name, val) in enumerate(top, 1):
            text += f"{i}. {name or uid} — {val}{CURRENCY}\n"
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    elif data == "help":
        text = "❓ **Помощь**\n\nИгры: Слоты, Кубик\nПополнение: кнопка Пополнить\nВывод: раз в неделю\nПремиум: шахта + бонусы"
        await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    
    await callback.answer()

async def handle_bet(message: types.Message, state: FSMContext):
    try:
        parts = message.text.split()
        bet = int(parts[0])
    except:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    game = data.get("game")
    user_id = message.from_user.id
    
    if game == "slots":
        win, result = await play_slots(user_id, bet)
        await message.answer(result)
    elif game == "dice":
        choice = int(parts[1]) if len(parts) > 1 else None
        win, result = await play_dice(user_id, bet, choice)
        await message.answer(result)
    
    await state.clear()

async def handle_donate_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
    except:
        await message.answer("❌ Введите число!")
        return
    await state.update_data(amount=amount)
    await message.answer("Выберите способ оплаты:", reply_markup=get_payment_keyboard())
    await state.set_state(DonateStates.waiting_method)

async def handle_donate_method(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[2]
    data = await state.get_data()
    amount = data.get("amount")
    success, req_id, pac = await create_deposit_request(callback.from_user.id, amount, method)
    if not success:
        await callback.answer("Ошибка!")
        return
    wallet = YOUR_WALLETS.get(method, "Уточните")
    await callback.message.edit_text(
        f"💎 Заявка #{req_id}\nСумма: {amount}₽ → {pac} {COIN_NAME}\nРеквизиты: {wallet}\nПосле оплаты /confirm_{req_id}"
    )
    await state.clear()

async def handle_withdraw_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
    except:
        await message.answer("❌ Введите число!")
        return
    success, result = await create_withdraw_request(message.from_user.id, amount)
    await message.answer(result)
    await state.clear()

async def confirm_deposit(message: types.Message):
    try:
        req_id = int(message.text.split("_")[1])
    except:
        await message.answer("❌ Используйте: /confirm_123")
        return
    success, result = await approve_deposit(req_id)
    await message.answer(result)