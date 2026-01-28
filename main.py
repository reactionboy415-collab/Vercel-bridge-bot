import os
import asyncio
import base64
import httpx
import shutil
import zipfile
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- [ RENDER PORT FIX ] ---
# Render needs a web server to stay alive
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Vercel Bridge ⚡ is Running..."

def run_web():
    # Render automatically provides PORT 10000
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- [ CREDITS & CONFIG ] ---
# Double check these from my.telegram.org
API_ID = 25139739 
API_HASH = "81427282b0f496156e9c0c3258838334"
BOT_TOKEN = "7864871444:AAFe3oR1p0DqS1H9y2fS0W_7V107U2_Nstk"

VERCEL_TOKEN = "TYt6xV8Gnr99oJG3FNTcQQmd"
TEAM_ID = "team_IKARugTrm6K77V5MqC2C9XCd"
ADMIN_ID = "@CBXDQ"

HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; LAVA Blaze)",
    "Content-Type": "application/json"
}

app = Client("VercelBridge", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_sessions = {}

# --- [ KEYBOARDS ] ---
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("📊 Status"), KeyboardButton("🗑️ Clear Buffer")],
     [KeyboardButton("ℹ️ Help"), KeyboardButton("👨‍💻 Admin")]],
    resize_keyboard=True
)

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("⚡ **Vercel Bridge** Operational.", reply_markup=MAIN_KEYBOARD)

# ... (Existing Document & Deploy Logic remains the same) ...
# Note: Ensure execute_deployment logic from previous version is pasted here

@app.on_message(filters.command("deploy"))
async def deploy_trigger(client, message):
    user_id = message.from_user.id
    if user_id not in user_sessions or not user_sessions[user_id]:
        return await message.reply_text("❌ Buffer empty.")
    proj_name = message.command[1].lower().replace(" ", "-") if len(message.command) > 1 else f"strike-{message.id}"
    msg = await message.reply_text("🚀 **Initializing Deployment...**")
    await execute_deployment(message, msg, proj_name, user_sessions[user_id])
    user_sessions[user_id] = []

async def execute_deployment(message, msg, proj_name, payload_files):
    try:
        async with httpx.AsyncClient(http2=True, verify=False, timeout=60.0) as session:
            await msg.edit("📡 **Syncing...**")
            d_res = await session.post(
                f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}",
                headers=HEADERS,
                json={"name": proj_name, "files": payload_files, "projectSettings": {"framework": None}, "target": "production"}
            )
            d_data = d_res.json()
            d_id, preview = d_data['id'], d_data['url']
            
            while True:
                await asyncio.sleep(2)
                s_res = await session.get(f"https://api.vercel.com/v13/deployments/{d_id}?teamId={TEAM_ID}", headers=HEADERS)
                if s_res.json().get('readyState') == 'READY': break
            
            await session.post(f"https://api.vercel.com/v2/deployments/{d_id}/aliases?teamId={TEAM_ID}", 
                              headers=HEADERS, json={"alias": f"{proj_name}.vercel.app"})
            
            await msg.delete()
            await message.reply_text(f"⚡ **Success**\n🌐 `https://{proj_name}.vercel.app`", 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Open", url=f"https://{proj_name}.vercel.app")]]))
    except Exception as e:
        await msg.edit(f"❌ Error: {str(e)}")

# --- [ MAIN EXECUTION ] ---
if __name__ == "__main__":
    # Start Web Server for Render
    Thread(target=run_web).start()
    print("⚡ Web Server Active on Port 10000")
    
    # Start Bot
    print("⚡ Vercel Bridge Bot Starting...")
    app.run()
