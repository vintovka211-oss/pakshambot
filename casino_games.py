import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

class CasinoGames:
    """Класс с играми казино"""
    
    @staticmethod
    async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_pak: int, bet_rub: int):
        """Игра в кости"""
        player_roll = random.randint(1, 6)
        computer_roll = random.randint(1, 6)
        
        # Нечестные шансы: 30% выигрыш, 40% проигрыш, 30% ничья
        if player_roll > computer_roll:
            win_multiplier = random.uniform(1.1, 1.5)
            win_pak = int(bet_pak * win_multiplier)
            win_rub = int(bet_rub * win_multiplier)
            result_text = f"""
🎲 Игра в Кости!

Ваш бросок: {player_roll}
Бросок казино: {computer_roll}

🎉 ВЫ ВЫИГРАЛИ!
💰 Выигрыш: +{win_pak} PAK и +{win_rub} РУБ
⭐ Множитель: x{win_multiplier:.1f}
"""
            return True, win_pak, win_rub, result_text
            
        elif player_roll == computer_roll:
            result_text = f"""
🎲 Игра в Кости!

Ваш бросок: {player_roll}
Бросок казино: {computer_roll}

🤝 НИЧЬЯ!
💰 Возврат ставки: {bet_pak} PAK и {bet_rub} РУБ
"""
            return None, bet_pak, bet_rub, result_text
            
        else:
            loss_multiplier = random.uniform(1.2, 1.8)
            loss_pak = int(bet_pak * loss_multiplier)
            loss_rub = int(bet_rub * loss_multiplier)
            result_text = f"""
🎲 Игра в Кости!

Ваш бросок: {player_roll}
Бросок казино: {computer_roll}

💔 ВЫ ПРОИГРАЛИ!
💸 Потеряно: -{loss_pak} PAK и -{loss_rub} РУБ
😢 Множитель потери: x{loss_multiplier:.1f}
"""
            return False, loss_pak, loss_rub, result_text
    
    @staticmethod
    async def blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_pak: int, bet_rub: int):
        """Упрощенный Блэкджек"""
        def get_card():
            return random.randint(1, 11)
        
        player_cards = [get_card(), get_card()]
        dealer_cards = [get_card()]
        
        player_score = sum(player_cards)
        dealer_score = sum(dealer_cards)
        
        # Шансы: 35% выигрыш, 45% проигрыш, 20% ничья
        if random.random() < 0.35:
            win_multiplier = random.uniform(1.1, 1.4)
            win_pak = int(bet_pak * win_multiplier)
            win_rub = int(bet_rub * win_multiplier)
            result_text = f"""
🃏 Блэкджек!

Ваши карты: {player_cards[0]} + {player_cards[1]} = {player_score}
Карты дилера: {dealer_cards[0]} + ? = ?

🎉 ВЫ ВЫИГРАЛИ!
💰 Выигрыш: +{win_pak} PAK и +{win_rub} РУБ
"""
            return True, win_pak, win_rub, result_text
            
        elif random.random() < 0.55:
            loss_multiplier = random.uniform(1.3, 2.0)
            loss_pak = int(bet_pak * loss_multiplier)
            loss_rub = int(bet_rub * loss_multiplier)
            result_text = f"""
🃏 Блэкджек!

Ваши карты: {player_cards[0]} + {player_cards[1]} = {player_score}
Карты дилера: {dealer_cards[0]} + {random.randint(1, 11)} = {dealer_score + random.randint(1, 11)}

💔 ВЫ ПРОИГРАЛИ!
💸 Потеряно: -{loss_pak} PAK и -{loss_rub} РУБ
"""
            return False, loss_pak, loss_rub, result_text
            
        else:
            result_text = f"""
🃏 Блэкджек!

Ваши карты: {player_cards[0]} + {player_cards[1]} = {player_score}
Карты дилера: {dealer_cards[0]} + ? = ?

🤝 НИЧЬЯ!
💰 Возврат ставки: {bet_pak} PAK и {bet_rub} РУБ
"""
            return None, bet_pak, bet_rub, result_text
    
    @staticmethod
    async def slot_machine(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_pak: int, bet_rub: int):
        """Слот-машина"""
        symbols = ['🍒', '🍋', '🍊', '🍉', '⭐', '💎', '7️⃣']
        results = [random.choice(symbols) for _ in range(3)]
        
        # Проверка выигрышных комбинаций
        if results[0] == results[1] == results[2]:
            if results[0] == '💎':
                multiplier = 5.0
                win_text = "🎉 ДЖЕКПОТ! 🎉"
            elif results[0] == '7️⃣':
                multiplier = 4.0
                win_text = "🔥 СУПЕР ВЫИГРЫШ! 🔥"
            elif results[0] == '⭐':
                multiplier = 3.0
                win_text = "✨ БОЛЬШОЙ ВЫИГРЫШ! ✨"
            else:
                multiplier = 2.0
                win_text = "🎰 ВЫИГРЫШ! 🎰"
            
            win_pak = int(bet_pak * multiplier)
            win_rub = int(bet_rub * multiplier)
            result_text = f"""
🎰 СЛОТ-МАШИНА!

[{results[0]}] [{results[1]}] [{results[2]}]

{win_text}
💰 Выигрыш: +{win_pak} PAK и +{win_rub} РУБ
⭐ Множитель: x{multiplier}
"""
            return True, win_pak, win_rub, result_text
            
        elif results[0] == results[1] or results[1] == results[2] or results[0] == results[2]:
            multiplier = 1.3
            win_pak = int(bet_pak * multiplier)
            win_rub = int(bet_rub * multiplier)
            result_text = f"""
🎰 СЛОТ-МАШИНА!

[{results[0]}] [{results[1]}] [{results[2]}]

🎯 МАЛЕНЬКИЙ ВЫИГРЫШ!
💰 Выигрыш: +{win_pak} PAK и +{win_rub} РУБ
"""
            return True, win_pak, win_rub, result_text
            
        else:
            loss_multiplier = random.uniform(1.5, 2.5)
            loss_pak = int(bet_pak * loss_multiplier)
            loss_rub = int(bet_rub * loss_multiplier)
            result_text = f"""
🎰 СЛОТ-МАШИНА!

[{results[0]}] [{results[1]}] [{results[2]}]

💔 ВЫ ПРОИГРАЛИ!
💸 Потеряно: -{loss_pak} PAK и -{loss_rub} РУБ
😢 Крупный проигрыш!
"""
            return False, loss_pak, loss_rub, result_text
    
    @staticmethod
    async def high_risk(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_pak: int, bet_rub: int):
        """Игра с высоким риском"""
        chance = random.random()
        
        if chance < 0.15:  # 15% шанс на x5 выигрыш
            multiplier = 5.0
            win_pak = int(bet_pak * multiplier)
            win_rub = int(bet_rub * multiplier)
            result_text = f"""
💀 HIGH RISK GAME 💀

🎉 ЧУДО! ВЫ ВЫИГРАЛИ!
💰 Выигрыш: +{win_pak} PAK и +{win_rub} РУБ
⭐ Множитель: x{multiplier}
😱 Невероятная удача!
"""
            return True, win_pak, win_rub, result_text
            
        elif chance < 0.35:  # 20% шанс на x2 выигрыш
            multiplier = 2.0
            win_pak = int(bet_pak * multiplier)
            win_rub = int(bet_rub * multiplier)
            result_text = f"""
💀 HIGH RISK GAME 💀

🎉 ВЫ ВЫИГРАЛИ!
💰 Выигрыш: +{win_pak} PAK и +{win_rub} РУБ
⭐ Множитель: x{multiplier}
"""
            return True, win_pak, win_rub, result_text
            
        else:  # 65% шанс на крупный проигрыш
            loss_multiplier = random.uniform(2.5, 4.0)
            loss_pak = int(bet_pak * loss_multiplier)
            loss_rub = int(bet_rub * loss_multiplier)
            result_text = f"""
💀 HIGH RISK GAME 💀

💔 ВЫ ПРОИГРАЛИ!
💸 Потеряно: -{loss_pak} PAK и -{loss_rub} РУБ
😭 Множитель потери: x{loss_multiplier:.1f}
⚰️ Риск не оправдался...
"""
            return False, loss_pak, loss_rub, result_text
