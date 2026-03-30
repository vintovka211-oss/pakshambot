import random
import asyncio
from config import MIN_BET, COIN_NAME
from database import get_user, update_user, add_transaction

# ==================== МИНЫ (КАК В WINPACO) ====================
async def play_mines(user_id, bet, message):
    user = await get_user(user_id)
    if bet < MIN_BET:
        await message.edit_text(f"❌ Минимальная ставка: {MIN_BET} {COIN_NAME}!", reply_markup=get_back_keyboard())
        return None
    if user["pac_balance"] < bet:
        await message.edit_text("❌ Недостаточно PAC!", reply_markup=get_back_keyboard())
        return None
    
    # Поле 5x5
    mines = random.sample(range(25), 3)  # 3 мины
    opened = []
    multipliers = [1.15, 1.30, 1.50, 1.80, 2.20, 2.70, 3.30, 4.00, 5.00, 6.50, 8.50, 11.00, 15.00]
    
    game_data = {
        "type": "mines",
        "bet": bet,
        "mines": mines,
        "opened": opened,
        "multipliers": multipliers,
        "step": 0
    }
    
    from keyboards import get_mines_keyboard
    await message.edit_text(
        f"💣 **Мины**\n\n"
        f"💰 Ставка: {bet} {COIN_NAME}\n"
        f"🎁 Множитель: x{multipliers[0]:.2f}\n"
        f"💣 Мин на поле: 3\n\n"
        f"**Выберите ячейку:**",
        reply_markup=get_mines_keyboard(game_data),
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
            f"🎁 Множитель: x{multipliers[-1]:.2f}\n\n"
            f"✨ Вы выиграли {win} {COIN_NAME}!",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return None
    
    from keyboards import get_mines_keyboard
    await message.edit_text(
        f"💣 **Мины**\n\n"
        f"💰 Ставка: {bet} {COIN_NAME}\n"
        f"🎁 Множитель: x{multipliers[step]:.2f}\n"
        f"✅ Открыто: {len(opened)} ячеек\n\n"
        f"**Выберите следующую ячейку:**",
        reply_markup=get_mines_keyboard(game_data),
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

# ==================== БАШНЯ (8 УРОВНЕЙ, КАК В WINPACO) ====================
async def play_tower(user_id, bet, message):
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
        # На каждом уровне 3 мины (редко 2)
        mines_count = 3 if random.random() > 0.1 else 2
        mines = random.sample(range(5), mines_count)
        levels.append({
            "mines": mines,
            "selected": None,
            "revealed": False
        })
    
    multipliers = [1.30, 1.80, 2.30, 3.00, 4.00, 5.50, 7.50, 10.00]
    
    game_data = {
        "type": "tower",
        "bet": bet,
        "levels": levels,
        "current_level": 0,
        "multipliers": multipliers
    }
    
    from keyboards import get_tower_keyboard
    await message.edit_text(
        f"🗼 **Башня**\n\n"
        f"💰 Ставка: {bet} {COIN_NAME}\n"
        f"🏆 Уровень: 1/8\n"
        f"🎁 Множитель: x{multipliers[0]:.2f}\n\n"
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
    multipliers = game_data["multipliers"]
    
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
        win = int(bet * multipliers[7])
        await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
        await add_transaction(user_id, "tower_win", win, f"Выигрыш в башне")
        
        await message.edit_text(
            f"🗼 **Башня**\n\n"
            f"🎉 **ПОЛНАЯ ПОБЕДА!** 🎉\n\n"
            f"🏆 Уровни пройдены: 8/8\n"
            f"💰 Ставка: {bet} {COIN_NAME}\n"
            f"🎁 Множитель: x{multipliers[7]:.2f}\n\n"
            f"✨ Вы выиграли {win} {COIN_NAME}!",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown"
        )
        return None
    
    from keyboards import get_tower_keyboard
    current_multiplier = multipliers[game_data["current_level"]]
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
