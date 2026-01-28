import os
import telebot
import base64
import httpx
import asyncio
import zipfile
import shutil
from flask import Flask
from threading import Thread
from telebot import types

# --- [ RENDER WEB SERVER ] ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Vercel Bridge ⚡ Live"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- [ CONFIG ] ---
BOT_TOKEN = "8299663322:AAFbVh8WZrnlULT47fycTn_OqU32R3JnvEk"
VERCEL_TOKEN = "TYt6xV8Gnr99oJG3FNTcQQmd"
TEAM_ID = "team_IKARugTrm6K77V5MqC2C9XCd"
ADMIN_ID = "@CBXDQ"

bot = telebot.TeleBot(BOT_TOKEN)
user_sessions = {}
HEADERS = {"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"}

# --- [ UI KEYBOARD ] ---
def main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("📊 Status", "🗑️ Clear Buffer")
    m.row("ℹ️ Help", "👨‍💻 Admin")
    return m

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "⚡ **Vercel Bridge Operational**\nMapping fix is active.", reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    user_id = message.from_user.id
    if user_id not in user_sessions: user_sessions[user_id] = []
    
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    
    if message.document.file_name.endswith(".zip"):
        msg = bot.reply_to(message, "📝 **Enter Project Name for ZIP:**")
        bot.register_next_step_handler(msg, zip_deploy, downloaded)
    else:
        user_sessions[user_id].append({"file": message.document.file_name, "data": base64.b64encode(downloaded).decode(), "encoding": "base64"})
        bot.reply_to(message, f"✅ `{message.document.file_name}` Added. Use `/deploy <name>`", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⚡ Deploy Now", callback_data="dp")))

@bot.message_handler(commands=['deploy'])
def deploy_cmd(message):
    args = message.text.split()
    if len(args) < 2: return bot.reply_to(message, "❌ Usage: `/deploy name`")
    name = args[1].lower().replace(" ", "-")
    msg = bot.reply_to(message, f"🔍 scouting `{name}`...")
    asyncio.run(strike(message, msg, name, user_sessions.get(message.from_user.id, [])))
    user_sessions[message.from_user.id] = []

async def strike(message, msg, name, files):
    try:
        async with httpx.AsyncClient(http2=True, verify=False, timeout=60.0) as client:
            # 1. Availability Check
            chk = await client.get(f"https://api.vercel.com/v4/domains/status?name={name}.vercel.app&teamId={TEAM_ID}", headers=HEADERS)
            if chk.status_code == 200 and not chk.json().get("available", True):
                return bot.edit_message_text(f"❌ `{name}.vercel.app` is TAKEN.", msg.chat.id, msg.message_id)

            # 2. Strike Deployment
            bot.edit_message_text("📡 **Executing Strike...**", msg.chat.id, msg.message_id)
            d_res = await client.post(f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}", headers=HEADERS, 
                                     json={"name": name, "files": files, "projectSettings": {"framework": None}, "target": "production"})
            d_data = d_res.json()
            d_id, preview = d_data['id'], d_data['url']

            # 3. Polling
            while True:
                await asyncio.sleep(2)
                s = await client.get(f"https://api.vercel.com/v13/deployments/{d_id}?teamId={TEAM_ID}", headers=HEADERS)
                if s.json().get('readyState') == 'READY': break

            # 4. FIXED MAPPING (Attach domain to project first)
            bot.edit_message_text("🔗 **Synchronizing Domain...**", msg.chat.id, msg.message_id)
            await client.post(f"https://api.vercel.com/v9/projects/{name}/domains?teamId={TEAM_ID}", headers=HEADERS, json={"name": f"{name}.vercel.app"})
            
            # 5. Alias Hit
            await client.post(f"https://api.vercel.com/v2/deployments/{d_id}/aliases?teamId={TEAM_ID}", headers=HEADERS, json={"alias": f"{name}.vercel.app"})

            bot.delete_message(msg.chat.id, msg.message_id)
            kb = types.InlineKeyboardMarkup().row(types.InlineKeyboardButton("🌐 Open Main Link", url=f"https://{name}.vercel.app"))
            bot.send_message(message.chat.id, f"🔱 **STRIKE SUCCESSFUL**\n\n🌐 **Main:** `https://{name}.vercel.app`", reply_markup=kb)

    except Exception as e: bot.edit_message_text(f"❌ Error: {str(e)}", msg.chat.id, msg.message_id)

def zip_deploy(message, data):
    name = message.text.lower().replace(" ", "-")
    with open("t.zip", "wb") as f: f.write(data)
    ext = f"temp_{message.from_user.id}"
    with zipfile.ZipFile("t.zip", 'r') as z: z.extractall(ext)
    files = []
    for r, _, fs in os.walk(ext):
        for f in fs:
            p = os.path.join(r, f)
            with open(p, "rb") as file: files.append({"file": os.path.relpath(p, ext).replace("\\","/"), "data": base64.b64encode(file.read()).decode(), "encoding": "base64"})
    shutil.rmtree(ext)
    os.remove("t.zip")
    asyncio.run(strike(message, bot.reply_to(message, "🚀 ZIP Strike Initiated..."), name, files))

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.infinity_polling()
