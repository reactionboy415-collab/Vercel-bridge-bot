import logging
import asyncio
import base64
import random
import string
import httpx
import os
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- RENDER WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Vercel Bridge ⚡ Pro is Active"

def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

# --- CONFIG ---
API_TOKEN = '8299663322:AAEZZqcqpgJFyi9lmqRCPjPUD35smcHPiL8'
VERCEL_TOKEN = "TYt6xV8Gnr99oJG3FNTcQQmd"
TEAM_ID = "team_IKARugTrm6K77V5MqC2C9XCd"
ADMIN_ID = 6043602577
ADMIN_HANDLE = "@cbxdq"

# In-memory stats (Restart hone par reset honge, Render pe database nahi hai)
db_stats = {"total_live": 0, "users": {}}

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- KEYBOARDS ---
def get_main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Deploy Project")],
        [KeyboardButton(text="📊 Stats"), KeyboardButton(text="👨‍💻 Developer")]
    ], resize_keyboard=True)

# --- CORE DEPLOY FUNCTION ---
async def strike_vercel(name, content):
    url = f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}"
    encoded = base64.b64encode(content.encode()).decode()
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "name": name,
        "files": [{"file": "Dockerfile", "data": encoded, "encoding": "base64"}],
        "projectSettings": {"framework": None}
    }
    async with httpx.AsyncClient(http2=True, timeout=60.0) as client:
        try:
            r = await client.post(url, headers=headers, json=payload)
            return r.json() if r.status_code == 200 else {"error": r.text}
        except Exception as e:
            return {"error": str(e)}

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "⚡ <b>VERCEL BRIDGE v12.5 PRO</b> ⚡\n\n"
        "<i>Direct API Strike Engine for Vercel.</i>\n\n"
        "<b>Admin:</b> " + ADMIN_HANDLE + "\n"
        "<b>Status:</b> 🟢 Ready to Deploy",
        parse_mode="HTML", reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "👨‍💻 Developer")
async def show_dev(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Contact Admin", url=f"https://t.me/{ADMIN_HANDLE[1:]}")]])
    await message.answer(f"🔱 <b>Main Developer:</b> {ADMIN_HANDLE}\n<i>Expert in API Decryption & Cloud Striking.</i>", parse_mode="HTML", reply_markup=kb)

@dp.message(F.text == "📊 Stats")
async def show_stats(message: types.Message):
    user_id = message.from_user.id
    user_count = db_stats["users"].get(user_id, 0)
    
    status_text = (
        "📊 <b>SYSTEM STATISTICS</b>\n\n"
        f"🚀 <b>Global Deployments:</b> {db_stats['total_live']}\n"
        f"👤 <b>Your Deployments:</b> {user_count}\n"
        "🛡️ <b>Engine:</b> Vercel v13 (Stable)"
    )
    await message.answer(status_text, parse_mode="HTML")

@dp.message(F.text == "🚀 Deploy Project")
async def ask_deploy(message: types.Message):
    await message.answer("📤 <b>Ready for Strike!</b>\n\nSend me your <b>Dockerfile</b> as a <u>Text Message</u> or <u>Document File</u>.", parse_mode="HTML")

# Handler for both Text and File uploads
@dp.message(lambda message: message.text and message.text.startswith("FROM") or message.document)
async def process_deploy(message: types.Message):
    user = message.from_user
    content = ""

    # Get content from File or Text
    if message.document:
        file_info = await bot.get_file(message.document.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        content = downloaded_file.read().decode('utf-8')
    else:
        content = message.text

    if not content.strip().startswith("FROM"):
        return await message.answer("❌ <b>Invalid Content!</b> Please send a valid Dockerfile.")

    p_name = f"vb-{user.id}-" + ''.join(random.choices(string.ascii_lowercase, k=4))
    status_msg = await message.answer("🔄 <b>Infiltrating Vercel Servers...</b>", parse_mode="HTML")
    
    res = await strike_vercel(p_name, content)
    
    if res and "url" in res:
        db_stats["total_live"] += 1
        db_stats["users"][user.id] = db_stats["users"].get(user.id, 0) + 1
        d_url = f"https://{res['url']}"
        
        await status_msg.edit_text(f"🚀 <b>STRIKE SUCCESSFUL!</b>\n\n🔗 <b>URL:</b> {d_url}\n📂 <b>ID:</b> <code>{res['id']}</code>", parse_mode="HTML")
        
        # Notify Admin
        admin_log = (
            f"🚨 <b>DEPLOY LOG</b>\n"
            f"👤 <b>User:</b> {user.full_name} (@{user.username})\n"
            f"🔗 <b>Link:</b> {d_url}\n"
            f"📊 <b>Total Global:</b> {db_stats['total_live']}"
        )
        await bot.send_message(ADMIN_ID, admin_log, parse_mode="HTML")
    else:
        error_log = res.get("error", "Unknown Timeout")
        await status_msg.edit_text(f"❌ <b>Strike Failed!</b>\n<code>{str(error_log)[:100]}</code>", parse_mode="HTML")

async def main():
    keep_alive()
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
