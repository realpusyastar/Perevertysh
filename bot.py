import os
import json
import logging
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
    if data.get("action") == "buy
