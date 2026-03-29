import random
import asyncio
from config import COIN_NAME
from database import get_user, update_user, add_transaction

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

# СЛОТЫ
async def play_slots(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    symbols = ["🍒", "🍋", "🍊", "🍉", "⭐", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance
    
    if is_win:
        multiplier = random.choice([1.5, 2, 3, 5])
        win = int(bet * multiplier)
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "slots", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "slots_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"🎰 **Слоты**\n\n`{result[0]}` | `{result[1]}` | `{result[2]}`\n\n🎉 Вы выиграли {win} {COIN_NAME}!"
    else:
        return 0, f"🎰 **Слоты**\n\n`{result[0]}` | `{result[1]}` | `{result[2]}`\n\n😔 Вы проиграли {bet} {COIN_NAME}."

# КУБИК
async def play_dice(user_id, bet, choice, message):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    dice_message = await message.answer_dice(emoji="🎲")
    await asyncio.sleep(2)
    dice = dice_message.dice.value
    
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and choice == dice
    
    if is_win:
        win = int(bet * 5)
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

# РУЛЕТКА
async def play_roulette(user_id, bet, color_choice, message):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    frames = ["🎡", "🌀", "🎲", "🎯"]
    msg = await message.answer("🎡")
    for frame in frames:
        await msg.edit_text(frame)
        await asyncio.sleep(0.3)
    await msg.delete()
    
    colors = ["🔴", "⚫"]
    result = random.choice(colors)
    
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and color_choice == result
    
    if is_win:
        win = int(bet * 2)
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

# ОРЁЛ/РЕШКА
async def play_coin(user_id, bet, choice):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
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

# МИНЫ
async def play_mines(user_id, bet, cell, message):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    field = ["⬜", "⬜", "⬜", "⬜", "⬜", "⬜", "⬜", "⬜", "⬜"]
    mines = random.sample(range(9), 3)
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and cell not in mines
    
    if is_win:
        field[cell] = "💰"
        win = int(bet * 2.5)
        await apply_win_reduction(user_id, True)
    else:
        field[cell] = "💣"
        win = 0
        await apply_win_reduction(user_id, False)
    
    field_display = f"`{field[0]} {field[1]} {field[2]}\n{field[3]} {field[4]} {field[5]}\n{field[6]} {field[7]} {field[8]}`"
    
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "mines", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "mines_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"💣 **Мины**\n\n{field_display}\n\nВы выбрали ячейку {cell+1}\n🎉 Вы не наступили на мину! +{win} {COIN_NAME}!"
    else:
        return 0, f"💣 **Мины**\n\n{field_display}\n\nВы выбрали ячейку {cell+1}\n💥 БАХ! Вы проиграли {bet} {COIN_NAME}."

# КОЛЕСО
async def play_wheel(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    segments = [0, 0, 0, 0, 1, 1, 2, 2, 3, 5]
    result = random.choice(segments)
    win = bet * result
    
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and result > 0
    
    if is_win:
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "wheel", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "wheel_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"🎡 **Колесо Фортуны**\n\nВыпал множитель **x{result}**!\n🎉 Вы выиграли {win} {COIN_NAME}!"
    else:
        return 0, f"🎡 **Колесо Фортуны**\n\nВыпал **0**!\n😔 Вы проиграли {bet} {COIN_NAME}."

# БЛЭКДЖЕК
async def play_blackjack(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    cards = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    player = [random.choice(cards), random.choice(cards)]
    dealer = [random.choice(cards), random.choice(cards)]
    
    def card_value(card):
        if card in ["J", "Q", "K"]:
            return 10
        if card == "A":
            return 11
        return int(card)
    
    player_sum = sum(card_value(c) for c in player)
    dealer_sum = sum(card_value(c) for c in dealer)
    
    while player_sum < 17 and len(player) < 5:
        player.append(random.choice(cards))
        player_sum = sum(card_value(c) for c in player)
    while dealer_sum < 17 and len(dealer) < 5:
        dealer.append(random.choice(cards))
        dealer_sum = sum(card_value(c) for c in dealer)
    
    if player_sum > 21:
        player_sum = 0
    if dealer_sum > 21:
        dealer_sum = 0
    
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and player_sum > dealer_sum
    
    if is_win:
        win = int(bet * 2)
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "blackjack", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "blackjack_win", win, "Выигрыш")
    
    player_cards = " | ".join(player)
    dealer_cards = " | ".join(dealer)
    
    if win > 0:
        return win, f"🃏 **Блэкджек**\n\n**Ваши карты:** {player_cards} = {player_sum}\n**Карты дилера:** {dealer_cards} = {dealer_sum}\n\n🎉 Вы выиграли {win} {COIN_NAME}!"
    else:
        return 0, f"🃏 **Блэкджек**\n\n**Ваши карты:** {player_cards} = {player_sum}\n**Карты дилера:** {dealer_cards} = {dealer_sum}\n\n😔 Вы проиграли {bet} {COIN_NAME}."

# ОСТАЛЬНЫЕ ИГРЫ (упрощённые)
async def play_sticks(user_id, bet, choice):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    sticks = random.randint(1, 10)
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and choice == sticks
    if is_win:
        win = int(bet * 3)
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "sticks", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "sticks_win", win, "Выигрыш")
    if win > 0:
        return win, f"🥢 **Палки**\n\nВыпало: **{sticks}**\nВаше число: **{choice}**\n\n🎉 Вы угадали! +{win} {COIN_NAME}!"
    else:
        return 0, f"🥢 **Палки**\n\nВыпало: **{sticks}**\nВаше число: **{choice}**\n\n😔 Вы не угадали. -{bet} {COIN_NAME}."

async def play_high_low(user_id, bet, choice):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    number = random.randint(1, 100)
    chance = await get_win_chance(user_id)
    if choice == "high":
        is_win = random.random() < chance and number > 50
    else:
        is_win = random.random() < chance and number < 50
    if is_win:
        win = int(bet * 1.9)
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "highlow", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "highlow_win", win, "Выигрыш")
    if win > 0:
        return win, f"📈 **Больше-Меньше**\n\nВыпало: **{number}**\n\n🎉 Вы выиграли {win} {COIN_NAME}!"
    else:
        return 0, f"📉 **Больше-Меньше**\n\nВыпало: **{number}**\n\n😔 Вы проиграли {bet} {COIN_NAME}."

async def play_keno(user_id, bet, choice):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    numbers = random.sample(range(1, 21), 10)
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and choice in numbers
    if is_win:
        win = int(bet * 4)
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "keno", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "keno_win", win, "Выигрыш")
    if win > 0:
        return win, f"🎲 **Кено**\n\nВыпавшие числа: {numbers[:5]}...\nВаше число: **{choice}**\n\n🎉 Вы угадали! +{win} {COIN_NAME}!"
    else:
        return 0, f"🎲 **Кено**\n\nВыпавшие числа: {numbers[:5]}...\nВаше число: **{choice}**\n\n😔 Вы не угадали. -{bet} {COIN_NAME}."

async def play_baccarat(user_id, bet, choice):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    player = random.randint(0, 9)
    banker = random.randint(0, 9)
    chance = await get_win_chance(user_id)
    if choice == "player":
        is_win = random.random() < chance and player > banker
    elif choice == "banker":
        is_win = random.random() < chance and banker > player
    else:
        is_win = random.random() < chance and player == banker
    if is_win:
        win = int(bet * 2)
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "baccarat", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "baccarat_win", win, "Выигрыш")
    if win > 0:
        return win, f"🃏 **Баккара**\n\nИгрок: **{player}** | Банкир: **{banker}**\n\n🎉 Вы выиграли {win} {COIN_NAME}!"
    else:
        return 0, f"🃏 **Баккара**\n\nИгрок: **{player}** | Банкир: **{banker}**\n\n😔 Вы проиграли {bet} {COIN_NAME}."

async def play_poker(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance
    if is_win:
        win = int(bet * 3)
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "poker", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "poker_win", win, "Выигрыш")
    if win > 0:
        return win, f"🃏 **Покер**\n\n🎉 Вы выиграли {win} {COIN_NAME}!"
    else:
        return 0, f"🃏 **Покер**\n\n😔 Вы проиграли {bet} {COIN_NAME}."

async def play_craps(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    total = dice1 + dice2
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and total in [7, 11]
    if is_win:
        win = int(bet * 2)
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "craps", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "craps_win", win, "Выигрыш")
    if win > 0:
        return win, f"🎲 **Крэпс**\n\nКости: **{dice1}** + **{dice2}** = **{total}**\n\n🎉 Вы выиграли {win} {COIN_NAME}!"
    else:
        return 0, f"🎲 **Крэпс**\n\nКости: **{dice1}** + **{dice2}** = **{total}**\n\n😔 Вы проиграли {bet} {COIN_NAME}."

async def play_video_poker(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance
    if is_win:
        win = int(bet * 2.5)
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "video_poker", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "video_poker_win", win, "Выигрыш")
    if win > 0:
        return win, f"🎰 **Видео-покер**\n\n🎉 Вы выиграли {win} {COIN_NAME}!"
    else:
        return 0, f"🎰 **Видео-покер**\n\n😔 Вы проиграли {bet} {COIN_NAME}."

async def play_lucky7(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    number = random.randint(1, 100)
    chance = await get_win_chance(user_id)
    is_win = random.random() < chance and number == 7
    if is_win:
        win = int(bet * 10)
        await apply_win_reduction(user_id, True)
    else:
        win = 0
        await apply_win_reduction(user_id, False)
    await update_user(user_id, pac_balance=user["pac_balance"] - bet + win)
    await add_transaction(user_id, "lucky7", -bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "lucky7_win", win, "Выигрыш")
    if win > 0:
        return win, f"7️⃣ **Лакки 7**\n\nВыпало: **{number}**\n\n🎉 ВЫПАЛО 7! +{win} {COIN_NAME}!"
    else:
        return 0, f"7️⃣ **Лакки 7**\n\nВыпало: **{number}**\n\n😔 Вы проиграли {bet} {COIN_NAME}."
