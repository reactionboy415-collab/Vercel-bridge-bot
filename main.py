import logging
import asyncio
import base64
import random
import string
import httpx
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- RENDER PORT BYPASS ---
app = Flask('')
@app.route('/')
def home(): return "Vercel Bridge ⚡ Direct is Active"

def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

# --- CONFIG ---
API_TOKEN = '8299663322:AAEZZqcqpgJFyi9lmqRCPjPUD35smcHPiL8'
VERCEL_TOKEN = "TYt6xV8Gnr99oJG3FNTcQQmd"
TEAM_ID = "team_IKARugTrm6K77V5MqC2C9XCd"
ADMIN_ID = 6043602577
ADMIN_HANDLE = "@cbxdq"

db_stats = {"total_live": 0, "users": {}}

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- KEYBOARDS ---
def get_main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Deploy Project")],
        [KeyboardButton(text="📊 Stats"), KeyboardButton(text="👨‍💻 Developer")]
    ], resize_keyboard=True)

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "⚡ <b>VERCEL BRIDGE v15.0</b> ⚡\n\n"
        "<i>Direct Cloud Strike Engine.</i>\n\n"
        "<b>Status:</b> 🟢 Ready to Fire",
        parse_mode="HTML", reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "👨‍💻 Developer")
async def show_dev(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Contact Admin", url=f"https://t.me/{ADMIN_HANDLE[1:]}")]])
    await message.answer(f"🔱 <b>Developer:</b> {ADMIN_HANDLE}", parse_mode="HTML", reply_markup=kb)

@dp.message(F.text == "📊 Stats")
async def show_stats(message: types.Message):
    user_id = message.from_user.id
    user_count = db_stats["users"].get(user_id, 0)
    await message.answer(
        f"📊 <b>SYSTEM STATS</b>\n\n"
        f"🚀 <b>Global Projects:</b> {db_stats['total_live']}\n"
        f"👤 <b>Your Projects:</b> {user_count}",
        parse_mode="HTML"
    )

@dp.message(F.text == "🚀 Deploy Project")
async def ask_deploy(message: types.Message):
    await message.answer("📥 <b>Send any Code or File now!</b>\nI will deploy it instantly.", parse_mode="HTML")

@dp.message(lambda message: message.text or message.document)
async def direct_deploy(message: types.Message):
    if message.text in ["🚀 Deploy Project", "📊 Stats", "👨‍💻 Developer", "/start"]: return

    user = message.from_user
    content = ""
    f_name = "index.html"

    # Extraction Logic
    if message.document:
        file_info = await bot.get_file(message.document.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        content = downloaded.read().decode('utf-8', errors='ignore')
        f_name = message.document.file_name
    else:
        content = message.text
        if "FROM" in content: f_name = "Dockerfile"

    status_msg = await message.answer("🚀 <b>Striking Vercel...</b>", parse_mode="HTML")

    # Name Generation
    p_name = f"vb-{user.id}-" + ''.join(random.choices(string.ascii_lowercase, k=4))

    # Deployment
    url = f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}"
    encoded = base64.b64encode(content.encode()).decode()
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"}
    
    payload = {
        "name": p_name,
        "files": [{"file": f_name, "data": encoded, "encoding": "base64"}],
        "projectSettings": {"framework": None}
    }
    
    async with httpx.AsyncClient(http2=True, timeout=60.0) as client:
        try:
            r = await client.post(url, headers=headers, json=payload)
            if r.status_code == 200:
                db_stats["total_live"] += 1
                db_stats["users"][user.id] = db_stats["users"].get(user.id, 0) + 1
                d_url = f"https://{r.json()['url']}"
                
                await status_msg.edit_text(f"✅ <b>LIVE!</b>\n\n🔗 {d_url}", parse_mode="HTML")
                
                # Admin Log
                await bot.send_message(ADMIN_ID, f"🚨 <b>LOG:</b> {user.full_name} deployed {d_url}", parse_mode="HTML")
            else:
                await status_msg.edit_text(f"❌ <b>Error:</b> <code>{r.status_code}</code>")
        except Exception as e:
            await status_msg.edit_text(f"❌ <b>Failed:</b> <code>{str(e)}</code>")

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
