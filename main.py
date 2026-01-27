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

# --- WEB SERVER FOR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "CLOUD ENGINE ACTIVE"
def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

# --- FSM STATES ---
class DeployState(StatesGroup):
    waiting_for_name = State()
    waiting_for_file = State()

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
db_stats = {"total": 0}

# --- KEYBOARD ---
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Create New Instance")],
        [KeyboardButton(text="📊 Engine Stats"), KeyboardButton(text="👨‍💻 Developer")]
    ], resize_keyboard=True)

# --- VERCEL UTILS ---
async def is_name_available(name):
    url = f"https://api.vercel.com/v9/projects/{name}?teamId={TEAM_ID}"
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers)
        return r.status_code == 404

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🔱 <b>OVERCHAT CLOUD ENGINE v16.0</b> 🔱\n\n"
        "<i>Enterprise-grade automated deployment system.</i>\n\n"
        "🟢 <b>Core Status:</b> Operational\n"
        "🛰️ <b>Network:</b> Optimized",
        parse_mode="HTML", reply_markup=get_main_kb()
    )

@dp.message(F.text == "🚀 Create New Instance")
async def start_deploy(message: types.Message, state: FSMContext):
    await message.answer("🆔 <b>Enter Project Name:</b>\n<i>(e.g., my-cool-api)</i>", parse_mode="HTML")
    await state.set_state(DeployState.waiting_for_name)

@dp.message(DeployState.waiting_for_name)
async def handle_name(message: types.Message, state: FSMContext):
    name = message.text.lower().replace(" ", "-")
    msg = await message.answer("🔍 <b>Syncing with Global Registry...</b>", parse_mode="HTML")
    
    if await is_name_available(name):
        await state.update_data(p_name=name)
        await msg.edit_text(f"✅ <b>Name Available:</b> <code>{name}</code>\n\n📥 <b>Now send your Source Code or File:</b>", parse_mode="HTML")
        await state.set_state(DeployState.waiting_for_file)
    else:
        await msg.edit_text("❌ <b>Identity Conflict:</b> Name already in use.\n\nPlease enter a different name:", parse_mode="HTML")

@dp.message(DeployState.waiting_for_file)
async def handle_file(message: types.Message, state: FSMContext):
    data = await state.get_data()
    p_name = data.get("p_name")
    user = message.from_user
    
    content, f_name = "", "index.html"
    if message.document:
        file_info = await bot.get_file(message.document.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        content = downloaded.read().decode('utf-8', errors='ignore')
        f_name = message.document.file_name
    else:
        content = message.text
        if "FROM" in content: f_name = "Dockerfile"

    status_msg = await message.answer("⚙️ <b>Configuring Environment...</b>", parse_mode="HTML")
    await asyncio.sleep(1)
    await status_msg.edit_text("📡 <b>Transferring Data Packets...</b>", parse_mode="HTML")

    # --- DEPLOYMENT ---
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
                await status_msg.edit_text("🛰️ <b>Finalizing Production Build...</b>", parse_mode="HTML")
                await asyncio.sleep(1)
                
                db_stats["total"] += 1
                # Vercel gives aliases, we pick the first production one
                prod_url = f"https://{p_name}.vercel.app" 
                
                final_text = (
                    "🔱 <b>INSTANCE LIVE!</b>\n\n"
                    f"🔗 <b>Endpoint:</b> {prod_url}\n"
                    "🛡️ <b>Protocol:</b> <code>HTTPS/TLS-1.3</code>\n"
                    "📊 <b>Status:</b> <code>STABLE</code>"
                )
                await status_msg.edit_text(final_text, parse_mode="HTML", disable_web_page_preview=True)
                await bot.send_message(ADMIN_ID, f"🚨 <b>DEPLOY LOG:</b> {user.full_name} created {prod_url}")
                await state.clear()
            else:
                await status_msg.edit_text(f"❌ <b>ENGINE ERROR:</b> <code>{r.status_code}</code>")
        except Exception as e:
            await status_msg.edit_text(f"❌ <b>CRITICAL FAILURE:</b> <code>{str(e)[:50]}</code>")

@dp.message(F.text == "📊 Engine Stats")
async def show_stats(message: types.Message):
    await message.answer(f"📊 <b>ENGINE STATUS</b>\n\n🚀 <b>Total Instances:</b> {db_stats['total']}\n🟢 <b>Load:</b> Normal", parse_mode="HTML")

@dp.message(F.text == "👨‍💻 Developer")
async def show_dev(message: types.Message):
    await message.answer(f"🔱 <b>Developer:</b> {ADMIN_HANDLE}", parse_mode="HTML")

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
