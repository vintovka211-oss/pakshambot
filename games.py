import random
from database import get_user, update_user, add_transaction
from config import CURRENCY, GAME_COMMISSION, add_income

async def play_slots(user_id: int, bet: int) -> tuple:
    """Игра Слоты"""
    user = await get_user(user_id)
    
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    
    if user["balance"] < bet:
        return 0, "❌ Недостаточно средств!"
    
    symbols = ["🍒", "🍋", "🍊", "🍉", "⭐", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    
    win = 0
    if result[0] == result[1] == result[2]:
        if result[0] == "7️⃣":
            win = bet * 10
        elif result[0] == "💎":
            win = bet * 5
        elif result[0] == "⭐":
            win = bet * 3
        else:
            win = bet * 2
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win = bet // 2
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    new_balance = user["balance"] - actual_bet + win
    await update_user(
        user_id,
        balance=new_balance,
        total_games=user["total_games"] + 1,
        turnover=user["turnover"] + actual_bet
    )
    
    await add_transaction(user_id, "game_bet", -actual_bet, f"Ставка в слотах")
    if win > 0:
        await add_transaction(user_id, "game_win", win, f"Выигрыш в слотах")
    
    await add_income("game_commission", commission, user_id)
    
    if win > 0:
        return win, f"🎰 {result[0]} | {result[1]} | {result[2]}\n🎉 Вы выиграли {win}{CURRENCY}!"
    else:
        return 0, f"🎰 {result[0]} | {result[1]} | {result[2]}\n😔 Вы проиграли {actual_bet}{CURRENCY}."

async def play_dice(user_id: int, bet: int, choice: int = None) -> tuple:
    """Игра Кубик"""
    user = await get_user(user_id)
    
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    
    if user["balance"] < bet:
        return 0, "❌ Недостаточно средств!"
    
    dice = random.randint(1, 6)
    
    win = 0
    if choice and 1 <= choice <= 6:
        if dice == choice:
            win = bet * 5
    elif choice in ["even", "odd"]:
        if (choice == "even" and dice % 2 == 0) or (choice == "odd" and dice % 2 == 1):
            win = bet * 2
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    new_balance = user["balance"] - actual_bet + win
    await update_user(
        user_id,
        balance=new_balance,
        total_games=user["total_games"] + 1,
        turnover=user["turnover"] + actual_bet
    )
    
    await add_transaction(user_id, "game_bet", -actual_bet, f"Ставка в кубик")
    if win > 0:
        await add_transaction(user_id, "game_win", win, f"Выигрыш в кубик")
    
    await add_income("game_commission", commission, user_id)
    
    if win > 0:
        return win, f"🎲 Выпало: {dice}\n🎉 Вы выиграли {win}{CURRENCY}!"
    else:
        return 0, f"🎲 Выпало: {dice}\n😔 Вы проиграли {actual_bet}{CURRENCY}."

async def play_roulette(user_id: int, bet: int, color: str) -> tuple:
    """Рулетка"""
    user = await get_user(user_id)
    
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    
    if user["balance"] < bet:
        return 0, "❌ Недостаточно средств!"
    
    colors = ["🔴", "⚫", "🟢"]
    result_color = random.choice(colors)
    
    win = 0
    if result_color == color:
        if color == "🟢":
            win = bet * 14
        else:
            win = bet * 2
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    new_balance = user["balance"] - actual_bet + win
    await update_user(
        user_id,
        balance=new_balance,
        total_games=user["total_games"] + 1,
        turnover=user["turnover"] + actual_bet
    )
    
    await add_transaction(user_id, "game_bet", -actual_bet, f"Ставка в рулетку")
    if win > 0:
        await add_transaction(user_id, "game_win", win, f"Выигрыш в рулетку")
    
    await add_income("game_commission", commission, user_id)
    
    if win > 0:
        return win, f"🎡 Выпало: {result_color}\n🎉 Вы выиграли {win}{CURRENCY}!"
    else:
        return 0, f"🎡 Выпало: {result_color}\n😔 Вы проиграли {actual_bet}{CURRENCY}."
