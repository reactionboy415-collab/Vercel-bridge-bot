import logging
import asyncio
import base64
import httpx
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- ENGINE CONFIG ---
API_TOKEN = '8299663322:AAEZZqcqpgJFyi9lmqRCPjPUD35smcHPiL8'
VERCEL_TOKEN = "TYt6xV8Gnr99oJG3FNTcQQmd"
TEAM_ID = "team_IKARugTrm6K77V5MqC2C9XCd"
ADMIN_ID = 6043602577
ADMIN_HANDLE = "@cbxdq"

# --- RENDER WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "ENGINE v16.1 ONLINE"
def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

class DeployState(StatesGroup):
    waiting_for_name = State()
    waiting_for_file = State()

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- HELPER: NAME AVAILABILITY (Based on your Log) ---
async def check_name(name):
    url = f"https://api.vercel.com/v9/projects/{name}?teamId={TEAM_ID}"
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url, headers=headers)
        # As per your log: 404 means {"error":{"code":"not_found"...}} which is GOOD.
        return r.status_code == 404

# --- HELPER: PHISHING PROTECTOR (Based on your Log) ---
async def scan_payload(content):
    url = "https://bj-phishing-protector.vercel.app/protect"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(url, content=content, headers={"Content-Type": "text/plain"})
            data = r.json()
            return data.get("results", {}).get("can_upload", True)
        except:
            return True # Fallback if scanner is down

# --- KEYBOARD ---
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Create Instance")],
        [KeyboardButton(text="📊 Engine Stats"), KeyboardButton(text="👨‍💻 Developer")]
    ], resize_keyboard=True)

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🔱 <b>OVERCHAT CLOUD ENGINE v16.1</b>\n\n"
        "<i>Protocol: Direct Strike Implementation</i>\n"
        "🟢 Status: <b>Operational</b>",
        parse_mode="HTML", reply_markup=get_main_kb()
    )

@dp.message(F.text == "🚀 Create Instance")
async def start_deploy(message: types.Message, state: FSMContext):
    await message.answer("🆔 <b>Set Instance Identity:</b>\n(Enter desired project name)", parse_mode="HTML")
    await state.set_state(DeployState.waiting_for_name)

@dp.message(DeployState.waiting_for_name)
async def handle_name(message: types.Message, state: FSMContext):
    name = message.text.lower().replace(" ", "-")
    status = await message.answer("🔍 <b>Verifying Identity Availability...</b>", parse_mode="HTML")
    
    if await check_name(name):
        await state.update_data(p_name=name)
        await status.edit_text(f"✅ <b>Identity Verified:</b> <code>{name}</code>\n\n📥 <b>Upload Source Code / File:</b>", parse_mode="HTML")
        await state.set_state(DeployState.waiting_for_file)
    else:
        await status.edit_text("❌ <b>Identity Conflict:</b> Name already exists in Cloud Database.\n\nTry another name:", parse_mode="HTML")

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

    status_msg = await message.answer("🧪 <b>Running Phishing Protection Scan...</b>", parse_mode="HTML")
    
    # BJ-Protector Call
    if not await scan_payload(content):
        return await status_msg.edit_text("❌ <b>Payload Rejected:</b> Malicious code signature detected.")

    await status_msg.edit_text("🛰️ <b>Initiating Cloud Strike...</b>", parse_mode="HTML")

    # Final Deployment v13
    url = f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}"
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "name": p_name,
        "files": [{"file": f_name, "data": base64.b64encode(content.encode()).decode(), "encoding": "base64"}],
        "projectSettings": {"framework": None}
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            r = await client.post(url, headers=headers, json=payload)
            if r.status_code == 200:
                await status_msg.edit_text("🔱 <b>STRIKE SUCCESSFUL!</b>", parse_mode="HTML")
                prod_url = f"https://{p_name}.vercel.app"
                
                await message.answer(
                    f"🔗 <b>Access Point:</b> {prod_url}\n"
                    f"🛡️ <b>Status:</b> <code>LIVE_PRODUCTION</code>",
                    parse_mode="HTML", disable_web_page_preview=True
                )
                await bot.send_message(ADMIN_ID, f"🚨 <b>LOG:</b> {message.from_user.full_name} deployed {prod_url}")
                await state.clear()
            else:
                await status_msg.edit_text(f"❌ <b>Cloud Error:</b> {r.status_code}")
        except Exception as e:
            await status_msg.edit_text(f"❌ <b>System Crash:</b> {str(e)[:50]}")

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
