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
def home(): return "Vercel Bridge ⚡ Pro is Live"

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
HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; LAVA Blaze)"
}

# --- [ UI COMPONENTS ] ---
def main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("📊 Status", "🗑️ Clear Buffer")
    m.row("ℹ️ Help", "👨‍💻 Admin")
    return m

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "⚡ **Vercel Bridge: Production Elite**\n\nAdvanced Scouting & View-Link System Active.", reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    user_id = message.from_user.id
    if user_id not in user_sessions: user_sessions[user_id] = []
    
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    
    if message.document.file_name.endswith(".zip"):
        msg = bot.reply_to(message, "📝 **Enter Project Name for ZIP bundle:**")
        bot.register_next_step_handler(msg, zip_deploy, downloaded)
    else:
        user_sessions[user_id].append({
            "file": message.document.file_name, 
            "data": base64.b64encode(downloaded).decode(), 
            "encoding": "base64"
        })
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Deploy Now", callback_data="ask_name"))
        bot.reply_to(message, f"✅ `{message.document.file_name}` Buffered.", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "ask_name")
def callback_ask_name(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📝 Send: `/deploy <name>`")

@bot.message_handler(commands=['deploy'])
def deploy_cmd(message):
    args = message.text.split()
    if len(args) < 2: return bot.reply_to(message, "❌ Usage: `/deploy <name>`")
    name = args[1].lower().strip().replace(" ", "-")
    msg = bot.reply_to(message, f"🔍 **Scouting Target:** `{name}`...")
    asyncio.run(strike(message, msg, name, user_sessions.get(message.from_user.id, [])))
    user_sessions[message.from_user.id] = []

async def strike(message, msg, name, files):
    try:
        async with httpx.AsyncClient(http2=True, verify=False, timeout=60.0) as client:
            # --- PHASE 0: ADVANCED SCOUTING (Exactly as per your data) ---
            scout_url = f"https://api.vercel.com/v9/projects/{name}?teamId={TEAM_ID}"
            scout_res = await client.get(scout_url, headers=HEADERS)
            
            # 200 means project exists (Not Available)
            if scout_res.status_code == 200:
                bot.edit_message_text(f"❌ **Domain Taken:** `{name}.vercel.app` is already registered in Vercel.\nChoose a new name.", msg.chat.id, msg.message_id)
                user_sessions[message.from_user.id] = files # Save buffer
                return
            
            # 404 means Project Not Found (Available to take)
            if scout_res.status_code != 404:
                bot.edit_message_text(f"⚠️ **Scouting Warning:** Unexpected Response `{scout_res.status_code}`. Proceeding anyway...", msg.chat.id, msg.message_id)

            # --- PHASE 1: STRIKE DEPLOYMENT ---
            bot.edit_message_text("📡 **Domain Available. Launching Strike...**", msg.chat.id, msg.message_id)
            d_res = await client.post(
                f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}", 
                headers=HEADERS, 
                json={"name": name, "files": files, "projectSettings": {"framework": None}, "target": "production"}
            )
            d_data = d_res.json()
            if "id" not in d_data: raise Exception(d_data.get("error", {}).get("message", "Strike Blocked"))
            
            d_id, preview = d_data['id'], d_data['url']

            # --- PHASE 2: PROCESSING POLLING ---
            while True:
                await asyncio.sleep(2)
                s_res = await client.get(f"https://api.vercel.com/v13/deployments/{d_id}?teamId={TEAM_ID}", headers=HEADERS)
                if s_res.json().get('readyState') == 'READY': break

            # --- PHASE 3: PRODUCTION MAPPING ---
            bot.edit_message_text("🔗 **Mapping Production Links...**", msg.chat.id, msg.message_id)
            await client.post(f"https://api.vercel.com/v9/projects/{name}/domains?teamId={TEAM_ID}", headers=HEADERS, json={"name": f"{name}.vercel.app"})
            await client.post(f"https://api.vercel.com/v2/deployments/{d_id}/aliases?teamId={TEAM_ID}", headers=HEADERS, json={"alias": f"{name}.vercel.app"})

            # --- PHASE 4: GENERATE VIEW LINKS ---
            view_links = ""
            for f in files[:5]: # Showing top 5 files to avoid long message
                view_links += f"📄 `{f['file']}`: [View](https://{name}.vercel.app/{f['file']})\n"

            # --- PHASE 5: ELITE SUCCESS OUTPUT ---
            bot.delete_message(msg.chat.id, msg.message_id)
            kb = types.InlineKeyboardMarkup()
            kb.row(types.InlineKeyboardButton("🌐 Main Domain", url=f"https://{name}.vercel.app"))
            kb.row(types.InlineKeyboardButton("🔗 Preview Node", url=f"https://{preview}"))
            
            final_msg = (
                f"🔱 **MISSION ACCOMPLISHED**\n\n"
                f"🚀 **Main:** `https://{name}.vercel.app` \n"
                f"🛰️ **Preview:** `https://{preview}` \n\n"
                f"📂 **View Links:**\n{view_links}"
                f"\n👤 **Developer:** {ADMIN_ID}"
            )
            bot.send_message(message.chat.id, final_msg, reply_markup=kb, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        bot.edit_message_text(f"❌ **System Crash:** `{str(e)}`", msg.chat.id, msg.message_id)

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
                files.append({"file": os.path.relpath(p, ext).replace("\\","/"), "data": base64.b64encode(file.read()).decode(), "encoding": "base64"})
    shutil.rmtree(ext)
    os.remove("t.zip")
    msg = bot.reply_to(message, "🚀 **ZIP Buffer Processed. Scouting...**")
    asyncio.run(strike(message, msg, name, files))

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.infinity_polling()
