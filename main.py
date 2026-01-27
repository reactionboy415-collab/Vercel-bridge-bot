import logging
import asyncio
import base64
import httpx
import random
import string
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- ENGINE CONFIG (PRE-CONFIGURED) ---
API_TOKEN = '8299663322:AAEZZqcqpgJFyi9lmqRCPjPUD35smcHPiL8'
VERCEL_TOKEN = "TYt6xV8Gnr99oJG3FNTcQQmd"
TEAM_ID = "team_IKARugTrm6K77V5MqC2C9XCd"
ADMIN_ID = 6043602577
ADMIN_HANDLE = "@cbxdq"

# --- RENDER PORT BYPASS ---
app = Flask('')
@app.route('/')
def home(): return "OVERCHAT ENGINE v16.5 ACTIVE"
def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

# --- FSM STATES ---
class DeployState(StatesGroup):
    waiting_for_name = State()
    waiting_for_file = State()

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- BROWSER REPLICATION HEADERS ---
BROWSER_HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; LAVA Blaze) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.7559.59 Mobile Safari/537.36",
    "Origin": "https://bj-vercel-bridge.vercel.app",
    "Referer": "https://bj-vercel-bridge.vercel.app/",
    "Content-Type": "application/json",
    "Accept": "*/*"
}

# --- CORE UTILITIES ---

async def check_identity_availability(name):
    """Checks if the project name is free (404 = Available)"""
    url = f"https://api.vercel.com/v9/projects/{name}?teamId={TEAM_ID}"
    async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
        try:
            await client.options(url, headers=BROWSER_HEADERS)
            r = await client.get(url, headers=BROWSER_HEADERS)
            return r.status_code == 404
        except: return False

async def run_security_scan(content):
    """Runs the payload through the Phishing Protector"""
    url = "https://bj-phishing-protector.vercel.app/protect"
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        try:
            r = await client.post(url, content=content, headers={"Content-Type": "text/plain"})
            data = r.json()
            return data.get("results", {}).get("can_upload", True)
        except: return True

# --- KEYBOARDS ---
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Initialize Instance")],
        [KeyboardButton(text="📊 Engine Stats"), KeyboardButton(text="👨‍💻 Developer")]
    ], resize_keyboard=True)

# --- HANDLERS ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🔱 <b>OVERCHAT CLOUD ENGINE v16.5</b> 🔱\n\n"
        "<i>Enterprise-grade Deployment Infrastructure.</i>\n\n"
        "🟢 <b>Status:</b> Ready\n"
        "🛡️ <b>Security:</b> Active",
        parse_mode="HTML", reply_markup=get_main_kb()
    )

@dp.message(F.text == "🚀 Initialize Instance")
async def start_deploy(message: types.Message, state: FSMContext):
    await message.answer("🆔 <b>Provide Project Identity:</b>\n<i>(Min 4 chars, no spaces)</i>", parse_mode="HTML")
    await state.set_state(DeployState.waiting_for_name)

@dp.message(DeployState.waiting_for_name)
async def handle_name(message: types.Message, state: FSMContext):
    name = message.text.lower().strip().replace(" ", "-")
    status = await message.answer("🔍 <b>Analyzing Global Registry...</b>", parse_mode="HTML")
    
    if await check_identity_availability(name):
        await state.update_data(p_name=name)
        await status.edit_text(f"✅ <b>Identity Verified:</b> <code>{name}</code>\n\n📥 <b>Upload Payload (Code/File):</b>", parse_mode="HTML")
        await state.set_state(DeployState.waiting_for_file)
    else:
        await status.edit_text("❌ <b>Identity Conflict:</b> Name already in use.\n\nTry another name:", parse_mode="HTML")

@dp.message(DeployState.waiting_for_file)
async def handle_file(message: types.Message, state: FSMContext):
    data = await state.get_data()
    p_name = data.get("p_name")
    
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

    status_msg = await message.answer("⚙️ <b>Configuring Environment...</b>", parse_mode="HTML")
    
    # 1. Security Scan
    if not await run_security_scan(content):
        return await status_msg.edit_text("❌ <b>Security Violation:</b> Payload rejected by Protector.")

    await status_msg.edit_text("📡 <b>Synchronizing Production Link...</b>", parse_mode="HTML")

    # 2. Vercel Strike
    url = f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}"
    encoded_data = base64.b64encode(content.encode()).decode()
    
    payload = {
        "name": p_name,
        "files": [{"file": f_name, "data": encoded_data, "encoding": "base64"}],
        "projectSettings": {"framework": None}
    }

    async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
        try:
            await client.options(url, headers=BROWSER_HEADERS)
            r = await client.post(url, headers=BROWSER_HEADERS, json=payload)
            
            if r.status_code == 200:
                res = r.json()
                # Extracting the correct Production Alias
                prod_url = f"https://{res['alias'][0]}"
                
                final_msg = (
                    "🔱 <b>INSTANCE LIVE!</b>\n\n"
                    f"🔗 <b>Endpoint:</b> {prod_url}\n"
                    "🛡️ <b>Status:</b> <code>LIVE_PRODUCTION</code>\n"
                    "📊 <b>Region:</b> <code>Global-Edge</code>"
                )
                await status_msg.edit_text(final_msg, parse_mode="HTML", disable_web_page_preview=True)
                await bot.send_message(ADMIN_ID, f"🚨 <b>DEPLOY LOG:</b> {p_name} | {prod_url}")
                await state.clear()
            else:
                await status_msg.edit_text(f"❌ <b>Deployment Error:</b> {r.status_code}\n<code>{r.text[:100]}</code>")
        except Exception as e:
            await status_msg.edit_text(f"❌ <b>Core Failure:</b> <code>{str(e)[:50]}</code>")

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
