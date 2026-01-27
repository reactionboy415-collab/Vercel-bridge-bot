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
def home(): return "STRIKER ENGINE v15.2 ACTIVE"

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

# --- KEYBOARD ---
def get_main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Start Strike")],
        [KeyboardButton(text="📊 System Stats"), KeyboardButton(text="👨‍💻 Developer")]
    ], resize_keyboard=True)

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "💀 <b>STRIKER ENGINE v15.2 ONLINE</b> 💀\n\n"
        "<i>Initializing secure bridge...</i>\n"
        "✅ Connection: <b>Encrypted</b>\n"
        "⚡ Protocol: <b>Ghost-Strike</b>",
        parse_mode="HTML", reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "📊 System Stats")
async def show_stats(message: types.Message):
    await message.answer(
        f"🔱 <b>CORE STATISTICS</b>\n\n"
        f"🛰️ <b>Global Nodes:</b> {db_stats['total_live']}\n"
        f"🟢 <b>Server Status:</b> Optimal",
        parse_mode="HTML"
    )

@dp.message(F.text == "🚀 Start Strike")
async def ask_deploy(message: types.Message):
    await message.answer("📥 <b>Waiting for Payload...</b>\nSend your code or file to initiate strike.", parse_mode="HTML")

@dp.message(lambda message: message.text or message.document)
async def masked_deploy(message: types.Message):
    if message.text in ["🚀 Start Strike", "📊 System Stats", "👨‍💻 Developer", "/start"]: return

    user = message.from_user
    content = ""
    f_name = "index.html"

    if message.document:
        file_info = await bot.get_file(message.document.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        content = downloaded.read().decode('utf-8', errors='ignore')
        f_name = message.document.file_name
    else:
        content = message.text
        if "FROM" in content: f_name = "Dockerfile"

    # --- PROFESSIONAL MASKED SEQUENCE ---
    status_msg = await message.answer("⚡ <b>Injecting Payload...</b>", parse_mode="HTML")
    await asyncio.sleep(1)
    await status_msg.edit_text("📡 <b>Bypassing Firewalls...</b>", parse_mode="HTML")
    
    p_name = f"strike-{user.id}-" + ''.join(random.choices(string.ascii_lowercase, k=4))
    url = f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}"
    encoded = base64.b64encode(content.encode()).decode()
    
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "name": p_name,
        "files": [{"file": f_name, "data": encoded, "encoding": "base64"}],
        "projectSettings": {"framework": None}
    }
    
    async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
        try:
            r = await client.post(url, headers=headers, json=payload)
            
            if r.status_code == 200:
                await status_msg.edit_text("🛰️ <b>Establishing Link...</b>", parse_mode="HTML")
                await asyncio.sleep(1)
                
                db_stats["total_live"] += 1
                res_data = r.json()
                d_url = f"https://{res_data['url']}"
                
                # FINAL SUCCESS MESSAGE (CLEAN & PROFESSIONAL)
                final_text = (
                    "🔱 <b>STRIKE SUCCESSFUL!</b>\n\n"
                    f"🔗 <b>Access Point:</b> {d_url}\n"
                    "🛡️ <b>Status:</b> <code>LIVE_PRODUCTION</code>"
                )
                await status_msg.edit_text(final_text, parse_mode="HTML")
                
                # Admin Log
                await bot.send_message(ADMIN_ID, f"🚨 <b>LOG:</b> {user.full_name} struck {d_url}", parse_mode="HTML")
            else:
                # Masking the error to look like a system failure
                await status_msg.edit_text(f"❌ <b>STRIKE FAILED</b>\nCode: <code>ERR_STRIKE_{r.status_code}</code>\n<i>Re-initializing engine...</i>", parse_mode="HTML")
        except Exception as e:
            await status_msg.edit_text(f"❌ <b>CORE ERROR</b>\n<code>{str(e)[:50]}...</code>", parse_mode="HTML")

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
