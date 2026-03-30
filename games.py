import random
import asyncio
from config import *

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
async def get_win_chance(user_id):
    from database import get_user
    user = await get_user(user_id)
    consecutive_wins = user.get("consecutive_wins", 0)
    base_chance = 0.45
    chance = base_chance / (3 ** consecutive_wins)
    return max(chance, 0.01)

async def apply_win_reduction(user_id, won):
    from database import get_user, update_user
    user = await get_user(user_id)
    if won:
        await update_user(user_id, consecutive_wins=user.get("consecutive_wins", 0) + 1)
    else:
        await update_user(user_id, consecutive_wins=0)

# ==================== СЛОТЫ (КАК В WINPACO) ====================
async def play_slots(user_id, bet, message):
    from database import get_user, update_user, add_transaction
    user = await get_user(user_id)
    if bet < MIN_BET:
        return 0, f"❌ Минимальная ставка: {MIN_BET} {COIN_NAME}!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    # Анимация
    frames = ["🎰", "🌀", "🎲", "🎯"]
    msg = await message.answer("🎰")
    for frame in frames:
        await msg.edit_text(frame)
        await asyncio.sleep(0.3)
    await msg.delete()
    
    # Результат
    result = [random.choice(SLOTS_SYMBOLS) for _ in range(3)]
    
    # Проверка выигрыша
    win = 0
    key = tuple(result)
    if key in SLOTS_MULTIPLIERS:
        win = bet * SLOTS_MULTIPLIERS[key]
    
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and win > 0
    
    if not is_win:
        win = 0
    
    await apply_win_reduction(user_id, win > 0)
    
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "slots", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "slots_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"🎰 **Слоты**\n\n{result[0]} | {result[1]} | {result[2]}\n\n🎉 Вы выиграли {win} {COIN_NAME}!"
    else:
        return 0, f"🎰 **Слоты**\n\n{result[0]} | {result[1]} | {result[2]}\n\n😔 Вы проиграли {bet} {COIN_NAME}."

# ==================== КУБИК (КАК В WINPACO) ====================
async def play_dice(user_id, bet, choice, message):
    from database import get_user, update_user, add_transaction
    user = await get_user(user_id)
    if bet < MIN_BET:
        return 0, f"❌ Минимальная ставка: {MIN_BET} {COIN_NAME}!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    dice_message = await message.answer_dice(emoji="🎲")
    await asyncio.sleep(2)
    dice = dice_message.dice.value
    
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and choice == dice
    
    if is_win:
        win = bet * DICE_MULTIPLIER
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "dice", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "dice_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"🎲 **Кубик**\n\nВыпало: **{dice}**\nВаше число: **{choice}**\n\n🎉 Вы угадали! +{win} {COIN_NAME}!"
    else:
        return 0, f"🎲 **Кубик**\n\nВыпало: **{dice}**\nВаше число: **{choice}**\n\n😔 Вы не угадали. -{bet} {COIN_NAME}."

# ==================== РУЛЕТКА (КАК В WINPACO) ====================
async def play_roulette(user_id, bet, color_choice, message):
    from database import get_user, update_user, add_transaction
    user = await get_user(user_id)
    if bet < MIN_BET:
        return 0, f"❌ Минимальная ставка: {MIN_BET} {COIN_NAME}!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    frames = ["🎡", "🌀", "🎲", "🎯"]
    msg = await message.answer("🎡")
    for frame in frames:
        await msg.edit_text(frame)
        await asyncio.sleep(0.3)
    await msg.delete()
    
    # Результат (48% красное, 48% чёрное, 4% зелёное)
    colors = ["🔴", "⚫", "🟢"]
    result = random.choices(colors, weights=[48, 48, 4])[0]
    
    chance = await get_win_chance(user_id)
    
    if result == "🟢" and color_choice == "🟢":
        win = bet * ROULETTE_GREEN_MULTIPLIER
        is_win = random.random() < chance
    elif result == color_choice:
        win = bet * ROULETTE_MULTIPLIER
        is_win = random.random() < chance
    else:
        win = 0
        is_win = False
    
    if is_win:
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "roulette", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "roulette_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"🎡 **Рулетка**\n\nВыпало: {result}\nВы выбрали: {color_choice}\n\n🎉 Вы выиграли {win} {COIN_NAME}!"
    else:
        return 0, f"🎡 **Рулетка**\n\nВыпало: {result}\nВы выбрали: {color_choice}\n\n😔 Вы проиграли {bet} {COIN_NAME}."

# ==================== ОРЁЛ/РЕШКА (КАК В WINPACO) ====================
async def play_coin(user_id, bet, choice):
    from database import get_user, update_user, add_transaction
    user = await get_user(user_id)
    if bet < MIN_BET:
        return 0, f"❌ Минимальная ставка: {MIN_BET} {COIN_NAME}!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    result = random.choice(["орел", "решка"])
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and choice == result
    
    if is_win:
        win = int(bet * COIN_MULTIPLIER)
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

# ==================== МИНЫ (КАК В WINPACO) ====================
async def play_mines(user_id, bet, message):
    from database import get_user, update_user, add_transaction
    user = await get_user(user_id)
    if bet < MIN_BET:
        await message.edit_text(f"❌ Минимальная ставка: {MIN_BET} {COIN_NAME}!", reply_markup=get_back_keyboard())
        return None
    if user["pac_balance"] < bet:
        await message.edit_text("❌ Недостаточно PAC!", reply_markup=get_back_keyboard())
        return None
    
    # Создаём поле 5x5
    mines = random.sample(range(25), 3)
    opened = []
    
    game_data = {
        "type": "mines",
        "bet": bet,
        "mines": mines,
        "opened": opened,
        "multipliers": MINES_MULTIPLIERS,
        "step": 0
    }
    
    from keyboards import get_mines_field_keyboard
    await message.edit_text(
        f"💣 **Мины**\n\n"
        f"💰 Ставка: {bet} {COIN_NAME}\n"
        f"🎁 Текущий множитель: x{MINES_MULTIPLIERS[0]:.2f}\n"
        f"💣 Мин на поле: 3\n"
        f"✅ Открыто: 0/25\n\n"
        f"**Выберите ячейку:**",
        reply_markup=get_mines_field_keyboard(game_data),
        parse_mode="Markdown"
    )
    return game_data

async def mines_click(user_id, cell, game_data, message):
    from database import get_user, update_user, add_transaction
    user = await get_user(user_id)
    bet = game_data["bet"]
    mines = game_data["mines"]
    opened = game_data["opened"]
    step = game_data["step"]
    multipliers = game_data["multipliers"]
    
    if cell in opened:
        await message.answer("❌ Вы уже открыли эту ячейку!", show_alert=True)
        return game_data
    
    if cell in mines:
        # Проигрыш
        await update_user(user_id, pac_balance=user["pac_balance"] - bet)
        await add_transaction(user_id, "mines_lose", -bet, f"Проигрыш в минах")
        
        from keyboards import get_mines_result_keyboard
        await message.edit_text(
            f"💣 **Мины**\n\n"
            f"💥 **ВЫ ПРОИГРАЛИ!**\n\n"
            f"💰 Ставка: {bet} {COIN_NAME}\n"
            f"💀 Вы наступили на мину!\n\n"
            f"😔 Вы проиграли {bet} {COIN_NAME}!",
            reply_markup=get_mines_result_keyboard(game_data),
            parse_mode="Markdown"
        )
        return None
    
    # Выигрышный ход
    opened.append(cell)
    step += 1
    
    game_data["step"] = step
    
    if step >= len(multipliers):
        # Полная победа
        win = int(bet * multipliers[-1])
        await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
        await add_transaction(user_id, "mines_win", win, f"Выигрыш в минах")
        
        await message.edit_text(
            f"💣 **Мины**\n\n"
            f"🎉 **ПОБЕДА!** 🎉\n\n"
            f"💰 Ставка: {bet} {COIN_NAME}\n"
            f"🎁 Множитель: x{multipliers[-1]:.2f}\n"
            f"✅ Открыто: {len(opened)}/25\n\n"
            f"✨ Вы выиграли {win} {COIN_NAME}!",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return None
    
    from keyboards import get_mines_field_keyboard
    current_multiplier = multipliers[step]
    await message.edit_text(
        f"💣 **Мины**\n\n"
        f"💰 Ставка: {bet} {COIN_NAME}\n"
        f"🎁 Текущий множитель: x{current_multiplier:.2f}\n"
        f"💣 Мин на поле: 3\n"
        f"✅ Открыто: {len(opened)}/25\n\n"
        f"**Выберите следующую ячейку:**",
        reply_markup=get_mines_field_keyboard(game_data),
        parse_mode="Markdown"
    )
    return game_data

async def mines_cashout(user_id, bet, step, multiplier, message):
    from database import get_user, update_user, add_transaction
    win = int(bet * multiplier)
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "mines_win", win, f"Выигрыш в минах")
    
    await message.edit_text(
        f"💣 **Мины**\n\n"
        f"💰 **ВЫ ЗАБРАЛИ ВЫИГРЫШ!**\n\n"
        f"💰 Ставка: {bet} {COIN_NAME}\n"
        f"🎁 Множитель: x{multiplier:.2f}\n"
        f"✅ Открыто: {step} ячеек\n\n"
        f"🎉 Вы выиграли {win} {COIN_NAME}!",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )

# ==================== БАШНЯ (КАК В WINPACO) ====================
async def play_tower(user_id, bet, message):
    from database import get_user, update_user, add_transaction
    user = await get_user(user_id)
    if bet < MIN_BET:
        await message.edit_text(f"❌ Минимальная ставка: {MIN_BET} {COIN_NAME}!", reply_markup=get_back_keyboard())
        return None
    if user["pac_balance"] < bet:
        await message.edit_text("❌ Недостаточно PAC!", reply_markup=get_back_keyboard())
        return None
    
    # Создаём башню 8 уровней
    levels = []
    for i in range(8):
        # На каждом уровне 3 мины (иногда 2)
        mines_count = 3 if random.random() > 0.1 else 2
        mines = random.sample(range(5), mines_count)
        levels.append({
            "mines": mines,
            "selected": None,
            "revealed": False
        })
    
    game_data = {
        "type": "tower",
        "bet": bet,
        "levels": levels,
        "current_level": 0,
        "multipliers": TOWER_MULTIPLIERS,
        "won": False
    }
    
    from keyboards import get_tower_keyboard
    await message.edit_text(
        f"🗼 **Башня**\n\n"
        f"💰 Ставка: {bet} {COIN_NAME}\n"
        f"🏆 Уровень: 1/8\n"
        f"🎁 Множитель: x{TOWER_MULTIPLIERS[0]:.2f}\n\n"
        f"**Выберите путь (1-5):**",
        reply_markup=get_tower_keyboard(game_data),
        parse_mode="Markdown"
    )
    return game_data

async def tower_click(user_id, choice, game_data, message):
    from database import get_user, update_user, add_transaction
    user = await get_user(user_id)
    bet = game_data["bet"]
    level_idx = game_data["current_level"]
    level = game_data["levels"][level_idx]
    
    level["selected"] = choice
    level["revealed"] = True
    
    if choice in level["mines"]:
        # Проигрыш
        await update_user(user_id, pac_balance=user["pac_balance"] - bet)
        await add_transaction(user_id, "tower_lose", -bet, f"Проигрыш в башне на уровне {level_idx+1}")
        
        from keyboards import get_tower_result_keyboard
        await message.edit_text(
            f"🗼 **Башня**\n\n"
            f"💥 **ВЫ ПРОИГРАЛИ!**\n\n"
            f"🏆 Уровень: {level_idx+1}/8\n"
            f"💰 Ставка: {bet} {COIN_NAME}\n"
            f"💀 Вы наступили на мину в пути {choice+1}!\n\n"
            f"😔 Вы проиграли {bet} {COIN_NAME}!",
            reply_markup=get_tower_result_keyboard(game_data),
            parse_mode="Markdown"
        )
        return None
    
    game_data["current_level"] += 1
    
    if game_data["current_level"] >= 8:
        # Полная победа
        win = int(bet * TOWER_MULTIPLIERS[7])
        await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
        await add_transaction(user_id, "tower_win", win, f"Выигрыш в башне")
        
        await message.edit_text(
            f"🗼 **Башня**\n\n"
            f"🎉 **ПОЛНАЯ ПОБЕДА!** 🎉\n\n"
            f"🏆 Уровни пройдены: 8/8\n"
            f"💰 Ставка: {bet} {COIN_NAME}\n"
            f"🎁 Множитель: x{TOWER_MULTIPLIERS[7]:.2f}\n\n"
            f"✨ Вы выиграли {win} {COIN_NAME}!",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return None
    
    from keyboards import get_tower_keyboard
    current_multiplier = TOWER_MULTIPLIERS[game_data["current_level"]]
    await message.edit_text(
        f"🗼 **Башня**\n\n"
        f"✅ **Уровень {level_idx+1} пройден!**\n"
        f"Вы выбрали путь {choice+1} - БЕЗОПАСНО!\n\n"
        f"💰 Ставка: {bet} {COIN_NAME}\n"
        f"🏆 Уровень: {game_data['current_level']+1}/8\n"
        f"🎁 Множитель: x{current_multiplier:.2f}\n\n"
        f"**Выберите следующий путь (1-5):**",
        reply_markup=get_tower_keyboard(game_data),
        parse_mode="Markdown"
    )
    return game_data

async def tower_cashout(user_id, bet, current_level, multiplier, message):
    from database import get_user, update_user, add_transaction
    win = int(bet * multiplier)
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "tower_win", win, f"Выигрыш в башне на уровне {current_level+1}")
    
    await message.edit_text(
        f"🗼 **Башня**\n\n"
        f"💰 **ВЫ ЗАБРАЛИ ВЫИГРЫШ!**\n\n"
        f"🏆 Уровень пройден: {current_level+1}/8\n"
        f"💰 Ставка: {bet} {COIN_NAME}\n"
        f"🎁 Множитель: x{multiplier:.2f}\n\n"
        f"🎉 Вы выиграли {win} {COIN_NAME}!",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )
