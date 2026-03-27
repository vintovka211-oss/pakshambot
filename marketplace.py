from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user, add_transaction, add_income, update_user
from config import MARKETPLACE_COMMISSION, PREMIUM_MARKETPLACE_COMMISSION, COIN_NAME
import aiosqlite

DB_PATH = "w1npaksham.db"

async def get_marketplace_items():
    """Получить активные товары"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, seller_id, item_name, price, quantity FROM marketplace_items WHERE status = 'active' ORDER BY created_at DESC"
        ) as cursor:
            return await cursor.fetchall()

async def buy_item(user_id: int, item_id: int, quantity: int = 1) -> tuple:
    """Купить предмет"""
    user = await get_user(user_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT seller_id, item_name, price, quantity FROM marketplace_items WHERE id = ? AND status = 'active'",
            (item_id,)
        ) as cursor:
            item = await cursor.fetchone()
        
        if not item:
            return False, "❌ Товар не найден"
        
        seller_id, item_name, price, available = item
        
        if quantity > available:
            return False, f"❌ Доступно только {available} шт."
        
        total_price = price * quantity
        
        if user["pac_balance"] < total_price:
            return False, f"❌ Недостаточно {COIN_NAME}! Нужно: {total_price}"
        
        commission_rate = MARKETPLACE_COMMISSION
        if user["is_premium"]:
            commission_rate = PREMIUM_MARKETPLACE_COMMISSION
        
        seller_income = int(total_price * (100 - commission_rate) / 100)
        bot_income = total_price - seller_income
        
        new_buyer_balance = user["pac_balance"] - total_price
        await db.execute(
            "UPDATE users SET pac_balance = ? WHERE user_id = ?",
            (new_buyer_balance, user_id)
        )
        
        seller = await get_user(seller_id)
        new_seller_balance = seller["pac_balance"] + seller_income
        await db.execute(
            "UPDATE users SET pac_balance = ? WHERE user_id = ?",
            (new_seller_balance, seller_id)
        )
        
        new_quantity = available - quantity
        if new_quantity == 0:
            await db.execute(
                "UPDATE marketplace_items SET status = 'sold' WHERE id = ?",
                (item_id,)
            )
        else:
            await db.execute(
                "UPDATE marketplace_items SET quantity = ? WHERE id = ?",
                (new_quantity, item_id)
            )
        
        await db.execute(
            "INSERT INTO inventory (user_id, item_name, item_type, quantity) VALUES (?, ?, ?, ?)",
            (user_id, item_name, "item", quantity)
        )
        
        await db.commit()
        
        await add_transaction(user_id, "marketplace_buy", -total_price, f"Покупка {item_name}")
        await add_transaction(seller_id, "marketplace_sell", seller_income, f"Продажа {item_name}")
        await add_income("marketplace", bot_income, user_id)
        
        return True, f"✅ Куплено {quantity} x {item_name} за {total_price} {COIN_NAME}!"
