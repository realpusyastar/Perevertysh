import os
import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    LabeledPrice, 
    PreCheckoutQuery, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
import aiohttp

# ================= КОНФИГУРАЦИЯ =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "864559012:AAER-t_KkX3Qf5yjNTS66ZOhA7PZDJN5sBs")
ADMIN_ID = 6845733552
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN", "659079:AAQgt4MWbonxZOeWfZfF3trNmt8xluwzCgw")
# ================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_FILE = "subscribers.json"

def load_subs():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_subs(subs):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(subs, f, ensure_ascii=False, indent=2)

# 1. ОБРАБОТКА СИГНАЛОВ НА ОПЛАТУ ИЗ MINI APP
@dp.message(F.web_app_data)
async def handle_webapp_payment(message: types.Message):
    data = json.loads(message.web_app_data.data)
    user = message.from_user

    # А) Оплата Telegram Stars (150 звёзд)
    if data.get("action") == "buy_pro_stars":
        prices = [LabeledPrice(label="PRO доступ Перевертыш", amount=150)]
        await bot.send_invoice(
            chat_id=user.id,
            title="Тариф Перевертыш PRO",
            description="Неограниченное создание блоков и слов",
            payload=f"stars_pro_{user.id}",
            currency="XTR",
            prices=prices,
            provider_token=""
        )

    # Б) Оплата криптовалютой (1.5 TON через CryptoBot)
    elif data.get("action") == "buy_pro_crypto":
        headers = {"Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN}
        payload = {
            "asset": "TON",
            "amount": "1.5",
            "description": f"PRO Перевертыш {user.id}",
            "payload": str(user.id)
        }
        async with aiohttp.ClientSession() as session:
            async with session.post("https://pay.crypt.bot/api/createInvoice", json=payload, headers=headers) as resp:
                res = await resp.json()
                if res.get("ok"):
                    url = res["result"]["pay_url"]
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="💎 Оплатить 1.5 TON", url=url)]
                    ])
                    await message.answer(
                        "Счет на оплату готов. Нажмите кнопку ниже для оплаты:", 
                        reply_markup=kb
                    )
                else:
                    await message.answer("Ошибка связи с CryptoBot.")

# 2. ПОДТВЕРЖДЕНИЕ И НАЧИСЛЕНИЕ STARS
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    user = message.from_user
    subs = load_subs()
    subs[str(user.id)] = {
        "username": user.username or "нет юзернейма",
        "first_name": user.first_name,
        "type": "stars",
        "amount": 150
    }
    save_subs(subs)

    await message.answer("🎉 Оплата 150 Stars прошла успешно! Ваш PRO-статус активирован.")

    await bot.send_message(
        ADMIN_ID,
        f"💰 Новая оплата Stars!\n"
        f"Пользователь: @{user.username or 'без_ника'} (ID: {user.id})\n"
        f"Сумма: 150 Telegram Stars"
    )

# 3. АДМИН-ПАНЕЛЬ (/admin)
@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Список подписчиков", callback_data="admin_subs")]
    ])
    await message.answer("👑 Панель управления Перевертыш\nВыберите действие:", reply_markup=kb)

@dp.callback_query(F.data == "admin_stats")
async def show_stats(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    subs = load_subs()
    total_stars = sum(item.get("amount", 0) for item in subs.values() if item.get("type") == "stars")
    await call.message.edit_text(
        f"📊 Статистика бота:\n\n"
        f"Всего PRO-подписчиков: {len(subs)}\n"
        f"Заработано звезд: {total_stars} ★"
    )

@dp.callback_query(F.data == "admin_subs")
async def show_subs(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    subs = load_subs()
    if not subs:
        await call.message.answer("Пока нет активных PRO-подписчиков.")
        return

    text = "👥 Список активных PRO:\n\n"
    for uid, info in subs.items():
        text += f"• @{info.get('username')} (ID: {uid}) — {info.get('type')}\n"
    await call.message.answer(text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
