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

# --- RENDER PORT BYPASS (Flask Server) ---
app = Flask('')

@app.route('/')
def home():
    return "Vercel Bridge is Running ⚡"

def run():
    # Render requires port 10000
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURATION ---
API_TOKEN = '8299663322:AAEZZqcqpgJFyi9lmqRCPjPUD35smcHPiL8'
VERCEL_TOKEN = "TYt6xV8Gnr99oJG3FNTcQQmd"
TEAM_ID = "team_IKARugTrm6K77V5MqC2C9XCd"
ADMIN_ID = 6043602577
ADMIN_HANDLE = "@cbxdq"

live_projects_count = 0

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- KEYBOARDS ---
def get_main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Deploy New Project")],
        [KeyboardButton(text="📊 Stats"), KeyboardButton(text="👨‍💻 Developer")]
    ], resize_keyboard=True)

def get_inline_dev():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Contact Admin", url=f"https://t.me/{ADMIN_HANDLE[1:]}")]
    ])

# --- VERCEL DEPLOY LOGIC ---
async def deploy_to_vercel(project_name, docker_content):
    url = f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}"
    encoded_data = base64.b64encode(docker_content.encode()).decode()
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "name": project_name,
        "files": [{"file": "Dockerfile", "data": encoded_data, "encoding": "base64"}],
        "projectSettings": {"framework": None}
    }
    async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        return r.json() if r.status_code == 200 else None

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome = (
        "⚡ <b>WELCOME TO VERCEL BRIDGE</b> ⚡\n\n"
        "Deploy your Dockerfiles to Vercel instantly.\n"
        "Professional. Fast. Secure."
    )
    await message.answer(welcome, parse_mode="HTML", reply_markup=get_main_keyboard())

@dp.message(F.text == "👨‍💻 Developer")
async def show_dev(message: types.Message):
    await message.answer(f"🔱 <b>Developer:</b> {ADMIN_HANDLE}", 
                         parse_mode="HTML", reply_markup=get_inline_dev())

@dp.message(F.text == "🚀 Deploy New Project")
async def ask_file(message: types.Message):
    await message.answer("📥 <b>Send me your Dockerfile text now:</b>", parse_mode="HTML")

@dp.message(F.text.startswith("FROM"))
async def handle_deployment(message: types.Message):
    global live_projects_count
    user = message.from_user
    project_name = f"vb-{user.id}-" + ''.join(random.choices(string.ascii_lowercase, k=4))
    
    status_msg = await message.answer("🔄 <b>Initializing Strike...</b>", parse_mode="HTML")
    result = await deploy_to_vercel(project_name, message.text)
    
    if result:
        live_projects_count += 1
        d_url = f"https://{result['url']}"
        await status_msg.edit_text(f"🚀 <b>LIVE!</b>\n🔗 {d_url}", parse_mode="HTML")
        
        # Admin Notification
        alert = (
            f"🚨 <b>LOG: NEW DEPLOY</b>\n"
            f"👤 {user.full_name}\n"
            f"🆔 <code>{user.id}</code>\n"
            f"🔗 {d_url}\n"
            f"📊 Total: {live_projects_count}"
        )
        await bot.send_message(ADMIN_ID, alert, parse_mode="HTML")
    else:
        await status_msg.edit_text("❌ <b>Deployment Failed!</b>", parse_mode="HTML")

async def main():
    keep_alive() # Starts Flask on Port 10000
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
