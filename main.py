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
def home(): return "Vercel Bridge ⚡ Operational"

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
    bot.send_message(message.chat.id, "⚡ **Vercel Bridge: Strike Engine**\nDomain Scouting & Fixed Mapping Active.", reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    user_id = message.from_user.id
    if user_id not in user_sessions: user_sessions[user_id] = []
    
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    
    if message.document.file_name.endswith(".zip"):
        msg = bot.reply_to(message, "📝 **Enter Project Name for this ZIP bundle:**")
        bot.register_next_step_handler(msg, zip_deploy, downloaded)
    else:
        user_sessions[user_id].append({
            "file": message.document.file_name, 
            "data": base64.b64encode(downloaded).decode(), 
            "encoding": "base64"
        })
        # Deploy Now button ab /deploy command suggest karega jisse name mil sake
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Set Name & Deploy", callback_data="ask_name"))
        bot.reply_to(message, f"✅ `{message.document.file_name}` Added.\nUse `/deploy <name>`", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "ask_name")
def callback_ask_name(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📝 Please send: `/deploy your-project-name`")

@bot.message_handler(commands=['deploy'])
def deploy_cmd(message):
    args = message.text.split()
    if len(args) < 2: return bot.reply_to(message, "❌ Usage: `/deploy <project-name>`")
    name = args[1].lower().strip().replace(" ", "-")
    msg = bot.reply_to(message, f"🔍 Scouting `{name}.vercel.app`...")
    asyncio.run(strike(message, msg, name, user_sessions.get(message.from_user.id, [])))
    user_sessions[message.from_user.id] = []

async def strike(message, msg, name, files):
    try:
        async with httpx.AsyncClient(http2=True, verify=False, timeout=60.0) as client:
            # --- 1. DOMAIN SCOUTING (Accurate Data Check) ---
            scout_url = f"https://api.vercel.com/v4/domains/status?name={name}.vercel.app&teamId={TEAM_ID}"
            scout_res = await client.get(scout_url, headers=HEADERS)
            
            if scout_res.status_code == 200:
                availability = scout_res.json().get("available")
                if availability is False:
                    bot.edit_message_text(f"❌ **Domain Taken:** `{name}.vercel.app` is already in use.\nTry a different name with `/deploy`.", msg.chat.id, msg.message_id)
                    user_sessions[message.from_user.id] = files # Restore buffer
                    return

            # --- 2. EXECUTE DEPLOYMENT ---
            bot.edit_message_text("📡 **Executing Strike...**", msg.chat.id, msg.message_id)
            d_res = await client.post(
                f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}", 
                headers=HEADERS, 
                json={"name": name, "files": files, "projectSettings": {"framework": None}, "target": "production"}
            )
            d_data = d_res.json()
            if "id" not in d_data:
                raise Exception(d_data.get("error", {}).get("message", "Unknown Strike Error"))
            
            d_id, preview = d_data['id'], d_data['url']

            # --- 3. POLLING (Wait for READY) ---
            while True:
                await asyncio.sleep(2)
                s_res = await client.get(f"https://api.vercel.com/v13/deployments/{d_id}?teamId={TEAM_ID}", headers=HEADERS)
                if s_res.json().get('readyState') == 'READY': break

            # --- 4. FIXED MAPPING (Domain Integration) ---
            bot.edit_message_text("🔗 **Mapping Main Domain...**", msg.chat.id, msg.message_id)
            # Link domain to project
            await client.post(f"https://api.vercel.com/v9/projects/{name}/domains?teamId={TEAM_ID}", headers=HEADERS, json={"name": f"{name}.vercel.app"})
            # Apply Alias
            await client.post(f"https://api.vercel.com/v2/deployments/{d_id}/aliases?teamId={TEAM_ID}", headers=HEADERS, json={"alias": f"{name}.vercel.app"})

            # --- 5. SUCCESS ---
            bot.delete_message(msg.chat.id, msg.message_id)
            kb = types.InlineKeyboardMarkup().row(types.InlineKeyboardButton("🌐 Open Main Link", url=f"https://{name}.vercel.app"))
            bot.send_message(message.chat.id, f"🔱 **STRIKE SUCCESSFUL**\n\n🌐 **Main:** `https://{name}.vercel.app` \n🔗 **Preview:** `https://{preview}`", reply_markup=kb, parse_mode="Markdown")

    except Exception as e:
        bot.edit_message_text(f"❌ **Strike Failed:** `{str(e)}`", msg.chat.id, msg.message_id)

def zip_deploy(message, data):
    name = message.text.lower().strip().replace(" ", "-")
    with open("t.zip", "wb") as f: f.write(data)
    ext = f"temp_{message.from_user.id}"
    if not os.path.exists(ext): os.makedirs(ext)
    
    with zipfile.ZipFile("t.zip", 'r') as z: z.extractall(ext)
    files = []
    for r, _, fs in os.walk(ext):
        for f in fs:
            p = os.path.join(r, f)
            with open(p, "rb") as file:
                files.append({
                    "file": os.path.relpath(p, ext).replace("\\","/"), 
                    "data": base64.b64encode(file.read()).decode(), 
                    "encoding": "base64"
                })
    shutil.rmtree(ext)
    os.remove("t.zip")
    msg = bot.reply_to(message, "🚀 **ZIP Detected. Initializing Scouting...**")
    asyncio.run(strike(message, msg, name, files))

# Menu Handlers
@bot.message_handler(func=lambda m: m.text == "📊 Status")
def status_h(m): bot.reply_to(m, "🛰️ **Bridge:** `Operational` \n⚡ **Port:** `10000`")

@bot.message_handler(func=lambda m: m.text == "🗑️ Clear Buffer")
def clear_h(m):
    user_sessions[m.from_user.id] = []
    bot.reply_to(m, "🧹 Buffer Cleared.")

if __name__ == "__main__":
    Thread(target=run_web).start()
    print("⚡ Vercel Bridge Ultimate Live")
    bot.infinity_polling()
