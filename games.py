import random
import asyncio
from config import COIN_NAME, MIN_BET
from database import get_user, update_user, add_transaction

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
async def get_win_chance(user_id):
    user = await get_user(user_id)
    consecutive_wins = user.get("consecutive_wins", 0)
    base_chance = 0.45
    chance = base_chance / (3 ** consecutive_wins)
    return max(chance, 0.01)

async def apply_win_reduction(user_id, won):
    user = await get_user(user_id)
    if won:
        await update_user(user_id, consecutive_wins=user.get("consecutive_wins", 0) + 1)
    else:
        await update_user(user_id, consecutive_wins=0)

async def show_animation(message, win_amount):
    frames = ["🎲", "🎰", "🎯", "💰", "💎", "🏆"]
    msg = await message.answer("🎲")
    for frame in frames:
        await msg.edit_text(frame)
        await asyncio.sleep(0.2)
    await msg.delete()
    await message.answer(f"🎉 **ПОБЕДА! +{win_amount} {COIN_NAME}!** 🎉", parse_mode="Markdown")

# ==================== КУБИК (ЧЁТ/НЕЧЁТ) ====================
async def play_dice_even_odd(user_id, bet, choice, message):
    user = await get_user(user_id)
    if bet < MIN_BET:
        return 0, f"❌ Минимальная ставка: {MIN_BET} {COIN_NAME}!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    dice_message = await message.answer_dice(emoji="🎲")
    await asyncio.sleep(2)
    dice = dice_message.dice.value
    
    is_even = dice % 2 == 0
    is_win = (choice == "even" and is_even) or (choice == "odd" and not is_even)
    
    chance = await get_win_chance(user_id)
    is_win = is_win and random.random() < chance
    
    if is_win:
        win = bet * 2
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "dice", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "dice_win", win, "Выигрыш")
    
    result_text = "ЧЁТНОЕ" if is_even else "НЕЧЁТНОЕ"
    if win > 0:
        return win, f"🎲 **Кубик**\n\nВыпало: **{dice}** ({result_text})\nВы выбрали: {'ЧЁТ' if choice == 'even' else 'НЕЧЁТ'}\n\n🎉 Вы угадали! +{win} {COIN_NAME}!"
    else:
        return 0, f"🎲 **Кубик**\n\nВыпало: **{dice}** ({result_text})\nВы выбрали: {'ЧЁТ' if choice == 'even' else 'НЕЧЁТ'}\n\n😔 Вы не угадали. -{bet} {COIN_NAME}."

# ==================== ОРЁЛ/РЕШКА ====================
async def play_coin(user_id, bet, choice):
    user = await get_user(user_id)
    if bet < MIN_BET:
        return 0, f"❌ Минимальная ставка: {MIN_BET} {COIN_NAME}!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    result = random.choice(["орел", "решка"])
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and choice == result
    
    if is_win:
        win = int(bet * 1.8)
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "coin", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "coin_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"🪙 **Орёл/Решка**\n\nВыпал: {result}\nВы выбрали: {choice}\n\n🎉 Вы угадали! +{win} {COIN_NAME}!"
    else:
        return 0, f"🪙 **Орёл/Решка**\n\nВыпал: {result}\nВы выбрали: {choice}\n\n😔 Вы не угадали. -{bet} {COIN_NAME}."

# ==================== МИНЫ 5x5 (ПРОГРЕССИВНЫЙ МНОЖИТЕЛЬ) ====================
async def play_mines(user_id, bet, message):
    user = await get_user(user_id)
    if bet < MIN_BET:
        return 0, f"❌ Минимальная ставка: {MIN_BET} {COIN_NAME}!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    # Создаём поле 5x5
    field = [[f"{i*5+j+1:2d}" for j in range(5)] for i in range(5)]
    mines = random.sample(range(25), 3)  # 3 мины
    opened = []
    current_multiplier = 1.0
    
    # Сохраняем состояние игры
    game_data = {
        "type": "mines",
        "bet": bet,
        "field": field,
        "mines": mines,
        "opened": opened,
        "multiplier": current_multiplier,
        "step": 0
    }
    
    from keyboards import get_mines_field_keyboard
    await message.edit_text(
        f"💣 **Мины 5x5**\n\n💰 Ставка: {bet} {COIN_NAME}\n🎁 Текущий множитель: x{current_multiplier:.2f}\n\nВыберите ячейку:",
        reply_markup=get_mines_field_keyboard(game_data),
        parse_mode="Markdown"
    )
    return game_data

async def mines_click(user_id, bet, cell, game_data, message):
    user = await get_user(user_id)
    mines = game_data["mines"]
    opened = game_data["opened"]
    step = game_data["step"]
    
    if cell in opened:
        await message.answer("❌ Вы уже открыли эту ячейку!", show_alert=True)
        return None
    
    if cell in mines:
        # Проигрыш
        await update_user(user_id, pac_balance=user["pac_balance"] - bet)
        await add_transaction(user_id, "mines_lose", -bet, f"Проигрыш в минах")
        await message.edit_text(
            f"💣 **Мины**\n\n💥 Вы наступили на мину!\n😔 Вы проиграли {bet} {COIN_NAME}!",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return None
    
    # Выигрышный ход
    opened.append(cell)
    step += 1
    
    # Расчёт множителя (увеличивается с каждым ходом)
    multipliers = [1.15, 1.30, 1.50, 1.80, 2.20, 2.70, 3.30, 4.00, 5.00, 6.50, 8.50, 11.00, 15.00]
    multiplier = multipliers[min(step, len(multipliers)-1)]
    
    game_data["step"] = step
    game_data["multiplier"] = multiplier
    
    if step >= 10 or len(opened) + len(mines) >= 25:
        # Победа
        win = int(bet * multiplier)
        await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
        await add_transaction(user_id, "mines_win", win, f"Выигрыш в минах")
        await message.edit_text(
            f"💣 **Мины**\n\n🎉 ПОБЕДА! Вы открыли {step} ячеек!\n💰 Выигрыш: {win} {COIN_NAME}!\n🎁 Множитель: x{multiplier:.2f}",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return None
    
    from keyboards import get_mines_field_keyboard
    await message.edit_text(
        f"💣 **Мины**\n\n💰 Ставка: {bet} {COIN_NAME}\n🎁 Текущий множитель: x{multiplier:.2f}\n✅ Открыто: {len(opened)} ячеек\n\nВыберите следующую ячейку:",
        reply_markup=get_mines_field_keyboard(game_data),
        parse_mode="Markdown"
    )
    return game_data

# ==================== БАШНЯ ====================
async def play_tower(user_id, bet, message):
    user = await get_user(user_id)
    if bet < MIN_BET:
        return 0, f"❌ Минимальная ставка: {MIN_BET} {COIN_NAME}!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    # Создаём башню 8 уровней
    levels = []
    for i in range(8):
        mines_count = random.randint(1, 3)  # 1-3 мины на уровне
        level = {
            "mines": random.sample(range(5), mines_count),
            "selected": None
        }
        levels.append(level)
    
    game_data = {
        "type": "tower",
        "bet": bet,
        "levels": levels,
        "current_level": 0,
        "multiplier": 1.0,
        "won": False
    }
    
    multipliers = [1.30, 1.80, 2.30, 3.00, 4.00, 5.50, 7.50, 10.00]
    
    from keyboards import get_tower_level_keyboard
    await message.edit_text(
        f"🗼 **Башня**\n\n💰 Ставка: {bet} {COIN_NAME}\n🏆 Уровень: 1/8\n🎁 Множитель: x{multipliers[0]:.2f}\n\nВыберите путь (1-5):",
        reply_markup=get_tower_level_keyboard(game_data),
        parse_mode="Markdown"
    )
    return game_data

async def tower_click(user_id, bet, choice, game_data, message):
    user = await get_user(user_id)
    level_idx = game_data["current_level"]
    level = game_data["levels"][level_idx]
    
    if choice in level["mines"]:
        # Проигрыш
        await update_user(user_id, pac_balance=user["pac_balance"] - bet)
        await add_transaction(user_id, "tower_lose", -bet, f"Проигрыш в башне")
        await message.edit_text(
            f"🗼 **Башня**\n\n💥 Вы наступили на мину на уровне {level_idx+1}!\n😔 Вы проиграли {bet} {COIN_NAME}!",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return None
    
    # Выигрышный ход
    level["selected"] = choice
    game_data["current_level"] += 1
    
    multipliers = [1.30, 1.80, 2.30, 3.00, 4.00, 5.50, 7.50, 10.00]
    current_multiplier = multipliers[game_data["current_level"]]
    
    if game_data["current_level"] >= 8:
        # Полная победа
        win = int(bet * current_multiplier)
        await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
        await add_transaction(user_id, "tower_win", win, f"Выигрыш в башне")
        await message.edit_text(
            f"🗼 **Башня**\n\n🎉 ПОЛНАЯ ПОБЕДА! Вы прошли все 8 уровней!\n💰 Выигрыш: {win} {COIN_NAME}!\n🎁 Множитель: x{current_multiplier:.2f}",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return None
    
    from keyboards import get_tower_level_keyboard
    await message.edit_text(
        f"🗼 **Башня**\n\n💰 Ставка: {bet} {COIN_NAME}\n🏆 Уровень: {game_data['current_level']+1}/8\n🎁 Множитель: x{current_multiplier:.2f}\n✅ Выбрано: путь {choice+1}\n\nВыберите следующий путь:",
        reply_markup=get_tower_level_keyboard(game_data),
        parse_mode="Markdown"
    )
    return game_data
